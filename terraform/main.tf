# Configure the Azure provider
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

# Variables (you can override these in terraform.tfvars)
variable "resource_group_name" {
  default = "rg-databricks-demo"
}
variable "location" {
  default = "northeurope"
}
variable "workspace_name" {
  default = "adb-demo-workspace"
}
variable "pricing_tier" {
  default = "premium" # options: standard, premium, trial
}

# Resource Group
resource "azurerm_resource_group" "rg" {
  name     = var.resource_group_name
  location = var.location
}

# Databricks Workspace
resource "azurerm_databricks_workspace" "adb" {
  name                = var.workspace_name
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  sku                 = var.pricing_tier

}

# Output the workspace URL
output "databricks_url" {
  value = azurerm_databricks_workspace.adb.workspace_url
}
