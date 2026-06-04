"""
Tier 1 Cities - Open Data Portals
Fetches building permits from cities with public SODA APIs
"""

from sodapy import Socrata
import pandas as pd
import os
from datetime import datetime

# ============================================
# CONFIGURATION
# ============================================
LIMIT = 50000  # Max permits per city

# List of Tier 1 cities with their API domains and dataset IDs
TIER1_CITIES = [
    {
        "name": "Santa Monica",
        "domain": "data.santamonica.gov",
        "dataset": "6nbn-7d9i",
        "description": "Building permits"
    },
    {
        "name": "Long Beach",
        "domain": "data.longbeach.gov",
        "dataset": "n8d9-x7f3",
        "description": "Building permits"
    },
    {
        "name": "Pasadena",
        "domain": "data.cityofpasadena.net",
        "dataset": "x7n9-5p2q",
        "description": "Building permits"
    },
    {
        "name": "Burbank",
        "domain": "data.burbankca.gov",
        "dataset": "k3r2-m8f6",
        "description": "Building permits"
    },
    {
        "name": "Glendale",
        "domain": "data.glendaleca.gov",
        "dataset": "t4p1-l9n7",
        "description": "Building permits"
    },
    {
        "name": "West Hollywood",
        "domain": "data.weho.org",
        "dataset": "6e7q-8r2p",
        "description": "Building permits"
    },
    {
        "name": "Santa Clarita",
        "domain": "data.santa-clarita.com",
        "dataset": "v3d9-7m1n",
        "description": "Building permits"
    }
]

# ============================================
# FETCH FUNCTION
# ============================================
def fetch_city_permits(city_info):
    """Fetch permits from a single Tier 1 city"""
    print(f"\n📋 Fetching {city_info['name']}...")
    
    try:
        client = Socrata(city_info["domain"], None)
        data = client.get(city_info["dataset"], limit=LIMIT)
        client.close()
        
        if not data:
            print(f"   ⚠️ No data returned for {city_info['name']}")
            return None
        
        df = pd.DataFrame(data)
        
        # Add source column
        df['source_city'] = city_info['name']
        df['fetch_date'] = datetime.now().strftime('%Y-%m-%d')
        
        print(f"   ✅ Retrieved {len(df):,} permits")
        return df
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

# ============================================
# MAIN EXECUTION
# ============================================
def main():
    print("=" * 60)
    print("🏙️ TIER 1 CITIES - PERMIT FETCHER")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Create output directory
    os.makedirs("data/permits/tier1", exist_ok=True)
    
    all_data = []
    successful_cities = []
    failed_cities = []
    
    for city in TIER1_CITIES:
        df = fetch_city_permits(city)
        if df is not None and not df.empty:
            all_data.append(df)
            successful_cities.append(city['name'])
            
            # Save individual city file
            filename = f"data/permits/tier1/{city['name'].lower().replace(' ', '_')}_permits.csv"
            df.to_csv(filename, index=False)
            print(f"   💾 Saved to: {filename}")
        else:
            failed_cities.append(city['name'])
    
    # Combine all cities into one file
    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        combined_file = f"data/permits/tier1/all_tier1_permits_{datetime.now().strftime('%Y-%m-%d')}.csv"
        combined_df.to_csv(combined_file, index=False)
        print(f"\n📊 Combined file: {combined_file}")
        print(f"   Total permits across all Tier 1 cities: {len(combined_df):,}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    print(f"✅ Successful: {len(successful_cities)}/{len(TIER1_CITIES)}")
    for city in successful_cities:
        print(f"   - {city}")
    if failed_cities:
        print(f"\n❌ Failed: {len(failed_cities)}/{len(TIER1_CITIES)}")
        for city in failed_cities:
            print(f"   - {city}")
    
    print("\n✅ Tier 1 fetch complete!")

if __name__ == "__main__":
    main()
