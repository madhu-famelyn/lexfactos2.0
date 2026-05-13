"""
Check all lawyers in database
"""
import sys
sys.path.insert(0, r'c:\Users\iampr\OneDrive\Desktop\lexfactos2.0')

import models.base
from config.db.session import SessionLocal
from models.lawyer.lawyer import Lawyer

db = SessionLocal()

try:
    lawyers = db.query(Lawyer).all()
    
    if not lawyers:
        print("❌ No lawyers found")
    else:
        print(f"Found {len(lawyers)} lawyer(s):\n")
        print("=" * 70)
        for i, lawyer in enumerate(lawyers, 1):
            print(f"{i}. {lawyer.full_name}")
            print(f"   Email: {lawyer.email}")
            print(f"   Phone: {lawyer.phone_number}")
            print(f"   Status: {lawyer.status}")
            print()
    
    db.close()
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
