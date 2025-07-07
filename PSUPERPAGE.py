import csv
import time
import random
import os
import gc
import signal
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

CATEGORIES = ["Masonary",
              "Security+Guard", "Photography", "Moving+Companies", "Tow"
              "+Truck"]


city_url_tuples = [
    (["Salt Lake City", "West Valley City", "Saint George", "Ogden", "Logan", "Moab",
      "West Jordan", "Orem", "Lehi", "Sandy", "South Jordan", "Layton", "Provo"], "UT"),
    (["Denver", "Colorado Springs", "Aurora", "Fort Collins",
     "Lakewood", "Thornton", "Pueblo", "Arvada", "Westminster"], "CO"),
    (["Wichita", "Overland Park", "Kansas City", "Olathe",
     "Topeka", "Lawrence", "Shawnee", "Manhattan", "Lenexa"], "KS"),
    (["Oklahoma City", "Tulsa", "Norman", "Broken Arrow", "Edmond", "Lawton"], "OK"),
    (["Houston", "San Antonio", "Dallas", "Austin", "Fort Worth", "El Paso",
     "Arlington", "Corpus Christi", "Plano", "Laredo", "Lubbock", "Garland"], "TX"),
    (["Kansas City", "Saint Louis", "Springfield", "Columbia",
     "Independence", "Lee’s Summit", "O’Fallon", "Saint Joseph"], "MO"),
    (["New Orleans", "Baton Rouge", "Shreveport",
     "Lafayette", "Lake Charles", "Kenner"], "LA"),
    (["Chicago", "Aurora", "Naperville", "Joliet", "Rockford",
     "Springfield", "Peoria", "Elgin", "Waukegan", "Cicero"], "IL"),
    (["Columbus", "Cleveland", "Cincinnati", "Toledo", "Akron",
     "Dayton", "Parma", "Canton", "Youngstown"], "OH"),
    (["Detroit", "Grand Rapids", "Warren", "Sterling Heights", "Lansing",
     "Ann Arbor", "Flint", "Dearborn", "Livonia", "Westland", "Troy"], "MI"),
    (["Nashville", "Memphis", "Knoxville", "Chattanooga",
     "Clarksville", "Murfreesboro"], "TN"),
    (["Jacksonville", "Miami", "Tampa", "Orlando", "St. Petersburg", "Hialeah", "Port St. Lucie", "Cape Coral", "Tallahassee", "Fort Lauderdale",
     "Pembroke Pines", "Hollywood", "Gainesville", "Miramar", "Coral Springs", "Palm Bay", "Clearwater", "Lakeland", "Pompano Beach", "West Palm Beach"], "FL"),
    (["Atlanta", "Augusta", "Columbus", "Macon", "Savannah", "Athens", "Sandy Springs", "Roswell", "Johns Creek",
     "Albany", "Warner Robins", "Alpharetta", "Marietta", "Valdosta", "Smyrna", "Dunwoody"], "GA"),
    (["Columbia", "Charleston", "North Charleston", "Mount Pleasant", "Rock Hill",
     "Greenville", "Summerville", "Sumter", "Goose Creek", "Hilton Head Island"], "SC"),
    (["Charlotte", "Raleigh", "Greensboro", "Durham", "Winston-Salem",
     "Fayetteville", "Cary", "Wilmington", "High Point", "Concord"], "NC"),
    (["Virginia Beach", "Norfolk", "Chesapeake", "Richmond", "Newport News",
     "Alexandria", "Hampton", "Roanoke", "Portsmouth", "Suffolk"], "VA"),
    (["Baltimore", "Columbia", "Germantown", "Silver Spring", "Waldorf",
     "Glen Burnie", "Ellicott City", "Frederick", "Dundalk", "Rockville"], "MD"),
    (["Indianapolis", "Fort Wayne", "Evansville", "South Bend", "Carmel",
     "Fishers", "Bloomington", "Hammond", "Gary", "Lafayette"], "IN")
]

last_page_file = "last_page.txt"
output_file = "07.03Freelance.csv"

all_data = set()
entry_count = 0
page_counter = 0
pages_before_restart = 200

browser = None
context = None
page = None


def log(msg, tag="INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{tag}] {timestamp} - {msg}")


def load_existing_data():
    global all_data, entry_count
    if os.path.exists(output_file):
        with open(output_file, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                if len(row) >= 5:
                    all_data.add(tuple(row[:5]))
        entry_count = len(all_data)


def load_last_page():
    if os.path.exists(last_page_file):
        with open(last_page_file, "r") as f:
            line = f.read().strip()
            if line.isdigit():
                return int(line)
    return 1


def save_last_page(page_num):
    with open(last_page_file, "w") as f:
        f.write(str(page_num))


def save_data():
    with open(output_file, "w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Business Name", "Phone Number",
                        "Address", "Category", "State"])
        for row in all_data:
            writer.writerow(row)


def create_browser(playwright):
    global browser, context, page
    if browser:
        browser.close()

    user_agent = random.choice([
        "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",

        # 📱 Android
        "Mozilla/5.0 (Linux; Android 13; Pixel 7 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Mobile Safari/537.36",

        # 💻 MacBook (Safari)
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15",

        # 💻 MacBook (Chrome)
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.5845.97 Safari/537.36",

        # 💻 Windows (Chrome)
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",

        # 💻 Windows (Edge)
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36 Edg/115.0.1901.188"
        # 📱 Android (Samsung)
        "Mozilla/5.0 (Linux; Android 13; SAMSUNG SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.80 Mobile Safari/537.36",

        # 📱 iPad (Safari)
        "Mozilla/5.0 (iPad; CPU OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",

        # 💻 Windows (Firefox)
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:118.0) Gecko/20100101 Firefox/118.0",

        # 💻 Linux (Chrome)
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.5938.149 Safari/537.36",

        # 💻 Chromebook (Chrome OS)
        # (your list as before)
        "Mozilla/5.0 (X11; CrOS x86_64 15474.61.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.234 Safari/537.36"
    ])

    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context(
        user_agent=user_agent,
        java_script_enabled=True,
        viewport={'width': 1200, 'height': 800},
        bypass_csp=True
    )

    context.route("**/*", lambda route, request: route.abort()
                  if request.resource_type in ["image", "stylesheet", "font"] else route.continue_())

    page = context.new_page()


def scrape_page(category, state):
    global entry_count
    try:
        page.wait_for_selector("a.business-name", timeout=20000)
    except PlaywrightTimeoutError:
        log("Timeout waiting for business listings", "TIMEOUT")
        return

    listings = page.query_selector_all("div.result")
    for listing in listings:
        name = listing.query_selector("a.business-name span")
        phone = listing.query_selector(
            "a.phones.phone.primary span.call-number")
        adr_block = listing.query_selector("p.adr")
        address = (adr_block.query_selector("span.street-address").inner_text().strip()
                   if adr_block and adr_block.query_selector("span.street-address")
                   else (adr_block.inner_text().strip() if adr_block else "N/A"))

        entry = (
            name.inner_text().strip() if name else "N/A",
            phone.inner_text().strip() if phone else "N/A",
            address,
            category,
            state
        )
        if entry not in all_data:
            all_data.add(entry)
            entry_count += 1
            print(f"{entry_count}: {entry[0]} | {entry[1]} | {entry[2]}")


def run_scraper():
    global page_counter, all_data, entry_count

    signal.signal(signal.SIGINT, lambda sig, frame: (save_data(), exit(0)))

    with sync_playwright() as p:
        for category in CATEGORIES:
            # Prepare variables for each category
            global CATEGORY, CATEGORY_FOR_URL, CATEGORY_FOR_OUTPUT, output_file, all_data, entry_count

            CATEGORY = category
            CATEGORY_FOR_URL = CATEGORY.replace(" ", "+")
            CATEGORY_FOR_OUTPUT = CATEGORY.title()
            output_file = f"07.02superpages{CATEGORY}_.csv"

            all_data = set()
            entry_count = 0
            page_counter = 0

            load_existing_data()
            current_page_num = load_last_page()

            create_browser(p)

            for cities, state in city_url_tuples:
                for city in cities:
                    log(f"Starting city: {city}, {state} for category {CATEGORY}")
                    base_url = f"https://www.superpages.com/search?search_terms={CATEGORY_FOR_URL}&geo_location_terms={city.replace(' ', '+')}%2C+{state}"
                    page_url = base_url
                    while page_url:
                        try:
                            page.goto(page_url, timeout=45000)
                            scrape_page(CATEGORY_FOR_OUTPUT, state)
                            page_counter += 1
                            current_page_num += 1
                            save_last_page(current_page_num)

                            if page_counter >= pages_before_restart:
                                log("Restarting browser to free memory")
                                gc.collect()
                                create_browser(p)
                                page_counter = 0

                            next_btn = page.query_selector("a.next.ajax-page")
                            next_href = next_btn.get_attribute(
                                "href") if next_btn else None
                            if next_href:
                                page_url = "https://www.superpages.com" + \
                                    next_href if not next_href.startswith(
                                        "http") else next_href
                            else:
                                break
                        except Exception as e:
                            log(f"Error: {e}", "ERROR")
                            time.sleep(2)
                save_data()
                create_browser(p)
            save_data()
            log(f"Finished category '{CATEGORY}'. Total unique entries: {entry_count}", "DONE")


if __name__ == "__main__":
    run_scraper()
