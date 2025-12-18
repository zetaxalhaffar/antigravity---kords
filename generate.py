import argparse
import sys
import os

# Import modules
# Ensure current directory is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from realty_scraper import run as run_scraper
from page_generator import generate_landing_page

def main():
    parser = argparse.ArgumentParser(description="Scrape Nawy project and generate landing page.")
    parser.add_argument("url", help="Nawy Project URL")
    args = parser.parse_args()
    
    print(f"Starting process for: {args.url}")
    
    # 1. Scrape Data
    print(">>> Phase 1: Scraping Data...")
    data_list = run_scraper(args.url)
    
    if not data_list:
        print("Error: No data extracted.")
        return
    
    # Assuming single project for this flow
    project_data = data_list[0]
    
    # 2. Generate Page
    print(">>> Phase 2: Generating Landing Page...")
    page_path = generate_landing_page(project_data)
    
    print(f"\nSUCCESS! Landing page created at:\n{page_path}")
    print(f"Open this file in your browser to view the result.")
    
    # Attempt to open (Mac specific)
    try:
        os.system(f"open '{page_path}'")
    except:
        pass

if __name__ == "__main__":
    main()
