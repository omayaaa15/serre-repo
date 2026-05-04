import azure.functions as func
import json
import os
from azure.cosmos import CosmosClient
from azure.iot.hub import IoTHubRegistryManager

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

# Headers de sécurité pour autoriser ton site GitHub
CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Content-Type": "application/json"
}

@app.route(route="data") # Route simplifiée : /api/data
def get_serre_data(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return func.HttpResponse(status_code=200, headers=CORS_HEADERS)

    try:
        client = CosmosClient(os.environ["COSMOS_ENDPOINT"], os.environ["COSMOS_KEY"])
        container = client.get_database_client("serreBD").get_container_client("data")

        items = list(container.query_items(
            query="SELECT TOP 1 * FROM c ORDER BY c._ts DESC",
            enable_cross_partition_query=True
        ))

        if items:
            doc = items[0]
            msg = doc.get("Body", doc)
            return func.HttpResponse(json.dumps(msg), status_code=200, headers=CORS_HEADERS)

        return func.HttpResponse(json.dumps({"erreur": "Aucune donnée"}), status_code=200, headers=CORS_HEADERS)
    except Exception as e:
        return func.HttpResponse(json.dumps({"erreur": str(e)}), status_code=500, headers=CORS_HEADERS)

@app.route(route="commande", methods=["POST", "OPTIONS"]) # Route simplifiée : /api/commande
def send_serre_command(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return func.HttpResponse(status_code=200, headers=CORS_HEADERS)

    try:
        data = req.get_json()
        registry_manager = IoTHubRegistryManager(os.environ["IOTHUB_CONNECTION_STRING"])
        registry_manager.send_c2d_message("serre_01", json.dumps(data))
        return func.HttpResponse("OK", status_code=200, headers=CORS_HEADERS)
    except Exception as e:
        return func.HttpResponse(str(e), status_code=500, headers=CORS_HEADERS)
