from playwright.sync_api import sync_playwright
import json
import argparse
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def extract_data(xpath, page):
    try:
        locator = page.locator(xpath)
        if locator.count() > 0:
            return locator.inner_text().strip()
    except Exception as e:
        logging.error(f"Error extracting data for xpath '{xpath}': {e}")
    return ""

def extract_links(xpath, page):
    try:
        links = page.locator(xpath).all()
        return [link.get_attribute('href') for link in links if link.get_attribute('href')]
    except Exception as e:
        logging.error(f"Error extracting links for xpath '{xpath}': {e}")
    return []

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path='C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe', headless=False)
        page = browser.new_page()

        try:
            page.goto("https://www.google.com/maps/@32.9817464,70.1930781,3.67z?", timeout=60000)
            page.wait_for_timeout(2000)

            page.locator('//input[@id="searchboxinput"]').fill(search_for)
            page.keyboard.press("Enter")
            page.wait_for_selector('//a[contains(@href, "https://www.google.com/maps/place")]')

            results = []
            unique_entries = set()
            scroll_distance = 10000
            max_scrolls = 10
            scroll_count = 0

            while len(results) < total and scroll_count < max_scrolls:
                page.mouse.wheel(0, scroll_distance)
                page.wait_for_timeout(3000)

                listings = page.locator('//a[contains(@href, "https://www.google.com/maps/place")]').all()
                logging.info(f"Found {len(listings)} listings")

                for listing in listings:
                    url = listing.get_attribute('href')
                    logging.info(f"Processing URL: {url}")

                    if url in unique_entries:
                        continue

                    try:
                        listing.click()
                        page.wait_for_timeout(2000)

                        data = {
                            "Name": extract_data('//div[@class="TIHn2 "]//h1[@class="DUwDvf lfPIob"]', page),
                            "Address": extract_data('//button[@data-item-id="address"]//div[contains(@class, "fontBodyMedium")]', page),
                            "Phone Number": extract_data('//button[contains(@data-item-id, "phone:tel:")]//div[contains(@class, "fontBodyMedium")]', page),
                            "URL": url,
                            "Hours of Operation": extract_data('//button[contains(@data-item-id, "oh")]//div[contains(@class, "fontBodyMedium")]', page).replace("\u202f",""),
                            "Reviews": {
                                "Count": extract_data('//div[@class="TIHn2 "]//div[@class="fontBodyMedium dmRWX"]//div//span//span//span[@aria-label]', page).replace('(','').replace(')','').replace(',',''),
                                "Average": extract_data('//div[@class="TIHn2 "]//div[@class="fontBodyMedium dmRWX"]//div//span[@aria-hidden]', page).replace(' ','').replace(',','.')
                            },
                            "Social Media Links": extract_links('//a[contains(@href, "facebook.com") or contains(@href, "twitter.com") or contains(@href, "instagram.com")]', page)
                        }

                        logging.info(f"Extracted Data: {data}")

                        if all(value for value in [data["Name"], data["Address"]]):
                            results.append(data)
                            unique_entries.add(url)
                            logging.info(f"Added to results: {data}")
                        
                        if len(results) >= total:
                            break
                    except Exception as e:
                        logging.error(f"Error processing URL '{url}': {e}")

                scroll_count += 1

            logging.info(f"Final results count: {len(results)}")

            # Load existing data from JSON file if it exists
            try:
                with open('escape_rooms.json', 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            except FileNotFoundError:
                existing_data = []

            # Append new data to existing data
            existing_data.extend(results)

            # Save updated data back to JSON file
            with open('escape_rooms.json', 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=4)
            
            logging.info(f"Scraping completed. {len(results)} records added to escape_rooms.json")
        
        except Exception as e:
            logging.error(f"An error occurred during the scraping process: {e}")
        
        finally:
            browser.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--search", type=str, default="room for rent")
    parser.add_argument("-t", "--total", type=int, default=101)
    args = parser.parse_args()

    search_for = args.search
    total = args.total

    main()
