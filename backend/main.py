import datetime
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from database import get_db, engine
import models
from models import WeaverProfile, WalletLedger, ProductionLogs, ActiveLoans
import lci_engine

app = FastAPI(title="KarigarPay Backend", version="1.0.0")

# Enable CORS for frontend connection (Expo)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import subprocess
import threading
import sys
import os
import traceback

bot_status_info = {"status": "not started", "error": None}

@app.on_event("startup")
def startup_event():
    if "PORT" in os.environ:
        print("Render environment detected. Launching Telegram Bot in background...")
        bot_status_info["status"] = "starting"
        def run_bot():
            try:
                base_dir = os.path.dirname(os.path.abspath(__file__))
                bot_path = os.path.join(base_dir, "telegram_bot.py")
                # Run the process and capture output if it fails
                result = subprocess.run(
                    [sys.executable, bot_path],
                    capture_output=True,
                    text=True,
                    check=True
                )
                bot_status_info["status"] = "finished successfully"
                bot_status_info["stdout"] = result.stdout
            except subprocess.CalledProcessError as e:
                bot_status_info["status"] = "crashed"
                bot_status_info["error"] = str(e)
                bot_status_info["stdout"] = e.stdout
                bot_status_info["stderr"] = e.stderr
            except Exception as e:
                bot_status_info["status"] = "failed to launch"
                bot_status_info["error"] = str(e)
                bot_status_info["traceback"] = traceback.format_exc()
        
        threading.Thread(target=run_bot, daemon=True).start()

@app.get("/api/bot-status")
def get_bot_status():
    return bot_status_info


# Pydantic schemas
class LoanRequest(BaseModel):
    amount: float

class SaleSimulation(BaseModel):
    amount: float
    description: str

class InsuranceToggle(BaseModel):
    enrolled: bool

class ClaimRequest(BaseModel):
    type: str  # "loom" or "health"

def get_weaver_lci_details(db: Session, weaver_id: int = 1):
    weaver = db.query(WeaverProfile).filter(WeaverProfile.id == weaver_id).first()
    if not weaver:
        raise HTTPException(status_code=404, detail="Weaver profile not found")
    
    # Fetch 12 months production logs
    logs = db.query(ProductionLogs).filter(ProductionLogs.weaver_id == weaver_id).order_by(ProductionLogs.log_id).all()
    months_production = [log.units_woven for log in logs]
    
    # Handle case where logs don't exist yet
    if not months_production:
        months_production = [36, 35, 34, 37, 36, 35, 20, 18, 22, 34, 36, 35] # default backup
        
    # Calculate LCI metrics
    lci = lci_engine.compute_lci(
        months_production=months_production,
        fulfillment=weaver.fulfillment_score,
        coop=weaver.coop_score,
        digital=weaver.digital_score,
        govt=weaver.govt_score,
        monsoon_adjustment_enabled=True
    )
    
    return weaver, logs, lci

@app.get("/api/weaver")
def get_weaver(db: Session = Depends(get_db)):
    weaver, logs, lci = get_weaver_lci_details(db)
    
    # Fetch active loan if any
    active_loan = db.query(ActiveLoans).filter(
        ActiveLoans.weaver_id == weaver.id, 
        ActiveLoans.is_active == True
    ).first()
    
    loan_data = None
    if active_loan:
        loan_data = {
            "loan_id": active_loan.loan_id,
            "principal": active_loan.principal,
            "outstanding_balance": active_loan.outstanding_balance,
            "emi_split_percentage": active_loan.emi_split_percentage,
            "is_active": active_loan.is_active
        }
        
    return {
        "profile": {
            "id": weaver.id,
            "name": weaver.name,
            "cooperative_name": weaver.cooperative_name,
            "aadhar_linked": weaver.aadhar_linked,
            "upi_id": weaver.upi_id,
            "wallet_balance": weaver.wallet_balance,
            "monsoon_savings_balance": weaver.monsoon_savings_balance,
            "loom_suraksha_enrolled": weaver.loom_suraksha_enrolled,
            "scores": {
                "fulfillment": weaver.fulfillment_score,
                "coop": weaver.coop_score,
                "digital": weaver.digital_score,
                "govt": weaver.govt_score
            }
        },
        "production_logs": [{"month": log.month, "units_woven": log.units_woven} for log in logs],
        "lci": lci,
        "active_loan": loan_data
    }

@app.get("/api/wallet")
def get_wallet(db: Session = Depends(get_db)):
    weaver = db.query(WeaverProfile).filter(WeaverProfile.id == 1).first()
    if not weaver:
        raise HTTPException(status_code=404, detail="Weaver profile not found")
        
    ledger = db.query(WalletLedger).filter(WalletLedger.weaver_id == weaver.id).order_by(WalletLedger.tx_id.desc()).limit(20).all()
    
    return {
        "wallet_balance": weaver.wallet_balance,
        "monsoon_savings_balance": weaver.monsoon_savings_balance,
        "ledger": [
            {
                "tx_id": t.tx_id,
                "type": t.type,
                "amount": t.amount,
                "description": t.description,
                "timestamp": t.timestamp.isoformat()
            } for t in ledger
        ]
    }

@app.post("/api/loan/buy-yarn")
def buy_yarn(req: LoanRequest, db: Session = Depends(get_db)):
    weaver, _, lci = get_weaver_lci_details(db)
    
    # Check for active loan
    existing_loan = db.query(ActiveLoans).filter(
        ActiveLoans.weaver_id == weaver.id,
        ActiveLoans.is_active == True
    ).first()
    
    if existing_loan:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot disburse loan. You have an active loan with ₹{existing_loan.outstanding_balance:.2f} outstanding."
        )
        
    # Check credit limit
    available_limit = lci["loan_limit"]
    if req.amount > available_limit:
        raise HTTPException(
            status_code=400,
            detail=f"Requested amount ₹{req.amount} exceeds your pre-approved limit of ₹{available_limit}."
        )
        
    # Disburse loan
    new_loan = ActiveLoans(
        weaver_id=weaver.id,
        principal=req.amount,
        outstanding_balance=req.amount,
        emi_split_percentage=15.0,
        is_active=True
    )
    db.add(new_loan)
    
    # Ledger entry - neutral / off-wallet
    ledger_entry = WalletLedger(
        weaver_id=weaver.id,
        type="LN",  # Loan Info
        amount=req.amount,
        description=f"Loom Loan disbursed → Yarn Supplier (off-wallet)",
        timestamp=datetime.datetime.utcnow()
    )
    db.add(ledger_entry)
    db.commit()
    db.refresh(new_loan)
    
    return {
        "status": "success",
        "message": f"Loan of ₹{req.amount} disbursed directly to Yarn Supplier.",
        "loan": {
            "loan_id": new_loan.loan_id,
            "principal": new_loan.principal,
            "outstanding_balance": new_loan.outstanding_balance,
            "is_active": new_loan.is_active
        }
    }

@app.post("/api/simulate-sale")
def simulate_sale(req: SaleSimulation, db: Session = Depends(get_db)):
    weaver = db.query(WeaverProfile).filter(WeaverProfile.id == 1).first()
    if not weaver:
        raise HTTPException(status_code=404, detail="Weaver profile not found")
        
    # Calculate sweep for Monsoon Reserve (5%)
    sweep_amount = round(req.amount * 0.05, 2)
    
    # Calculate repayment if loan active (15%)
    repay_amount = 0.0
    active_loan = db.query(ActiveLoans).filter(
        ActiveLoans.weaver_id == weaver.id,
        ActiveLoans.is_active == True
    ).first()
    
    if active_loan:
        raw_repay = req.amount * 0.15
        repay_amount = round(min(raw_repay, active_loan.outstanding_balance), 2)
        active_loan.outstanding_balance = round(active_loan.outstanding_balance - repay_amount, 2)
        
        if active_loan.outstanding_balance <= 0.0:
            active_loan.is_active = False
            active_loan.outstanding_balance = 0.0
            
    # Calculate final share released to wallet
    weaver_share = round(req.amount - repay_amount - sweep_amount, 2)
    
    # Update profile balances
    weaver.wallet_balance = round(weaver.wallet_balance + weaver_share, 2)
    weaver.monsoon_savings_balance = round(weaver.monsoon_savings_balance + sweep_amount, 2)
    
    # Add ledger entries
    # 1. Total Sale Payout (Credit)
    sale_log = WalletLedger(
        weaver_id=weaver.id,
        type="CR",
        amount=req.amount,
        description=req.description,
        timestamp=datetime.datetime.utcnow()
    )
    db.add(sale_log)
    
    # 2. Monsoon Sweep (Debit)
    sweep_log = WalletLedger(
        weaver_id=weaver.id,
        type="DR",
        amount=sweep_amount,
        description="Monsoon Reserve Auto-Sweep (5%)",
        timestamp=datetime.datetime.utcnow()
    )
    db.add(sweep_log)
    
    # 3. Loan Repayment (Debit, if active)
    if repay_amount > 0.0:
        repay_log = WalletLedger(
            weaver_id=weaver.id,
            type="DR",
            amount=repay_amount,
            description="Auto-repayment to Loom Loan (15%)",
            timestamp=datetime.datetime.utcnow()
        )
        db.add(repay_log)
        
    db.commit()
    
    # Prepare message response
    repay_status = ""
    if repay_amount > 0.0:
        repay_status = f" Repaid ₹{repay_amount:.2f} of Loom Loan. Outstanding: ₹{active_loan.outstanding_balance:.2f}."
        if not active_loan.is_active:
            repay_status += " Loan fully cleared!"
            
    return {
        "status": "success",
        "message": f"Sale of ₹{req.amount:.2f} simulated.{repay_status} Swept ₹{sweep_amount:.2f} to Monsoon Reserve. Wallet received ₹{weaver_share:.2f}.",
        "balances": {
            "wallet_balance": weaver.wallet_balance,
            "monsoon_savings_balance": weaver.monsoon_savings_balance,
            "loan_outstanding": active_loan.outstanding_balance if active_loan else 0.0
        }
    }

@app.post("/api/insurance/toggle")
def toggle_insurance(req: InsuranceToggle, db: Session = Depends(get_db)):
    weaver = db.query(WeaverProfile).filter(WeaverProfile.id == 1).first()
    if not weaver:
        raise HTTPException(status_code=404, detail="Weaver profile not found")
        
    weaver.loom_suraksha_enrolled = req.enrolled
    db.commit()
    
    status_str = "enrolled in" if req.enrolled else "unsubscribed from"
    return {
        "status": "success",
        "message": f"Successfully {status_str} Loom Suraksha.",
        "enrolled": weaver.loom_suraksha_enrolled
    }

@app.post("/api/insurance/simulate-month")
def simulate_month(db: Session = Depends(get_db)):
    weaver = db.query(WeaverProfile).filter(WeaverProfile.id == 1).first()
    if not weaver:
        raise HTTPException(status_code=404, detail="Weaver profile not found")
        
    if not weaver.loom_suraksha_enrolled:
        raise HTTPException(status_code=400, detail="Loom Suraksha coverage is not active. Enroll first.")
        
    # Deduct ₹10 premium
    weaver.wallet_balance = round(weaver.wallet_balance - 10.0, 2)
    
    premium_log = WalletLedger(
        weaver_id=weaver.id,
        type="DR",
        amount=10.0,
        description="Loom Suraksha monthly premium",
        timestamp=datetime.datetime.utcnow()
    )
    db.add(premium_log)
    db.commit()
    
    return {
        "status": "success",
        "message": "Simulated one month passing. ₹10.00 premium deducted.",
        "wallet_balance": weaver.wallet_balance
    }

@app.post("/api/insurance/file-claim")
def file_claim(req: ClaimRequest, db: Session = Depends(get_db)):
    weaver = db.query(WeaverProfile).filter(WeaverProfile.id == 1).first()
    if not weaver:
        raise HTTPException(status_code=404, detail="Weaver profile not found")
        
    if not weaver.loom_suraksha_enrolled:
        raise HTTPException(status_code=400, detail="Cannot file claim. Loom Suraksha is not active.")
        
    # Pay out flat ₹2,000
    weaver.wallet_balance = round(weaver.wallet_balance + 2000.0, 2)
    
    label = "Loom breakdown confirmed by partner repair-shop" if req.type == "loom" else "Hospital admission confirmed by insurer API"
    
    claim_log = WalletLedger(
        weaver_id=weaver.id,
        type="CR",
        amount=2000.0,
        description=f"Loom Suraksha payout: {label}",
        timestamp=datetime.datetime.utcnow()
    )
    db.add(claim_log)
    db.commit()
    
    return {
        "status": "success",
        "message": f"Claim approved! ₹2,000.00 released instantly.",
        "wallet_balance": weaver.wallet_balance
    }

@app.post("/api/reset")
def reset_database(db: Session = Depends(get_db)):
    try:
        # Clear tables
        db.query(WalletLedger).delete()
        db.query(ActiveLoans).delete()
        db.query(ProductionLogs).delete()
        db.query(WeaverProfile).delete()
        db.commit()
        
        # Seed database
        models.seed_data()
        return {"status": "success", "message": "Database reset to original seeded state."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database reset failed: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
