"""
Diagnostic + Fix script for lawyer login 401 error.
Run: python fix_lawyer_login.py
"""
import sys
sys.path.insert(0, r'c:\Users\iampr\OneDrive\Desktop\lexfactos2.0')
sys.stdout.reconfigure(encoding='utf-8')

import models.base  # initialize all relationships

from config.db.session import SessionLocal
from models.lawyer.lawyer import Lawyer
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

TARGET_EMAIL = "ssah75368@gmail.com"
NEW_PASSWORD = "Sonusah@1234"  # set the known password here

db = SessionLocal()

try:
    lawyer = db.query(Lawyer).filter(Lawyer.email == TARGET_EMAIL).first()

    if not lawyer:
        print(f"[NOT FOUND] No lawyer with email: {TARGET_EMAIL}")
        sys.exit(1)

    print(f"[FOUND] Lawyer record located")
    print(f"  ID     : {lawyer.id}")
    print(f"  Name   : {lawyer.full_name}")
    print(f"  Email  : {lawyer.email}")
    print(f"  Status : {lawyer.status}")
    print(f"  Role   : {lawyer.role}")
    print(f"  PW hash: {lawyer.password[:60]}...")

    is_bcrypt = lawyer.password.startswith("$2b$") or lawyer.password.startswith("$2a$")
    print(f"  Is bcrypt hash? {is_bcrypt}")

    try:
        match = pwd_context.verify(NEW_PASSWORD, lawyer.password)
        print(f"  Password '{NEW_PASSWORD}' matches stored hash? {match}")
    except Exception as e:
        print(f"  [WARNING] verify() error: {e}")
        match = False

    if match:
        print("\n[OK] Password is already correct - login should work.")
        print("  -> The 401 may be caused by wrong password typed on frontend,")
        print("     or the lawyer status is not 'approved'.")
    else:
        print(f"\n[MISMATCH] Resetting password to: '{NEW_PASSWORD}'")
        lawyer.password = pwd_context.hash(NEW_PASSWORD)
        db.commit()
        db.refresh(lawyer)

        verify_ok = pwd_context.verify(NEW_PASSWORD, lawyer.password)
        if verify_ok:
            print("[SUCCESS] Password reset and verified!")
        else:
            print("[ERROR] Something went wrong during reset.")

finally:
    db.close()
