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

CARD_TESTS = {
    "PL!-sd1-022-SD": {
        "card_number": "PL!-sd1-022-SD",
        "img_url": "https://llofficial-cardgame.com/wordpress/wp-content/images/cardlist/PLSD01/PL!-pb1-022-SD.png",
        "name": "僕らは今のなかで",
        "set": "スタートデッキ ラブライブ！",
        "card_type": "ライブ",
        "group": ["ラブライブ！"],
        "score": "4",
        "required_hearts": {
            "heart01": "2",
            "heart03": "2",
            "heart06": "2",
            "heart0": "6",
        },
        "blade_hearts": {"b_heart03": "1"},
        "special_hearts": "ドロー",
        "rarity": "SD",
        "info_text": [
            "ライブ開始時 自分の成功ライブカード置き場にあるカード1枚につき、このカードを成功させるための必要ハートは heart0 heart0 少なくなる。"
        ],
    },
    "LL-bp2-001-R＋": {
        "card_number": "LL-bp2-001-R＋",
        "img_url": "https://llofficial-cardgame.com/wordpress/wp-content/images/cardlist/BP02/LL-bp2-001-R2.png",
        "name": "渡辺 曜&鬼塚夏美&大沢瑠璃乃",
        "set": "ブースターパック NEXT STEP",
        "card_type": "メンバー",
        "group": [
            "ラブライブ！サンシャイン!!",
            "ラブライブ！スーパースター!!",
            "蓮ノ空女学院スクールアイドルクラブ",
        ],
        "cost": "20",
        "hearts": {"heart01": "2", "heart03": "2", "heart04": "2"},
        "blades": "6",
        "rarity": "R+",
        "info_text": [
            "常時 手札にあるこのメンバーカードのコストは、このカード以外の自分の手札1枚につき、1少なくなる。",
            "常時 このメンバーはバトンタッチで控え室に置けない。",
            "ライブ開始時 手札の「渡辺 曜」と「鬼塚夏美」と「大沢瑠璃乃」を、好きな枚数控え室に置いてもよい：ライブ終了時まで、これによって控え室に置いた枚数1枚につき、 ブレード を得る。 （手札のこのカードもこの効果で控え室に置ける。）",
        ],
    },
    "LL-bp1-001-R＋": {
        "card_number": "LL-bp1-001-R＋",
        "img_url": "https://llofficial-cardgame.com/wordpress/wp-content/images/cardlist/BP01/LL-bp1-001-R2.png",
        "name": "上原歩夢&澁谷かのん&日野下花帆",
        "set": "ブースターパック vol.1",
        "card_type": "メンバー",
        "group": [
            "ラブライブ！虹ヶ咲学園スクールアイドル同好会",
            "ラブライブ！スーパースター!!",
            "蓮ノ空女学院スクールアイドルクラブ",
        ],
        "cost": "20",
        "hearts": {"heart01": "3", "heart04": "3", "heart06": "3"},
        "blades": "5",
        "rarity": "R+",
        "info_text": [
            "登場 自分の控え室からメンバーカードを1枚手札に加える。",
            "ライブ開始時 手札の「上原歩夢」と「澁谷かのん」と「日野下花帆」を、好きな組み合わせで合計3枚、控え室に置いてもよい：ライブ終了時まで、「 常時 ライブの合計スコアを＋３する。」を得る。 （手札のこのカードもこの効果で控え室に置ける。）",
        ],
    },
    "PL!SP-bp2-024-L": {
        "card_number": "PL!SP-bp2-024-L",
        "img_url": "https://llofficial-cardgame.com/wordpress/wp-content/images/cardlist/BP02/PL!SP-bp2-024-L.png",
        "name": "ビタミンSUMMER!",
        "set": "ブースターパック NEXT STEP",
        "card_type": "ライブ",
        "group": ["ラブライブ！スーパースター!!"],
        "score": "5",
        "required_hearts": {
            "heart02": "1",
            "heart03": "4",
            "heart06": "1",
            "heart0": "6",
        },
        "blade_hearts": {"b_heart03": "1"},
        "special_hearts": "ドロー",
        "rarity": "L",
        "info_text": [
            "ライブ成功時 自分の手札の枚数が相手より多い場合、このカードのスコアを＋１する。"
        ],
    },
    "PL!SP-pb1-024-L": {
        "card_number": "PL!SP-pb1-024-L",
        "img_url": "https://llofficial-cardgame.com/wordpress/wp-content/images/cardlist/PBSP/PL!SP-pb1_024-L.png",
        "name": "ニュートラル",
        "set": "プレミアムブースター ラブライブ！スーパースター!!",
        "card_type": "ライブ",
        "group": ["ラブライブ！スーパースター!!"],
        "unit": "KALEIDOSCORE",
        "score": "6",
        "required_hearts": {"heart06": "8", "heart0": "7"},
        "blade_hearts": {"b_heart06": "1"},
        "special_hearts": "ドロー",
        "rarity": "L",
        "info_text": [
            "ライブ開始時 自分のステージに名前の異なる『KALEIDOSCORE』のメンバーが2人以上いる場合、このカードのスコアを＋１する。"
        ],
    },
    "PL!SP-bp2-023-L": {
        "card_number": "PL!SP-bp2-023-L",
        "img_url": "https://llofficial-cardgame.com/wordpress/wp-content/images/cardlist/BP02/PL!SP-bp2-023-L.png",
        "name": "Go!! リスタート",
        "set": "ブースターパック NEXT STEP",
        "card_type": "ライブ",
        "group": ["ラブライブ！スーパースター!!"],
        "score": "1",
        "required_hearts": {
            "heart02": "1",
            "heart03": "1",
            "heart06": "1",
            "heart0": "1",
        },
        "special_hearts": "スコア",
        "rarity": "L",
        "info_text": [
            "ライブ開始時 自分の成功ライブカード置き場のカード枚数が相手より少ない場合、このカードのスコアを＋１する。"
        ],
    },
    "PL!SP-bp2-009-SEC": {
        "card_number": "PL!SP-bp2-009-SEC",
        "img_url": "https://llofficial-cardgame.com/wordpress/wp-content/images/cardlist/BP02/PL!SP-bp2-009-SEC.png",
        "name": "鬼塚夏美",
        "set": "ブースターパック NEXT STEP",
        "card_type": "メンバー",
        "group": ["ラブライブ！スーパースター!!"],
        "unit": "5yncri5e!",
        "cost": "13",
        "hearts": {"heart02": "1", "heart03": "3", "heart06": "2"},
        "blade_hearts": {"b_heart03": "1"},
        "blades": "1",
        "rarity": "SEC",
        "info_text": [
            "ライブ開始時 ライブ終了時まで、自分の手札2枚につき、 ブレード を得る。",
            "ライブ成功時 カードを2枚引き、手札を1枚控え室に置く。",
        ],
    },
    # Add more card tests as needed.
}


@pytest.mark.integration
def test_get_card_details_for_specific_card():
    """
    Tests that get_card_details correctly fetches and parses the details
    for a specific card (PL!-sd1-022-SD) from the live site.
    """
    card_number = "PL!-sd1-022-SD"

    # These are the expected details for this specific card.
    # This test will fail if the card details on the live site change.
    expected_details = {
        "card_number": "PL!-sd1-022-SD",
        "img_url": "https://llofficial-cardgame.com/wordpress/wp-content/images/cardlist/PLSD01/PL!-pb1-022-SD.png",
        "name": "僕らは今のなかで",
        "set": "スタートデッキ ラブライブ！",
        "card_type": "ライブ",
        "group": ["ラブライブ！"],
        "score": "4",
        "required_hearts": {
            "heart01": "2",
            "heart03": "2",
            "heart06": "2",
            "heart0": "6",
        },
        "blade_hearts": {"b_heart03": "1"},
        "special_hearts": "ドロー",
        "rarity": "SD",
        "info_text": [
            "ライブ開始時 自分の成功ライブカード置き場にあるカード1枚につき、このカードを成功させるための必要ハートは heart0 heart0 少なくなる。"
        ],
    }

    try:
        # A simple HEAD request is enough to check connectivity without downloading content.
        requests.head(DETAIL_URL, headers=HEADERS, timeout=10).raise_for_status()
    except requests.exceptions.RequestException as e:
        pytest.skip(
            f"Skipping integration test: Could not connect to live site. Error: {e}"
        )

    actual_details = get_card_details(card_number)

    assert actual_details is not None, (
        f"Scraper returned None for card {card_number}. The card may not exist or the site structure has changed."
    )
    assert actual_details == expected_details


@pytest.mark.integration
def test_get_card_details_for_multiple_cards():
    for card_number, expected_details in CARD_TESTS.items():
        try:
            # A simple HEAD request is enough to check connectivity without downloading content.
            requests.head(DETAIL_URL, headers=HEADERS, timeout=10).raise_for_status()
        except requests.exceptions.RequestException as e:
            pytest.skip(
                f"Skipping integration test: Could not connect to live site. Error: {e}"
            )

        actual_details = get_card_details(card_number)

        assert actual_details is not None, (
            f"Scraper returned None for card {card_number}. The card may not exist or the site structure has changed."
        )
        assert actual_details == expected_details
