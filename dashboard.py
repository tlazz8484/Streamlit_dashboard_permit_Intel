import streamlit as st
import pandas as pd
import plotly.express as px
from sodapy import Socrata

st.set_page_config(page_title="LA Permit Forecaster", layout="wide")
st.title("🏛️ LA Building Permit Forecaster")

@st.cache_data(ttl=3600)
def fetch_permits():
    with st.spinner("Fetching permits from LA City API..."):
        client = Socrata("data.lacity.org", None)
        data = client.get("n3xg-rixm", limit=20000)
        client.close()
        return pd.DataFrame(data)

@st.cache_data(ttl=3600)
def classify_permits(df):
    def classify(row):
        work = str(row.get('work_desc', ''))
        permit_type = str(row.get('permit_type', ''))
        text = (work + ' ' + permit_type).upper()

        if 'ADU' in text or 'ACCESSORY DWELLING' in text:
            return 'ADU'
        if 'SOLAR' in text or 'PV' in text or 'PHOTOVOLTAIC' in text:
            return 'Solar + Storage'
        if 'EV' in text or 'CHARGING' in text or 'ELECTRIC VEHICLE' in text:
            return 'EV Charging'

        du_value = row.get('du_changed', 0)
        if du_value:
            try:
                du_int = int(float(du_value))
                if 5 <= du_int <= 50:
                    return 'Small Multifamily'
            except (ValueError, TypeError):
                pass
        return 'Other'

    df['vertical'] = df.apply(classify, axis=1)

    if 'issue_date' in df.columns:
        df['issue_date'] = pd.to_datetime(df['issue_date'], errors='coerce')
    return df

df = fetch_permits()
df = classify_permits(df)

st.success(f"✅ Loaded {len(df):,} permits")

col1, col2, col3, col4, col5 = st.columns(5)
total = len(df)
adu = len(df[df['vertical'] == 'ADU'])
solar = len(df[df['vertical'] == 'Solar + Storage'])
ev = len(df[df['vertical'] == 'EV Charging'])
multi = len(df[df['vertical'] == 'Small Multifamily'])

col1.metric("Total Permits", f"{total:,}")
col2.metric("ADU", f"{adu:,}")
col3.metric("Solar + Storage", f"{solar:,}")
col4.metric("EV Charging", f"{ev:,}")
col5.metric("Small Multifamily", f"{multi:,}")

if total > 0:
    fig = px.pie(df, names='vertical', title='Permits by Vertical', hole=0.4)
    st.plotly_chart(fig, use_container_width=True)

st.subheader("Sample Permits by Vertical")
for vert in ['ADU', 'Solar + Storage', 'EV Charging', 'Small Multifamily']:
    subset = df[df['vertical'] == vert].head(5)
    if len(subset) > 0:
        with st.expander(f"{vert} ({len(subset)} samples)"):
            st.dataframe(subset[['permit_nbr', 'primary_address', 'valuation']])

csv = df.to_csv(index=False).encode('utf-8')
st.download_button("📥 Download Full CSV", csv, "permits_export.csv", "text/csv")            lat="latitude",
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
