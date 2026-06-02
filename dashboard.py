# dashboard.py
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="LA Building Permit Forecaster",
    layout="wide"
)

st.title("LA Building Permit Forecaster")
st.markdown("Daily automated monitoring of urban development tracking metrics across Los Angeles.")

@st.cache_data(ttl=3600)
def load_cached_permits():
    try:
        # Reads the static CSV file updated daily by GitHub Actions
        return pd.read_csv("data/permits.csv")
    except FileNotFoundError:
        st.error("⚠️ Data cache file not found at `data/permits.csv`.")
        st.info("Please run your 'Daily Permit Fetch' GitHub Action to generate this data file.")
        return pd.DataFrame()

df = load_cached_permits()

if not df.empty:
    st.success(f"📈 Total active tracking records loaded from GitHub cache: {len(df):,}")
    
    # Calculate metrics from the pre-classified data
    adu_count = len(df[df["category"] == "ADU"])
    solar_count = len(df[df["category"] == "Solar + Storage"])
    ev_count = len(df[df["category"] == "EV Charging"])
    
    # Layout KPI Blocks
    m1, m2, m3 = st.columns(3)
    m1.metric(label="ADU Permits", value=f"{adu_count:,}")
    m2.metric(label="Solar + Storage Permits", value=f"{solar_count:,}")
    m3.metric(label="EV Charging Stations", value=f"{ev_count:,}")
    
    st.divider()
    
    # Visual Layout Split
    col_chart, col_table = st.columns([1, 1])
    
    with col_chart:
        st.subheader("Permit Category Distribution")
        category_counts = df["category"].value_counts().reset_index()
        category_counts.columns = ["Category", "Count"]
        fig = px.pie(category_counts, values="Count", names="Category", hole=0.4)
        st.plotly_chart(fig, use_container_width=True)
        
    with col_table:
        st.subheader("Recent Permit Logs Preview")
        st.dataframe(df[["permit_type", "work_description", "category"]].head(100), use_container_width=True)
else:
    st.warning("Dashboard visualization components are offline until a valid dataset source is provided.")
