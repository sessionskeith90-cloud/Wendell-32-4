# Create an Azure resource group
export RANDOM_ID="$(openssl rand -hex 3)"
export MY_RESOURCE_GROUP_NAME="myAOAIResourceGroup$RANDOM_ID"
export REGION="eastus"
export TAGS="owner=user"

az group create --name $MY_RESOURCE_GROUP_NAME --location $REGION --tags $TAGS

# Create a resource
export MY_OPENAI_RESOURCE_NAME="myOAIResource$RANDOM_ID"
az cognitiveservices account create \
--name $MY_OPENAI_RESOURCE_NAME \
--resource-group $MY_RESOURCE_GROUP_NAME \
--location $REGION \
--kind OpenAI \
--sku s0 \

# Get the endpoint URL
az cognitiveservices account show \
--name $MY_OPENAI_RESOURCE_NAME \
--resource-group $MY_RESOURCE_GROUP_NAME \
| jq -r .properties.endpoint

# Get the primary API key
az cognitiveservices account keys list \
--name $MY_OPENAI_RESOURCE_NAME \
--resource-group $MY_RESOURCE_GROUP_NAME \
| jq -r .key1

# Deploy a model
export MY_MODEL_NAME="myModel$RANDOM_ID"
az cognitiveservices account deployment create \
--name $MY_OPENAI_RESOURCE_NAME \
--resource-group $MY_RESOURCE_GROUP_NAME \
--deployment-name $MY_MODEL_NAME \
--model-name text-embedding-ada-002 \
--model-version "2"  \
--model-format OpenAI \
--sku-capacity "1" \
--sku-name "Standard"

