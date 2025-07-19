import pytest
import sys
import os
import requests

# Add the project root to the Python path to allow imports from the 'scrape' directory.
# This makes the test runnable from the 'tests' directory or the project root.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scrape.scrape import (
    _parse_expansion_codes,
    get_card_numbers_from_expansion,
    get_card_details,
    HEADERS,
    BASE_URL,
    SEARCH_URL,
    DETAIL_URL,
)

# --- Test Configuration ---

# This list should be kept up-to-date with the live site's expansion codes.
# Note: An integration test like this can be brittle if the website content changes frequently.
EXPECTED_CODES = ["PLSD01", "PBLS", "BP02", "PBSP", "BP01", "NSD01", "SPSD01", "PR"]


# --- Test Case ---


@pytest.mark.integration
def test_parse_expansion_codes_from_live_site():
    """
    Tests that _parse_expansion_codes correctly extracts all expansion codes
    from the live cardlist page.

    This is an integration test that makes a live network request.
    """
    cardlist_url = f"{BASE_URL}cardlist/"

    try:
        response = requests.get(cardlist_url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        html_content = response.text
    except requests.exceptions.RequestException as e:
        pytest.skip(
            f"Skipping integration test: Could not connect to live site at {cardlist_url}. Error: {e}"
        )

    actual_codes = _parse_expansion_codes(html_content)

    # Sorting the lists makes the test independent of the order of elements on the page
    assert sorted(actual_codes) == sorted(EXPECTED_CODES)


@pytest.mark.integration
def test_parse_expansion_codes_from_live_site_is_valid():
    """
    Tests that _parse_expansion_codes returns a valid, non-empty list of strings
    from the live cardlist page.

    This test is less brittle than checking for exact codes. It verifies the
    scraper's ability to parse the page structure correctly, even if the
    specific expansion codes change.
    """
    cardlist_url = f"{BASE_URL}cardlist/"

    try:
        response = requests.get(cardlist_url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        html_content = response.text
    except requests.exceptions.RequestException as e:
        pytest.skip(
            f"Skipping integration test: Could not connect to live site at {cardlist_url}. Error: {e}"
        )

    actual_codes = _parse_expansion_codes(html_content)

    # 1. Check if the result is a list
    assert isinstance(actual_codes, list), "The function should return a list."

    # 2. Check if the list is not empty (we expect at least one expansion)
    assert len(actual_codes) > 0, "The scraper should find at least one expansion code."

    # 3. Check if all items in the list are non-empty strings
    assert all(isinstance(code, str) and code for code in actual_codes), (
        "All items in the list should be non-empty strings."
    )


@pytest.mark.integration
def test_get_card_numbers_for_plsd01_from_live_site():
    """
    Tests that get_card_numbers_from_expansion correctly fetches and parses
    all card numbers for a specific expansion (PLSD01) from the live site.
    """
    expansion_code = "PLSD01"
    # This starter deck contains 18 member cards, 4 live cards, and 9 energy cards.
    expected_cards = (
        ["LL-E-001-SD"]
        + [f"PL!-sd1-{i:03d}-SD" for i in range(1, 23)]
        + [f"PL!-sd1-{i:03d}-P" for i in range(23, 32)]
    )

    try:
        # A simple HEAD request is enough to check connectivity without downloading content.
        requests.head(SEARCH_URL, headers=HEADERS, timeout=10).raise_for_status()
    except requests.exceptions.RequestException as e:
        pytest.skip(
            f"Skipping integration test: Could not connect to live site. Error: {e}"
        )

    actual_cards = get_card_numbers_from_expansion(expansion_code)

    assert len(actual_cards) > 0, (
        "Scraper returned an empty list of cards. The site structure may have changed or the expansion is empty."
    )

    # Sort both lists to ensure the comparison is order-independent.
    assert sorted(actual_cards) == sorted(expected_cards)


