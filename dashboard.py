```python
# LA Permit Dashboard - Full Version with Policy Indicators
import streamlit as st
import pandas as pd
import plotly.express as px
from sodapy import Socrata
import os

st.set_page_config(page_title="LA Permit Forecaster", layout="wide")
st.title("🏛️ LA Building Permit Forecaster")

@st.cache_data(ttl=3600)
def fetch_permits():
    client = Socrata("data.lacity.org", None)
    data = client.get("n3xg-rixm", limit=20000)
    client.close()
    return pd.DataFrame(data)

@st.cache_data(ttl=3600)
def classify_permits(df):
    def classify(row):
        work = str(row.get('work_desc', ''))
        ptype = str(row.get('permit_type', ''))
        text = (work + ' ' + ptype).upper()
        
        if 'ADU' in text or 'ACCESSORY DWELLING' in text:
            return 'ADU'
        elif 'SOLAR' in text or 'PV' in text:
            return 'Solar + Storage'
        elif 'EV' in text or 'CHARGING' in text:
            return 'EV Charging'
        else:
            du = row.get('du_changed', 0)
            if du:
                try:
                    du_int = int(float(du))
                    if 5 <= du_int <= 50:
                        return 'Small Multifamily'
                except:
                    pass
            return 'Other'
    
    df['vertical'] = df.apply(classify, axis=1)
    return df

# Load data
df = fetch_permits()
df = classify_permits(df)

st.success(f"✅ Loaded {len(df):,} permits")

# Metrics
col1, col2, col3, col4, col5 = st.columns(5)
total = len(df)
col1.metric("Total Permits", f"{total:,}")
col2.metric("ADU", f"{len(df[df['vertical'] == 'ADU']):,}")
col3.metric("Solar", f"{len(df[df['vertical'] == 'Solar + Storage']):,}")
col4.metric("EV Charging", f"{len(df[df['vertical'] == 'EV Charging']):,}")
col5.metric("Small Multi", f"{len(df[df['vertical'] == 'Small Multifamily']):,}")

# Pie chart
if total > 0:
    fig = px.pie(df, names='vertical', title='Permits by Vertical', hole=0.4)
    st.plotly_chart(fig, use_container_width=True)

# ============================================
# NEW: Policy Indicators Section
# ============================================
st.subheader("📜 Policy & Zoning Indicators")

# Load keyword tracking results
if os.path.exists("data/keywords_index/keywords_tracked.csv"):
    keywords_df = pd.read_csv("data/keywords_index/keywords_tracked.csv")
    tracked = keywords_df['keyword'].tolist() if 'keyword' in keywords_df.columns else []
    
    policy_categories = {
        "ADU Laws": ["ADU Ordinance", "SB13", "SB 13"],
        "Density/Zoning": ["Density Bonus", "Upzoning", "REZONE", "Mixed-Use Overlay", "SB9", "SB-9"],
        "Housing Mandates": ["RHNA", "Builders Remedy", "SB35", "SB-35", "SB1000"],
        "Environmental": ["CEQA", "California Title 24", "Title 24"],
        "Land Use": ["General Plan", "Zoning Capacity", "Opportunity Zone"],
    }
    
    for category, keywords in policy_categories.items():
        found = [k for k in keywords if any(k.lower() in str(t).lower() for t in tracked)]
        st.metric(category, f"{len(found)}/{len(keywords)} active")
else:
    st.info("Policy tracking data will appear after GitHub Actions runs")

# Load alerts if they exist
alert_files = []
if os.path.exists("data/keywords_index"):
    alert_files = [f for f in os.listdir("data/keywords_index") if f.startswith("alerts_")]

if alert_files:
    with st.expander("🚨 Recent Policy Alerts"):
        latest_alert = sorted(alert_files)[-1]
        alerts_df = pd.read_csv(f"data/keywords_index/{latest_alert}")
        st.dataframe(alerts_df)

# Download button
csv = df.to_csv(index=False).encode('utf-8')
st.download_button("📥 Download CSV", csv, "permits.csv", "text/csv")
```
    
