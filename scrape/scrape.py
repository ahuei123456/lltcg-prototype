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


def get_card_list(expansion="NSD01"):
    """Fetch all cards from the search results, handling pagination automatically."""
    page = 1
    all_cards = []

    while True:
        print(f"Fetching page {page} for expansion {expansion}...")
        params = {"expansion": expansion, "page": page}
        response = requests.get(SEARCH_URL, headers=HEADERS, params=params)

        if response.status_code == 404:
            break  # Stop when we hit a 404 (no more pages)

        soup = BeautifulSoup(response.text, "html.parser")
        card_items = soup.select(".ex-item.cardlist-Result_Item.image-Item")

        if not card_items:
            break  # Stop if no more cards are found

        for div in card_items:
            card_number = div.get("card", "").strip()
            img_tag = div.find("img")
            img_url = BASE_URL + img_tag["src"].lstrip("/") if img_tag else None
            all_cards.append({"card_number": card_number, "img_url": img_url})

        page += 1
        time.sleep(1)  # Avoid spamming the server

    return all_cards


def clean_class_name(class_name):
    """Remove 'icon' prefix from class names."""
    return " ".join(c for c in class_name.split() if c != "icon")


def parse_info_text(info_text_tag):
    """Extract text from <p class='info-Text'>, replacing <img> tags with their alt text.
    Handles <br> tags correctly: starts a new line only if followed by an <img>.
    """
    lines = []
    current_line = []

    for content in info_text_tag.children:
        if content.name == "img":
            current_line.append(content["alt"])  # Replace <img> with its alt text
        elif isinstance(content, str):  # Text node
            text = content.strip()
            if text:
                current_line.append(text)
        elif content.name == "br":
            # Check next non-whitespace element after <br>
            next_sibling = content.find_next_sibling()
            if next_sibling and next_sibling.name == "img":
                # Start a new line if next is an <img>
                if current_line:
                    lines.append(" ".join(current_line))
                    current_line = []
            else:
                # Otherwise, <br> behaves as inline spacing
                current_line.append(" ")

    # Add the last line if it contains any text
    if current_line:
        lines.append(" ".join(current_line))

    return [line.strip() for line in lines if line.strip()]  # Remove empty lines


def get_card_details(card_number):
    """Fetch detailed card info using a POST request."""
    response = requests.post(DETAIL_URL, headers=HEADERS, data={"cardno": card_number})

    if response.status_code != 200:
        return None  # Skip if there's an error

    soup = BeautifulSoup(response.text, "html.parser")
    card_data = {"card_number": card_number}

    # Extract the name
    member_tag = soup.find("p", class_="info-Heading")
    if member_tag:
        card_data["name"] = member_tag.text.strip()

    # Extract main card info
    info_detail = soup.select_one(".info-Detail")
    if info_detail:
        for dl_item in info_detail.select(".dl-Item"):
            dt = dl_item.find("dt")
            dd = dl_item.find("dd")

            if dt and dd:
                key = dt.get_text(strip=True)

                # Special handling for '必要ハート', '基本ハート', and 'ブレードハート'
                if key == "必要ハート":
                    values = {}
                    for span in dd.find_all("span", class_=True):
                        class_name = next(
                            (cls for cls in span["class"] if "heart" in cls), None
                        )  # Find class containing "heart"
                        heart_value = span.get_text(
                            strip=True
                        )  # Extract number inside span
                        if class_name:
                            values[class_name] = heart_value  # Store as dictionary
                    card_data[key] = values
                elif key in ["基本ハート", "ブレードハート"]:
                    values = {}
                    for span in dd.find_all("span", class_=True):
                        class_name = next(
                            (cls for cls in span["class"] if "heart" in cls), None
                        )
                        if class_name:
                            values[class_name] = span.get_text(strip=True)
                    card_data[key] = values
                else:
                    # If there's an <img>, replace it with its alt text
                    content = []
                    for item in dd.contents:
                        if item.name == "img":
                            content.append(item["alt"])  # Use alt text of the image
                        elif isinstance(item, str):
                            content.append(item.strip())  # Extract normal text

                    # Store as a string if it's a single value, otherwise as a list
                    filtered_content = list(
                        filter(None, content)
                    )  # Remove empty values
                    card_data[key] = (
                        filtered_content
                        if len(filtered_content) > 1
                        else filtered_content[0]
                    )

    # Extract info-Text
    info_text_tag = soup.select_one(".info-Text")
    if info_text_tag:
        card_data["info_text"] = parse_info_text(info_text_tag)

    return card_data


def scrape_all_cards(expansion="NSD01"):
    """Main function to fetch all cards and their details."""
    all_cards = get_card_list(expansion)

    for card in all_cards:
        print(f"Fetching details for {card['card_number']}...")
        details = get_card_details(card["card_number"])
        if details:
            card.update(details)

        time.sleep(1)  # Avoid spamming the server

    return all_cards


def get_expansion_codes():
    """Scrape the main card list page and extract expansion codes."""
    response = requests.get(f"{BASE_URL}cardlist/", headers=HEADERS)

    if response.status_code != 200:
        return []  # Return an empty list if request fails

    soup = BeautifulSoup(response.text, "html.parser")
    expansion_codes = []

    for item in soup.select(".productsSearch-Item a"):
        href = item.get("href", "")
        match = re.search(r"expansion=([\w\d-]+)", href)
        if match:
            expansion_codes.append(match.group(1))

    return expansion_codes


# # Run the scraper
# cards_data = scrape_all_cards()

# # Print or save the data
# for card in cards_data:
#     print(card)

# test = get_card_details("LL-bp1-001-R＋")
# print(test)

codes = get_expansion_codes()
cards = []

for code in codes:
    data = scrape_all_cards(code)
    cards.extend(data)

# Save the scraped data to a JSON file
output_file = "card_data.json"
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(cards, f, ensure_ascii=False, indent=4)

print(f"Data saved to {output_file}")
