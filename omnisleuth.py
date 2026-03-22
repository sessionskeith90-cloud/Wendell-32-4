#!/usr/bin/env python3
"""
OmniSleuth – Comprehensive forensic analysis of your 30‑year evidence collection.
"""
import json
import os
import re
import hashlib
from datetime import datetime
from pathlib import Path
from collections import Counter, defaultdict

# ============================================================================
# CONFIGURATION
# ============================================================================
INDEX_FILE = Path("/data/data/com.termux/files/home/forensic_data/bulk_index.json")
EVIDENCE_ROOT = Path("/data/data/com.termux/files/home/forensic_data/bulk_evidence")
REPORT_FILE = Path("/data/data/com.termux/files/home/forensic_data/omnisleuth_report.json")
SUMMARY_FILE = Path("/data/data/com.termux/files/home/forensic_data/omnisleuth_summary.txt")

# Key terms from your investigation (expand as needed)
KEY_TERMS = {
    "names": [
        "wendell stewart allen", "keith sessions", "keith brian", "keith bryan",
        "roberta cado", "shahaada jihaad", "rakesh patel", "rajvi patel", "kalperna patel",
        "james strother", "kathryn purdom", "mary schaffner"
    ],
    "regulatory": [
        "801-37967", "19616", "crd 19616", "sec 801", "finra", "norwest",
        "cik 0000072971", "001-02979", "file no. 3-19704", "fair fund"
    ],
    "companies": [
        "wells fargo", "wachovia", "norwest", "everen", "first clearing",
        "computershare", "eq shareowner", "ubs", "american funds", "capital group"
    ],
    "account_formats": [
        r"C\d{10}",                         # Computershare C + 10 digits
        r"\d{4}-\d{4}",                     # Wells Fargo Advisors 8-digit dash
        r"^\d{8}$",                          # 8 digits
        r"^\d{9}$",                          # 9 digits (SSN / Robinhood)
        r"^\d{10}$",                         # 10 digits
        r"^\d{11}$",                         # 11 digits
        r"^[A-Za-z]\d{3,8}$",                # Interactive Brokers letter + digits
    ],
    "custodian_ids": [
        "271", "2044693604", "7383176507", "2628909003",  # Wells Fargo divisions
        "1050423503", "308", "891", "569",                # Computershare
        "9168885905", "9955868907",                       # Vanguard
        "7841829605", "1259673707",                       # T. Rowe Price
        "402", "4692805208",                               # JP Morgan
        "4301811202", "3355",                              # Interactive Brokers, Robinhood
        "4626179308", "814726505", "887",                  # Ameriprise
        "2868540502",                                      # Capital Group
        "9766109303",                                       # Charles Schwab
    ]
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================
def load_index():
    if not INDEX_FILE.exists():
        print(f"❌ Index file not found: {INDEX_FILE}")
        return None
    with open(INDEX_FILE) as f:
        return json.load(f)

def extract_text(filepath):
    """Attempt to extract text from common file types."""
    ext = filepath.suffix.lower()
    try:
        if ext in ['.txt', '.json', '.csv', '.md', '.html', '.xml']:
            with open(filepath, 'r', errors='ignore') as f:
                return f.read()
        # Add PDF extraction if you have pdftotext installed
        # elif ext == '.pdf':
        #     import subprocess
        #     result = subprocess.run(['pdftotext', filepath, '-'], capture_output=True, text=True)
        #     return result.stdout
    except:
        pass
    return ""

def search_in_text(text, terms):
    hits = defaultdict(list)
    lower = text.lower()
    for category, term_list in terms.items():
        for term in term_list:
            if isinstance(term, str):
                if term.lower() in lower:
                    hits[category].append(term)
            else:  # regex pattern
                if re.search(term, text):
                    hits[category].append(term.pattern)
    return hits

def extract_dates(text):
    """Find dates in ISO, US, or other common formats."""
    patterns = [
        r'\d{4}-\d{2}-\d{2}',                     # 2023-07-11
        r'\d{2}/\d{2}/\d{4}',                     # 07/11/2023
        r'\d{2}-\d{2}-\d{4}',                     # 07-11-2023
        r'[A-Z][a-z]{2} \d{1,2},? \d{4}',         # Jul 11, 2023
    ]
    dates = []
    for pat in patterns:
        dates.extend(re.findall(pat, text))
    return dates

# ============================================================================
# MAIN ANALYSIS
# ============================================================================
def main():
    print("\n🔍 OmniSleuth – Starting comprehensive analysis...\n")
    index = load_index()
    if index is None:
        return

    total = len(index)
    print(f"📊 Index contains {total} files.\n")

    # Statistics
    results = {
        "scan_time": datetime.now().isoformat(),
        "total_files": total,
        "files_with_hits": 0,
        "hits_by_category": Counter(),
        "date_mentions": Counter(),
        "term_hits": defaultdict(list),
        "file_details": [],
        "timeline": []
    }

    for i, entry in enumerate(index, 1):
        if i % 50 == 0:
            print(f"  Processed {i}/{total} files...")
        filepath = EVIDENCE_ROOT.parent / entry["path"]   # entry["path"] includes forensic_data/...
        if not filepath.exists():
            continue

        # Basic info
        info = {
            "filename": entry["filename"],
            "path": entry["path"],
            "size": entry["size"],
            "modified": entry["modified"],
            "sha256": entry["sha256"]
        }

        # Extract text content if possible
        text = extract_text(filepath)
        if text:
            # Search for key terms
            hits = search_in_text(text, KEY_TERMS)
            if hits:
                results["files_with_hits"] += 1
                info["hits"] = {k: list(set(v)) for k, v in hits.items()}
                for cat, terms in hits.items():
                    results["hits_by_category"][cat] += len(terms)
                    for term in terms:
                        results["term_hits"][term].append(entry["filename"])

            # Extract dates
            dates = extract_dates(text)
            if dates:
                info["dates_found"] = dates[:10]   # first 10
                for d in dates:
                    results["date_mentions"][d] += 1
                # Build timeline entries (simplified)
                for d in dates[:5]:
                    results["timeline"].append({
                        "date": d,
                        "file": entry["filename"],
                        "sha256": entry["sha256"][:16]
                    })

        results["file_details"].append(info)

    # Sort timeline
    results["timeline"].sort(key=lambda x: x.get("date", ""))

    # Generate summary
    print("\n" + "="*60)
    print("📋 OMNISLEUTH SUMMARY REPORT")
    print("="*60)
    print(f"Total files analyzed: {results['total_files']}")
    print(f"Files containing key terms: {results['files_with_hits']}")
    print("\nHits by category:")
    for cat, count in results["hits_by_category"].most_common():
        print(f"  {cat:15}: {count}")
    print("\nTop 10 date mentions:")
    for date, cnt in results["date_mentions"].most_common(10):
        print(f"  {date}: {cnt} files")
    print("\nTerm frequency (top 10):")
    for term, files in sorted(results["term_hits"].items(), key=lambda x: len(x[1]), reverse=True)[:10]:
        print(f"  {term}: {len(files)} files")

    # Save full report
    with open(REPORT_FILE, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n💾 Full report saved to: {REPORT_FILE}")

    # Write a human-readable summary
    with open(SUMMARY_FILE, 'w') as f:
        f.write("OMNISLEUTH FORENSIC SUMMARY\n")
        f.write("="*50 + "\n")
        f.write(f"Generated: {results['scan_time']}\n")
        f.write(f"Total files: {results['total_files']}\n")
        f.write(f"Files with hits: {results['files_with_hits']}\n\n")
        f.write("Hits by category:\n")
        for cat, count in results["hits_by_category"].most_common():
            f.write(f"  {cat}: {count}\n")
        f.write("\nTerm frequency (top 20):\n")
        for term, files in sorted(results["term_hits"].items(), key=lambda x: len(x[1]), reverse=True)[:20]:
            f.write(f"  {term}: {len(files)} files\n")
        f.write("\nTimeline (first 50 events):\n")
        for ev in results["timeline"][:50]:
            f.write(f"  {ev['date']} – {ev['file']} (hash: {ev['sha256']}...)\n")
    print(f"📄 Summary saved to: {SUMMARY_FILE}")

    print("\n✅ Analysis complete. You can now review the report and anchor it.")
    print("   Use: python simple_forensic.py to add the JSON report as evidence.\n")

if __name__ == "__main__":
    main()
