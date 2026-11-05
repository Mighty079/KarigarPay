import os
import re
import logging
import datetime
try:
    import soundfile as sf
    AUDIO_AVAILABLE = True
except Exception:
    AUDIO_AVAILABLE = False

try:
    import speech_recognition as sr
    SPEECH_AVAILABLE = True
except Exception:
    SPEECH_AVAILABLE = False
from dotenv import load_dotenv
from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)

# Load environment variables
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Setup logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Database session & models
from database import SessionLocal
from models import WeaverProfile, WalletLedger, ProductionLogs, ActiveLoans
import lci_engine

# Session caches
user_languages = {}  # { user_id: "en" | "hi" | "ta" | "te" }
user_weavers = {}    # { user_id: weaver_profile_id }

# Multilingual UI Strings
STRINGS = {
    "en": {
        "choose_lang": "🌐 *Select your language / अपनी भाषा चुनें:*",
        "prompt_login": "🙏 Namaste! Welcome to *Karigar Sahayak* (AI Neobank Assistant).\n\nPlease select your language, then type your unique **KarigarID** to login (e.g., `K-101` or `K-102`):",
        "login_success": "🔓 *Login Successful!*\n\n👤 *Karigar Profile Credentials:*\n• *KarigarID:* `{karigar_id}`\n• *Name:* {name}\n• *Cooperative:* {coop}\n• *UPI ID:* {upi}\n• *Aadhar Linked:* Yes (Verified ✅)\n\nYou have unlocked neobank access. Select an option from the keyboard below to begin.",
        "login_fail": "❌ *KarigarID Not Found.*\n\nPlease check the ID and enter a valid one (e.g. `K-101` or `K-102`):",
        "auth_required": "🔒 *Access Locked.*\n\nPlease type your **KarigarID** to unlock neobank services.",
        "lang_selected": "🌐 Language set to **English**.",
        "balance": "💼 *Karigar Wallet Balance*\n\n• *Available Balance:* ₹{wallet:,.2f}\n• *Monsoon Reserve Vault (Savings):* ₹{savings:,.2f}\n\n_5% of all cooperative payments are automatically swept into your Monsoon Reserve vault._",
        "lci_report": "📈 *Livelihood Capital Index (LCI) Report*\n\n• *Your Credit Score:* `{score}` / 900\n• *Risk Rating Band:* *{band}*\n• *Pre-approved Credit Limit:* ₹{limit:,.2f}\n\n💡 *Financial Nudge:*\n_{nudge}_",
        "loans_welcome": "🧶 *Loans & Credit Portal*\n\nYour LCI Credit Score supports micro-credit. Select an option below to inspect active/previous loans or apply for yarn capital.",
        "active_loans_header": "\n📋 *Active Loom Loans:*",
        "no_active_loans": "\n❌ _No active loans._",
        "prev_loans_header": "\n📋 *Previous Loan History:*",
        "no_prev_loans": "\n❌ _No previous loan history._",
        "apply_loan_welcome": "✍️ *Apply for Micro-Credit*\n\n• *Pre-approved Limit:* ₹{limit:,.2f}\n\nPlease select a pre-configured package below or type your custom amount (e.g., *\"loan for 5k\"* or *\"loan for 15000\"*):",
        "suraksha_vault": "🛡️ *Suraksha & Savings Overview*\n\n• *Monsoon Reserve Swept Funds:* ₹{savings:,.2f}\n• *Loom Suraksha Status:* {status}\n• *Active Emergency Coverage:* {cover}\n• *Premium Rate:* ₹10/month\n\n_Use the buttons below to toggle coverage or simulate a month passage (premium deduction)._",
        "govt_schemes": "🏛️ *Indian Government Schemes for Weavers*\n\n• *Bunkar Mudra Yojana*:\n  - Direct subvention of 6% interest rate.\n  - Financial support up to ₹10,000 for yarn.\n  - MUDRA loans up to ₹2.00 Lakhs.\n\n• *Hathkargha Samvardhan Sahayata (HSS)*:\n  - Direct financial sharing for technical loom upgradation.\n  - Government covers 90% of loom tech cost.\n\n• *Yarn Supply Scheme (YSS)*:\n  - Freight-free delivery of high-quality yarn at mill gate price.\n  - 10% price subsidy for silk & cotton yarn.\n\n• *National Handloom Development Programme (NHDP)*:\n  - Block-level clusters receive funding up to ₹2.00 Crore for design studios and weaving infrastructure.",
        "loan_active_err": "❌ *Active Loan Outstanding*\nYou already have an active loan with ₹{outstanding:,.2f} outstanding. Please repay this loan before taking a new one.",
        "loan_limit_err": "❌ *Limit Exceeded*\nRequested loan of ₹{amount:,.2f} exceeds your pre-approved credit limit of ₹{limit:,.2f}.",
        "loan_success": "🧶 *Loom Loan Approved & Disbursed!*\n\n• *Disbursed Amount:* ₹{amount:,.2f}\n• *Yarn Supplier:* Varanasi Weaving Mills (settled off-wallet)\n• *Repayment:* 15% automatic sweep from cooperative sales.",
        "sale_success": "💸 *Cooperative Payment Received*\n\n• *Total Sale Revenue:* ₹{amount:,.2f}\n• *Monsoon Reserve Sweep (5%):* -₹{sweep:,.2f}\n{repay_info}• *Net Released to Wallet:* +₹{weaver_share:,.2f}\n\n💼 *New Wallet Balance:* ₹{wallet:,.2f}\n🐷 *Monsoon Savings Vault:* ₹{savings:,.2f}",
        "voice_success": "🎙️ *AI Speech Engine Transcription*\n🗣️ *Heard:* \"{text}\"\n\n",
        "voice_fail": "🎙️ *Voice Note Received ({dur}s)*\n\nI couldn't transcribe the speech clearly. What action would you like to perform?",
        "unknown_nlp": "🤖 I read your request: *\"{text}\"*\n\nI can help you borrow loans (e.g. *\"loan for 5k\"*), check balance, check score, or simulate sales (e.g. *\"sale of 10000\"*).",
        "welcome": "👋 Namaste *{name}*!\nWelcome back to your **KarigarPay** Neobank Dashboard.\n\nCooperative: *{coop}*\n\nChoose an option from the menu below:",
        "prompt_sale_amount": "💸 *Simulate Saree Sale*\n\nPlease specify a valid sale amount (e.g. \"sale of 10000\" or \"sale of 5k\")."
    },
    "hi": {
        "choose_lang": "🌐 *अपनी भाषा चुनें:*",
        "prompt_login": "🙏 नमस्ते! *कारीगर सहायक* (नियॉबैंक असिस्टेंट) में आपका स्वागत है।\n\nकृपया अपनी भाषा चुनें, फिर लॉग इन करने के लिए अपना **KarigarID** टाइप करें (जैसे `K-101` या `K-102`):",
        "login_success": "🔓 *लॉगिन सफल!*\n\n👤 *कारीगर विवरण:*\n• *KarigarID:* `{karigar_id}`\n• *नाम:* {name}\n• *सहकारी समिति:* {coop}\n• *UPI ID:* {upi}\n• *आधार लिंक्ड:* हाँ (सत्यापित ✅)\n\nनेओबैंक सेवाओं तक पहुंच अनलॉक हो गई है। नीचे दिए गए मेनू से विकल्प चुनें।",
        "login_fail": "❌ *KarigarID नहीं मिला.*\n\nकृपया आईडी की जांच करें और एक सही आईडी दर्ज करें (जैसे `K-101` या `K-102`):",
        "auth_required": "🔒 *पहुंच अवरुद्ध.*\n\nकृप्या नेओबैंक सेवाओं के लिए पहले अपना **KarigarID** दर्ज करें।",
        "lang_selected": "🌐 भाषा **हिंदी** सेट की गई है।",
        "balance": "💼 *कारीगर वॉलेट बैलेंस*\n\n• *उपलब्ध बैलेंस:* ₹{wallet:,.2f}\n• *मानसून रिज़र्व वॉल्ट:* ₹{savings:,.2f}",
        "lci_report": "📈 *LCI क्रेडिट स्कोर रिपोर्ट*\n\n• *स्कोर:* `{score}` / 900\n• *रेटिंग:* *{band}*\n• *पूर्व-स्वीकृत सीमा:* ₹{limit:,.2f}\n\n💡 *वित्तीय सुझाव:*\n_{nudge}_",
        "loans_welcome": "🧶 *ऋण एवं क्रेडिट पोर्टल*\n\nसक्रिय/पिछले ऋणों की जांच करने या नए ऋण के लिए आवेदन करने के लिए विकल्प चुनें।",
        "active_loans_header": "\n📋 *सक्रिय ऋण (Active Loans):*",
        "no_active_loans": "\n❌ _कोई सक्रिय ऋण नहीं है।_",
        "prev_loans_header": "\n📋 *पिछले ऋणों का इतिहास:*",
        "no_prev_loans": "\n❌ _कोई पिछला इतिहास नहीं है।_",
        "apply_loan_welcome": "✍️ *ऋण के लिए आवेदन करें*\n\n• *पूर्व-स्वीकृत सीमा:* ₹{limit:,.2f}\n\nकृपया नीचे से एक ऋण पैकेज चुनें या अपनी राशि टाइप करें (उदा. *\"5000 का लोन\"*):",
        "suraksha_vault": "🛡️ *सुरक्षा और बचत*\n\n• *मानसून बचत कोष:* ₹{savings:,.2f}\n• *लूम सुरक्षा नामांकन:* {status}\n• *सक्रिय आपातकालीन सुरक्षा:* {cover}\n• *प्रीमियम दर:* ₹10/माह",
        "govt_schemes": "🏛️ *बुनकरों के लिए भारतीय सरकारी योजनाएं*\n\n• *बुनकर मुद्रा योजना*:\n  - 6% की रियायती ब्याज दर।\n  - धागे के लिए ₹10,000 की वित्तीय सहायता।\n  - ₹2.00 लाख तक का मुद्रा लोन।\n\n• *हथकरघा संवर्धन सहायता (HSS)*:\n  - लूम अपग्रेड के लिए 90% सरकारी सब्सिडी।",
        "loan_active_err": "❌ *बकाया ऋण मौजूद है*\nआपके पास पहले से ऋण बकाया है।",
        "loan_limit_err": "❌ *सीमा से अधिक*\n₹{amount:,.2f} आपकी स्वीकृत सीमा ₹{limit:,.2f} से अधिक है।",
        "loan_success": "🧶 *ऋण स्वीकृत!*\n\n• *वितरित राशि:* ₹{amount:,.2f}\n• *ऑटो-पेमेंट:* बिक्री से 15% की कटौती की जाएगी।",
        "sale_success": "💸 *सहकारी भुगतान प्राप्त हुआ*\n\n• *कुल बिक्री आय:* ₹{amount:,.2f}\n• *मानसून बचत (5%):* -₹{sweep:,.2f}\n{repay_info}• *वॉलेट में जमा:* +₹{weaver_share:,.2f}\n\n💼 *नया वॉलेट बैलेंस:* ₹{wallet:,.2f}\n🐷 *मानसून बचत:* ₹{savings:,.2f}",
        "voice_success": "🎙️ *AI वॉयस ट्रांसक्रिप्शन*\n🗣️ *सुना:* \"{text}\"\n\n",
        "voice_fail": "🎙️ *वॉयस मैसेज प्राप्त हुआ ({dur}s)*\n\nआवाज स्पष्ट नहीं थी। आप क्या करना चाहते हैं?",
        "unknown_nlp": "🤖 आपकी पोस्ट: *\"{text}\"*",
        "welcome": "👋 नमस्ते *{name}*!\nआपके **KarigarPay** नेओबैंक डैशबोर्ड पर आपका स्वागत है।\n\nसहकारी समिति: *{coop}*\n\nनीचे दिए गए मेनू से एक विकल्प चुनें:",
        "prompt_sale_amount": "💸 *बिक्री सिमुलेशन*\n\nकृपया एक सही बिक्री राशि दर्ज करें (जैसे \"10000 की बिक्री\" या \"5k की बिक्री\")."
    }
}

def get_db():
    db = SessionLocal()
    try:
        return db
    except Exception as e:
        logger.error(f"Database error: {e}")
        return None

def get_weaver_and_lci_by_id(db, weaver_db_id):
    weaver = db.query(WeaverProfile).filter(WeaverProfile.id == weaver_db_id).first()
    logs = db.query(ProductionLogs).filter(ProductionLogs.weaver_id == weaver_db_id).order_by(ProductionLogs.log_id).all()
    months_production = [log.units_woven for log in logs]
    if not months_production:
        months_production = [36, 35, 34, 37, 36, 35, 20, 18, 22, 34, 36, 35]
        
    lci = lci_engine.compute_lci(
        months_production=months_production,
        fulfillment=weaver.fulfillment_score,
        coop=weaver.coop_score,
        digital=weaver.digital_score,
        govt=weaver.govt_score,
        monsoon_adjustment_enabled=True
    )
    return weaver, lci

def get_main_keyboard():
    keyboard = [
        ["📊 Check Balance", "📈 My Credit Score"],
        ["🧶 Loans", "🛡️ Suraksha & Savings"],
        ["🏛️ Govt Schemes", "💸 Simulate Sale"],
        ["🌐 Language / भाषा"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_language_flashcard_inline():
    keyboard = [
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"), InlineKeyboardButton("🇮🇳 हिंदी (Hindi)", callback_data="lang_hi")],
        [InlineKeyboardButton("🇮🇳 தமிழ் (Tamil)", callback_data="lang_ta"), InlineKeyboardButton("🇮🇳 తెలుగు (Telugu)", callback_data="lang_te")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_voice_actions_inline():
    keyboard = [
        [InlineKeyboardButton("🧶 Loan ₹5,000", callback_data="voice_loan_5000"), InlineKeyboardButton("🧶 Loan ₹10,000", callback_data="voice_loan_10000")],
        [InlineKeyboardButton("🧶 Loan ₹20,000", callback_data="voice_loan_20000"), InlineKeyboardButton("💸 Sale ₹10,000", callback_data="voice_sale_10000")],
        [InlineKeyboardButton("📊 Check Balance", callback_data="voice_bal"), InlineKeyboardButton("📈 View Score", callback_data="voice_score")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_loans_actions_inline():
    keyboard = [
        [InlineKeyboardButton("📋 View Loans", callback_data="loan_view_all")],
        [InlineKeyboardButton("✍️ Apply for Loan", callback_data="loan_apply_portal")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_loan_apply_inline(limit):
    keyboard = []
    if limit >= 3000:
        keyboard.append([InlineKeyboardButton("🧶 Apply ₹3,000", callback_data="voice_loan_3000")])
    if limit >= 5000:
        keyboard.append([InlineKeyboardButton("🧶 Apply ₹5,000", callback_data="voice_loan_5000")])
    if limit >= 10000:
        keyboard.append([InlineKeyboardButton("🧶 Apply ₹10,000", callback_data="voice_loan_10000")])
    
    keyboard.append([InlineKeyboardButton("🔙 Back to Loans", callback_data="loan_back_menu")])
    return InlineKeyboardMarkup(keyboard)

def get_suraksha_actions_inline(enrolled):
    label = "Toggle Off Coverage" if enrolled else "Toggle On Coverage"
    keyboard = [
        [InlineKeyboardButton(label, callback_data="suraksha_toggle_status")],
        [InlineKeyboardButton("📅 Simulate 1 Month", callback_data="suraksha_sim_month")]
    ]
    return InlineKeyboardMarkup(keyboard)

# -------------------------------------------------------------
# DYNAMIC NLP AMOUNT & INTENT PARSER
# -------------------------------------------------------------
def extract_amount(text):
    text = text.lower().replace(",", "")
    
    k_match = re.search(r'(\d+(?:\.\d+)?)\s*k\b', text)
    if k_match:
        return float(k_match.group(1)) * 1000.0
        
    th_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:thousand|lakh|हजार|ஆயிரம்|வேలు)', text)
    if th_match:
        val = float(th_match.group(1))
        if 'lakh' in text:
            return val * 100000.0
        return val * 1000.0

    num_match = re.search(r'(?:₹|rs\.?|inr)?\s*(\d{3,7})', text)
    if num_match:
        return float(num_match.group(1))
        
    return None

def parse_nlp_intent(text):
    t = text.lower()
    
    if any(k in t for k in ["language", "bhasha", "भाषा", "மொழி", "భావన", "lang"]):
        return "LANGUAGE"
        
    if any(k in t for k in ["loan", "borrow", "yarn", "need money", "disburse", "credit", "ऋण", "उधार", "धागा", "கடன்", "అప్పు"]):
        return "LOAN"
        
    if any(k in t for k in ["balance", "wallet", "savings", "money", "बैलेंस", "रुपये", "இருப்பு", "பணம்", "నిల్వ"]):
        return "BALANCE"
        
    if any(k in t for k in ["score", "lci", "cibil", "rating", "limit", "स्कोर", "रेटिंग", "மதிப்பெண்", "స్కోర్"]):
        return "SCORE"
        
    if any(k in t for k in ["sale", "income", "payment", "received", "saree", "sold", "बिक्री", "कमाई", "விற்பனை", "అమ్మకం"]):
        return "SALE"
        
    return "UNKNOWN"

# -------------------------------------------------------------
# CORE ACTIONS (USER AUTHENTICATED)
# -------------------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = user_languages.get(user_id, "en")
    strings = STRINGS.get(lang, STRINGS["en"])
    
    # Check if user is logged in
    if user_id not in user_weavers:
        # Prompt login
        await update.message.reply_text(strings["prompt_login"], parse_mode="Markdown")
        await update.message.reply_text(strings["choose_lang"], reply_markup=get_language_flashcard_inline(), parse_mode="Markdown")
        return
        
    # Logged in -> Greet normally
    db = get_db()
    weaver = db.query(WeaverProfile).filter(WeaverProfile.id == user_weavers[user_id]).first()
    db.close()
    
    txt = strings["welcome"].format(name=weaver.name, coop=weaver.cooperative_name)
    await update.message.reply_text(txt, reply_markup=get_main_keyboard(), parse_mode="Markdown")

async def language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    code = query.data.replace("lang_", "")
    user_languages[user_id] = code
    strings = STRINGS.get(code, STRINGS["en"])
    
    await query.edit_message_text(strings["lang_selected"], parse_mode="Markdown")

async def execute_loan_menu(update, context):
    user_id = update.effective_user.id
    lang = user_languages.get(user_id, "en")
    strings = STRINGS.get(lang, STRINGS["en"])
    
    send_message = update.callback_query.message.reply_text if update.callback_query else update.message.reply_text
    await send_message(strings["loans_welcome"], reply_markup=get_loans_actions_inline(), parse_mode="Markdown")

async def execute_view_all_loans(update, context):
    user_id = update.effective_user.id
    lang = user_languages.get(user_id, "en")
    strings = STRINGS.get(lang, STRINGS["en"])
    
    send_message = update.callback_query.message.reply_text if update.callback_query else update.message.reply_text
    
    db = get_db()
    if not db:
        await send_message("Database connection error.")
        return
        
    weaver_db_id = user_weavers[user_id]
    
    # Active Loans
    active_loans = db.query(ActiveLoans).filter(ActiveLoans.weaver_id == weaver_db_id, ActiveLoans.is_active == True).all()
    # Previous Completed Loans
    previous_loans = db.query(ActiveLoans).filter(ActiveLoans.weaver_id == weaver_db_id, ActiveLoans.is_active == False).all()
    db.close()
    
    response = "📊 *Karigar Loans Overview*\n"
    
    # Render Active Loans
    response += strings["active_loans_header"] + "\n"
    if active_loans:
        for loan in active_loans:
            response += f"• *Loan ID:* `LN-{loan.loan_id}`\n  - *Principal:* ₹{loan.principal:,.2f}\n  - *Outstanding Balance:* ₹{loan.outstanding_balance:,.2f}\n  - *Auto-Repayment Split:* {loan.emi_split_percentage}%\n"
    else:
        response += strings["no_active_loans"] + "\n"
        
    # Render Previous Loans
    response += strings["prev_loans_header"] + "\n"
    if previous_loans:
        for loan in previous_loans:
            response += f"• *Loan ID:* `LN-{loan.loan_id}`\n  - *Principal Amount:* ₹{loan.principal:,.2f}\n  - *Status:* Fully Settled & Closed ✅\n"
    else:
        response += strings["no_prev_loans"] + "\n"
        
    await send_message(response, parse_mode="Markdown")

async def execute_apply_loan_portal(update, context):
    user_id = update.effective_user.id
    lang = user_languages.get(user_id, "en")
    strings = STRINGS.get(lang, STRINGS["en"])
    
    send_message = update.callback_query.message.reply_text if update.callback_query else update.message.reply_text
    
    db = get_db()
    _, lci = get_weaver_and_lci_by_id(db, user_weavers[user_id])
    db.close()
    
    limit = lci["loan_limit"]
    txt = strings["apply_loan_welcome"].format(limit=limit)
    await send_message(txt, reply_markup=get_loan_apply_inline(limit), parse_mode="Markdown")

async def execute_suraksha_savings_portal(update, context):
    user_id = update.effective_user.id
    lang = user_languages.get(user_id, "en")
    strings = STRINGS.get(lang, STRINGS["en"])
    
    send_message = update.callback_query.message.reply_text if update.callback_query else update.message.reply_text
    
    db = get_db()
    weaver = db.query(WeaverProfile).filter(WeaverProfile.id == user_weavers[user_id]).first()
    db.close()
    
    status_label = "Active ✅" if weaver.loom_suraksha_enrolled else "Not Enrolled ❌"
    cover_label = "₹2,000 parametric emergency protection active" if weaver.loom_suraksha_enrolled else "No cover"
    
    txt = strings["suraksha_vault"].format(
        savings=weaver.monsoon_savings_balance,
        status=status_label,
        cover=cover_label
    )
    await send_message(txt, reply_markup=get_suraksha_actions_inline(weaver.loom_suraksha_enrolled), parse_mode="Markdown")

async def execute_gov_schemes_directory(update, context):
    user_id = update.effective_user.id
    lang = user_languages.get(user_id, "en")
    strings = STRINGS.get(lang, STRINGS["en"])
    
    send_message = update.callback_query.message.reply_text if update.callback_query else update.message.reply_text
    await send_message(strings["govt_schemes"], parse_mode="Markdown")

async def execute_loan_action(update, context, amount=None):
    user_id = update.effective_user.id
    lang = user_languages.get(user_id, "en")
    strings = STRINGS.get(lang, STRINGS["en"])
    
    send_message = update.callback_query.message.reply_text if update.callback_query else update.message.reply_text
    
    db = get_db()
    weaver_db_id = user_weavers[user_id]
    weaver, lci = get_weaver_and_lci_by_id(db, weaver_db_id)
    available_limit = lci["loan_limit"]
    
    existing_loan = db.query(ActiveLoans).filter(ActiveLoans.weaver_id == weaver.id, ActiveLoans.is_active == True).first()
    if existing_loan:
        txt = strings["loan_active_err"].format(outstanding=existing_loan.outstanding_balance)
        await send_message(txt, parse_mode="Markdown")
        db.close()
        return
        
    if amount is None or amount <= 0:
        txt = strings["prompt_loan_amount"].format(limit=available_limit)
        await send_message(txt, parse_mode="Markdown")
        db.close()
        return
        
    if amount > available_limit:
        txt = strings["loan_limit_err"].format(amount=amount, limit=available_limit)
        await send_message(txt, parse_mode="Markdown")
        db.close()
        return
        
    new_loan = ActiveLoans(
        weaver_id=weaver.id,
        principal=amount,
        outstanding_balance=amount,
        emi_split_percentage=15.0,
        is_active=True
    )
    db.add(new_loan)
    
    db.add(WalletLedger(
        weaver_id=weaver.id,
        type="LN",
        amount=amount,
        description=f"Loom Loan disbursed → Yarn Supplier (AI Assistant)",
        timestamp=datetime.datetime.utcnow()
    ))
    db.commit()
    db.close()
    
    txt = strings["loan_success"].format(amount=amount)
    await send_message(txt, parse_mode="Markdown")

async def execute_sale_action(update, context, amount=None):
    user_id = update.effective_user.id
    lang = user_languages.get(user_id, "en")
    strings = STRINGS.get(lang, STRINGS["en"])
    
    send_message = update.callback_query.message.reply_text if update.callback_query else update.message.reply_text
    
    if amount is None or amount <= 0:
        txt = strings["prompt_sale_amount"]
        await send_message(txt, parse_mode="Markdown")
        return
        
    db = get_db()
    weaver_db_id = user_weavers[user_id]
    weaver = db.query(WeaverProfile).filter(WeaverProfile.id == weaver_db_id).first()
    sale_amount = amount
    
    sweep_amount = round(sale_amount * 0.05, 2)
    
    repay_amount = 0.0
    active_loan = db.query(ActiveLoans).filter(ActiveLoans.weaver_id == weaver.id, ActiveLoans.is_active == True).first()
    
    repay_info = ""
    if active_loan:
        raw_repay = sale_amount * 0.15
        repay_amount = round(min(raw_repay, active_loan.outstanding_balance), 2)
        active_loan.outstanding_balance = round(active_loan.outstanding_balance - repay_amount, 2)
        
        if active_loan.outstanding_balance <= 0.0:
            active_loan.is_active = False
            active_loan.outstanding_balance = 0.0
            repay_info = f"• *Loom Loan Repayment (15%):* -₹{repay_amount:,.2f} *(LOAN FULLY CLEARED!)*\n"
        else:
            repay_info = f"• *Loom Loan Repayment (15%):* -₹{repay_amount:,.2f} (Outstanding: ₹{active_loan.outstanding_balance:,.2f})\n"
            
    weaver_share = round(sale_amount - repay_amount - sweep_amount, 2)
    weaver.wallet_balance = round(weaver.wallet_balance + weaver_share, 2)
    weaver.monsoon_savings_balance = round(weaver.monsoon_savings_balance + sweep_amount, 2)
    
    db.add(WalletLedger(weaver_id=weaver.id, type="CR", amount=sale_amount, description="Cooperative Sale Payout (AI Assist)", timestamp=datetime.datetime.utcnow()))
    db.add(WalletLedger(weaver_id=weaver.id, type="DR", amount=sweep_amount, description="Monsoon Reserve Auto-Sweep (5%)", timestamp=datetime.datetime.utcnow()))
    if repay_amount > 0.0:
        db.add(WalletLedger(weaver_id=weaver.id, type="DR", amount=repay_amount, description="Auto-repayment to Loom Loan (15%)", timestamp=datetime.datetime.utcnow()))
        
    db.commit()
    
    txt = strings["sale_success"].format(
        amount=sale_amount,
        sweep=sweep_amount,
        repay_info=repay_info,
        weaver_share=weaver_share,
        wallet=weaver.wallet_balance,
        savings=weaver.monsoon_savings_balance
    )
    db.close()
    await send_message(txt, parse_mode="Markdown")

async def execute_balance_action(update, context):
    user_id = update.effective_user.id
    lang = user_languages.get(user_id, "en")
    strings = STRINGS.get(lang, STRINGS["en"])
    send_message = update.callback_query.message.reply_text if update.callback_query else update.message.reply_text
    
    db = get_db()
    weaver = db.query(WeaverProfile).filter(WeaverProfile.id == user_weavers[user_id]).first()
    
    txt = strings["balance"].format(wallet=weaver.wallet_balance, savings=weaver.monsoon_savings_balance)
    db.close()
    await send_message(txt, parse_mode="Markdown")

async def execute_score_action(update, context):
    user_id = update.effective_user.id
    lang = user_languages.get(user_id, "en")
    strings = STRINGS.get(lang, STRINGS["en"])
    send_message = update.callback_query.message.reply_text if update.callback_query else update.message.reply_text
    
    db = get_db()
    weaver, lci = get_weaver_and_lci_by_id(db, user_weavers[user_id])
    
    txt = strings["lci_report"].format(
        score=lci["score"],
        band=lci["band"],
        limit=lci["loan_limit"],
        nudge=lci["voice_nudge"]
    )
    db.close()
    await send_message(txt, parse_mode="Markdown")

# -------------------------------------------------------------
# CALLBACK QUERY ROUTING (INLINE BUTTONS)
# -------------------------------------------------------------
async def inline_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    # 1. Allow language selection callback before login
    if data.startswith("lang_"):
        code = data.replace("lang_", "")
        user_languages[user_id] = code
        strings = STRINGS.get(code, STRINGS["en"])
        await query.edit_message_text(strings["lang_selected"], parse_mode="Markdown")
        return
        
    # 2. Block other callbacks if not logged in
    if user_id not in user_weavers:
        lang = user_languages.get(user_id, "en")
        strings = STRINGS.get(lang, STRINGS["en"])
        await query.message.reply_text(strings["auth_required"], parse_mode="Markdown")
        return
        
    # 3. Route authenticated callback operations
    if data.startswith("voice_loan_"):
        amt = float(data.replace("voice_loan_", ""))
        await execute_loan_action(update, context, amount=amt)
    elif data.startswith("voice_sale_"):
        amt = float(data.replace("voice_sale_", ""))
        await execute_sale_action(update, context, amount=amt)
    elif data == "voice_bal":
        await execute_balance_action(update, context)
    elif data == "voice_score":
        await execute_score_action(update, context)
    elif data == "loan_view_all":
        await execute_view_all_loans(update, context)
    elif data == "loan_apply_portal":
        await execute_apply_loan_portal(update, context)
    elif data == "loan_back_menu":
        await execute_loan_menu(update, context)
    elif data == "suraksha_toggle_status":
        db = get_db()
        weaver = db.query(WeaverProfile).filter(WeaverProfile.id == user_weavers[user_id]).first()
        weaver.loom_suraksha_enrolled = not weaver.loom_suraksha_enrolled
        db.commit()
        db.close()
        await execute_suraksha_savings_portal(update, context)
    elif data == "suraksha_sim_month":
        db = get_db()
        weaver = db.query(WeaverProfile).filter(WeaverProfile.id == user_weavers[user_id]).first()
        if not weaver.loom_suraksha_enrolled:
            await query.message.reply_text("Please enroll in Loom Suraksha first.")
            db.close()
            return
        weaver.wallet_balance -= 10.0
        db.add(WalletLedger(weaver_id=weaver.id, type="DR", amount=10.0, description="Loom Suraksha monthly premium", timestamp=datetime.datetime.utcnow()))
        db.commit()
        db.close()
        await execute_suraksha_savings_portal(update, context)

# -------------------------------------------------------------
# NLP & VOICE MESSAGE PROCESSING
# -------------------------------------------------------------
async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_id = update.effective_user.id
    lang = user_languages.get(user_id, "en")
    strings = STRINGS.get(lang, STRINGS["en"])
    
    # A. LOGIN GATEKEEPER FLOW
    if user_id not in user_weavers:
        # Check if the text matches a seeded KarigarID (K-101 / K-102)
        karigar_id_clean = text.upper()
        db = get_db()
        weaver = db.query(WeaverProfile).filter(WeaverProfile.karigar_id == karigar_id_clean).first()
        db.close()
        
        if weaver:
            # Login Success
            user_weavers[user_id] = weaver.id
            # Load strings in case they chose language before typing ID
            strings = STRINGS.get(lang, STRINGS["en"])
            success_txt = strings["login_success"].format(
                karigar_id=weaver.karigar_id,
                name=weaver.name,
                coop=weaver.cooperative_name,
                upi=weaver.upi_id
            )
            await update.message.reply_text(success_txt, reply_markup=get_main_keyboard(), parse_mode="Markdown")
        else:
            # Login Failed
            await update.message.reply_text(strings["login_fail"], parse_mode="Markdown")
        return
        
    # B. AUTHENTICATED KEYBOARD AND TEXT NLP PORTAL
    # 1. Primary Keyboard Button Clicks
    if "Check Balance" in text or "बैलेंस" in text:
        await execute_balance_action(update, context)
        return
    elif "Credit Score" in text or "स्कोर" in text:
        await execute_score_action(update, context)
        return
    elif "Govt Schemes" in text or "भारतीय सरकारी योजनाएं" in text:
        await execute_gov_schemes_directory(update, context)
        return
    elif "Loans" in text or "ऋण एवं क्रेडिट" in text:
        await execute_loan_menu(update, context)
        return
    elif "Suraksha & Savings" in text or "सुरक्षा और बचत" in text:
        await execute_suraksha_savings_portal(update, context)
        return
    elif "Language" in text or "भाषा" in text:
        await update.message.reply_text(strings["choose_lang"], reply_markup=get_language_flashcard_inline(), parse_mode="Markdown")
        return
        
    # 2. NLP Intent & Amount Parsing
    intent = parse_nlp_intent(text)
    extracted_amt = extract_amount(text)
    
    if intent == "LOAN":
        await execute_loan_action(update, context, amount=extracted_amt)
    elif intent == "SALE":
        await execute_sale_action(update, context, amount=extracted_amt)
    elif intent == "BALANCE":
        await execute_balance_action(update, context)
    elif intent == "SCORE":
        await execute_score_action(update, context)
    elif intent == "LANGUAGE":
        await update.message.reply_text(strings["choose_lang"], reply_markup=get_language_flashcard_inline(), parse_mode="Markdown")
    else:
        txt = strings["unknown_nlp"].format(text=text)
        await update.message.reply_text(txt, parse_mode="Markdown")

async def handle_voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = user_languages.get(user_id, "en")
    strings = STRINGS.get(lang, STRINGS["en"])
    
    # Check audio capabilities
    if not AUDIO_AVAILABLE or not SPEECH_AVAILABLE:
        await update.message.reply_text("🎙️ Voice transcription is disabled in cloud hosting. Please type your message!")
        return

    # Check authentication
    if user_id not in user_weavers:
        await update.message.reply_text(strings["auth_required"], parse_mode="Markdown")
        return
        
    voice = update.message.voice
    duration = voice.duration if voice else 5
    
    ogg_path = f"voice_{user_id}.ogg"
    wav_path = f"voice_{user_id}.wav"
    
    try:
        new_file = await context.bot.get_file(voice.file_id)
        await new_file.download_to_drive(ogg_path)
        
        # OGG to WAV conversion
        data, samplerate = sf.read(ogg_path)
        sf.write(wav_path, data, samplerate)
        
        # speech recognition
        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)
            lang_map = {
                "en": "en-IN",
                "hi": "hi-IN",
                "ta": "ta-IN",
                "te": "te-IN"
            }
            speech_lang = lang_map.get(lang, "en-IN")
            transcribed_text = recognizer.recognize_google(audio_data, language=speech_lang)
    except Exception as e:
        logger.error(f"Speech transcription failure: {e}")
        transcribed_text = ""
    finally:
        # cleanup
        for path in [ogg_path, wav_path]:
            if os.path.exists(path):
                try: os.remove(path)
                except: pass
                
    if transcribed_text.strip():
        # Display transcript & run through NLP
        success_banner = strings["voice_success"].format(text=transcribed_text)
        await update.message.reply_text(success_banner, parse_mode="Markdown")
        
        intent = parse_nlp_intent(transcribed_text)
        extracted_amt = extract_amount(transcribed_text)
        
        if intent == "LOAN":
            await execute_loan_action(update, context, amount=extracted_amt)
        elif intent == "SALE":
            await execute_sale_action(update, context, amount=extracted_amt)
        elif intent == "BALANCE":
            await execute_balance_action(update, context)
        elif intent == "SCORE":
            await execute_score_action(update, context)
        else:
            txt = strings["unknown_nlp"].format(text=transcribed_text)
            await update.message.reply_text(txt, parse_mode="Markdown")
    else:
        # Fall back to interactive buttons
        fail_txt = strings["voice_fail"].format(dur=duration)
        await update.message.reply_text(fail_txt, reply_markup=get_voice_actions_inline(), parse_mode="Markdown")

def main():
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN":
        print("WARNING: TELEGRAM_BOT_TOKEN not set!")
        return

    try:
        import models
        models.seed_data()
    except Exception as e:
        logger.error(f"Seeding failed: {e}")

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Callback & update handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(inline_callback_handler))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_voice_message))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))

    print("Telegram AI Assistant 'Karigar Sahayak' is running with Login verification and Loans/Suraksha portals...")
    app.run_polling()

if __name__ == "__main__":
    main()
