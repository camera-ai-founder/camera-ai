import os
import uuid
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

# Connect to the Black Box
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

print("💉 Injecting simulated performance crash into the Black Box...")

# Inject a fake, terrible performance report with a VALID UUID
fake_report = {
    "report_id": str(uuid.uuid4()),
    "timestamp_ms": 999999999,
    "current_fps": 12.5,          
    "dropped_frames": 450,        
    "memory_usage_mb": 850.0,     
    "bottleneck_component": "render" 
}

supabase.table("telemetry_logs").insert(fake_report).execute()
print("✅ Virus injected successfully! The Black Box thinks the engine is dying.")