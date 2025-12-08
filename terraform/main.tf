terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "=4.27.0"
    }
    azuread = {
      source  = "hashicorp/azuread"
      version = "3.7.0"
    }
  }
}

provider "azurerm" {
  features {}
  subscription_id = var.SUBSCRIPTION_ID
}
provider "azuread" {}

variable "resource_group_name" { default = "rg-databricks-demo" }
variable "location" { default = "northeurope" }
variable "workspace_name" { default = "adb-demo-workspace" }
variable "pricing_tier" { default = "premium" }
variable "storage_account_name" {
  default = "adlsdbdemo123" # MUST be globally unique
}
variable "container_name" {
  default = "datalake"
}

data "azurerm_subscription" "current" {
  subscription_id = var.SUBSCRIPTION_ID
}

resource "azurerm_resource_group" "rg" {
  name     = var.resource_group_name
  location = var.location
}

########################################
# ADLS Gen2 Storage Account (Required for Delta)
########################################
resource "azurerm_storage_account" "adls" {
  name                     = var.storage_account_name
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = azurerm_resource_group.rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  account_kind             = "StorageV2"

  # Required for Delta Lake (hierarchical namespace)
  is_hns_enabled = true
  #   public_network_access_enabled = false # for prod and private endpoints
}

resource "azurerm_storage_container" "container" {
  name                  = var.container_name
  storage_account_id    = azurerm_storage_account.adls.id
  container_access_type = "private"
}

resource "azurerm_databricks_workspace" "adb" {
  name                = var.workspace_name
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  sku                 = var.pricing_tier
}

resource "azurerm_key_vault" "kv" {
  name                        = "demo-kv-12345"
  resource_group_name         = azurerm_resource_group.rg.name
  location                    = azurerm_resource_group.rg.location
  tenant_id                   = data.azurerm_subscription.current.tenant_id
  sku_name                    = "standard"
  purge_protection_enabled    = false
  access_policy {
    tenant_id = data.azurerm_client_config.current.tenant_id
    object_id = data.azurerm_client_config.current.object_id

    secret_permissions = ["Get", "Set", "List","Delete","Purge"]
  }
}

data "azurerm_client_config" "current" {}

resource "azuread_application" "app" {
  display_name = "my-joo-app"
}

resource "azuread_service_principal" "sp" {
  client_id = azuread_application.app.client_id
}

resource "azuread_service_principal_password" "sp_pwd" {
  service_principal_id = azuread_service_principal.sp.id
}
resource "azurerm_key_vault_secret" "sp_secret" {
  name         = "client-secret"
  value        = azuread_service_principal_password.sp_pwd.value
  key_vault_id = azurerm_key_vault.kv.id

  depends_on = [
    azurerm_key_vault.kv
  ]
}

resource "azurerm_key_vault_secret" "client_id" {
  name         = "client-id"
  value        = azuread_application.app.client_id
  key_vault_id = azurerm_key_vault.kv.id

  depends_on = [
    azurerm_key_vault.kv
  ]
}
resource "azurerm_key_vault_secret" "tenant_id" {
  name         = "tenant-id"
  value        = data.azurerm_subscription.current.tenant_id
  key_vault_id = azurerm_key_vault.kv.id

  depends_on = [
    azurerm_key_vault.kv
  ]
}

resource "azurerm_role_assignment" "adb_storage_blob_data_contributor" {
  scope                = azurerm_storage_account.adls.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azuread_service_principal.sp.object_id
}

output "databricks_url" {
  value = azurerm_databricks_workspace.adb.workspace_url
}

output "delta_storage_path" {
  value = "abfss://${var.container_name}@${var.storage_account_name}.dfs.core.windows.net"
}


output "databricks_client_id" {
  value = azuread_application.app.client_id
}
