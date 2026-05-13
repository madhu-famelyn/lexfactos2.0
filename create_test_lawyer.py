"""
Create a test lawyer and test login
"""
import sys
sys.path.insert(0, r'c:\Users\iampr\OneDrive\Desktop\lexfactos2.0')

import models.base
from config.db.session import SessionLocal
from models.lawyer.lawyer import Lawyer
from service.lawyer.lawyer import LawyerService
from schemas.lawyer.lawyer import LawyerCreate
import uuid

db = SessionLocal()

try:
    # Create test lawyer
    test_email = "testlawyer@lexfactos.com"
    test_password = "TestPass123"
    
    # Check if already exists
    existing = db.query(Lawyer).filter(Lawyer.email == test_email).first()
    if existing:
        print(f"✅ Test lawyer already exists: {test_email}")
        print(f"   Password: {test_password}")
    else:
        print("Creating test lawyer...")
        lawyer_data = LawyerCreate(
            full_name="Test Lawyer",
            address_line_1="123 Test St",
            city="Test City",
            state="Test State",
            country="Test Country",
            zip_code="123456",
            email=test_email,
            phone_number="9999999999",
            password=test_password
        )
        
        lawyer = LawyerService.create_lawyer(db, lawyer_data)
        print(f"✅ Test lawyer created!")
        print(f"   Email: {lawyer.email}")
        print(f"   Password: {test_password}")
        print(f"   ID: {lawyer.id}")
    
    db.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
