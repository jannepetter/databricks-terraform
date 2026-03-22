locals {
  tags = {
    environment = var.environment
    project     = var.app_name
  }
}

# ---- reference existing spoke vnet (created in bash script) ----
data "azurerm_virtual_network" "spoke" {
  name                = "vnet-spoke-${var.app_name}-${var.environment}-${var.location}"
  resource_group_name = var.resource_group_name
}

# ---- reference existing hub vnet ----
data "azurerm_virtual_network" "hub" {
  name                = "vnet-hub-${var.app_name}-${var.location}"
  resource_group_name = var.hub_resource_group_name
}

# ---- vnet peering: spoke -> hub ----
resource "azurerm_virtual_network_peering" "spoke_to_hub" {
  name                         = "peer-spoke-to-hub-${var.environment}"
  resource_group_name          = var.resource_group_name
  virtual_network_name         = data.azurerm_virtual_network.spoke.name
  remote_virtual_network_id    = data.azurerm_virtual_network.hub.id
  allow_virtual_network_access = true
  allow_forwarded_traffic      = true
}

# ---- vnet peering: hub -> spoke ----
resource "azurerm_virtual_network_peering" "hub_to_spoke" {
  name                         = "peer-hub-to-spoke-${var.environment}"
  resource_group_name          = var.hub_resource_group_name
  virtual_network_name         = data.azurerm_virtual_network.hub.name
  remote_virtual_network_id    = data.azurerm_virtual_network.spoke.id
  allow_virtual_network_access = true
  allow_forwarded_traffic      = true
}

data "azurerm_private_dns_zone" "vault" {
  name                = "privatelink.vaultcore.azure.net"
  resource_group_name = var.hub_resource_group_name
}

resource "azurerm_private_dns_zone_virtual_network_link" "vault" {
  name                  = "dnslink-spoke-${var.environment}-vault"
  resource_group_name   = var.hub_resource_group_name
  private_dns_zone_name = data.azurerm_private_dns_zone.vault.name
  virtual_network_id    = data.azurerm_virtual_network.spoke.id
  registration_enabled  = false
  tags                  = local.tags
}

# ---- reference existing access connector ----
data "azurerm_databricks_access_connector" "this" {
  name                = "ac-adb-${var.app_name}-${var.environment}-${var.p_version}"
  resource_group_name = var.resource_group_name
}

# ---- reference existing metastore storage (in hub) ----
data "azurerm_storage_account" "metastore" {
  name                = var.metastore_storage_account_name
  resource_group_name = var.hub_resource_group_name
}

# ---- reference existing queue storage ----
data "azurerm_storage_account" "queue" {
  name                = var.queue_storage_account_name
  resource_group_name = var.resource_group_name
}

data "azurerm_key_vault" "kv" {
  name                = "kv-${var.app_name}-base"
  resource_group_name = var.hub_resource_group_name
}

# ---- role assignments: metastore storage ----
resource "azurerm_role_assignment" "metastore_blob_contributor" {
  scope                = data.azurerm_storage_account.metastore.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = data.azurerm_databricks_access_connector.this.identity[0].principal_id
}

resource "azurerm_role_assignment" "metastore_acc_contributor" {
  scope                = data.azurerm_storage_account.metastore.id
  role_definition_name = "Storage Account Contributor"
  principal_id         = data.azurerm_databricks_access_connector.this.identity[0].principal_id
}

resource "azurerm_role_assignment" "metastore_queue_contributor" {
  scope                = data.azurerm_storage_account.metastore.id
  role_definition_name = "Storage Queue Data Contributor"
  principal_id         = data.azurerm_databricks_access_connector.this.identity[0].principal_id
}

resource "azurerm_role_assignment" "metastore_es_contributor" {
  scope                = data.azurerm_storage_account.metastore.id
  role_definition_name = "EventGrid EventSubscription Contributor"
  principal_id         = data.azurerm_databricks_access_connector.this.identity[0].principal_id
}

resource "azurerm_role_assignment" "blob_delegator" {
  scope                = data.azurerm_storage_account.metastore.id
  role_definition_name = "Storage Blob Delegator"
  principal_id         = data.azurerm_databricks_access_connector.this.identity[0].principal_id
}
resource "azurerm_role_assignment" "queue_data_contributor" {
  scope                = data.azurerm_storage_account.queue.id
  role_definition_name = "Storage Queue Data Contributor"
  principal_id         = data.azurerm_databricks_access_connector.this.identity[0].principal_id
}

resource "azurerm_role_assignment" "kv_secrets_user" {
  scope                = data.azurerm_key_vault.kv.id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = data.azurerm_databricks_access_connector.this.identity[0].principal_id
}

