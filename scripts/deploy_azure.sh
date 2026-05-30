#!/bin/bash
set -e

echo "====================================================="
echo "🚀 INIZIO DEPLOY SU AZURE APP SERVICE (LINUX)"
echo "====================================================="

# Configurazione Variabili (Sostituisci con i tuoi valori se necessario)
RESOURCE_GROUP="rg-social-exposure"
APP_SERVICE_PLAN="asp-social-exposure"
APP_NAME="app-social-exposure-$RANDOM" # Generiamo un nome univoco
LOCATION="westeurope"
PYTHON_VERSION="3.11"

echo "[1/4] Creazione Resource Group ($RESOURCE_GROUP) in $LOCATION..."
az group create --name "$RESOURCE_GROUP" --location "$LOCATION" -o none

echo "[2/4] Creazione App Service Plan (Tier: B1 - Linux)..."
az appservice plan create --name "$APP_SERVICE_PLAN" \
  --resource-group "$RESOURCE_GROUP" \
  --sku B1 --is-linux -o none

echo "[3/4] Creazione della Web App ($APP_NAME)..."
az webapp create --resource-group "$RESOURCE_GROUP" \
  --plan "$APP_SERVICE_PLAN" \
  --name "$APP_NAME" \
  --runtime "PYTHON|$PYTHON_VERSION" -o none

echo "[4/4] Configurazione Variabili d'Ambiente e Startup Command..."
# Legge la API KEY dal file .env (assicurarsi di averlo configurato in locale)
if [ -f .env ]; then
    GEMINI_KEY=$(grep GEMINI_API_KEY .env | cut -d '=' -f2)
    echo "Trovata GEMINI_API_KEY nel .env locale. Configurazione su Azure..."
    az webapp config appsettings set --resource-group "$RESOURCE_GROUP" \
      --name "$APP_NAME" \
      --settings GEMINI_API_KEY="$GEMINI_KEY" -o none
else
    echo "ATTENZIONE: File .env non trovato. La GEMINI_API_KEY non è stata configurata!"
fi

# Imposta il comando di avvio per usare startup.sh
az webapp config set --resource-group "$RESOURCE_GROUP" \
  --name "$APP_NAME" \
  --startup-file "startup.sh" -o none

echo "====================================================="
echo "✅ INFRASTRUTTURA PRONTA!"
echo "L'applicazione risponderà all'URL: https://$APP_NAME.azurewebsites.net"
echo "Per deployare il codice esegui:"
echo "az webapp up --name $APP_NAME --resource-group $RESOURCE_GROUP"
echo "====================================================="
