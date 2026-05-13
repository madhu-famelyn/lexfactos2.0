import os
from dotenv import load_dotenv
load_dotenv()

from passlib.context import CryptContext

# Hash the password correctly
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
password = "Sonusah@1234"
hashed_password = pwd_context.hash(password)

print(f"Original password: {password}")
print(f"Hashed password: {hashed_password}")
print()

# Now update the database directly using raw SQL
from config.db.session import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    # Update using raw SQL to avoid the Review model issue
    query = text("""
        UPDATE lawyers 
        SET password = :password 
        WHERE email = :email
    """)
    
    result = db.execute(query, {"password": hashed_password, "email": "ssah75368@gmail.com"})
    db.commit()
    
    print(f"✅ Password updated successfully!")
    print(f"   Email: ssah75368@gmail.com")
    print(f"   New Password: Sonusah@1234")
    print()
    print("Try logging in now with:")
    print(f"   Email: ssah75368@gmail.com")
    print(f"   Password: Sonusah@1234")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
