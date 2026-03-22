#!/usr/bin/env bash

set -e

# ======script for spoke deployment=========

ENV=dev
echo "Deploying for environment: $ENV"
VERSION=v1

# ---- variables ----
PROJECT=mytest
LOCATION="northeurope"
RESOURCE_GROUP="rg-$PROJECT-$ENV-$LOCATION-$VERSION"
QUEUE_STORAGE_ACCOUNT_NAME="stq$PROJECT$ENV$VERSION"
WORKSPACE_NAME="adb-$PROJECT-$ENV-$VERSION"

VNET_PRE=10.1
SPOKE_VNET_PREFIX="$VNET_PRE.0.0/16"
PRIVATE_SUBNET_PREFIX="$VNET_PRE.0.0/24"
PUBLIC_SUBNET_PREFIX="$VNET_PRE.1.0/24"

# ---- variables (spoke network) ----
SPOKE_VNET_NAME="vnet-spoke-$PROJECT-$ENV-$LOCATION"
PRIVATE_SUBNET_NAME="snet-databricks-private"
PUBLIC_SUBNET_NAME="snet-databricks-public"

# ---- create resource group ----
az group create \
  --name $RESOURCE_GROUP \
  --location $LOCATION \
  --tags environment=${ENV} project=${PROJECT}

# ---- create storage account ----
az storage account create \
  --name $QUEUE_STORAGE_ACCOUNT_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku Standard_LRS \
  --kind StorageV2 \
  --min-tls-version TLS1_2 \
  --https-only true \
  --allow-blob-public-access false \
  --allow-shared-key-access false \
  --tags environment=${ENV} project=${PROJECT}

# ---- create queues ----
az storage queue create \
  --name "job-queue-1" \
  --account-name $QUEUE_STORAGE_ACCOUNT_NAME \
  --auth-mode login

az storage queue create \
  --name "job-queue-1" \
  --account-name $QUEUE_STORAGE_ACCOUNT_NAME \
  --auth-mode login

# ---- create spoke vnet + subnets ----
az network vnet create \
  --name $SPOKE_VNET_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --address-prefix $SPOKE_VNET_PREFIX \
  --tags environment=${ENV} project=${PROJECT}

az network vnet subnet create \
  --name $PRIVATE_SUBNET_NAME \
  --resource-group $RESOURCE_GROUP \
  --vnet-name $SPOKE_VNET_NAME \
  --address-prefix $PRIVATE_SUBNET_PREFIX \
  --delegations "Microsoft.Databricks/workspaces"

az network vnet subnet create \
  --name $PUBLIC_SUBNET_NAME \
  --resource-group $RESOURCE_GROUP \
  --vnet-name $SPOKE_VNET_NAME \
  --address-prefix $PUBLIC_SUBNET_PREFIX \
  --delegations "Microsoft.Databricks/workspaces"

# ---- create nsg -----

az network nsg create \
  --name "nsg-databricks-$ENV" \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --tags environment=${ENV} project=${PROJECT}

NSG_ID=$(az network nsg show \
  --name "nsg-databricks-$ENV" \
  --resource-group $RESOURCE_GROUP \
  --query id -o tsv)

az network vnet subnet update \
  --name $PRIVATE_SUBNET_NAME \
  --resource-group $RESOURCE_GROUP \
  --vnet-name $SPOKE_VNET_NAME \
  --network-security-group $NSG_ID

az network vnet subnet update \
  --name $PUBLIC_SUBNET_NAME \
  --resource-group $RESOURCE_GROUP \
  --vnet-name $SPOKE_VNET_NAME \
  --network-security-group $NSG_ID

# ---- create access connector -----
az databricks access-connector create \
  --name "ac-$WORKSPACE_NAME" \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --identity-type SystemAssigned \
  --tags environment=${ENV} project=${PROJECT}

ACCESS_CONNECTOR_ID=$(az databricks access-connector show \
  --name "ac-$WORKSPACE_NAME" \
  --resource-group $RESOURCE_GROUP \
  --query id -o tsv)

# ---- create databricks workspace ----
SPOKE_VNET_ID=$(az network vnet show \
  --name $SPOKE_VNET_NAME \
  --resource-group $RESOURCE_GROUP \
  --query id -o tsv)

az databricks workspace create \
  --name $WORKSPACE_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku premium \
  --managed-resource-group "rg-managed-${WORKSPACE_NAME}" \
  --vnet $SPOKE_VNET_ID \
  --private-subnet $PRIVATE_SUBNET_NAME \
  --public-subnet $PUBLIC_SUBNET_NAME \
  --access-connector "{id:$ACCESS_CONNECTOR_ID,identity-type:SystemAssigned}" \
  --default-storage-firewall Enabled \
  --tags environment=${ENV} project=${PROJECT}

# Disable storage firewall post-creation to allow serverless compute (cannot create workspace with it disabled directly)
az databricks workspace update \
  --name $WORKSPACE_NAME \
  --resource-group $RESOURCE_GROUP \
  --default-storage-firewall Disabled

echo "done"