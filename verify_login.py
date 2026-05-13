import requests
import json

# Test login with the fixed password
payload = {
    "email": "ssah75368@gmail.com",
    "password": "Sonusah@1234",
    "role": "lawyer"
}

print("Testing login with updated password...")
print(json.dumps(payload, indent=2))
print()

response = requests.post(
    "http://127.0.0.1:8000/auth/login",
    json=payload,
    timeout=15
)

print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print("✅ LOGIN SUCCESSFUL!")
    print(f"   User: {data['user']['full_name']}")
    print(f"   Email: {data['user']['email']}")
    print(f"   Token: {data['token']['access_token'][:50]}...")
else:
    print(f"Response: {json.dumps(response.json(), indent=2)}")
