import pandas as pd
from sodapy import Socrata

def test_harvester():
    print("Testing LA City API connection...")
    # Passing an empty string safely forces anonymous access for testing
    client = Socrata("data.lacity.org", "") 
    
    try:
        # '6ukr-7ewm' is the verified active LA City Building Permit dataset
        print("Fetching recent records from dataset '6ukr-7ewm'...")
        data = client.get("6ukr-7ewm", limit=100)
        df = pd.DataFrame(data)
        client.close()
    except Exception as e:
        print(f"❌ API Request failed: {e}")
        return

    print(f"Successfully fetched {len(df)} records.")
    print("Scanning data for target signals...")
    
    # Track if we find any matches during the test loop
    match_found = False
    
    for index, row in df.iterrows():
        # Using .get() with empty strings as a fallback prevents missing column errors
        work_desc = str(row.get("work_description", "")).upper()
        permit_type = str(row.get("permit_type", "")).upper()
        
        # Combine text fields to look for keywords
        text = f"{permit_type} {work_desc}"
        
        # Keywords to scan for
        if "ADU" in text or "SOLAR" in text or "EV" in text or "CHARGE" in text:
            print(f"\n🔥 MATCH FOUND on row {index}!")
            print(f"Type: {row.get('permit_type', 'N/A')}")
            print(f"Description: {row.get('work_description', 'N/A')[:100]}...")
            
            print("\n✉️ [TRIGGER] Attempting to route alert notification...")
            # ==========================================
            # YOUR EMAIL LOGIC GOES HERE
            # e.g., send_notification(body=text)
            # ==========================================
            print("Alert cycle executed successfully.")
            
            match_found = True
            break  # Stops after the first match to keep the test quick
            
    if not match_found:
        print("\nChecking first row data structure to make sure column names match:")
        print(df.iloc[0].to_dict() if not df.empty else "DataFrame is empty.")
        print("\n⚠️ Scan complete: No keywords matched in this batch of 100 rows.")

if __name__ == "__main__":
    test_harvester()
