from sodapy import Socrata
import pandas as pd
from datetime import datetime
import os

os.makedirs("data/permits", exist_ok=True)

client = Socrata("data.lacity.org", None)

historical = client.get("n3xg-rixm", limit=50000)
recent = client.get("pi9x-tg5x", limit=50000)
client.close()

df_historical = pd.DataFrame(historical)
df_recent = pd.DataFrame(recent)
df_historical['source'] = '2010-2019'
df_recent['source'] = '2020-present'

df = pd.concat([df_historical, df_recent], ignore_index=True)

today = datetime.now().strftime('%Y-%m-%d')
df.to_csv(f"data/permits/permits_{today}.csv", index=False)
df.to_csv("data/permits/permits_latest.csv", index=False)

print(f"✅ Saved {len(df):,} permits")
