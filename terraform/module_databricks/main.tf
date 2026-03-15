resource "azurerm_network_security_group" "nsg_public" {
  name                = "nsg-${var.workspace_name}-public"
  location            = var.location
  resource_group_name = var.resource_group_name
}

resource "azurerm_network_security_group" "nsg_private" {
  name                = "nsg-${var.workspace_name}-private"
  location            = var.location
  resource_group_name = var.resource_group_name
}

resource "azurerm_network_security_group" "nsg_pe" {
  name                = "nsg-${var.workspace_name}-pe"
  location            = var.location
  resource_group_name = var.resource_group_name
  security_rule {
    name                        = "allow-inbound-from-dbx-public"
    priority                    = 1000
    direction                   = "Inbound"
    access                      = "Allow"
    protocol                    = "Tcp"
    source_address_prefixes     = var.public_subnet_prefix
    destination_address_prefixes = var.pe_subnet_prefix
    source_port_range           = "*"
    destination_port_range      = "443"
  }

  security_rule {
    name                        = "allow-inbound-from-dbx-private"
    priority                    = 1100
    direction                   = "Inbound"
    access                      = "Allow"
    protocol                    = "Tcp"
    source_address_prefixes     = var.private_subnet_prefix
    destination_address_prefixes = var.pe_subnet_prefix
    source_port_range           = "*"
    destination_port_range      = "443"
  }

  security_rule {
    name                        = "deny-inbound-all"
    priority                    = 4096
    direction                   = "Inbound"
    access                      = "Deny"
    protocol                    = "*"
    source_address_prefix       = "*"
    destination_address_prefix  = "*"
    source_port_range           = "*"
    destination_port_range      = "*"
  }
  security_rule {
    name                       = "deny-outbound-internet"
    priority                   = 1000
    direction                  = "Outbound"
    access                     = "Deny"
    protocol                   = "*"
    source_address_prefix      = "*"
    destination_address_prefix = "Internet"
    source_port_range          = "*"
    destination_port_range     = "*"
  }
}

resource "azurerm_virtual_network" "vnet" {
  name                = "vnet-${var.workspace_name}"
  address_space       = var.vnet_address_space
  location            = var.location
  resource_group_name = var.resource_group_name
}

resource "azurerm_subnet" "public" {
  name                 = "public-subnet"
  resource_group_name  = var.resource_group_name
  virtual_network_name = azurerm_virtual_network.vnet.name
  address_prefixes     = var.public_subnet_prefix

  delegation {
    name = "databricks-del-public"
    service_delegation {
      name    = "Microsoft.Databricks/workspaces"
      actions = ["Microsoft.Network/virtualNetworks/subnets/join/action", "Microsoft.Network/virtualNetworks/subnets/prepareNetworkPolicies/action", "Microsoft.Network/virtualNetworks/subnets/unprepareNetworkPolicies/action"]
    }
  }
}

resource "azurerm_subnet" "private" {
  name                 = "private-subnet"
  resource_group_name  = var.resource_group_name
  virtual_network_name = azurerm_virtual_network.vnet.name
  address_prefixes     = var.private_subnet_prefix

  delegation {
    name = "databricks-del-private"
    service_delegation {
      name    = "Microsoft.Databricks/workspaces"
      actions = ["Microsoft.Network/virtualNetworks/subnets/join/action", "Microsoft.Network/virtualNetworks/subnets/prepareNetworkPolicies/action", "Microsoft.Network/virtualNetworks/subnets/unprepareNetworkPolicies/action"]
    }
  }
}

resource "azurerm_subnet" "pe_subnet" {
  name                 = "subnet-pe"
  resource_group_name  = var.resource_group_name
  virtual_network_name = azurerm_virtual_network.vnet.name
  address_prefixes     = var.pe_subnet_prefix
}

resource "azurerm_subnet_network_security_group_association" "public" {
  subnet_id                 = azurerm_subnet.public.id
  network_security_group_id = azurerm_network_security_group.nsg_public.id
}

resource "azurerm_subnet_network_security_group_association" "private" {
  subnet_id                 = azurerm_subnet.private.id
  network_security_group_id = azurerm_network_security_group.nsg_private.id
}

resource "azurerm_subnet_network_security_group_association" "pe" {
  subnet_id                 = azurerm_subnet.pe_subnet.id
  network_security_group_id = azurerm_network_security_group.nsg_pe.id
}

# this needs to be connected to the storage (databricks
resource "azurerm_databricks_access_connector" "this" {
  name                = "ac-${var.workspace_name}"
  location            = var.location
  resource_group_name = var.resource_group_name

  identity {
    type = "SystemAssigned" 
  }
}

output "access_connector_id" {
  value = azurerm_databricks_access_connector.this.id
}


resource "azurerm_databricks_workspace" "this" {
  name                        = var.workspace_name
  resource_group_name         = var.resource_group_name
  location                    = var.location
  sku                         = "premium"
  managed_resource_group_name = "${var.workspace_name}-managed-rg"

  custom_parameters {
    no_public_ip        = true
    virtual_network_id  = azurerm_virtual_network.vnet.id
    public_subnet_name  = azurerm_subnet.public.name
    private_subnet_name = azurerm_subnet.private.name

    public_subnet_network_security_group_association_id  = azurerm_subnet_network_security_group_association.public.id
    private_subnet_network_security_group_association_id = azurerm_subnet_network_security_group_association.private.id
  }
}

data "azurerm_storage_account" "st" {
  name                = var.storage_account_name
  resource_group_name = var.resource_group_name
}

resource "azurerm_private_dns_zone" "blob" {
  name                = "privatelink.blob.core.windows.net"
  resource_group_name = var.resource_group_name
}

resource "azurerm_private_dns_zone" "queue" {
  name                = "privatelink.queue.core.windows.net"
  resource_group_name = var.resource_group_name
}

resource "azurerm_private_dns_zone" "vault" {
  name                = "privatelink.vaultcore.azure.net"
  resource_group_name = var.resource_group_name
}

resource "azurerm_private_dns_zone_virtual_network_link" "blob" {
  name                  = "${var.workspace_name}-blob-link"
  resource_group_name   = var.resource_group_name
  private_dns_zone_name = azurerm_private_dns_zone.blob.name
  virtual_network_id    = azurerm_virtual_network.vnet.id
}

resource "azurerm_private_dns_zone_virtual_network_link" "queue" {
  name                  = "${var.workspace_name}-queue-link"
  resource_group_name   = var.resource_group_name
  private_dns_zone_name = azurerm_private_dns_zone.queue.name
  virtual_network_id    = azurerm_virtual_network.vnet.id
}

resource "azurerm_private_dns_zone_virtual_network_link" "vault" {
  name                  = "${var.workspace_name}-vault-link"
  resource_group_name   = var.resource_group_name
  private_dns_zone_name = azurerm_private_dns_zone.vault.name
  virtual_network_id    = azurerm_virtual_network.vnet.id
}

resource "azurerm_private_endpoint" "st_pe" {
  name                = "pe-st-${var.workspace_name}"
  location            = var.location
  resource_group_name = var.resource_group_name
  subnet_id           = azurerm_subnet.pe_subnet.id

  private_service_connection {
    name                           = "psc-st"
    private_connection_resource_id = data.azurerm_storage_account.st.id
    subresource_names              = ["blob"]
    is_manual_connection           = false
  }

  private_dns_zone_group {
    name                 = "dns-group-st"
    private_dns_zone_ids = [azurerm_private_dns_zone.blob.id]
  }
}

resource "azurerm_private_endpoint" "queue_pe" {
  name                = "pe-queue-${var.workspace_name}"
  location            = var.location
  resource_group_name = var.resource_group_name
  subnet_id           = azurerm_subnet.pe_subnet.id

  private_service_connection {
    name                           = "psc-queue"
    private_connection_resource_id = data.azurerm_storage_account.st.id
    subresource_names              = ["queue"]
    is_manual_connection           = false
  }

  private_dns_zone_group {
    name                 = "dns-group-queue"
    private_dns_zone_ids = [azurerm_private_dns_zone.queue.id]
  }
}

resource "azurerm_private_endpoint" "kv_pe" {
  name                = "pe-kv-${var.workspace_name}"
  location            = var.location
  resource_group_name = var.resource_group_name
  subnet_id           = azurerm_subnet.pe_subnet.id

  private_service_connection {
    name                           = "psc-kv"
    private_connection_resource_id = var.key_vault_id
    subresource_names              = ["vault"]
    is_manual_connection           = false
  }

  private_dns_zone_group {
    name                 = "dns-group-kv"
    private_dns_zone_ids = [azurerm_private_dns_zone.vault.id]
  }
}

resource "azurerm_role_assignment" "blob_data_contributor" {
  scope                = data.azurerm_storage_account.st.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_databricks_access_connector.this.identity[0].principal_id
}

resource "azurerm_role_assignment" "queue_data_contributor" {
  scope                = data.azurerm_storage_account.st.id
  role_definition_name = "Storage Queue Data Contributor"
  principal_id         = azurerm_databricks_access_connector.this.identity[0].principal_id
}
