import asyncio
import json
import re
import os
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

class INDmoneyScraper:
    def __init__(self, urls):
        self.urls = urls
        self.results = []

    async def fetch_page(self, url):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            print(f"Scraping: {url}...")
            try:
                await page.goto(url, wait_until="networkidle", timeout=60000)
                await asyncio.sleep(2) 
                content = await page.content()
                return content
            except Exception as e:
                print(f"Error fetching {url}: {e}")
                return None
            finally:
                await browser.close()

    def parse_json(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string and '"props"' in script.string:
                try:
                    match = re.search(r'\{.*\}', script.string)
                    if match:
                        return json.loads(match.group(0))
                except:
                    continue
        return None

    def extract_fields(self, data, url):
        try:
            fund_data = data['props']['pageProps']['mutualFundsDetailData']['data']
            
            # Helper to find items in fund_overview.info
            info_list = fund_data.get('fund_overview', {}).get('info', [])
            info_map = {item['name'].lower().replace(' ', ''): item.get('value') or item.get('description') for item in info_list if 'name' in item}

            # Map basic fields
            fields = {
                "Fund Name": fund_data.get('name'),
                "AMC": next((link['name'] for link in fund_data.get('tag_links', []) if 'amc' in link.get('link', '')), "N/A"),
                "Category": next((link['name'] for link in fund_data.get('tag_links', []) if 'category' in link.get('link', '') or '-cap-' in link.get('link', '')), "N/A"),
                "NAV": fund_data.get('nav'),
                "Expense Ratio": info_map.get('expenseratio', 'N/A'),
                "Benchmark": info_map.get('benchmark', 'N/A'),
                "AUM": next((str(item.get('value') or item.get('description', '')) for item in info_list if 'aum' in str(item.get('name', '')).lower()), 'N/A'),
                "Inception Date": info_map.get('inceptiondate', 'N/A'),
                "Minimum Lumpsum": info_map.get('minlumpsum/sip', 'N/A').split('/')[0] if 'minlumpsum/sip' in info_map else 'N/A',
                "Minimum SIP": info_map.get('minlumpsum/sip', 'N/A'). split('/')[-1] if 'minlumpsum/sip' in info_map else 'N/A',
                "Exit Load": info_map.get('exitload', 'N/A'),
                "Lock-in Period": info_map.get('lockin', 'N/A'),
                "Portfolio Turnover": info_map.get('turnover', 'N/A'),
                "Source URL": url
            }

            # Riskometer (Verified Path)
            risk_props = fund_data.get('risk_meter', {}).get('widget_properties', {})
            fields["Riskometer"] = risk_props.get('zone_title') or risk_props.get('body') or "N/A"

            # Fund Manager (Multi-strategy)
            manager_data = fund_data.get('about', {}).get('managers', {}).get('widget_properties', {}).get('card_data', {}).get('rows', [])
            fields["Fund Manager"] = ", ".join([m.get('title') for m in manager_data if 'title' in m]) or "N/A"
            
            faqs = fund_data.get('static_content', {}).get('faqs', [])
            if fields["Fund Manager"] == "N/A":
                for faq in faqs:
                    if 'manager' in faq.get('ques', '').lower():
                        fields["Fund Manager"] = faq['ans'][0]['text']['label'].replace('The fund managers are ', '').replace('The fund manager is ', '').strip('.')
                        break

            # Investment Objective (Expanded strategy)
            about_items = fund_data.get('about', {}).get('about_fund', [])
            objective_item = next((item for item in about_items if any(k in item.get('title', '').lower() for k in ['objective', 'aim', 'investment'])), None)
            if objective_item and objective_item.get('text'):
                obj_text = objective_item['text'][0].get('title', '')
                fields["Investment Objective"] = BeautifulSoup(obj_text, 'html.parser').get_text().strip()
            else:
                # Search FAQs for objective
                for faq in faqs:
                    if any(k in faq.get('ques', '').lower() for k in ['objective', 'aim']):
                        fields["Investment Objective"] = faq['ans'][0]['text']['label']
                        break
            if "Investment Objective" not in fields or fields["Investment Objective"] == "N/A":
                # Final fallback: search all 'about_fund' for the longest text block that looks like an objective
                texts = [BeautifulSoup(item['text'][0]['title'], 'html.parser').get_text().strip() for item in about_items if item.get('text')]
                if texts: fields["Investment Objective"] = max(texts, key=len)

            # Statement Logic
            statement_faq = next((faq for faq in faqs if any(k in faq.get('ques', '').lower() for k in ['statement', 'download'])), None)
            fields["How to Download Statement"] = statement_faq['ans'][0]['text']['label'] if statement_faq else "Visit the official AMC website or use the AMC mobile app to download statements."

            return fields
        except Exception as e:
            print(f"Error parsing fields for {url}: {e}")
            return None

    async def run(self):
        print(f"--- Starting Scraper for {len(self.urls)} URLs ---")
        for url in self.urls:
            try:
                html = await self.fetch_page(url)
                if html:
                    json_data = self.parse_json(html)
                    if json_data:
                        extracted = self.extract_fields(json_data, url)
                        if extracted:
                            self.results.append(extracted)
                            print(f"Successfully scraped: {extracted['Fund Name']}")
                        else:
                            print(f"Failed to extract fields for: {url}")
                    else:
                        print(f"Failed to parse JSON for: {url}")
                else:
                    print(f"Failed to fetch HTML for: {url}")
            except Exception as e:
                print(f"Unexpected error scraping {url}: {e}")
        
        if not self.results:
            print("CRITICAL: No funds were scraped. Skipping save to prevent data loss.")
            sys.exit(1) # Exit with error to notify GitHub Actions

        print(f"--- Scraping Complete. Collected {len(self.results)} funds. ---")
        output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "structured_funds.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2)
        print(f"Successfully saved to {output_path}")

if __name__ == "__main__":
    urls = [
        "https://www.indmoney.com/mutual-funds/kotak-large-cap-direct-growth-3941",
        "https://www.indmoney.com/mutual-funds/hdfc-large-cap-fund-direct-plan-growth-option-2989",
        "https://www.indmoney.com/mutual-funds/hdfc-small-cap-fund-direct-growth-option-3580",
        "https://www.indmoney.com/mutual-funds/hdfc-mid-cap-fund-direct-plan-growth-option-3097",
        "https://www.indmoney.com/mutual-funds/icici-prudential-large-cap-fund-direct-plan-growth-2995",
        "https://www.indmoney.com/mutual-funds/icici-prudential-smallcap-fund-direct-plan-growth-3588",
        "https://www.indmoney.com/mutual-funds/icici-prudential-midcap-fund-direct-plan-growth-3190",
        "https://www.indmoney.com/mutual-funds/kotak-midcap-fund-direct-growth-3945",
        "https://www.indmoney.com/mutual-funds/kotak-small-cap-direct-growth-3979"
    ]
    scraper = INDmoneyScraper(urls)
    asyncio.run(scraper.run())
