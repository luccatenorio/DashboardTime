import os
import base64
import json
from dotenv import load_dotenv

load_dotenv()
key = os.getenv('SUPABASE_KEY')

print(f"Key preview: {key[:10]}...")

try:
    # JWT is header.payload.signature
    parts = key.split('.')
    if len(parts) < 2:
        print("Not a JWT")
    else:
        # Padding for base64
        payload_b64 = parts[1] + '=' * (-len(parts[1]) % 4)
        payload = json.loads(base64.b64decode(payload_b64).decode('utf-8'))
        print(f"Role: {payload.get('role')}")
        print(f"Exp: {payload.get('exp')}")
except Exception as e:
    print(f"Error decoding: {e}")
