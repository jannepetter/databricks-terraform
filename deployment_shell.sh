#!/usr/bin/env bash

ENV=dev
echo "Deploying for environment: $ENV"

# ---- variables ----
RESOURCE_GROUP="rg-adb-demo-$ENV"
LOCATION="northeurope"
KEYVAULT_NAME="demo-kv-123456-$ENV"
STORAGE_ACCOUNT_NAME="stagedemo${ENV}1234"
CONTAINER_NAME="default"

# ---- create resource group (common) ----
echo "Creating/Checking Resource Group..."
az group create \
  --name $RESOURCE_GROUP \
  --location $LOCATION

# ---- create key vault (common) ----
echo "Creating/Checking Key Vault..."
az keyvault create \
  --name $KEYVAULT_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku standard \
  --enable-rbac-authorization true

# ---- create storage account ----
echo "Creating/Checking Storage Account: $STORAGE_ACCOUNT_NAME"
az storage account create \
  --name $STORAGE_ACCOUNT_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku Standard_LRS \
  --kind StorageV2 \
  --hns true \
  --min-tls-version TLS1_2 \
  --https-only true \
  --allow-blob-public-access false \
  --allow-shared-key-access false

# ---- create container ----
echo "Creating/Checking Container: $CONTAINER_NAME"
az storage fs create \
  --name $CONTAINER_NAME \
  --account-name $STORAGE_ACCOUNT_NAME \
  --public-access off \
   --auth-mode login

# ---- create queue ----
echo "Creating/Checking Queues
az storage queue create \
  --name "job-queue-1" \
  --account-name $STORAGE_ACCOUNT_NAME \
   --auth-mode login

az storage queue create \
  --name "job-queue-2" \
  --account-name $STORAGE_ACCOUNT_NAME \
   --auth-mode login

echo "done"
