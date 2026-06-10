"""
LA Building Permit Forecaster - Fully Integrated & Optimized
Includes: LA City permits + Tier 1 Cities + Policy Alerts + Download + Timeouts
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from sodapy import Socrata
import os
from datetime import datetime
import time

st.set_page_config(page_title="LA Permit Forecaster", layout="wide")
st.title("🏛️ LA Building Permit Forecaster")

# ============================================
# CACHED FETCH FUNCTIONS WITH TIMEOUTS
# ============================================

@st.cache_data(ttl=3600)
def fetch_la_city_permits():
    """Fetch LA City permits from API"""
    try:
        client = Socrata("data.lacity.org", None, timeout=30)
        data = client.get("n3xg-rixm", limit=20000)
        client.close()
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"LA City fetch failed: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def fetch_tier1_cities():
    """Fetch all Tier 1 cities data with timeouts and error handling"""
    
    # Start with 3 confirmed working cities
    cities = {
        "Santa Monica": {"domain": "data.santamonica.gov", "dataset": "6nbn-7d9i"},
        "Long Beach": {"domain": "data.longbeach.gov", "dataset": "n8d9-x7f3"},
        "Pasadena": {"domain": "data.cityofpasadena.net", "dataset": "x7n9-5p2q"},
        # Add more cities after testing individually
        # "Burbank": {"domain": "data.burbankca.gov", "dataset": "k3r2-m8f6"},
        # "Glendale": {"domain": "data.glendaleca.gov", "dataset": "t4p1-l9n7"},
        # "West Hollywood": {"domain": "data.weho.org", "dataset": "6e7q-8r2p"},
        # "Santa Clarita": {"domain": "data.santa-clarita.com", "dataset": "v3d9-7m1n"},
    }
    
    all_data = []
    status = {}
    
    for name, info in cities.items():
        try:
            # Add timeout to prevent hanging
            client = Socrata(info["domain"], None, timeout=30)
            data = client.get(info["dataset"], limit=10000)  # Limit for speed
            client.close()
            
            if data and len(data) > 0:
                df = pd.DataFrame(data)
                df['source_city'] = name
                df['fetch_date'] = datetime.now().strftime('%Y-%m-%d')
                all_data.append(df)
                status[name] = f"✅ {len(df):,} permits"
            else:
                status[name] = "⚠️ No data returned"
                
        except Exception as e:
            status[name] = f"❌ Error: {str(e)[:50]}"
            continue
    
    if all_data:
        combined = pd.concat(all_data, ignore_index=True)
        return combined, status
    return pd.DataFrame(), status

@st.cache_data(ttl=3600)
def classify_permits(df):
    """Classify permits into verticals"""
    if df.empty:
        return df
    
    def classify(row):
        work = str(row.get('work_desc', ''))
        ptype = str(row.get('permit_type', ''))
        text = (work + ' ' + ptype).upper()
        
        if 'ADU' in text or 'ACCESSORY DWELLING' in text:
            return 'ADU'
        elif 'SOLAR' in text or 'PV' in text or 'PHOTOVOLTAIC' in text:
            return 'Solar + Storage'
        elif 'EV' in text or 'CHARGING' in text or 'ELECTRIC VEHICLE' in text:
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
    
    if 'issue_date' in df.columns:
        df['issue_date'] = pd.to_datetime(df['issue_date'], errors='coerce')
    
    return df

# ============================================
# LOAD LA CITY DATA (Always loads first)
# ============================================

with st.spinner("Loading LA City permits..."):
    df_la = fetch_la_city_permits()
    df_la = classify_permits(df_la)

# ============================================
# CREATE TABS
# ============================================

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 LA City", "🏡 Verticals", "📥 Tier 1 Cities", "📜 Policy Alerts", "📈 Time Series"])

# ============================================
# TAB 1: LA CITY PERMITS
# ============================================
with tab1:
    st.subheader("City of Los Angeles Permits")
    
    if not df_la.empty:
        st.success(f"✅ Loaded {len(df_la):,} LA City permits")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        total = len(df_la)
        col1.metric("Total Permits", f"{total:,}")
        col2.metric("ADU", f"{len(df_la[df_la['vertical'] == 'ADU']):,}")
        col3.metric("Solar", f"{len(df_la[df_la['vertical'] == 'Solar + Storage']):,}")
        col4.metric("EV Charging", f"{len(df_la[df_la['vertical'] == 'EV Charging']):,}")
        col5.metric("Small Multi", f"{len(df_la[df_la['vertical'] == 'Small Multifamily']):,}")
        
        if total > 0:
            fig = px.pie(df_la, names='vertical', title='LA City Permits by Vertical', hole=0.4)
            st.plotly_chart(fig, use_container_width=True)
        
        # Download LA City data
        csv_la = df_la.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 Download LA City Permits CSV",
            csv_la,
            f"la_city_permits_{datetime.now().strftime('%Y-%m-%d')}.csv",
            "text/csv"
        )
    else:
        st.error("Unable to load LA City permits. Please try again later.")

# ============================================
# TAB 2: VERTICALS (LA City only)
# ============================================
with tab2:
    st.subheader("Permit Verticals Breakdown")
    
    if not df_la.empty:
        for vert in ['ADU', 'Solar + Storage', 'EV Charging', 'Small Multifamily']:
            subset = df_la[df_la['vertical'] == vert].head(10)
            if len(subset) > 0:
                with st.expander(f"{vert} ({len(subset)} samples)"):
                    st.dataframe(subset[['permit_nbr', 'primary_address', 'valuation']])
    else:
        st.info("No data available")

# ============================================
# TAB 3: TIER 1 CITIES (Optimized)
# ============================================
with tab3:
    st.subheader("Tier 1 Cities - Open Data Portals")
    st.caption("Santa Monica, Long Beach, Pasadena (more cities coming soon)")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        if st.button("🔄 Fetch Tier 1 Cities Data", use_container_width=True):
            with st.spinner("Fetching permits from Tier 1 cities... This may take 30-60 seconds..."):
                df_tier1, status = fetch_tier1_cities()
                st.session_state['df_tier1'] = df_tier1
                st.session_state['tier1_status'] = status
                st.rerun()
    
    with col2:
        if 'tier1_status' in st.session_state:
            st.write("**Fetch Results:**")
            for city, result in st.session_state['tier1_status'].items():
                if "✅" in result:
                    st.success(f"{city}: {result}")
                elif "❌" in result:
                    st.error(f"{city}: {result}")
                else:
                    st.warning(f"{city}: {result}")
    
    if 'df_tier1' in st.session_state and not st.session_state['df_tier1'].empty:
        df_tier1 = st.session_state['df_tier1']
        st.success(f"✅ Total Tier 1 permits: {len(df_tier1):,}")
        
        # City breakdown
        city_counts = df_tier1['source_city'].value_counts().reset_index()
        city_counts.columns = ['City', 'Permit Count']
        st.dataframe(city_counts, use_container_width=True)
        
        # Download Tier 1 data
        csv_tier1 = df_tier1.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 Download Tier 1 Permits CSV",
            csv_tier1,
            f"tier1_permits_{datetime.now().strftime('%Y-%m-%d')}.csv",
            "text/csv"
        )
    else:
        st.info("Click 'Fetch Tier 1 Cities Data' to load permit data from open data portals.")

# ============================================
# TAB 4: POLICY ALERTS
# ============================================
with tab4:
    st.subheader("📜 Policy & Zoning Indicators")
    
    # Check for alert files in data folder
    alert_files = []
    if os.path.exists("data/keywords_index"):
        alert_files = [f for f in os.listdir("data/keywords_index") if f.startswith("alerts_")]
    
    if alert_files:
        latest_alert = sorted(alert_files)[-1]
        alerts_df = pd.read_csv(f"data/keywords_index/{latest_alert}")
        st.warning(f"🚨 {len(alerts_df)} Active Policy Alerts Found")
        st.dataframe(alerts_df, use_container_width=True)
    else:
        st.info("No policy alerts found. Run GitHub Actions workflow to generate alerts.")
    
    # Policy categories
    st.subheader("Policy Tracking Status")
    policy_categories = {
        "ADU Laws": ["ADU Ordinance", "SB13"],
        "Density/Zoning": ["Density Bonus", "Upzoning", "SB9"],
        "Housing Mandates": ["RHNA", "Builders Remedy", "SB35"],
        "Environmental": ["CEQA", "Title 24"],
    }
    
    col_a, col_b, col_c, col_d = st.columns(4)
    cols = [col_a, col_b, col_c, col_d]
    for idx, (category, keywords) in enumerate(policy_categories.items()):
        with cols[idx]:
            st.metric(category, f"Tracking {len(keywords)} keywords")

# ============================================
# TAB 5: TIME SERIES
# ============================================
with tab5:
    st.subheader("Permit Trends Over Time")
    
    if not df_la.empty and 'issue_date' in df_la.columns and df_la['issue_date'].notna().any():
        df_monthly = df_la[df_la['issue_date'].notna()].copy()
        df_monthly['month'] = df_monthly['issue_date'].dt.to_period('M').astype(str)
        monthly_counts = df_monthly.groupby(['month', 'vertical']).size().reset_index(name='count')
        
        fig = px.line(monthly_counts, x='month', y='count', color='vertical',
                      title='Monthly Permits by Vertical (LA City)')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Not enough date data available for time series.")

# ============================================
# FOOTER
# ============================================
st.divider()
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Data source: LA City Open Data + Tier 1 City Portals")
