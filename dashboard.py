"""
LA Building Permit Forecaster - Batched Fetch with Labels
Fetches permits in batches of 20,000 and labels each batch
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from sodapy import Socrata
import os
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import hashlib

st.set_page_config(page_title="LA Permit Forecaster", layout="wide")
st.title("🏛️ LA Building Permit Forecaster")

# ============================================
# EMAIL ALERT FUNCTION
# ============================================

def send_batch_email(batch_info, recipient_email):
    """Send email with batch details"""
    
    sender = st.secrets.get("EMAIL_SENDER", "")
    password = st.secrets.get("EMAIL_PASSWORD", "")
    recipient = st.secrets.get("EMAIL_RECIPIENT", recipient_email)
    
    if not sender or not recipient:
        return
    
    body = f"""
    📊 NEW PERMIT BATCH FETCHED
    
    Batch ID: {batch_info['batch_id']}
    Fetch Date: {batch_info['fetch_date']}
    Dataset: {batch_info['dataset']}
    Records in this batch: {batch_info['batch_size']:,}
    Cumulative total: {batch_info['cumulative_total']:,}
    
    Output Locations:
    • GitHub: data/permits/batches/{batch_info['batch_id']}.csv
    • Artifacts: Available in GitHub Actions
    • This email: Sent to {recipient}
    
    Batch Label: {batch_info['batch_label']}
    Offset: {batch_info['offset']}
    """
    
    msg = MIMEText(body)
    msg['Subject'] = f"📊 Permit Batch {batch_info['batch_id']} - {batch_info['batch_size']} records"
    msg['From'] = sender
    msg['To'] = recipient
    
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender, password)
            server.send_message(msg)
        print(f"📧 Email sent for batch {batch_info['batch_id']}")
    except Exception as e:
        print(f"⚠️ Email failed: {e}")

# ============================================
# BATCHED FETCH FUNCTION
# ============================================

def fetch_batch(dataset_id, batch_number, offset, batch_size=20000):
    """Fetch a single batch of permits"""
    
    client = Socrata("data.lacity.org", None, timeout=60)
    
    try:
        data = client.get(dataset_id, limit=batch_size, offset=offset)
        client.close()
        
        if data:
            df = pd.DataFrame(data)
            return df, len(data)
        return None, 0
        
    except Exception as e:
        client.close()
        st.error(f"Batch {batch_number} failed: {e}")
        return None, 0

def generate_batch_label(dataset_id, batch_number, offset, fetch_date):
    """Generate a unique, readable label for each batch"""
    
    dataset_name = "historical" if dataset_id == "n3xg-rixm" else "recent"
    batch_id = f"{dataset_name}_batch_{batch_number:03d}_{fetch_date.strftime('%Y%m%d_%H%M%S')}"
    
    return {
        'batch_id': batch_id,
        'batch_label': f"{dataset_name.upper()} | Batch {batch_number} | Offset {offset} | {fetch_date.strftime('%Y-%m-%d %H:%M')}",
        'filename': f"{batch_id}.csv"
    }

def fetch_all_batches():
    """Fetch all permits in batches of 20,000 with labels"""
    
    os.makedirs("data/permits/batches", exist_ok=True)
    os.makedirs("data/summaries", exist_ok=True)
    
    fetch_date = datetime.now()
    
    # Batch tracking
    all_batches = []
    cumulative_historical = 0
    cumulative_recent = 0
    
    # ========================================
    # DATASET 1: Historical (2010-2019)
    # ========================================
    st.subheader("📜 Fetching Historical Permits (2010-2019)")
    progress_hist = st.progress(0)
    
    historical_offset = 0
    historical_batch_num = 1
    historical_complete = False
    
    while not historical_complete:
        st.write(f"  Fetching historical batch {historical_batch_num} (offset: {historical_offset})...")
        
        df, count = fetch_batch("n3xg-rixm", historical_batch_num, historical_offset, 20000)
        
        if df is not None and count > 0:
            batch_label = generate_batch_label("n3xg-rixm", historical_batch_num, historical_offset, fetch_date)
            
            # Save batch
            batch_file = f"data/permits/batches/{batch_label['filename']}"
            df.to_csv(batch_file, index=False)
            
            cumulative_historical += count
            
            batch_info = {
                'batch_id': batch_label['batch_id'],
                'batch_label': batch_label['batch_label'],
                'batch_size': count,
                'cumulative_total': cumulative_historical,
                'dataset': 'historical (2010-2019)',
                'offset': historical_offset,
                'fetch_date': fetch_date.isoformat(),
                'filename': batch_label['filename']
            }
            all_batches.append(batch_info)
            
            # Send email for this batch
            send_batch_email(batch_info, st.secrets.get("EMAIL_RECIPIENT", ""))
            
            st.write(f"  ✅ Batch {historical_batch_num}: {count:,} permits (cumulative: {cumulative_historical:,})")
            
            historical_offset += count
            historical_batch_num += 1
            progress_hist.progress(min(historical_batch_num / 25, 1.0))  # ~25 batches max
            
        else:
            historical_complete = True
            st.write(f"  ✅ Historical fetch complete. Total: {cumulative_historical:,} permits")
    
    # ========================================
    # DATASET 2: Recent (2020-present)
    # ========================================
    st.subheader("🆕 Fetching Recent Permits (2020-present)")
    progress_recent = st.progress(0)
    
    recent_offset = 0
    recent_batch_num = 1
    recent_complete = False
    
    while not recent_complete:
        st.write(f"  Fetching recent batch {recent_batch_num} (offset: {recent_offset})...")
        
        df, count = fetch_batch("pi9x-tg5x", recent_batch_num, recent_offset, 20000)
        
        if df is not None and count > 0:
            batch_label = generate_batch_label("pi9x-tg5x", recent_batch_num, recent_offset, fetch_date)
            
            batch_file = f"data/permits/batches/{batch_label['filename']}"
            df.to_csv(batch_file, index=False)
            
            cumulative_recent += count
            
            batch_info = {
                'batch_id': batch_label['batch_id'],
                'batch_label': batch_label['batch_label'],
                'batch_size': count,
                'cumulative_total': cumulative_recent,
                'dataset': 'recent (2020-present)',
                'offset': recent_offset,
                'fetch_date': fetch_date.isoformat(),
                'filename': batch_label['filename']
            }
            all_batches.append(batch_info)
            
            send_batch_email(batch_info, st.secrets.get("EMAIL_RECIPIENT", ""))
            
            st.write(f"  ✅ Batch {recent_batch_num}: {count:,} permits (cumulative: {cumulative_recent:,})")
            
            recent_offset += count
            recent_batch_num += 1
            progress_recent.progress(min(recent_batch_num / 10, 1.0))
            
        else:
            recent_complete = True
            st.write(f"  ✅ Recent fetch complete. Total: {cumulative_recent:,} permits")
    
    # ========================================
    # SAVE MASTER SUMMARY
    # ========================================
    
    summary = {
        'fetch_date': fetch_date.isoformat(),
        'historical': {
            'total_permits': cumulative_historical,
            'batches': historical_batch_num - 1,
            'batch_size': 20000
        },
        'recent': {
            'total_permits': cumulative_recent,
            'batches': recent_batch_num - 1,
            'batch_size': 20000
        },
        'total_permits': cumulative_historical + cumulative_recent,
        'batches': all_batches
    }
    
    # Save summary
    with open("data/summaries/latest_batch_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    
    # Save batch manifest
    batch_manifest = pd.DataFrame(all_batches)
    batch_manifest.to_csv("data/summaries/batch_manifest.csv", index=False)
    
    return summary

# ============================================
# MAIN DASHBOARD
# ============================================

tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "📥 Batch Fetcher", "📜 Batch Manifest"])

# ============================================
# TAB 1: DASHBOARD
# ============================================
with tab1:
    st.subheader("City of Los Angeles Permits")
    
    # Check if any batches exist
    if os.path.exists("data/summaries/latest_batch_summary.json"):
        with open("data/summaries/latest_batch_summary.json", "r") as f:
            summary = json.load(f)
        
        st.success(f"✅ Total permits on record: {summary['total_permits']:,}")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Historical (2010-2019)", f"{summary['historical']['total_permits']:,}")
        col2.metric("Recent (2020-present)", f"{summary['recent']['total_permits']:,}")
        col3.metric("Total Batches", f"{summary['historical']['batches'] + summary['recent']['batches']}")
        
        # Load and display most recent batch
        if summary['batches']:
            latest_batch = summary['batches'][-1]
            st.info(f"📦 Latest batch: {latest_batch['batch_label']}")
            
            # Download latest batch
            latest_file = f"data/permits/batches/{latest_batch['filename']}"
            if os.path.exists(latest_file):
                with open(latest_file, 'rb') as f:
                    st.download_button(
                        "📥 Download Latest Batch",
                        f,
                        latest_batch['filename'],
                        "text/csv"
                    )
    else:
        st.info("No data fetched yet. Go to the 'Batch Fetcher' tab to start.")

# ============================================
# TAB 2: BATCH FETCHER
# ============================================
with tab2:
    st.subheader("Fetch Permits in Batches of 20,000")
    st.caption("Each batch is saved individually and you'll receive email notifications")
    
    if st.button("🚀 START BATCH FETCH", type="primary", use_container_width=True):
        with st.spinner("Fetching batches... This may take 5-10 minutes for full history..."):
            summary = fetch_all_batches()
            st.success(f"✅ Fetch complete! {summary['total_permits']:,} permits in {len(summary['batches'])} batches")
            st.balloons()
            st.rerun()

# ============================================
# TAB 3: BATCH MANIFEST
# ============================================
with tab3:
    st.subheader("Batch Manifest")
    
    if os.path.exists("data/summaries/batch_manifest.csv"):
        manifest = pd.read_csv("data/summaries/batch_manifest.csv")
        st.dataframe(manifest, use_container_width=True)
        
        # Download manifest
        csv = manifest.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Batch Manifest CSV", csv, "batch_manifest.csv", "text/csv")
    else:
        st.info("No batches fetched yet. Run the batch fetcher first.")
