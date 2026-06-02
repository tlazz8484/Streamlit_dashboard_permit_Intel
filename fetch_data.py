# fetch_data.py
import os
import pandas as pd
from sodapy import Socrata

print("Initializing Socrata client for data.lacity.org...")
client = Socrata("data.lacity.org", None)
dataset_id = "6ffd-by7r" 

try:
    print(f"Fetching latest records from dataset: {dataset_id}...")
    data = client.get(dataset_id, limit=20000)
    df = pd.DataFrame(data)
    
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
        os.makedirs("data", exist_ok=True)
        df.to_csv("data/permits.csv", index=False)
        print("Data processed and written successfully to data/permits.csv")
    else:
        print("Warning: Retrieved dataset was empty.")

except Exception as e:
    print(f"An error occurred: {e}")
    raise e
finally:
    client.close()
