from dotenv import load_dotenv
import os
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

print("Fetching clients structure...")
try:
    data = supabase.table('clients').select('*').limit(1).execute()
    if data.data:
        print("Columns:", data.data[0].keys())
        print("Sample:", data.data[0])
    else:
        print("Table is empty, cannot infer columns from data.")
except Exception as e:
    print(f"Error: {e}")
