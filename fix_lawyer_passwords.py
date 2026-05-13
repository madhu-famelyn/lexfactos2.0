"""
Script to hash all lawyer passwords in the database
Run this to fix login issues with existing lawyers
"""
import sys
sys.path.insert(0, r'c:\Users\iampr\OneDrive\Desktop\lexfactos2.0')

import models.base
from config.db.session import SessionLocal
from models.lawyer.lawyer import Lawyer
from service.lawyer.lawyer import LawyerService

db = SessionLocal()

try:
    # Get all lawyers
    lawyers = db.query(Lawyer).all()
    
    if not lawyers:
        print("❌ No lawyers found in database")
        db.close()
        exit()
    
    print(f"Found {len(lawyers)} lawyer(s)")
    print("=" * 60)
    
    updated_count = 0
    
    for lawyer in lawyers:
        # Check if password looks like a hash (bcrypt hashes start with $2a$, $2b$, or $2y$)
        if lawyer.password and not lawyer.password.startswith('$2'):
            print(f"🔄 Hashing password for: {lawyer.full_name} ({lawyer.email})")
            print(f"   Old password: {lawyer.password}")
            
            # Hash the plain text password
            lawyer.password = LawyerService.hash_password(lawyer.password)
            print(f"   New hash: {lawyer.password[:20]}...")
            
            updated_count += 1
        else:
            print(f"✅ {lawyer.full_name} - already hashed")
    
    if updated_count > 0:
        db.commit()
        print("\n" + "=" * 60)
        print(f"✅ Successfully hashed {updated_count} password(s)")
        print("Lawyers can now login with their existing passwords!")
    else:
        print("\n" + "=" * 60)
        print("✅ All passwords are already hashed")
    
    db.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    db.close()
