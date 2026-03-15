variable "resource_group_name" {
  type = string
}

variable "location" {
  type = string
}

variable "workspace_name" {
  type = string
}

variable "storage_account_name" {
  type = string
}

variable "key_vault_id" {
  type = string
}

variable "vnet_address_space" {
  type = list(string)
}

variable "public_subnet_prefix" {
  type = list(string)
}

variable "private_subnet_prefix" {
  type = list(string)
}

variable "pe_subnet_prefix" {
  type = list(string)
}
