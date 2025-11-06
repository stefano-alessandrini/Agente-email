# 🤖 Email Agent – Outlook Automation con Microsoft Graph

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Build Status](https://github.com/stefano-alessandrini/Agente-email/actions/workflows/build.yml/badge.svg)](https://github.com/stefano-alessandrini/Agente-email/actions)
![Windows EXE](https://img.shields.io/badge/Windows-.exe-blue)

Questo repository contiene un **agente intelligente** per automatizzare la gestione della posta elettronica in Outlook tramite Microsoft Graph.

L’agente:
- legge automaticamente le email dalla posta in arrivo
- classifica le email in base a edificio/campus, fornitore, tipo documento
- le smista nelle cartelle corrette su Outlook
- crea attività in Microsoft To Do (fatture, segnalazioni, preventivi, consuntivi)
- genera bozze di risposta automatica
- invia le bozze alla dashboard per approvazione
- apprende dalle decisioni dell’utente

Il tutto viene compilato come **eseguibile Windows (.exe)** tramite GitHub Actions, senza dover installare Python sul PC.

---

## ✅ Contenuto del repository

- `processor.py` → Agente principale (codice completo)
- `buildings.json` → Elenco edifici e campus gestiti
- `requirements.txt` → Librerie Python necessarie
- `.env.example` → Configurazione modello (da copiare in `.env`)
- `.github/workflows/build.yml` → Workflow GitHub Actions per creare l’eseguibile
- `LICENSE` (MIT)

---

## ✅ Build automatica (GitHub Actions)

Ogni volta che fai un commit su `main`, GitHub:

1. Installare Python  
2. Installare le dipendenze  
3. Esegue PyInstaller  
4. Genera il file `.exe`  
5. Pubblica l’eseguibile come artifact scaricabile

Puoi vederlo qui:  
👉 **Actions → Build Agent EXE**

---

## ✅ Download dell’eseguibile (Windows)

1. Vai su **Actions**  
2. Apri l’ultima build verde  
3. Scorri in basso fino a **Artifacts**  
4. Scarica:  
   ✅ `email-agent-exe.zip`  
5. All’interno troverai:  
   ✅ `processor.exe` pronto all’uso

---

## ✅ Configurazione del file `.env`
Crea un file chiamato `.env` nella stessa cartella dell’eseguibile:
CLIENT_ID=xxx
TENANT_ID=xxx
CLIENT_SECRET=xxx

opzionale

OPENAI_API_KEY=
ENABLE_LLM=false

POLL_SECONDS=20
BUILDINGS_FILE=buildings.json


Ottieni le credenziali Microsoft registrando un’app in **Azure Entra ID** con permessi:

- Mail.ReadWrite  
- Mail.Send  
- MailboxSettings.Read  
- Tasks.ReadWrite  
- Files.ReadWrite.All  

---

## ✅ Struttura cartelle generata in Outlook

### 📁 Immobili
Immobili/
Edificio A/
Edificio B/
Campus Padriciano/
Campus Basovizza/


Sottocartelle:
Contratti/
Fatture/
Preventivi/
Consuntivi/
Fornitori/
Segnalazioni/


### 📁 Operativo
Operativo/
Da Gestire
In Attesa Risposta
Urgenti
Attività Programmate
Amministrazione Generale
Comunicazioni Interne


---

## ✅ Funzionamento dell’agente

### 1️⃣ Lettura email  
Analizza oggetto, testo, mittente e allegati.

### 2️⃣ Classificazione  
Smistamento automatico → o richiesta alla dashboard se dubbio.

### 3️⃣ Task To Do  
Automatici per:
- fatture  
- preventivi  
- consuntivi  
- segnalazioni  

### 4️⃣ Risposte automatiche  
Genera una bozza → invia alla dashboard.

### 5️⃣ Apprendimento  
Registra le decisioni approvate dall’utente.

---

## ✅ Autore

Repository creato da **Stefano Alessandrini**  
Agente sviluppato con l’assistenza di **ChatGPT (GPT-5)**

---

## ✅ Licenza

Distribuito con licenza **MIT** – vedi file `LICENSE`.

Crea un file chiamato `.env` nella stessa cartella dell’eseguibile:

