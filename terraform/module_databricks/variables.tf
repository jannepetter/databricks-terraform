
variable "environment" {
  type = string
}

variable "app_name" {
  type = string
}

variable "location" {
  type = string
}

variable "p_version" {
  type        = string
  description = "Project version. (version is reserved)"
}

variable "resource_group_name" {
  type        = string
  description = "Spoke resource group"
}

variable "hub_resource_group_name" {
  type        = string
  description = "Hub/base resource group where hub VNet and DNS zones live"
}

variable "metastore_storage_account_name" {
  type        = string
  description = "Metastore storage account name in hub RG"
}

variable "queue_storage_account_name" {
  type        = string
  description = "Queue storage account name in spoke RG"
}
