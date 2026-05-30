
import streamlit as st
import pandas as pd
import plotly.express as px
from sodapy import Socrata
from datetime import datetime

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
        text = str(row.get('work_desc', '')) + ' ' + str(row.get('permit_type', ''))
        text = text.upper()
        if 'ADU' in text or 'ACCESSORY DWELLING' in text:
            return 'ADU'
        elif 'SOLAR' in text or 'PV' in text:
            return 'Solar + Storage'
        elif 'EV' in text or 'CHARGING' in text:
            return 'EV Charging'
        elif row.get('du_changed', 0) and 5 <= int(row.get('du_changed', 0)) <= 50:
            return 'Small Multifamily'
        else:
            return 'Other'
    df['vertical'] = df.apply(classify, axis=1)
    if 'issue_date' in df.columns:
        df['issue_date'] = pd.to_datetime(df['issue_date'], errors='coerce') # Use errors='coerce' for robustness
    # Convert latitude and longitude to numeric for mapping
    if 'latitude' in df.columns:
        df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
    if 'longitude' in df.columns:
        df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
    return df

with st.spinner("Fetching permits..."):
    df = fetch_permits()
    df = classify_permits(df)

# Handle potential empty issue_date column or NaTs for min/max date input default values
if 'issue_date' in df.columns and not df['issue_date'].empty and not df['issue_date'].isnull().all():
    min_date_val = df['issue_date'].min().date()
    max_date_val = df['issue_date'].max().date()
else:
    # Provide sensible defaults if no valid dates are present
    min_date_val = datetime(2020, 1, 1).date() # Example default start
    max_date_val = datetime.now().date()      # Example default end

st.success(f"✅ {len(df)} permits initially loaded.")

st.markdown("--- # Filters ---")

st.subheader("Filter by Date Range")
col_start_date, col_end_date = st.columns(2)
with col_start_date:
    start_date_filter = st.date_input("Start Date", value=min_date_val, min_value=min_date_val, max_value=max_date_val)
with col_end_date:
    end_date_filter = st.date_input("End Date", value=max_date_val, min_value=min_date_val, max_value=max_date_val)

# Convert selected dates to datetime for filtering
start_date_dt = pd.to_datetime(start_date_filter)
end_date_dt = pd.to_datetime(end_date_filter)

# Apply the date filter
df_filtered = df[(df['issue_date'] >= start_date_dt) & (df['issue_date'] <= end_date_dt)]

st.info(f"Displaying {len(df_filtered)} permits within the selected date range.")

# --- New Search Bar ---
search_query = st.text_input("Search by Address or Permit Number", "")
if search_query:
    df_filtered = df_filtered[
        df_filtered['primary_address'].astype(str).str.contains(search_query, case=False, na=False) |
        df_filtered['permit_nbr'].astype(str).str.contains(search_query, case=False, na=False)
    ]
    st.info(f"Displaying {len(df_filtered)} permits matching your search query.")

tab1, tab2 = st.tabs(["📊 Overview", "🏡 Verticals"])

with tab1:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Permits", f"{len(df_filtered):,}")
    col2.metric("ADU", f"{len(df_filtered[df_filtered['vertical'] == 'ADU']):,}")
    col3.metric("Solar", f"{len(df_filtered[df_filtered['vertical'] == 'Solar + Storage']):,}")
    col4.metric("EV Charging", f"{len(df_filtered[df_filtered['vertical'] == 'EV Charging']):,}")

    fig = px.pie(df_filtered, names='vertical', title='Permits by Vertical', hole=0.4)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Summary Statistics")
    st.dataframe(df_filtered.describe())

    st.subheader("Average Monthly Valuation")
    if not df_filtered.empty and 'issue_date' in df_filtered.columns and 'valuation' in df_filtered.columns:
        df_filtered['year_month'] = df_filtered['issue_date'].dt.to_period('M')
        monthly_avg_valuation = df_filtered.groupby('year_month')['valuation'].apply(lambda x: pd.to_numeric(x, errors='coerce').mean()).reset_index()
        monthly_avg_valuation['year_month'] = monthly_avg_valuation['year_month'].astype(str)
        st.dataframe(monthly_avg_valuation.rename(columns={'valuation': 'Average Valuation'}))
    else:
        st.write("No data to calculate monthly average valuation.")

    st.subheader("Permit Locations")
    # Filter out rows with missing lat/lon for mapping
    df_map_data = df_filtered.dropna(subset=['latitude', 'longitude'])

    if not df_map_data.empty:
        fig_map = px.scatter_mapbox(
            df_map_data,
            lat="latitude",
            lon="longitude",
            color="vertical", # Color points by vertical classification
            hover_name="primary_address",
            hover_data=["issue_date", "permit_type", "work_desc", "valuation"],
            zoom=9,
            height=500,
            title="Permit Locations",
        )
        fig_map.update_layout(
            mapbox_style="carto-positron", # Use a nice basemap
            margin={"r":0,"t":50,"l":0,"b":0}
        )
        st.plotly_chart(fig_map, use_container_width=True)
    else:
        st.write("No valid permit locations to display for the selected filters.")

with tab2:
    st.subheader("Filtered Permits (excluding 'Other')")
    filtered_df_no_other = df_filtered[df_filtered['vertical'] != 'Other']
    st.dataframe(filtered_df_no_other[['permit_nbr', 'primary_address', 'vertical', 'valuation']].head(50))

    csv = filtered_df_no_other.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download filtered data as CSV",
        data=csv,
        file_name='filtered_permits.csv',
        mime='text/csv',
    )
