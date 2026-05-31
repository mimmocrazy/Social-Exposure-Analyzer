#!/bin/bash
set -e

echo "====================================================="
echo "🚀 INIZIO DEPLOY SU AZURE APP SERVICE (LINUX)"
echo "====================================================="

# Configurazione Variabili
RESOURCE_GROUP="rg-social-exposure"
APP_SERVICE_PLAN="asp-social-exposure"
APP_NAME="app-social-exposure-$RANDOM"
DB_SERVER_NAME="db-social-exposure-$RANDOM"
DB_USER="cloudadmin"
DB_PASS="P@ssw0rd12345!" # Attenzione: in prod generare o usare KeyVault
DB_NAME="social_exposure_db"
LOCATION="westeurope"
PYTHON_VERSION="3.11"

echo "[1/5] Creazione Resource Group ($RESOURCE_GROUP) in $LOCATION..."
az group create --name "$RESOURCE_GROUP" --location "$LOCATION" -o none

echo "[2/5] Creazione Database PostgreSQL Flexible Server ($DB_SERVER_NAME)..."
# Disabilitiamo temporaneamente SSL enforcing per semplificare l'handshake (solo in PoC/Dev)
az postgres flexible-server create \
  --resource-group "$RESOURCE_GROUP" \
  --name "$DB_SERVER_NAME" \
  --location "$LOCATION" \
  --admin-user "$DB_USER" \
  --admin-password "$DB_PASS" \
  --database-name "$DB_NAME" \
  --public-access all \
  --tier Burstable --sku-name Standard_B1ms -o none

DATABASE_URL="postgresql://$DB_USER:$DB_PASS@$DB_SERVER_NAME.postgres.database.azure.com:5432/$DB_NAME"

echo "[3/5] Creazione App Service Plan (Tier: B1 - Linux)..."
az appservice plan create --name "$APP_SERVICE_PLAN" \
  --resource-group "$RESOURCE_GROUP" \
  --sku B1 --is-linux -o none

echo "[4/5] Creazione della Web App ($APP_NAME)..."
az webapp create --resource-group "$RESOURCE_GROUP" \
  --plan "$APP_SERVICE_PLAN" \
  --name "$APP_NAME" \
  --runtime "PYTHON|$PYTHON_VERSION" -o none

echo "[5/5] Configurazione Variabili d'Ambiente e Startup Command..."
az webapp config appsettings set --resource-group "$RESOURCE_GROUP" \
  --name "$APP_NAME" \
  --settings DATABASE_URL="$DATABASE_URL" \
  JWT_SECRET_KEY=$(openssl rand -hex 32) -o none

if [ -f .env ]; then
    GEMINI_KEY=$(grep GEMINI_API_KEY .env | cut -d '=' -f2)
    echo "Configurazione GEMINI_API_KEY su Azure..."
    az webapp config appsettings set --resource-group "$RESOURCE_GROUP" \
      --name "$APP_NAME" \
      --settings GEMINI_API_KEY="$GEMINI_KEY" -o none
fi

# Imposta il comando di avvio per usare startup.sh (che ora deve lanciare alembic prima di uvicorn)
az webapp config set --resource-group "$RESOURCE_GROUP" \
  --name "$APP_NAME" \
  --startup-file "startup.sh" -o none

echo "====================================================="
echo "✅ INFRASTRUTTURA CLOUD NATIVE PRONTA!"
echo "URL Database (Interno): $DB_SERVER_NAME.postgres.database.azure.com"
echo "L'applicazione risponderà all'URL: https://$APP_NAME.azurewebsites.net"
echo "Per deployare il codice esegui:"
echo "az webapp up --name $APP_NAME --resource-group $RESOURCE_GROUP"
echo "====================================================="
