from playwright.sync_api import sync_playwright
import pandas as pd
import os
import time
import re
import requests

# Constants
LOGIN_URL = "https://partners.nawy.com/login"
NAWY_HOME = "https://partners.nawy.com"
EREALTY_URL = "https://erealty.nawy.com/"
USERNAME = "01100228705"
PASSWORD = "Ahmed@1234"
OUTPUT_DIR = "output_files"

def sanitize_filename(name):
    return "".join([c for c in name if c.isalpha() or c.isdigit() or c in (' ', '-', '_')]).strip()

import argparse

def run(target_url=None):
    with sync_playwright() as p:
           browser = p.chromium.launch(headless=True)  # Changed from False to True
        context = browser.new_context()
        page = context.new_page()

        # 2. Determine Scope & Actions
        # Check for public Nawy page (Arabic or English) - simplistic check for main domain
        if target_url and "nawy.com" in target_url and "erealty" not in target_url and "partners" not in target_url:
            print(f"Targeting public Nawy Page: {target_url}")
            project_links = [target_url]
            # No login needed for public pages, but we already launched browser
        elif target_url:
            print(f"Targeting single URL (E-Realty): {target_url}")
            # Ensure Login for E-Realty
            login(page)
            project_links = [target_url]
        else:
            # Full E-Realty Scrape
            login(page)
            # Navigate to E-Realty and list projects
            print("Navigating to E-Realty...")
            page.goto(EREALTY_URL)
            
            # Wait for projects to load
            try:
                page.wait_for_selector("a.MuiStack-root.css-pgkduz", timeout=15000)
            except:
                print("Timeout waiting for projects. Reloading...")
                page.reload()
                page.wait_for_selector("a.MuiStack-root.css-pgkduz", timeout=15000)

            # List Projects
            print("Loading projects...")
            # Scroll down a few times to load more
            for _ in range(5):
                page.mouse.wheel(0, 1000)
                time.sleep(1)
            
            project_cards = page.query_selector_all("a.MuiStack-root.css-pgkduz")
            print(f"Found {len(project_cards)} projects.")
            
            for card in project_cards:
                href = card.get_attribute("href")
                if href:
                    full_url = href if href.startswith("http") else f"https://erealty.nawy.com{href}"
                    project_links.append(full_url)

        extracted_data = []

        # 3. Scrape Projects
        for link in project_links:
            try:
                print(f"Scraping: {link}")
                page.goto(link)
                
                # BRANCH: Public Nawy Page
                if "nawy.com" in link and "erealty" not in link and "partners" not in link:
                    # Check for generic container, but usually 'div#entity-data' is good for new Nawy
                    page.wait_for_selector("div#entity-data", timeout=20000)
                    
                    # 1. Project Name
                    try:
                        project_name = page.title().split('-')[0].strip()
                        # Fallback to header if title is generic
                        if not project_name or "Nawy" in project_name:
                             header = page.query_selector("h1")
                             if header: project_name = header.inner_text().strip()
                    except:
                        project_name = "Untitled_Project"
                    
                    safe_name = sanitize_filename(project_name)
                    print(f"Project Name: {project_name}")

                    # 2. Description
                    description = ""
                    try:
                        # Strategy: Verified via debug as `div#head div.description`
                        description_container = page.query_selector("div#head div.description")
                        if description_container:
                            description = description_container.inner_text().strip()
                        
                        if not description:
                             # Fallback: Strategy: Find header matching "About" or "عن" and get sibling/parent text
                             about_header = page.query_selector("h2:has-text('عن'), h2:has-text('About')")
                             if about_header:
                                 container = about_header.query_selector("xpath=..")
                                 if container:
                                     # Look for the description sibling
                                     desc_sibling = container.query_selector(".description")
                                     if desc_sibling:
                                         description = desc_sibling.inner_text().strip()
                                     else:
                                         paragraphs = container.query_selector_all("p")
                                         description = "\n".join([p.inner_text() for p in paragraphs if len(p.inner_text()) > 50])

                        if not description:
                            # Final Fallback: Look for any paragraph with substantial Arabic text
                            all_ps = page.query_selector_all("div#entity-data p")
                            candidates = [p.inner_text() for p in all_ps if len(p.inner_text()) > 100]
                            description = "\n".join(candidates)
                    except Exception as e:
                        print(f"Error extracting description: {e}")

                    image_urls = set()
                    master_plan_url = None

                    # 3. Master Plan
                    try:
                        # Try to find "Project Plan" or "مخطط المشروع" tab
                        tabs = page.query_selector_all("div, span, li, a")
                        project_plan_tab = None
                        for tab in tabs:
                            if "مخطط المشروع" in tab.inner_text() or "Project Plan" in tab.inner_text():
                                project_plan_tab = tab
                                break
                        
                        if project_plan_tab:
                            print("Found Master Plan tab, clicking...")
                            project_plan_tab.click()
                            time.sleep(2) # Wait for tab switch
                            
                            # Look for image in the likely active container or just search for new visible images
                            # Heuristic: The master plan is often chemically inside #entity-data or just a large image revealed
                            # Inspecting the page DOM from research: it seems to be inside div#entity-data img
                            mp_imgs = page.query_selector_all("div#entity-data img")
                            for img in mp_imgs:
                                src = img.get_attribute("src")
                                if src:
                                    master_plan_url = src
                                    break # Take the first one found in the content area
                        
                        if not master_plan_url:
                             # Fallback: Check if any image has 'master plan' or 'مخطط' in alt
                             all_imgs = page.query_selector_all("img")
                             for img in all_imgs:
                                 alt = img.get_attribute("alt") or ""
                                 if "مخطط" in alt or "master" in alt.lower():
                                     master_plan_url = img.get_attribute("src")
                                     break
                    except Exception as e:
                        print(f"Error iterating master plan: {e}")

                    # 4. Project Photos (Gallery)
                    try:
                         # The top gallery is typically separate from entity-data
                         # Research showed it as div#__next > div > div:nth-of-type(5)
                         # We can look for the large gallery container
                         gallery_imgs = page.query_selector_all("div#__next > div > div:nth-of-type(5) img")
                         if not gallery_imgs:
                             # Fallback global search for gallery-like images (excluding logos/icons)
                             gallery_imgs = page.query_selector_all("img[src*='images.nawy.com']")
                        
                         for img in gallery_imgs:
                             src = img.get_attribute("src")
                             if src:
                                 src_lower = src.lower()
                                 # Enhanced Filter: Exclude icons, logos, SVGs, and specific small assets
                                 if ("logo" not in src_lower and 
                                     "icon" not in src_lower and 
                                     ".svg" not in src_lower and 
                                     "placeholder" not in src_lower and
                                     src != master_plan_url):
                                     image_urls.add(src)
                    except Exception as e:
                        print(f"Error extracting gallery: {e}")

                # BRANCH: E-Realty Page (Original Logic)
                else: 
                    page.wait_for_selector("div.MuiStack-root.css-5t4gzz", timeout=10000) # Wait for content area

                    # Extract Project Name
                    try:
                        project_name = page.inner_text("h1, h2").split('\n')[0]
                    except:
                        project_name = "Untitled_Project"
                    
                    safe_name = sanitize_filename(project_name)
                    print(f"Project Name: {project_name}")

                    # Extract Description
                    description = ""
                    try:
                        desc_elements = page.query_selector_all("div.MuiStack-root.css-5t4gzz p, div.MuiStack-root.css-5t4gzz .MuiTypography-root")
                        description = "\n".join([el.inner_text() for el in desc_elements if len(el.inner_text()) > 20])
                    except Exception as e:
                        print(f"Error extracting description: {e}")

                    # Extract Photos
                    image_urls = set()
                    master_plan_url = None # E-Realty doesn't seem to split this well yet, treated as normal photo
                    try:
                        # Try multiple selectors
                        # 1. Gallery images with /gallery/ path
                        imgs = page.query_selector_all("img[src*='/gallery/']")
                        
                        # 2. Compound images (seen in The Crest)
                        if not imgs:
                            imgs = page.query_selector_all("img[src*='compound_image']")
                        
                        # 3. Sidebar gallery specific container
                        if not imgs:
                            imgs = page.query_selector_all(".MuiBox-root.css-1ml5yzj img")

                        for img in imgs:
                            src = img.get_attribute("src")
                            if src:
                                src_lower = src.lower()
                                if ("logo" not in src_lower and 
                                    "icon" not in src_lower and 
                                    ".svg" not in src_lower and
                                    "nawy-logo" not in src_lower): 
                                    image_urls.add(src)
                    except Exception as e:
                        print(f"Error extracting images: {e}")
                
                # Save Data
                
                # Download Images
                project_dir = os.path.join(OUTPUT_DIR, safe_name)
                os.makedirs(project_dir, exist_ok=True)
                
                # Save Description Text
                desc_path = os.path.join(project_dir, "description.txt")
                with open(desc_path, "w", encoding="utf-8") as f:
                    f.write(description)

                mp_path = None
                # Download Master Plan
                if master_plan_url:
                    try:
                        res = requests.get(master_plan_url, stream=True)
                        if res.status_code == 200:
                            ext = os.path.splitext(master_plan_url)[1] or ".jpg"
                            if "?" in ext: ext = ext.split("?")[0]
                            mp_path = os.path.join(project_dir, f"master_plan{ext}")
                            with open(mp_path, 'wb') as f:
                                for chunk in res.iter_content(1024):
                                    f.write(chunk)
                    except Exception as e:
                        print(f"Failed to download Master Plan: {e}")

                # Download Gallery
                gallery_paths = []
                if image_urls:
                    for i, img_url in enumerate(image_urls):
                        try:
                            # Using requests to download to avoid browser overhead for just bytes
                            res = requests.get(img_url, stream=True)
                            if res.status_code == 200:
                                ext = os.path.splitext(img_url)[1] 
                                if "?" in ext: ext = ext.split("?")[0]
                                if not ext or len(ext) > 5: ext = ".jpg"
                                img_path = os.path.join(project_dir, f"image_{i+1}{ext}")
                                with open(img_path, 'wb') as f:
                                    for chunk in res.iter_content(1024):
                                        f.write(chunk)
                                gallery_paths.append(img_path)
                        except Exception as e:
                            print(f"Failed to download image: {e}")
                
                # Add to result data
                extracted_data.append({
                    "Project Name": project_name,
                    "Link": link,
                    "Description": description,
                    "Description Path": desc_path,
                    "Image Count": len(image_urls),
                    "Has Master Plan": bool(master_plan_url),
                    "Master Plan Path": mp_path,
                    "Gallery Paths": gallery_paths,
                    "Output Dir": project_dir
                })
                            
            except Exception as e:
                print(f"Failed to scrape project {link}: {e}")

        browser.close()

        # Save Metadata to Excel
        if extracted_data:
            df = pd.DataFrame(extracted_data)
            output_path = os.path.join(OUTPUT_DIR, "extracted_projects.xlsx")
            df.to_excel(output_path, index=False)
            print(f"Saved metadata to {output_path}")
            
        return extracted_data

def login(page):
    print("Logging in...")
    try:
        # Go to home and click Login
        page.goto(NAWY_HOME)
        page.get_by_role("button", name="Login").click()
        
        # Now fill credentials
        page.fill("input[placeholder='Enter your Phone number']", USERNAME)
        page.fill("input[placeholder='Enter your password']", PASSWORD)
        # Use specific text selector to avoid background buttons
        page.click("button:has-text('Log In')")
        
        # Wait for login to complete (check for dashboard element or URL change)
        page.wait_for_url("**/landing/**", timeout=20000)
        print("Login successful.")
    except Exception as e:
        print(f"Login failed: {e}")
        page.screenshot(path="debug_login_fail.png")
        raise e

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape Nawy E-Realty")
    parser.add_argument("url", nargs="?", help="Specific project URL to scrape")
    args = parser.parse_args()
    
    try:
        run(target_url=args.url)
    except Exception as e:
        print(f"Global error: {e}")

