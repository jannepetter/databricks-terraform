#!/usr/bin/env bash

set -e

# ====== Script for hub/base deployment =======

ENV=prod
echo "Deploying for environment: $ENV"
VERSION=v1

# ---- variables ----
PROJECT=mytest
LOCATION="northeurope"
RESOURCE_GROUP="rg-base-$PROJECT-$LOCATION-$VERSION"
METASTORE_STORAGE_ACCOUNT=stmeta$PROJECT$VERSION
CONTAINER_NAME="datalake"
KEYVAULT_NAME="kv-$PROJECT-base"

# # ---- variables (hub network) ----
HUB_VNET_NAME="vnet-hub-$PROJECT-$LOCATION"
PE_SUBNET_NAME="snet-pe"
HUB_VNET_PREFIX="10.0.0.0/16"
PE_SUBNET_PREFIX="10.0.1.0/24"

# ----block accidental trigger
exit 1


# ---- create resource group (base) ----
az group create \
  --name $RESOURCE_GROUP \
  --location $LOCATION \
  --tags environment=${ENV} project=${PROJECT}

az storage account create \
  --name $METASTORE_STORAGE_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku Standard_LRS \
  --kind StorageV2 \
  --hns true \
  --min-tls-version TLS1_2 \
  --https-only true \
  --allow-blob-public-access false \
  --allow-shared-key-access false \
  --tags environment=${ENV} project=${PROJECT}

# ---- create container ----
az storage fs create \
  --name $CONTAINER_NAME \
  --account-name $METASTORE_STORAGE_ACCOUNT \
  --public-access off \
  --auth-mode login


az keyvault create \
  --name $KEYVAULT_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku standard \
  --enable-rbac-authorization true \
  --tags environment=${ENV} project=${PROJECT}

# ---- create hub vnet + subnet ----
az network vnet create \
  --name $HUB_VNET_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --address-prefix $HUB_VNET_PREFIX \
  --tags environment=${ENV} project=${PROJECT}

az network vnet subnet create \
  --name $PE_SUBNET_NAME \
  --resource-group $RESOURCE_GROUP \
  --vnet-name $HUB_VNET_NAME \
  --address-prefix $PE_SUBNET_PREFIX \
  --disable-private-endpoint-network-policies true


# ---- get key vault resource id ----
KV_ID=$(az keyvault show \
  --name $KEYVAULT_NAME \
  --resource-group $RESOURCE_GROUP \
  --query id -o tsv)

# ---- create private endpoint (keyvault) ----
az network private-endpoint create \
  --name "pe-$KEYVAULT_NAME" \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --subnet $(az network vnet subnet show --resource-group $RESOURCE_GROUP --vnet-name $HUB_VNET_NAME --name $PE_SUBNET_NAME --query id -o tsv) \
  --private-connection-resource-id $KV_ID \
  --group-id vault \
  --connection-name "pec-$KEYVAULT_NAME" \
  --tags environment=${ENV} project=${PROJECT}

# ---- create private dns zone (keyvault) ----
az network private-dns zone create \
  --resource-group $RESOURCE_GROUP \
  --name "privatelink.vaultcore.azure.net"

# ---- link dns zone to hub vnet ----
az network private-dns link vnet create \
  --resource-group $RESOURCE_GROUP \
  --zone-name "privatelink.vaultcore.azure.net" \
  --name "dnslink-hub-kv" \
  --virtual-network $HUB_VNET_NAME \
  --registration-enabled false \
  --tags environment=${ENV} project=${PROJECT}

# ---- link private endpoint to dns zone ----
az network private-endpoint dns-zone-group create \
  --resource-group $RESOURCE_GROUP \
  --endpoint-name "pe-$KEYVAULT_NAME" \
  --name "dzg-kv" \
  --private-dns-zone "privatelink.vaultcore.azure.net" \
  --zone-name "vault"

echo "done"