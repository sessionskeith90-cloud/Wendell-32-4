#!/usr/bin/env python3
"""
EDGAR Crawler Agent – Fetches SEC filings for specified companies/CIKs
and saves them to ~/incoming/ for automatic processing by watchdog.
"""
import os
import time
import json
import requests
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup

INCOMING = Path.home() / "incoming"
CRAWLER_DATA = Path.home() / "crawler_data"
CRAWLER_DATA.mkdir(exist_ok=True)

# Companies to track – add more as needed
TARGET_COMPANIES = [
    {"name": "Norwest Corporation", "cik": "0000072971"},
    {"name": "Wells Fargo & Company", "cik": "0000072971"},  # Same CIK post-merger
    {"name": "Wells Fargo Clearing Services", "crd": "19616"},  # FINRA CRD (placeholder)
]

# Filing types to prioritize
FILING_TYPES = ["10-K", "10-Q", "8-K", "DEF 14A", "S-8", "485BPOS"]

def fetch_filings(cik, filing_type=None, count=10):
    """Fetch recent filings for a CIK from EDGAR"""
    base_url = "https://www.sec.gov/cgi-bin/browse-edgar"
    params = {
        "action": "getcompany",
        "CIK": cik,
        "type": filing_type if filing_type else "",
        "dateb": "",
        "owner": "exclude",
        "start": "",
        "output": "atom",
        "count": count
    }
    
    headers = {
        "User-Agent": "Keith Sessions keith.coinode@gmail.com - Research Bot",
        "Accept-Encoding": "gzip, deflate",
        "Host": "www.sec.gov"
    }
    
    try:
        response = requests.get(base_url, params=params, headers=headers)
        if response.status_code == 200:
            return response.text
        else:
            print(f"   Error fetching {cik}: {response.status_code}")
            return None
    except Exception as e:
        print(f"   Exception: {e}")
        return None

def parse_filings(xml_data):
    """Extract filing info from EDGAR Atom feed using html.parser"""
    if not xml_data:
        return []
    
    filings = []
    soup = BeautifulSoup(xml_data, 'html.parser')
    
    # Try to find entries – Atom feed structure
    entries = soup.find_all('entry')
    
    for entry in entries:
        try:
            # Extract title
            title_elem = entry.find('title')
            title = title_elem.text if title_elem else ''
            
            # Extract filing date
            filing_date_elem = entry.find('filing-date')
            filing_date = filing_date_elem.text if filing_date_elem else ''
            
            # Extract form type
            form_type_elem = entry.find('filing-type')
            form_type = form_type_elem.text if form_type_elem else ''
            
            # Extract link
            link_elem = entry.find('link')
            link = link_elem['href'] if link_elem and link_elem.has_attr('href') else ''
            
            # Extract accession number
            accession_elem = entry.find('accession-number')
            accession = accession_elem.text if accession_elem else ''
            
            filing = {
                'title': title,
                'filing_date': filing_date,
                'form_type': form_type,
                'link': link,
                'accession': accession
            }
            filings.append(filing)
        except Exception as e:
            continue
    
    return filings

def download_filing_text(filing_url, accession, form_type, cik):
    """Download the full text of a filing"""
    # Convert HTML index URL to text filing URL
    if '/ix?doc=/' in filing_url:
        # Modern interactive filing – skip for now
        return None
    
    txt_url = filing_url.replace('-index.htm', '.txt')
    
    headers = {
        "User-Agent": "Keith Sessions keith.coinode@gmail.com - Research Bot"
    }
    
    try:
        response = requests.get(txt_url, headers=headers)
        if response.status_code == 200:
            # Clean form type to be filesystem-safe (replace / with _)
            safe_form_type = form_type.replace('/', '_')
            filename = f"{cik}_{accession}_{safe_form_type}.txt"
            filepath = INCOMING / filename
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(response.text)
            print(f"      ✅ Downloaded: {filename}")
            return filepath
        else:
            print(f"      ❌ Failed to download: {response.status_code}")
            return None
    except Exception as e:
        print(f"      ❌ Error: {e}")
        return None

def load_crawler_state():
    """Load previously downloaded filings to avoid duplicates"""
    state_file = CRAWLER_DATA / "crawler_state.json"
    if state_file.exists():
        with open(state_file, 'r') as f:
            return json.load(f)
    return {"downloaded": []}

def save_crawler_state(state):
    """Save downloaded filings list"""
    state_file = CRAWLER_DATA / "crawler_state.json"
    with open(state_file, 'w') as f:
        json.dump(state, f, indent=2)

def main():
    print("\n" + "="*60)
    print("🔍 EDGAR CRAWLER AGENT STARTING")
    print("="*60)
    
    state = load_crawler_state()
    downloaded = set(state.get("downloaded", []))
    
    for company in TARGET_COMPANIES:
        if "cik" not in company:
            continue
            
        cik = company["cik"]
        name = company["name"]
        
        print(f"\n📊 Fetching {name} (CIK: {cik})...")
        
        for filing_type in FILING_TYPES:
            print(f"   📋 {filing_type} filings...")
            xml = fetch_filings(cik, filing_type, count=10)
            filings = parse_filings(xml)
            
            for filing in filings:
                # Skip if missing essential data
                if not filing['accession'] or not filing['form_type']:
                    continue
                    
                # Create unique ID for this filing
                filing_id = f"{cik}_{filing['accession']}_{filing['form_type']}"
                
                if filing_id in downloaded:
                    print(f"      ⏭️  Already downloaded: {filing['form_type']} {filing['filing_date']}")
                    continue
                
                print(f"      ⬇️  New: {filing['form_type']} {filing['filing_date']}")
                filepath = download_filing_text(
                    filing['link'], 
                    filing['accession'], 
                    filing['form_type'],
                    cik
                )
                
                if filepath:
                    downloaded.add(filing_id)
                    
                # Be polite to SEC servers
                time.sleep(1)
    
    # Update state
    state["downloaded"] = list(downloaded)
    state["last_run"] = datetime.now().isoformat()
    save_crawler_state(state)
    
    print("\n" + "="*60)
    print(f"✅ Crawler complete. {len(downloaded)} total filings downloaded.")
    print("   Files saved to ~/incoming/ – watchdog will process them automatically.")
    print("="*60)

if __name__ == "__main__":
    main()
