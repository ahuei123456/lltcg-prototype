import requests
from bs4 import BeautifulSoup
import time
import re
import json

BASE_URL = "https://llofficial-cardgame.com/"
SEARCH_URL = f"{BASE_URL}cardlist/cardsearch_ex"
DETAIL_URL = f"{BASE_URL}cardlist/detail/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

CATEGORY_TRANSLATIONS = {
    "収録商品": "set",
    "カードタイプ": "card_type",
    "作品名": "group",
    "参加ユニット": "unit",
    "コスト": "cost",
    "基本ハート": "hearts",
    "ブレードハート": "blade_hearts",
    "ブレード": "blades",
    "レアリティ": "rarity",
    "カード番号": "card_number",
    "スコア": "score",
    "必要ハート": "required_hearts",
    "特殊ハート": "special_hearts",

}

TEXT_TRANSLATIONS = {

}


def _fetch_search_results_page(expansion, page):
    """Fetches a single page of card search results for an expansion."""
    print(f"Fetching page {page} for expansion {expansion}...")
    params = {"expansion": expansion, "page": page}
    try:
        response = requests.get(SEARCH_URL, headers=HEADERS, params=params)

        if response.status_code == 404:
            print(f"Page {page} not found. Reached end of expansion {expansion}.")
            return None  # Indicates end of pages

        response.raise_for_status()  # Raise an exception for other bad status codes
        return response.text

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None  # Indicates a network error


def _parse_card_numbers_from_html(html_content):
    """Parses search result HTML to extract card numbers."""
    soup = BeautifulSoup(html_content, "html.parser")
    card_items = soup.select(".ex-item.cardlist-Result_Item.image-Item")

    card_numbers = []
    for div in card_items:
        card_number = div.get("card", "").strip()
        if card_number:
            card_numbers.append(card_number)

    return card_numbers


def get_card_numbers_from_expansion(expansion="NSD01"):
    """Orchestrates fetching and parsing all card numbers for an expansion."""
    page = 1
    all_card_numbers = []

    while True:
        html_content = _fetch_search_results_page(expansion, page)
        if not html_content:
            break

        card_numbers_on_page = _parse_card_numbers_from_html(html_content)
        if not card_numbers_on_page:
            print(f"No cards found on page {page}. Assuming end of expansion {expansion}.")
            break

        all_card_numbers.extend(card_numbers_on_page)
        page += 1
        time.sleep(1)  # Be polite to the server

    return all_card_numbers

def parse_info_text(info_text_tag):
    """Extract and format text from the ability/info text block."""
    lines = []
    current_line = []
    prev_br = False
    for content in info_text_tag.descendants:
        if content.name == "img":
            if prev_br:
                lines.append(" ".join(current_line))
                current_line = []
                prev_br = False
            alt_text = content.get("alt", "").strip()
            if alt_text:
                current_line.append(alt_text)
        elif isinstance(content, str):
            text = content.strip()
            if text:
                prev_br = False
                current_line.append(text)
        elif content.name == "br":
            if current_line:
                prev_br = True

    if current_line:
        lines.append(" ".join(current_line))

    return [line.strip() for line in lines if line.strip()]


def _fetch_card_details_page(card_number):
    """Fetches the HTML for a single card's details page."""
    # This header makes our request look like it came from the card list page, which is crucial.
    detail_headers = HEADERS.copy()
    detail_headers['Referer'] = 'https://llofficial-cardgame.com/cardlist/'

    try:
        response = requests.post(DETAIL_URL, headers=detail_headers, data={"cardno": card_number})
        response.raise_for_status()

        if not response.text:
            print(f"Empty response for {card_number}.")
            return None
        return response.text

    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch details for {card_number}. Error: {e}")
        return None


def _parse_card_details(html_content, card_number):
    """Parses the HTML of a card detail page to extract its data."""
    soup = BeautifulSoup(html_content, "html.parser")

    # The main container for all the card's information.
    card_info_container = soup.select_one(".cardlist-Info")
    if not card_info_container:
        print(f"Card details container not found for {card_number}.")
        return None

    card_data = {"card_number": card_number}

    # Extract the image URL
    img_tag = card_info_container.select_one(".info-Image img")
    if img_tag and img_tag.has_attr('src'):
        # Ensure the URL is absolute
        img_src = img_tag['src']
        if img_src.startswith('/'):
            card_data["img_url"] = f"{BASE_URL.strip('/')}{img_src}"
        else:
            card_data["img_url"] = img_src

    # Extract the name
    member_tag = card_info_container.find("p", class_="info-Heading")
    if member_tag:
        card_data["name"] = member_tag.text.strip()

    # Extract main card attributes from the dl/dt/dd list
    info_detail = card_info_container.select_one(".info-Detail")
    if info_detail:
        for dl_item in info_detail.select(".dl-Item"):
            dt = dl_item.find("dt")
            dd = dl_item.find("dd")

            if dt and dd:
                key = dt.get_text(strip=True)
                if key in CATEGORY_TRANSLATIONS:
                    key = CATEGORY_TRANSLATIONS[key]

                # Handling for hearts, which can have nested spans or special images
                if key in ["required_hearts", "hearts", "blade_hearts"]:
                    values = {}
                    spans = dd.find_all("span")
                    if spans:
                        for span in spans:
                            class_name = next((cls for cls in span.get("class", []) if "heart" in cls), None)
                            if class_name:
                                text = span.get_text(strip=True)
                                # An empty span for a heart implies a value of 1, per business logic.
                                if len(text) == 0:
                                    text = "1"
                                values[class_name] = text
                        card_data[key] = values
                    # Handle edge case for blade_hearts with an 'ALL' image instead of spans
                    elif key == "blade_hearts" and dd.find("img", alt="ALL1"):
                        card_data[key] = {"ALL1": "1"}
                elif key == "special_hearts":
                    if len(dd.text.strip()) > 0:
                        card_data[key] = dd.text.strip()
                    else:
                        card_data[key] = dd.find("img")['alt'][:-1]
                elif key == "group":
                    card_data[key] = [group for group in dd.strings]
                else:
                    card_data[key] = dd.get_text(strip=True)

    # Extract the card's ability text
    info_text_tag = card_info_container.select_one(".info-Text")
    if info_text_tag:
        card_data["info_text"] = parse_info_text(info_text_tag)

    # Add the original card number again for consistency, as some older cards might have it in the details
    if "card_number" not in card_data:
        card_data["card_number"] = card_number

    return card_data


def get_card_details(card_number):
    """Fetches and parses detailed card info."""
    html_content = _fetch_card_details_page(card_number)
    if not html_content:
        return None

    return _parse_card_details(html_content, card_number)


def _fetch_cardlist_page():
    """Fetches the main cardlist page HTML."""
    cardlist_url = f"{BASE_URL}cardlist/"
    try:
        response = requests.get(cardlist_url, headers=HEADERS)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Could not fetch expansion codes page. Error: {e}")
        return None

def _parse_expansion_codes(html_content):
    """Parses the cardlist page HTML to extract expansion codes."""
    soup = BeautifulSoup(html_content, "html.parser")
    expansion_codes = []

    # Select all 'a' tags that have the 'productsList-Item' class.
    # The dot '.' is crucial for selecting by class name.
    for item in soup.select("a.productsList-Item"):
        href = item.get("href", "")
        match = re.search(r"expansion=([\w\d-]+)", href)
        if match:
            expansion_codes.append(match.group(1))

    # The same expansion code can appear multiple times on the page.
    # We return a list of unique codes, preserving the order of first appearance.
    return list(dict.fromkeys(expansion_codes))

def get_expansion_codes():
    """Scrape the main card list page and extract all expansion codes."""
    print("Fetching expansion codes...")
    html_content = _fetch_cardlist_page()
    if not html_content:
        return []
    expansion_codes = _parse_expansion_codes(html_content)
    print(f"Found {len(expansion_codes)} expansion codes.")
    return expansion_codes

# --- Main Execution ---
if __name__ == "__main__":
    all_expansion_codes = get_expansion_codes()
    all_cards_data = []

    if not all_expansion_codes:
        print("No expansion codes found. Exiting.")
    else:
        for code in all_expansion_codes:
            print(f"\n--- Starting scrape for expansion: {code} ---")
            card_numbers = get_card_numbers_from_expansion(code)
            
            for number in card_numbers:
                print(f"Fetching details for {number}...")
                details = get_card_details(number)
                if details:
                    all_cards_data.append(details)
                
                # time.sleep(1) # Be polite to the server

        # Save the scraped data to a JSON file
        output_file = "card_data_new.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(all_cards_data, f, ensure_ascii=False, indent=4)

        print(f"\nScraping complete. Data for {len(all_cards_data)} cards saved to {output_file}")