import smtplib
from email.mime.text import MIMEText

def send_tier1_alert(city_count, total_permits, status_dict, recipient_email):
    """Send email alert after Tier 1 fetch completes"""
    
    # Get your Gmail credentials from Streamlit secrets
    sender_email = st.secrets.get("EMAIL_SENDER", "")
    sender_password = st.secrets.get("EMAIL_PASSWORD", "")
    
    if not sender_email or not recipient_email:
        print("Email not configured - skipping")
        return
    
    # Build email body
    success_cities = [c for c, s in status_dict.items() if "✅" in s]
    failed_cities = [c for c, s in status_dict.items() if "❌" in s]
    
    body = f"""
    ✅ Tier 1 Permit Data Fetch Complete
    
    Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    Cities fetched: {city_count}
    Total permits: {total_permits:,}
    
    Successful: {len(success_cities)} cities
    {', '.join(success_cities) if success_cities else 'None'}
    
    Failed: {len(failed_cities)} cities
    {', '.join(failed_cities) if failed_cities else 'None'}
    
    Download the data from your dashboard:
    https://your-app.streamlit.app
    """
    
    msg = MIMEText(body)
    msg['Subject'] = f"✅ Tier 1 Permit Fetch Complete - {datetime.now().strftime('%Y-%m-%d')}"
    msg['From'] = sender_email
    msg['To'] = recipient_email
    
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        print("📧 Email alert sent")
    except Exception as e:
        print(f"⚠️ Email failed: {e}")

@st.cache_data(ttl=3600)
def fetch_tier1_cities():
    """Fetch all Tier 1 cities data with timeouts and email alert"""
    
    cities = {
        "Santa Monica": {"domain": "data.santamonica.gov", "dataset": "6nbn-7d9i"},
        "Long Beach": {"domain": "data.longbeach.gov", "dataset": "n8d9-x7f3"},
        "Pasadena": {"domain": "data.cityofpasadena.net", "dataset": "x7n9-5p2q"},
    }
    
    all_data = []
    status = {}
    
    for name, info in cities.items():
        try:
            client = Socrata(info["domain"], None, timeout=30)
            data = client.get(info["dataset"], limit=10000)
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
    
    # Send email alert (only if not in cache refresh)
    if all_data and not st.session_state.get('alert_sent', False):
        combined = pd.concat(all_data, ignore_index=True)
        # Get recipient email from secrets
        recipient = st.secrets.get("EMAIL_RECIPIENT", "")
        if recipient:
            send_tier1_alert(len(all_data), len(combined), status, recipient)
            st.session_state['alert_sent'] = True
    
    if all_data:
        combined = pd.concat(all_data, ignore_index=True)
        return combined, status
    return pd.DataFrame(), status
