# LA Permit Dashboard - Ultra Clean Version
import streamlit as st
import pandas as pd
import plotly.express as px
from sodapy import Socrata

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
    results = []
    for i in range(len(df)):
        row = df.iloc[i]
        work = str(row.get('work_desc', ''))
        ptype = str(row.get('permit_type', ''))
        text = (work + ' ' + ptype).upper()
        
        if 'ADU' in text or 'ACCESSORY DWELLING' in text:
            results.append('ADU')
        elif 'SOLAR' in text or 'PV' in text:
            results.append('Solar + Storage')
        elif 'EV' in text or 'CHARGING' in text:
            results.append('EV Charging')
        else:
            du = row.get('du_changed', 0)
            if du:
                try:
                    du_int = int(float(du))
                    if 5 <= du_int <= 50:
                        results.append('Small Multifamily')
                    else:
                        results.append('Other')
                except:
                    results.append('Other')
            else:
                results.append('Other')
    
    df['vertical'] = results
    return df

df = fetch_permits()
df = classify_permits(df)

st.success(f"Loaded {len(df):,} permits")

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

# Download
csv = df.to_csv(index=False).encode('utf-8')
st.download_button("Download CSV", csv, "permits.csv", "text/csv")
