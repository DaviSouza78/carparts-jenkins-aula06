#!/usr/bin/env bash
# Execute somente em uma assinatura Azure da equipe, após validar a calculadora e orçamento.
set -euo pipefail
: "${AZURE_SUBSCRIPTION_ID:?}"
: "${AZURE_RESOURCE_GROUP:?}"
: "${AZURE_ACR_NAME:?nome globalmente único, letras e números}"
: "${AZURE_LOCATION:=brazilsouth}"
: "${AZURE_ENVIRONMENT:=carparts-hml-env}"
: "${AZURE_STAGING_APP:=carparts-hml}"
: "${AZURE_PRODUCTION_APP:=carparts-prd}"

az account set --subscription "$AZURE_SUBSCRIPTION_ID"
az group create -n "$AZURE_RESOURCE_GROUP" -l "$AZURE_LOCATION" --output none
az acr create -n "$AZURE_ACR_NAME" -g "$AZURE_RESOURCE_GROUP" --sku Basic --admin-enabled false --output none
az containerapp env create -n "$AZURE_ENVIRONMENT" -g "$AZURE_RESOURCE_GROUP" -l "$AZURE_LOCATION" --output none

# Bootstrap com imagem pública; substitua pela imagem Carparts após o primeiro push.
for app in "$AZURE_STAGING_APP" "$AZURE_PRODUCTION_APP"; do
  az containerapp create -n "$app" -g "$AZURE_RESOURCE_GROUP" --environment "$AZURE_ENVIRONMENT" \
    --image mcr.microsoft.com/k8se/quickstart:latest --ingress external --target-port 80 \
    --cpu 0.25 --memory 0.5Gi --min-replicas 0 --max-replicas 1 --output none
  az containerapp identity assign -n "$app" -g "$AZURE_RESOURCE_GROUP" --system-assigned --output none
done

acr_id=$(az acr show -n "$AZURE_ACR_NAME" -g "$AZURE_RESOURCE_GROUP" --query id -o tsv)
for app in "$AZURE_STAGING_APP" "$AZURE_PRODUCTION_APP"; do
  principal_id=$(az containerapp identity show -n "$app" -g "$AZURE_RESOURCE_GROUP" --query principalId -o tsv)
  az role assignment create --assignee-object-id "$principal_id" --assignee-principal-type ServicePrincipal --role AcrPull --scope "$acr_id" --output none
  az containerapp registry set -n "$app" -g "$AZURE_RESOURCE_GROUP" --server "$AZURE_ACR_NAME.azurecr.io" --identity system --output none
done

# Crie o service principal sem exibir o segredo; importe-o no Jenkins e remova o arquivo local.
mkdir -p .runtime
chmod 700 .runtime
az ad sp create-for-rbac --name "carparts-jenkins-${AZURE_RESOURCE_GROUP}" --skip-assignment --output json > .runtime/azure-sp.json
chmod 600 .runtime/azure-sp.json
sp_object_id=$(az ad sp show --id "$(python3 -c 'import json; print(json.load(open(".runtime/azure-sp.json"))["appId"])')" --query id -o tsv)
az role assignment create --assignee-object-id "$sp_object_id" --assignee-principal-type ServicePrincipal --role AcrPush --scope "$acr_id" --output none
for app in "$AZURE_STAGING_APP" "$AZURE_PRODUCTION_APP"; do
  app_id=$(az containerapp show -n "$app" -g "$AZURE_RESOURCE_GROUP" --query id -o tsv)
  az role assignment create --assignee-object-id "$sp_object_id" --assignee-principal-type ServicePrincipal --role 'Container Apps Contributor' --scope "$app_id" --output none
done
echo 'Recursos criados. Importe .runtime/azure-sp.json no cofre Jenkins e remova-o em seguida.'
