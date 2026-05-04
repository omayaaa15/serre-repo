import azure.functions as func
import json
import os
from azure.cosmos import CosmosClient

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@app.route(route="serre-data")
def serre_data(req: func.HttpRequest) -> func.HttpResponse:
    client = CosmosClient(
        os.environ["COSMOS_ENDPOINT"],
        os.environ["COSMOS_KEY"]
    )
    container = client\
        .get_database_client("serreBD")\
        .get_container_client("data")

    items = list(container.query_items(
        query="SELECT TOP 1 * FROM c ORDER BY c._ts DESC",
        enable_cross_partition_query=True
    ))

    if items:
        msg = items[0]
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
            mimetype="application/json",
            headers={"Access-Control-Allow-Origin": "*"},
            status_code=200
        )

    return func.HttpResponse(
        json.dumps({"erreur": "non", "mode": "inconnu"}),
        mimetype="application/json",
        status_code=200
    )
