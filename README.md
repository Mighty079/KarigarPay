# 🧵 KarigarPay — Neobank & AI Companion for Handloom Artisans

> **National Handloom Hackathon 2026** — Organized by the **Ministry of Textiles, Government of India**  
> 🏛️ **Venue:** Indian Institute of Technology (IIT) Delhi  
> 🏆 **Achievement:** **Top 10 Finalist** (out of 2,600+ registered teams across India)  
> 👥 **Team:** **OneByZero** (Krishnaditya Prakash & Xitiz Raj)  
> 🎯 **Domain:** *Weaver's Livelihood and Financial Inclusion*

---

## 📖 Overview

Traditional handloom weavers across India face severe barriers to formal financial inclusion:
1. **Zero Formal Credit History (No CIBIL):** Traditional credit bureaus don't record handloom weaving cycles.
2. **Seasonal Income Volatility:** Monsoons and humidity disrupt loom operation and yarn stretching, causing severe cash flow dry-spells.
3. **Accessibility & Digital Literacy Barriers:** Complex banking apps with dense English/Hindi forms prevent weavers from engaging with financial services.

**KarigarPay** is a comprehensive, production-tested fintech ecosystem built specifically for weavers, bridging traditional craft with cutting-edge fintech infrastructure.

---

## 🌟 Key Features

### 1. 📊 Loom Credit Index (LCI™)
An alternative, production-backed algorithmic credit scoring engine. Instead of relying on formal credit scores, LCI analyzes 12-month production logs (units woven, output stability, cooperative verification, and loan repayment discipline) to generate an equitable credit score between 300 and 900.

### 2. 💰 Loomloan
A tailored micro-credit facility enabling weavers to instantly access production-backed credit specifically for raw material procurement (silk, cotton, dye) and loom maintenance/upgrades.

### 3. 🛡️ Suraksha & Monsoon Reserve
An artisan micro-insurance portal providing instant claims for health and loom breakdown. It features the **"Monsoon Reserve"**—a specialized emergency liquidity buffer safeguarding weaver livelihoods during high-humidity monsoon periods when looms cannot operate at capacity.

### 4. 🤖 Karigar Sahayak (Multilingual AI Companion)
An AI conversational assistant deployed directly on **Telegram** (`@KarigarPaybot`). Supports regional languages (Hindi, English, Tamil, Telugu), enabling artisans to check balances, log production, and apply for Loomloans simply by typing or sending voice messages.

---

## 🏗️ Architecture

```
                       ┌──────────────────────────────────────────────┐
                       │               KarigarPay Ecosystem           │
                       └──────────────────────┬───────────────────────┘
                                              │
                    ┌─────────────────────────┴────────────────────────┐
                    ▼                                                  ▼
      ┌───────────────────────────┐                      ┌───────────────────────────┐
      │ React Native / Expo App   │                      │  Karigar Sahayak (Bot)    │
      │  (Android Mobile Client)  │                      │    (Telegram Platform)    │
      └─────────────┬─────────────┘                      └─────────────┬─────────────┘
                    │                                                  │
                    │ REST API (HTTPS)                                 │ Webhook / Polling
                    ▼                                                  ▼
      ┌──────────────────────────────────────────────────────────────────────────────┐
      │                           FastAPI Central Backend                            │
      │   - REST Endpoints (/api/weaver, /api/wallet, /api/loans, /api/insurance)   │
      │   - LCI Scoring Engine (Mathematical production modeling)                    │
      │   - SQLite Persistent Ledger (SQLAlchemy ORM)                                │
      │   - Production Deployment: Render.com Cloud Platform                         │
      └──────────────────────────────────────────────────────────────────────────────┘
```

---

## 📂 Repository Structure

```
KarigarPay/
├── backend/
│   ├── main.py              # FastAPI server & route handlers
│   ├── telegram_bot.py      # Karigar Sahayak conversational AI bot
│   ├── lci_engine.py        # Loom Credit Index (LCI) scoring algorithm
│   ├── models.py            # SQLAlchemy database models & seed data
│   ├── database.py          # Database connection & session setup
│   ├── karigarpay.db        # SQLite persistent database
│   ├── requirements.txt     # Python dependencies
│   └── .env                 # Environment variables (Bot token, etc.)
│
├── frontend/
│   ├── App.js               # React Native neobank UI & navigation
│   ├── api.js               # Centralized API service & backend IP config
│   ├── app.json             # Expo project configuration
│   ├── package.json         # JavaScript dependencies & scripts
│   ├── KarigarPay.apk       # Pre-compiled standalone release Android APK
│   ├── assets/              # App branding, icons, illustrations
│   └── android/             # Native Android Gradle configuration & manifests
│
├── prototype.html           # Full interactive standalone web prototype
├── start_emulator.bat       # Script to launch Android emulator
├── run_app.bat              # Script to start Expo frontend development server
├── add_firewall.bat         # Script to open local port 8000 on Windows Firewall
└── README.md                # Project documentation
```

---

## 🚀 Getting Started

### 1. Prerequisites
- **Python 3.10+**
- **Node.js 18+** & npm / yarn
- **Android Studio** (for emulator testing) or physical Android device

### 2. Backend Setup
```bash
cd backend
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
python main.py
```
Backend will be live at `http://127.0.0.1:8000` (interactive API docs available at `http://127.0.0.1:8000/docs`).

### 3. Telegram Bot Setup
1. Create a bot using [@BotFather](https://t.me/BotFather) on Telegram.
2. Add your bot token to `backend/.env`:
   ```env
   TELEGRAM_BOT_TOKEN="your_bot_token_here"
   ```
3. Run the bot:
   ```bash
   python telegram_bot.py
   ```

### 4. Frontend Setup
```bash
cd frontend
npm install
npx expo start
```

---

## 👥 Authors & Acknowledgments

- **Krishnaditya Prakash** — [@Mighty079](https://github.com/Mighty079)
- **Xitiz Raj**

Developed for the **National Handloom Hackathon 2026**, organized by the **Ministry of Textiles, Government of India**, held at **IIT Delhi**.
