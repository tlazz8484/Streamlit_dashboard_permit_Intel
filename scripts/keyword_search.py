import requests
import pandas as pd
from datetime import datetime
import os
import re

KEYWORDS = [
    "General Plan", "Zoning Code", "Zoning Amendments", "Rezoning", "Upzoning",
    "SB35", "SB-35", "ADU Ordinance", "Builders Remedy", "Density Bonus",
    "Mixed-Use Overlay", "Transit-Oriented", "RHNA", "Zoning Capacity",
    "Opportunity Zone", "SB9", "SB-9", "CEQA", "Nimby", "SB1000",
    "California Title 24", "SB10", "SB-10", "SB13", "SB 13"
]

SOURCES = {
    "LA City Planning": "https://planning.lacity.gov/",
    "LA County Planning": "https://planning.lacounty.gov/",
}

os.makedirs("data/keywords_index", exist_ok=True)

def check_for_alerts():
    results = []
    new_alerts = []
    
    # Load previous hits to avoid duplicate alerts
    previous_file = "data/keywords_index/previous_hits.csv"
    previous_hits = set()
    if os.path.exists(previous_file):
        prev_df = pd.read_csv(previous_file)
        previous_hits = set(zip(prev_df['keyword'], prev_df['source']))
    
    for source_name, source_url in SOURCES.items():
        try:
            response = requests.get(source_url, timeout=30)
            text = response.text.lower()
            
            for keyword in KEYWORDS:
                if keyword.lower() in text:
                    hit_key = (keyword, source_name)
                    results.append({
                        'date': datetime.now().strftime('%Y-%m-%d'),
                        'source': source_name,
                        'url': source_url,
                        'keyword': keyword
                    })
                    
                    # New alert?
                    if hit_key not in previous_hits:
                        new_alerts.append({
                            'keyword': keyword,
                            'source': source_name,
                            'url': source_url
                        })
        except:
            pass
    
    # Save all hits
    df = pd.DataFrame(results)
    df.to_csv(previous_file, index=False)
    
    # Save alerts separately
    if new_alerts:
        alerts_df = pd.DataFrame(new_alerts)
        alert_file = f"data/keywords_index/alerts_{datetime.now().strftime('%Y-%m-%d')}.csv"
        alerts_df.to_csv(alert_file, index=False)
        print(f"🚨 {len(new_alerts)} NEW ALERTS found!")
        for alert in new_alerts:
            print(f"   - {alert['keyword']} at {alert['source']}")
    else:
        print("✅ No new keyword alerts")
    
    return new_alerts

if __name__ == "__main__":
    check_for_alerts()
