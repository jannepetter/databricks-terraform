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

data "azurerm_subscription" "current" {
  subscription_id = var.SUBSCRIPTION_ID
}

resource "azurerm_resource_group" "rg" {
  name     = var.resource_group_name
  location = var.location
}

resource "azurerm_databricks_workspace" "adb" {
  name                = var.workspace_name
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  sku                 = var.pricing_tier
}

resource "azurerm_key_vault" "kv" {
  name                        = "demo-kv-123456"
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

resource "azurerm_key_vault_secret" "tenant_id" {
  name         = "tenant-id"
  value        = data.azurerm_subscription.current.tenant_id
  key_vault_id = azurerm_key_vault.kv.id

  depends_on = [
    azurerm_key_vault.kv
  ]
}

output "databricks_url" {
  value = azurerm_databricks_workspace.adb.workspace_url
}
