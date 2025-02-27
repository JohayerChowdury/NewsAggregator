import os
import requests

from webflow.client import Webflow

WEBFLOW_ACCESS_TOKEN = os.environ.get("WEBFLOW_ACCESS_TOKEN")
HEADERS = {
    "Authorization": f"Bearer {WEBFLOW_ACCESS_TOKEN}",
    "Accept-Version": "1.0.0",
    "content-type": "application/json",
}
webflow_client = Webflow(access_token=WEBFLOW_ACCESS_TOKEN)


def update_collection(collection_id, items):
    url = f"https://api.webflow/collections{collection_id}/items"
    response = requests.put(url, headers=HEADERS, json={"items": items})
    return response.json()
