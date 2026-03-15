terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "=4.27.0"
    }
  }
}

provider "azurerm" {
  features {}
  subscription_id = var.SUBSCRIPTION_ID
}

variable "SUBSCRIPTION_ID" {
  type      = string
  sensitive = true
}

# Reference the existing Resource Group created by shell script
data "azurerm_resource_group" "rg" {
  name = "rg-adb-demo-prod"
}

# Reference the existing Key Vault created by shell script
data "azurerm_key_vault" "kv" {
  name                = "demo-kv-123456-prod"
  resource_group_name = data.azurerm_resource_group.rg.name
}

module "databricks" {
  source = "../module_databricks"

  resource_group_name   = data.azurerm_resource_group.rg.name
  location              = data.azurerm_resource_group.rg.location
  workspace_name        = "adb-demo-prod"
  storage_account_name  = "stagedemoprod1234"
  key_vault_id          = data.azurerm_key_vault.kv.id
  
  vnet_address_space    = ["10.1.0.0/16"]
  public_subnet_prefix  = ["10.1.1.0/24"]
  private_subnet_prefix = ["10.1.2.0/24"]
  pe_subnet_prefix      = ["10.1.3.0/24"]
}
