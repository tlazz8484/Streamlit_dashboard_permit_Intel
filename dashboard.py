import streamlit as st
import pandas as pd
import plotly.express as px
from sodapy import Socrata

st.set_page_config(layout="wide")
st.title("LA Building Permit Forecaster")

@st.cache_data(ttl=3600)
def load_permits():
    with st.spinner("Fetching permits from LA City API..."):
        client = Socrata("data.lacity.org", None)
        data = client.get("nxg-rxmx", limit=20000)
        client.close()
        return pd.DataFrame(data)

df = load_permits()
st.write(f"Total permits loaded: {len(df)}")

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
    
    adu_count = len(df[df["category"] == "ADU"])
    solar_count = len(df[df["category"] == "Solar + Storage"])
    
    col1, col2 = st.columns(2)
    col1.metric("ADU Permits", adu_count)
    col2.metric("Solar Permits", solar_count)
    
    st.dataframe(df[["permit_type", "work_description", "category"]].head(100))
