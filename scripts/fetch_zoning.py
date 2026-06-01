from sodapy import Socrata
import pandas as pd
from datetime import datetime
import os

os.makedirs("data/zoning", exist_ok=True)

client = Socrata("data.lacity.org", None)
zoning = client.get("jjxn-vhan", limit=50000)
client.close()

df = pd.DataFrame(zoning)
df.to_csv("data/zoning/la_city_zoning.csv", index=False)

print(f"✅ Saved {len(df)} zoning records")
