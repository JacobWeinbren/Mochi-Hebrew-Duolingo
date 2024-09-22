import csv
import requests
from requests.auth import HTTPBasicAuth
import os
import sys
import uuid
import os
from dotenv import load_dotenv
import time

# Load environment variables from .env file
load_dotenv()

# Get API key from environment variable
API_KEY = os.getenv("MOCHI_API_KEY")
BASE_URL = "https://app.mochi.cards/api"
HEADERS = {
    "Accept": "application/json",
    "Authorization": f"Basic {API_KEY}",
}

HEBREW_TEMPLATE_ID = "B2rpVqXM"  # The ID of the Hebrew template


def make_api_request(url, method="POST", data=None, files=None):
    try:
        auth = HTTPBasicAuth(API_KEY, "")
        headers = HEADERS.copy()
        if files is None:
            headers["Content-Type"] = "application/json"
            response = requests.request(
                method, url, json=data, auth=auth, headers=headers
            )
        else:
            response = requests.request(
                method, url, data=data, files=files, auth=auth, headers=headers
            )
        response.raise_for_status()
        return response.json() if response.text else {"status": "success"}
    except requests.exceptions.RequestException as e:
        print(f"Error making API request: {e}")
        if hasattr(e, "response"):
            print(f"Response status code: {e.response.status_code}")
            print(f"Response content: {e.response.text}")
        return None


def create_deck(name, parent_id=None, sort=0):
    data = {"name": name, "parent-id": parent_id, "sort": sort}
    response = make_api_request(f"{BASE_URL}/decks/", data=data)
    return response.get("id") if response else None


def upload_audio(card_id, audio_file_path):
    file_name = f"{uuid.uuid4().hex[:16]}{os.path.splitext(audio_file_path)[1]}"
    url = f"{BASE_URL}/cards/{card_id}/attachments/{file_name}"
    with open(audio_file_path, "rb") as audio_file:
        files = {"file": (file_name, audio_file, "audio/mpeg")}
        response = make_api_request(url, method="POST", files=files)
    return file_name if response and response.get("status") == "success" else None


def get_subdecks(parent_deck_id):
    subdecks = []
    url = f"{BASE_URL}/decks?parent-id={parent_deck_id}&limit=100"
    previous_bookmark = None

    while True:
        response = make_api_request(url, method="GET")
        if not response:
            break

        new_subdecks = response.get("docs", [])
        subdecks.extend(new_subdecks)

        print(f"Retrieved {len(new_subdecks)} subdecks. Total: {len(subdecks)}")

        bookmark = response.get("bookmark")
        if not bookmark or bookmark == previous_bookmark:
            break
        previous_bookmark = bookmark
        url = (
            f"{BASE_URL}/decks?parent-id={parent_deck_id}&limit=100&bookmark={bookmark}"
        )

    return subdecks


def get_existing_cards(subdecks):
    existing_cards = set()

    for subdeck in subdecks:
        subdeck_id = subdecks[subdeck]
        skill = subdeck
        url = f"{BASE_URL}/cards?deck-id={subdeck_id}&limit=100"
        previous_bookmark = None

        while True:
            response = make_api_request(url, method="GET")
            if not response:
                break

            for card in response.get("docs", []):
                fields = card.get("fields", {})
                translation = fields.get("BHGrp74l", {}).get("value")
                gender = fields.get("OubS6rNu", {}).get("value")
                number = fields.get("x2CPIOeh", {}).get("value")
                form = fields.get("hQpDm4Xy", {}).get("value")
                card_type = fields.get("C0QicIIh", {}).get("value")
                if translation and skill:
                    existing_cards.add(
                        (translation, skill, gender, number, form, card_type)
                    )

            print(f"Total existing cards: {len(existing_cards)}")

            bookmark = response.get("bookmark")
            if not bookmark or bookmark == previous_bookmark:
                break
            previous_bookmark = bookmark
            url = f"{BASE_URL}/cards?deck-id={subdeck_id}&limit=100&bookmark={bookmark}"

    return existing_cards


def create_card(deck_id, fields):
    content = f"# {fields['SN2D3Qsv']['value']} ({fields['bqI7P9U8']['value']})\n\n{fields['AB9ZA1Qw']['value']}\n\n---\n\n{fields['BHGrp74l']['value']}\n\nGender: {fields['OubS6rNu']['value']}\nNumber: {fields['x2CPIOeh']['value']}\nForm: {fields['hQpDm4Xy']['value']}\nType: {fields['C0QicIIh']['value']}"

    if "E17KMyhO" in fields:
        content += f"\n\n{fields['E17KMyhO']['value']}"

    data = {
        "deck-id": deck_id,
        "template-id": HEBREW_TEMPLATE_ID,
        "content": content,
        "fields": fields,
    }
    response = make_api_request(f"{BASE_URL}/cards/", data=data)
    return response.get("id") if response else None


def main():
    if not make_api_request(f"{BASE_URL}/decks/", method="GET"):
        print(
            "Failed to connect to the API. Please check your API key and internet connection."
        )
        sys.exit(1)

    main_deck_id = "M6ZIEbBg"  # Use the existing Hebrew Vocabulary deck ID
    if not make_api_request(f"{BASE_URL}/decks/{main_deck_id}", method="GET"):
        main_deck_id = create_deck("Hebrew Vocabulary")
        if not main_deck_id:
            print("Failed to create main deck. Exiting.")
            sys.exit(1)

    skills_deck_id = "bXzXrtLx"
    if not skills_deck_id:
        skills_deck_id = create_deck("Skills", main_deck_id)
        print("Failed to create Skills deck. Exiting.")
        sys.exit(1)

    # Fetch existing skill decks
    existing_subdecks = get_subdecks(skills_deck_id)
    skill_decks = {}
    for deck in existing_subdecks:
        deck_name_parts = deck["name"].split(". ", 1)
        if len(deck_name_parts) == 2 and deck_name_parts[1] != "Notes":
            skill_decks[deck_name_parts[1]] = deck["id"]

    print(f"Found {len(skill_decks)} existing skill decks")
    print(skill_decks)

    existing_cards = get_existing_cards(skill_decks)
    print(f"Found {len(existing_cards)} existing cards")

    with open(
        "Duolingo Hebrew Vocab COMPLETE - Words.csv", "r", encoding="utf-8"
    ) as csvfile:
        reader = csv.DictReader(csvfile)
        previous_skill_number = None
        for index, row in enumerate(reader):
            skill = row["Skill"]
            translation = row["Translation"]
            gender = row.get("Gender", "N/A")
            number = row.get("Number", "N/A")
            form = row.get("Form", "N/A")
            card_type = row.get("Type", "N/A")
            if (translation, skill, gender, number, form, card_type) in existing_cards:
                continue

            if skill not in skill_decks:
                try:
                    skill_number = int(row["#"])
                    previous_skill_number = skill_number
                except ValueError:
                    if previous_skill_number is None:
                        print(f"Invalid skill number for skill: {skill}. Skipping.")
                        continue
                    skill_number = previous_skill_number
                    print(
                        f"Using previous skill number {skill_number} for skill: {skill}"
                    )

                # Create a new deck for each skill if it doesn't exist
                deck_name = f"{skill_number}. {skill}"
                if deck_name not in skill_decks:
                    skill_deck_id = create_deck(
                        deck_name, skills_deck_id, sort=skill_number
                    )
                    if skill_deck_id:
                        skill_decks[skill] = skill_deck_id
                    else:
                        print(f"Failed to create skill deck: {skill}. Skipping.")
                        continue

            fields = {
                "SN2D3Qsv": {"id": "SN2D3Qsv", "value": row["Hebrew"]},
                "bqI7P9U8": {"id": "bqI7P9U8", "value": row["Niqqud"]},
                "AB9ZA1Qw": {"id": "AB9ZA1Qw", "value": row["Transliteration"]},
                "BHGrp74l": {"id": "BHGrp74l", "value": row["Translation"]},
                "OubS6rNu": {"id": "OubS6rNu", "value": row.get("Gender", "N/A")},
                "x2CPIOeh": {"id": "x2CPIOeh", "value": row.get("Number", "N/A")},
                "hQpDm4Xy": {"id": "hQpDm4Xy", "value": row.get("Form", "N/A")},
                "C0QicIIh": {"id": "C0QicIIh", "value": row.get("Type", "N/A")},
            }

            card_id = create_card(skill_decks[skill], fields)
            if card_id:
                print(
                    f"{time.strftime('%Y-%m-%d %H:%M:%S')} - Card created: {row['Hebrew']} {row['Niqqud']} (ID: {card_id})"
                )

                audio_file = f"audio/{row['Niqqud']}.mp3"
                if os.path.exists(audio_file):
                    new_file_name = upload_audio(card_id, audio_file)
                    if new_file_name:
                        fields["E17KMyhO"] = {
                            "id": "E17KMyhO",
                            "value": f"![audio](@media/{new_file_name})",
                        }
                        updated_card = make_api_request(
                            f"{BASE_URL}/cards/{card_id}",
                            method="POST",
                            data={"fields": fields},
                        )
                        if updated_card:
                            print(
                                f"{time.strftime('%Y-%m-%d %H:%M:%S')} - Card updated with audio: {row['Hebrew']} {row['Niqqud']} (ID: {card_id})"
                            )
                        else:
                            print(
                                f"{time.strftime('%Y-%m-%d %H:%M:%S')} - Failed to update card with audio: {row['Hebrew']} {row['Niqqud']}"
                            )
                    else:
                        print(
                            f"{time.strftime('%Y-%m-%d %H:%M:%S')} - Failed to upload audio for: {row['Hebrew']} {row['Niqqud']}"
                        )
                else:
                    print(
                        f"{time.strftime('%Y-%m-%d %H:%M:%S')} - Warning: Audio file not found for {row['Niqqud']}"
                    )
            else:
                print(
                    f"{time.strftime('%Y-%m-%d %H:%M:%S')} - Failed to create card: {row['Hebrew']} {row['Niqqud']}"
                )

    print(
        f"{time.strftime('%Y-%m-%d %H:%M:%S')} - Mochi cards creation process completed!"
    )


if __name__ == "__main__":
    main()
