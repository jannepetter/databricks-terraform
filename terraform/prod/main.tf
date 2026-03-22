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
variable "environment" {
  default = "prod"
}

variable "app_name" {
  default = "mytest"
}
variable "location" {
  default = "northeurope"
}
variable "version" {
  default = "v1"
}


module "databricks" {
  source                         = "../module_databricks"
  environment                    = var.environment
  queue_storage_account_name     = "stq${var.app_name}${var.environment}${var.version}"
  app_name                       = var.app_name
  metastore_storage_account_name = "stmeta${var.app_name}${var.version}"
  hub_resource_group_name        = "rg-base-${var.app_name}-${var.location}-${var.version}"
  resource_group_name            = "rg-${var.app_name}-${var.environment}-${var.location}-${var.version}"
  location                       = var.location
}