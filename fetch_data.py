# fetch_data.py
import os
import pandas as pd
from sodapy import Socrata

print("Initializing Socrata client for data.lacity.org...")
# We use None for the app_token since we are fetching a public dataset, 
# but it will use the correct dataset endpoint ID.
client = Socrata("data.lacity.org", None)

# Updated, active LA City Permit Dataset ID
dataset_id = "6ffd-by7r" 
print(f"Fetching latest records from dataset: {dataset_id}...")

try:
    # Pulling 20,000 records cleanly
    data = client.get(dataset_id, limit=20000)
    df = pd.DataFrame(data)
    print(f"Successfully retrieved {len(df)} rows.")
    
    # Classification Logic
    def classify_permit(row):
        work_desc = str(row.get("work_description", ""))
        permit_type = str(row.get("permit_type", ""))
        text = (work_desc + " " + permit_type).upper()
        
        if "ADU" in text or "ACCESSORY DWELLING" in text:
            return "ADU"
        if "SOLAR" in text or "PV" in text or "PHOTOVOLTAIC" in text:
            return "Solar + Storage"
        if "EV" in text or "CHARGE" in text or "ELECTRIC VEHICLE" in text:
            return "EV Charging"
        return "Other"

    if not df.empty:
        df["category"] = df.apply(classify_permit, axis=1)
        
        # Ensure the target 'data' directory exists for the GitHub runner
        os.makedirs("data", exist_ok=True)
        
        # Save out to a local repository CSV file
        df.to_csv("data/permits.csv", index=False)
        print("Data processed and written successfully to data/permits.csv")
    else:
        print("Warning: Retrieved dataset was empty.")

except Exception as e:
    print(f"An error occurred during execution: {e}")
    raise e
finally:
    client.close()
