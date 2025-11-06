import os
import time
import json
import logging
import threading
from datetime import datetime, timedelta

from dotenv import load_dotenv
import requests
from flask import Flask, render_template, jsonify, request


# ============================================================
#  LOGGING CONFIGURATION
# ============================================================
LOG_FILE = "agent.log"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8"
)

logging.info("=== Email Agent avviato ===")


# ============================================================
#  LOAD ENVIRONMENT
# ============================================================
load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
TENANT_ID = os.getenv("TENANT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ENABLE_LLM = os.getenv("ENABLE_LLM", "false").lower() == "true"

POLL_SECONDS = int(os.getenv("POLL_SECONDS", "20"))
BUILDINGS_FILE = os.getenv("BUILDINGS_FILE", "buildings.json")


# ============================================================
#  MICROSOFT GRAPH AUTH
# ============================================================
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
    return resp.json()["access_token"]


def graph_get(url, token):
    resp = requests.get(url, headers={"Authorization": f"Bearer {token}"})
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


# ============================================================
#  LOAD BUILDINGS
# ============================================================
def load_buildings():
    if not os.path.exists(BUILDINGS_FILE):
        logging.error(f"File buildings.json non trovato ({BUILDINGS_FILE})")
        return []

    with open(BUILDINGS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


BUILDINGS = load_buildings()


# ============================================================
#  CLASSIFICATION ENGINE
# ============================================================
def classify_email(subject, body, sender):
    subject_l = subject.lower()
    body_l = body.lower()

    building = None
    for b in BUILDINGS:
        if b.lower() in subject_l or b.lower() in body_l:
            building = b
            break

    # categorie
    if "fattur" in subject_l or "invoice" in subject_l:
        category = "Fatture"
    elif "preventiv" in subject_l:
        category = "Preventivi"
    elif "consuntiv" in subject_l:
        category = "Consuntivi"
    elif "guasto" in subject_l or "segnalazione" in subject_l:
        category = "Segnalazioni"
    else:
        category = "Da Gestire"

    confidence = 0.70
    if building:
        confidence += 0.20

    return building, category, confidence


# ============================================================
#  TODO TASK CREATION
# ============================================================
def create_todo_task(token, title, description):
    url = "https://graph.microsoft.com/v1.0/me/todo/lists"
    lists_data = graph_get(url, token)

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


# ============================================================
#  EMAIL MOVEMENT & FOLDERS
# ============================================================
def move_email(token, email_id, folder_id):
    url = f"https://graph.microsoft.com/v1.0/me/messages/{email_id}/move"
    payload = {"destinationId": folder_id}
    result = graph_post(url, token, payload)
    logging.info(f"Email spostata nella cartella ID={folder_id}")
    return result


def get_or_create_folder(token, name, parent_id="inbox"):
    url = f"https://graph.microsoft.com/v1.0/me/mailFolders/{parent_id}/childFolders"
    resp = graph_get(url, token)

    for f in resp.get("value", []):
        if f["displayName"].lower() == name.lower():
            return f["id"]

    # create new folder
    create_url = f"https://graph.microsoft.com/v1.0/me/mailFolders/{parent_id}/childFolders"
    payload = {"displayName": name}
    new_folder = graph_post(create_url, token, payload)

    logging.info(f"Creata cartella: {name}")
    return new_folder["id"]


# ============================================================
#  DASHBOARD DATA STORAGE
# ============================================================
pending_emails = []
pending_lock = threading.Lock()


# ============================================================
#  FLASK DASHBOARD
# ============================================================
app = Flask(__name__)


@app.route("/")
def dashboard():
    return render_template("dashboard.html")


@app.route("/pending")
def pending():
    with pending_lock:
        return jsonify(pending_emails)


@app.route("/approve", methods=["POST"])
def approve():
    data = request.json
    email_id = data["id"]
    folder = data["folder"]

    with pending_lock:
        email_to_process = None
        for e in pending_emails:
            if e["id"] == email_id:
                email_to_process = e
                pending_emails.remove(e)
                break

    if not email_to_process:
        return jsonify({"status": "error", "message": "Email non trovata"}), 404

    token = get_access_token()
    target_id = get_or_create_folder(token, folder, "inbox")

    move_email(token, email_id, target_id)
    logging.info(f"Email {email_id} approvata (cartella: {folder})")

    return jsonify({"status": "ok"})


@app.route("/reject", methods=["POST"])
def reject():
    data = request.json
    email_id = data["id"]

    with pending_lock:
        pending_emails[:] = [e for e in pending_emails if e["id"] != email_id]

    logging.info(f"Email {email_id} rifiutata dalla dashboard")
    return jsonify({"status": "ok"})


@app.route("/shutdown", methods=["POST"])
def shutdown():
    logging.info("Arresto richiesto dalla dashboard...")
    shutdown_func = request.environ.get("werkzeug.server.shutdown")
    if shutdown_func is None:
        return jsonify({"status": "error", "message": "Shutdown non supportato"}), 500

    shutdown_func()
    return jsonify({"status": "ok", "message": "Agente in arresto..."})


# ============================================================
#  EMAIL PROCESSOR LOOP
# ============================================================
def process_emails():
    token = get_access_token()

    # Create main folders
    immobili_id = get_or_create_folder(token, "Immobili", "inbox")
    operativo_id = get_or_create_folder(token, "Operativo", "inbox")

    da_gestire_id = get_or_create_folder(token, "Da Gestire", operativo_id)

    logging.info("Cartelle pronte. Inizio polling…")

    while True:
        token = get_access_token()
        url = "https://graph.microsoft.com/v1.0/me/mailFolders/Inbox/messages?$filter=isRead eq false"
        data = graph_get(url, token)

        for email in data.get("value", []):
            email_id = email["id"]
            subject = email.get("subject", "")
            sender = email.get("from", {}).get("emailAddress", {}).get("address", "")
            body = email.get("bodyPreview", "")

            logging.info(f"Nuova email: {subject} ({sender})")

            building, category, confidence = classify_email(subject, body, sender)
            logging.info(f"Classificazione → {building} / {category} / {confidence}")

            if confidence >= 0.80 and building:
                building_folder = get_or_create_folder(token, building, immobili_id)
                category_folder = get_or_create_folder(token, category, building_folder)
                move_email(token, email_id, category_folder)

                if category in ["Fatture", "Preventivi", "Consuntivi", "Segnalazioni"]:
                    create_todo_task(token, f"{category} - {subject}", body)

            else:
                # add to dashboard pending list
                with pending_lock:
                    pending_emails.append({
                        "id": email_id,
                        "subject": subject,
                        "sender": sender,
                        "preview": body[:400],
                        "building": building,
                        "category": category,
                        "confidence": confidence
                    })

                logging.info("Email ambigua → inviata alla dashboard")

        time.sleep(POLL_SECONDS)


# ============================================================
#  MAIN
# ============================================================
if __name__ == "__main__":
    # Web dashboard in parallel
    threading.Thread(
        target=lambda: app.run(port=5000, debug=False, use_reloader=False)
    ).start()

    try:
        process_emails()
    except Exception as e:
        logging.error(f"Errore critico: {str(e)}")
