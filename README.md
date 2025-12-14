# Databrics testing

## secrets
#secrets/createScope at the end of the host url (paste)

Add kv info to the scope, dns name https://mykv.vault.azure.net/ and resource id /subscriptions/my-subs/resourceGroups/my-rg/providers/Microsoft.KeyVault/vaults/my-kv

tenant_id = dbutils.secrets.get(scope="joo-scope", key="tenant-id")  
joo-scope is now mapped to mykv and you can fetch secrets with the key  

dbutils comes with databricks, when remote connecting. No need to import (at least with notebooks)


## UC memo

- UC metadata is stored in databricks services. It persists even when the storage is destroyed.  

