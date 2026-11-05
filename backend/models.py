import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base, engine, SessionLocal

class WeaverProfile(Base):
    __tablename__ = "weaver_profiles"

    id = Column(Integer, primary_key=True, index=True)
    karigar_id = Column(String, unique=True, index=True, nullable=False) # Unique ID (e.g., K-101)
    name = Column(String, nullable=False)
    cooperative_name = Column(String, nullable=False)
    aadhar_linked = Column(Boolean, default=True)
    upi_id = Column(String, nullable=False)
    
    # Financial state cache
    wallet_balance = Column(Float, default=3200.0)
    monsoon_savings_balance = Column(Float, default=0.0)
    loom_suraksha_enrolled = Column(Boolean, default=False)
    
    # Score metrics (0-100 scale)
    fulfillment_score = Column(Float, default=80.0)
    coop_score = Column(Float, default=70.0)
    digital_score = Column(Float, default=65.0)
    govt_score = Column(Float, default=66.0)

class WalletLedger(Base):
    __tablename__ = "wallet_ledger"

    tx_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    weaver_id = Column(Integer, ForeignKey("weaver_profiles.id"), nullable=False)
    type = Column(String, nullable=False)  # "CR" (Credit), "DR" (Debit), "LN" (Loan Info)
    amount = Column(Float, nullable=False)
    description = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

class ProductionLogs(Base):
    __tablename__ = "production_logs"

    log_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    weaver_id = Column(Integer, ForeignKey("weaver_profiles.id"), nullable=False)
    month = Column(String, nullable=False)  # "Jan", "Feb", etc.
    units_woven = Column(Integer, nullable=False)

class ActiveLoans(Base):
    __tablename__ = "active_loans"

    loan_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    weaver_id = Column(Integer, ForeignKey("weaver_profiles.id"), nullable=False)
    principal = Column(Float, nullable=False)
    outstanding_balance = Column(Float, nullable=False)
    emi_split_percentage = Column(Float, default=15.0)
    is_active = Column(Boolean, default=True)

# Create tables
Base.metadata.create_all(bind=engine)

def seed_data():
    db = SessionLocal()
    try:
        # Check if weaver K-101 already seeded
        weaver1 = db.query(WeaverProfile).filter(WeaverProfile.karigar_id == "K-101").first()
        if not weaver1:
            # 1. Seed Weaver Krishnaditya Prakash (K-101)
            weaver1 = WeaverProfile(
                karigar_id="K-101",
                name="Krishnaditya Prakash",
                cooperative_name="Varanasi Silk SHG",
                aadhar_linked=True,
                upi_id="krishnaditya@upi",
                wallet_balance=3200.0,
                monsoon_savings_balance=0.0,
                loom_suraksha_enrolled=False,
                fulfillment_score=80.0,
                coop_score=70.0,
                digital_score=65.0,
                govt_score=66.0
            )
            db.add(weaver1)
            db.commit()
            db.refresh(weaver1)

            # Seed 12 months production logs for K-101
            months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            units_101 = [36, 35, 34, 37, 36, 35, 20, 18, 22, 34, 36, 35]
            for m, u in zip(months, units_101):
                db.add(ProductionLogs(weaver_id=weaver1.id, month=m, units_woven=u))
            
            # Initial Ledger entry
            db.add(WalletLedger(
                weaver_id=weaver1.id,
                type="CR",
                amount=3200.0,
                description="Opening Balance Credit",
                timestamp=datetime.datetime.utcnow()
            ))
            db.commit()

        # Check if weaver K-102 already seeded
        weaver2 = db.query(WeaverProfile).filter(WeaverProfile.karigar_id == "K-102").first()
        if not weaver2:
            # 2. Seed Weaver Xitiz Raj (K-102)
            weaver2 = WeaverProfile(
                karigar_id="K-102",
                name="Xitiz Raj",
                cooperative_name="Varanasi Silk SHG",
                aadhar_linked=True,
                upi_id="xitiz@upi",
                wallet_balance=4500.0,
                monsoon_savings_balance=250.0,
                loom_suraksha_enrolled=True,
                fulfillment_score=85.0,
                coop_score=75.0,
                digital_score=70.0,
                govt_score=80.0
            )
            db.add(weaver2)
            db.commit()
            db.refresh(weaver2)

            # Seed 12 months production logs for K-102 (Different variations)
            months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            units_102 = [40, 42, 39, 41, 40, 42, 22, 19, 24, 41, 42, 40]
            for m, u in zip(months, units_102):
                db.add(ProductionLogs(weaver_id=weaver2.id, month=m, units_woven=u))

            # Initial Ledger entry
            db.add(WalletLedger(
                weaver_id=weaver2.id,
                type="CR",
                amount=4500.0,
                description="Opening Balance Credit",
                timestamp=datetime.datetime.utcnow()
            ))

            # Seed an active loan for K-102 (₹10,000 principal, ₹2,500 outstanding)
            active_loan = ActiveLoans(
                weaver_id=weaver2.id,
                principal=10000.0,
                outstanding_balance=2500.0,
                emi_split_percentage=15.0,
                is_active=True
            )
            db.add(active_loan)

            # Seed a previously completed loan for K-102 (₹5,000 principal, ₹0 outstanding, inactive)
            previous_loan = ActiveLoans(
                weaver_id=weaver2.id,
                principal=5000.0,
                outstanding_balance=0.0,
                emi_split_percentage=15.0,
                is_active=False
            )
            db.add(previous_loan)
            
            # Seed ledger entries showing previous payments
            db.add(WalletLedger(
                weaver_id=weaver2.id,
                type="LN",
                amount=5000.0,
                description="Loom Loan disbursed → Yarn Supplier (Previous Loan)",
                timestamp=datetime.datetime.utcnow() - datetime.timedelta(days=60)
            ))
            db.add(WalletLedger(
                weaver_id=weaver2.id,
                type="DR",
                amount=5000.0,
                description="Completed Loan Repayment (Auto-Escrow Settlement)",
                timestamp=datetime.datetime.utcnow() - datetime.timedelta(days=30)
            ))
            
            db.commit()
            print("Database successfully populated with K-101 and K-102 profiles.")
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
