import azure.functions as func
import json
import os
from azure.cosmos import CosmosClient
from azure.iot.hub import IoTHubRegistryManager

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@app.route(route="serre-data")
def serre_data(req: func.HttpRequest) -> func.HttpResponse:
    client = CosmosClient(os.environ["COSMOS_ENDPOINT"], os.environ["COSMOS_KEY"])
    container = client.get_database_client("serreBD").get_container_client("data")

    items = list(container.query_items(
        query="SELECT TOP 1 * FROM c ORDER BY c._ts DESC",
        enable_cross_partition_query=True
    ))

    # Préparation des headers CORS pour tout le monde
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, OPTIONS",
        "Content-Type": "application/json"
    }

    if items:
        doc = items[0]
        msg = doc.get("Body", doc)  
        return func.HttpResponse(
            json.dumps({
                "temperature": msg.get("temperature"),
                "luminosite": msg.get("luminosite"),
                "mode": msg.get("mode"),
                "ouverture_reelle": msg.get("ouverture_reelle"),
                "ouverture_automatique": msg.get("ouverture_automatique"),
                "erreur": msg.get("erreur"),
                "avertissement": msg.get("avertissement")
            }),
            status_code=200,
            headers=headers
        )

    # Correction ici : on ajoute les headers même si c'est vide !
    return func.HttpResponse(
        json.dumps({"erreur": "non", "mode": "inconnu"}),
        status_code=200,
        headers=headers
    )

    # Vous devrez ajouter 'azure-iot-hub' dans votre requirements.txt


@app.route(route="send-command", methods=["POST"])
def send_command(req: func.HttpRequest) -> func.HttpResponse:
    try:
        data = req.get_json()
        action = data.get('action')
        
        # Connexion au Hub pour envoyer un message à l'objet
        registry_manager = IoTHubRegistryManager(os.environ["IOTHUB_CONNECTION_STRING"])
        
        # On envoie la commande à l'appareil 'serre_01'
        registry_manager.send_c2d_message("serre_01", json.dumps(data))
        
        return func.HttpResponse("Commande envoyée", status_code=200)
    except Exception as e:
        return func.HttpResponse(f"Erreur: {str(e)}", status_code=500)
