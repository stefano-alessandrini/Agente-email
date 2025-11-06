# 🤖 Email Agent – Outlook Automation con Microsoft Graph

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

---

## ✅ Come funziona la build automatica (GitHub Actions)

Il workflow **Build Agent EXE** compila automaticamente l’agente.

Ogni volta che fai un commit su `main`, GitHub:
1. installa Python
2. installa le dipendenze da `requirements.txt`
3. esegue PyInstaller
4. genera un file `.exe`
5. pubblica l’eseguibile come artifact scaricabile

Puoi vedere gli eseguibili generati qui:

---

## ✅ Come scaricare l'eseguibile (.exe)

1. Apri la scheda **Actions**
2. Clicca sull’ultima build “✓ Build Agent EXE”
3. In basso trovi **Artifacts**
4. Scarica:  
   ✅ `email-agent-exe.zip`  
5. Dentro lo ZIP trovi:  
   ✅ `processor.exe` pronto all’uso

Non serve installare Python sul PC.

---

## ✅ Configurazione del file `.env`

Crea nella stessa cartella dell’eseguibile un file chiamato **`.env`** con questo contenuto:
CLIENT_ID=xxx
TENANT_ID=xxx
CLIENT_SECRET=xxx

opzionale

OPENAI_API_KEY=
ENABLE_LLM=false

POLL_SECONDS=20
BUILDINGS_FILE=buildings.json

Le credenziali (`CLIENT_ID`, `TENANT_ID`, `CLIENT_SECRET`) si ottengono registrando un’app su **Azure Entra ID** con permessi:

- Mail.ReadWrite  
- Mail.Send  
- MailboxSettings.Read  
- Tasks.ReadWrite  
- Files.ReadWrite.All  

---

## ✅ Struttura cartelle generata automaticamente in Outlook
Immobili/
Edificio A/
Edificio B/
Campus Padriciano/
Campus Basovizza/

### 📁 Immobili (include anche i campus)

Per ogni edificio:
Contratti/
Fatture/
Preventivi/
Consuntivi/
Fornitori/
Segnalazioni/


### 📁 Operativo
perativo/
Da Gestire
In Attesa Risposta
Urgenti
Attività Programmate
Amministrazione Generale
Comunicazioni Interne


---

## ✅ Come funziona l’agente

### 1️⃣ Lettura email
Legge le email non lette dalla inbox via Microsoft Graph.

### 2️⃣ Classificazione intelligente
Analizza oggetto, testo, mittente e allegati per determinare:
- edificio/campus
- tipo documento (fattura, segnalazione, ecc.)
- cartella corretta

### 3️⃣ Smistamento
Se la confidenza è alta → email spostata automaticamente.  
Se la confidenza è media → richiesta inviata alla dashboard.  
Se bassa → fallback in `Operativo/Da Gestire`.

### 4️⃣ Creazione task To Do
Per:
- fatture  
- preventivi  
- consuntivi  
- segnalazioni  

Viene creato un task con scadenza di 7 giorni.

### 5️⃣ Generazione risposte automatiche
Crea una bozza che invia alla dashboard per approvazione.

### 6️⃣ Apprendimento
Registra le decisioni approvate dall’utente per migliorare la classificazione futura.

---

## ✅ Come contribuire / modificare il progetto

Puoi modificare:
- `buildings.json` per aggiungere o rinominare edifici
- `processor.py` per estendere la logica
- `.env.example` per aggiungere nuove variabili
- `build.yml` per cambiare modalità di build

Dopo ogni modifica → GitHub ricostruirà automaticamente l’eseguibile.

---

## ✅ Autore

Repository creato da **Stefano Alessandrini**  
Agente sviluppato con l’assistenza di **ChatGPT (GPT-5)**

---

## ✅ Licenza

Puoi scegliere una licenza (MIT consigliata) o lasciare il progetto senza licenza.

