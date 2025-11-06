import os
import time
import json
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
import requests


# ============================
#  LOGGING CONFIGURATION
# ============================
LOG_FILE = "agent.log"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8"
)

logging.info("=== Email Agent avviato ===")


# ============================
#  LOAD ENVIRONMENT
# ============================
load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
TENANT_ID = os.getenv("TENANT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ENABLE_LLM = os.getenv("ENABLE_LLM", "false").lower() == "true"
POLL_SECONDS = int(os.getenv("POLL_SECONDS", "20"))
BUILDINGS_FILE = os.getenv("BUILDINGS_FILE", "buildings.json")


# ============================
#  AUTHENTICATION (MS GRAPH)
# ============================
def get_access_token():
    url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
    data = {
        "client_id": CLIENT_ID,
        "scope": "https://graph.microsoft.com/.default",
        "client_secret": CLIENT_SECRET,
        "grant_type": "client_credentials"
    }

    resp = requests.post(url, data=data)
    resp.raise_for_status()
    token = resp.json()["access_token"]
    return token


def graph_get(url, token):
    resp = requests.get(
        url,
        headers={"Authorization": f"Bearer {token}"}
    )
    resp.raise_for_status()
    return resp.json()


def graph_post(url, token, payload):
    resp = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        data=json.dumps(payload)
    )
    resp.raise_for_status()
    return resp.json()


def graph_patch(url, token, payload):
    resp = requests.patch(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        data=json.dumps(payload)
    )
    resp.raise_for_status()
    return resp.json()


# ============================
#  LOAD BUILDINGS
# ============================
def load_buildings():
    if not os.path.exists(BUILDINGS_FILE):
        logging.error(f"File buildings.json non trovato: {BUILDINGS_FILE}")
        return []

    with open(BUILDINGS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


BUILDINGS = load_buildings()


# ============================
#  CLASSIFICATION ENGINE
# ============================
def classify_email(subject, body, sender):
    """
    Classificazione semplice basata su parole chiave.
    (LLM opzionale se ENABLE_LLM=True)
    """

    subject_lower = subject.lower()
    body_lower = body.lower()

    # individuazione edificio/campus
    building = None
    for b in BUILDINGS:
        if b.lower() in subject_lower or b.lower() in body_lower:
            building = b
            break

    # categorie semplificate
    if "fattur" in subject_lower or "invoice" in subject_lower:
        category = "Fatture"
    elif "preventiv" in subject_lower:
        category = "Preventivi"
    elif "consuntiv" in subject_lower:
        category = "Consuntivi"
    elif "guasto" in subject_lower or "segnalazione" in subject_lower:
        category = "Segnalazioni"
    else:
        category = "Da Gestire"

    confidence = 0.70
    if building:
        confidence += 0.20

    return building, category, confidence


# ============================
#  CREATE TASK IN TO DO
# ============================
def create_todo_task(token, title, description):
    url = "https://graph.microsoft.com/v1.0/me/todo/lists"
    lists_data = graph_get(url, token)

    # get default task list
    default_list = lists_data["value"][0]["id"]

    create_url = f"https://graph.microsoft.com/v1.0/me/todo/lists/{default_list}/tasks"
    payload = {
        "title": title,
        "body": {"content": description},
        "dueDateTime": {
            "dateTime": (datetime.utcnow() + timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "timeZone": "UTC"
        }
    }

    graph_post(create_url, token, payload)
    logging.info(f"Creato task To Do: {title}")


# ============================
#  MOVE EMAIL
# ============================
def move_email(token, email_id, folder_id):
    url = f"https://graph.microsoft.com/v1.0/me/messages/{email_id}/move"
    payload = {"destinationId": folder_id}

    result = graph_post(url, token, payload)
    logging.info(f"Email spostata nella cartella ID={folder_id}")
    return result


# ============================
#  GET OR CREATE FOLDER
# ============================
def get_or_create_folder(token, name, parent_id="inbox"):
    url = f"https://graph.microsoft.com/v1.0/me/mailFolders/{parent_id}/childFolders"
    resp = graph_get(url, token)

    for f in resp.get("value", []):
        if f["displayName"].lower() == name.lower():
            return f["id"]

    # create folder
    create_url = f"https://graph.microsoft.com/v1.0/me/mailFolders/{parent_id}/childFolders"
    payload = {"displayName": name}

    new_folder = graph_post(create_url, token, payload)
    logging.info(f"Creata nuova cartella: {name}")

    return new_folder["id"]


# ============================
#  PROCESS EMAIL LOOP
# ============================
def process_emails():
    token = get_access_token()

    # cartelle principali
    immobili_id = get_or_create_folder(token, "Immobili", "inbox")
    operativo_id = get_or_create_folder(token, "Operativo", "inbox")

    # sottocartelle operative
    da_gestire_id = get_or_create_folder(token, "Da Gestire", operativo_id)

    logging.info("Preparazione cartelle completata. Avvio polling...")

    while True:
        token = get_access_token()

        url = "https://graph.microsoft.com/v1.0/me/mailFolders/Inbox/messages?$filter=isRead eq false"
        data = graph_get(url, token)

        for email in data.get("value", []):
            email_id = email["id"]
            subject = email.get("subject", "")
            sender = email.get("from", {}).get("emailAddress", {}).get("address", "")
            body = email.get("bodyPreview", "")

            logging.info(f"Email nuova: {subject} | {sender}")

            # Classificazione
            building, category, confidence = classify_email(subject, body, sender)
            logging.info(f"Classificazione → building={building}, categoria={category}, conf={confidence}")

            # cartella target
            if confidence >= 0.80 and building:
                building_folder = get_or_create_folder(token, building, immobili_id)
                category_folder = get_or_create_folder(token, category, building_folder)
                move_email(token, email_id, category_folder)

                # crea task solo per i documenti strutturati
                if category in ["Fatture", "Preventivi", "Consuntivi", "Segnalazioni"]:
                    create_todo_task(token, f"{category} - {subject}", body)

            else:
                # fallback: Da Gestire
                move_email(token, email_id, da_gestire_id)
                logging.info("Email ambigua → spostata in Operativo / Da Gestire")

        time.sleep(POLL_SECONDS)


# ============================
#  MAIN
# ============================
if __name__ == "__main__":
    try:
        process_emails()
    except Exception as e:
        logging.error(f"Errore critico: {str(e)}")
# Please copy the processor.py content from the canvas into this file.
