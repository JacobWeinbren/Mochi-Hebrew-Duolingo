import csv
import os
import genanki
import random

# Load the CSS file
with open("minimal.css", "r") as css_file:
    CSS = css_file.read()

HEBREW_MODEL = genanki.Model(
    random.randrange(1 << 30, 1 << 31),
    "Hebrew Vocabulary",
    fields=[
        {"name": f}
        for f in [
            "Hebrew",
            "Niqqud",
            "Transliteration",
            "Translation",
            "Gender",
            "Number",
            "Form",
            "Type",
            "Audio",
            "Tags",
        ]
    ],
    templates=[
        {
            "name": "Hebrew to English",
            "qfmt": """
            <div class="prettify-flashcard" style="text-align: center;">
                <div class="prettify-field prettify-field--front">
                    <h1>{{Hebrew}}</h1>
                    <h2>{{Niqqud}}</h2>
                    <p>{{Transliteration}}</p>
                    {{Audio}}
                </div>
            </div>
            """,
            "afmt": """
            <div class="prettify-flashcard" style="text-align: center;">
                <div class="prettify-field prettify-field--front">
                    <h1>{{Hebrew}}</h1>
                    <h2>{{Niqqud}}</h2>
                    <p>{{Transliteration}}</p>
                    {{Audio}}
                </div>
                <hr class="prettify-divider prettify-divider--answer" id="answer" />
                <div class="prettify-field prettify-field--back">
                    <h1>{{Translation}}</h1>
                    {{#Gender}}<p><strong>Gender:</strong> {{Gender}}</p>{{/Gender}}
                    {{#Number}}<p><strong>Number:</strong> {{Number}}</p>{{/Number}}
                    {{#Form}}<p><strong>Form:</strong> {{Form}}</p>{{/Form}}
                    {{#Type}}<p><strong>Type:</strong> {{Type}}</p>{{/Type}}
                </div>
                {{#Tags}}
                <div class="prettify-tags">{{clickable:Tags}}</div>
                {{/Tags}}
            </div>
            """,
        },
        {
            "name": "English to Hebrew",
            "qfmt": """
            <div class="prettify-flashcard" style="text-align: center;">
                <div class="prettify-field prettify-field--front">
                    <h1>{{Translation}}</h1>
                </div>
            </div>
            """,
            "afmt": """
            <div class="prettify-flashcard" style="text-align: center;">
                <div class="prettify-field prettify-field--front">
                    <h1>{{Translation}}</h1>
                    {{#Gender}}<p><strong>Gender:</strong> {{Gender}}</p>{{/Gender}}
                    {{#Number}}<p><strong>Number:</strong> {{Number}}</p>{{/Number}}
                    {{#Form}}<p><strong>Form:</strong> {{Form}}</p>{{/Form}}
                    {{#Type}}<p><strong>Type:</strong> {{Type}}</p>{{/Type}}
                </div>
                <hr class="prettify-divider prettify-divider--answer" id="answer" />
                <div class="prettify-field prettify-field--back">
                    <h1>{{Hebrew}}</h1>
                    <h2>{{Niqqud}}</h2>
                    <p>{{Transliteration}}</p>
                    {{Audio}}
                </div>
                {{#Tags}}
                <div class="prettify-tags">{{clickable:Tags}}</div>
                {{/Tags}}
            </div>
            """,
        },
    ],
    css=CSS,
)


def create_deck(name):
    return genanki.Deck(random.randrange(1 << 30, 1 << 31), name)


def create_note(fields):
    return genanki.Note(
        model=HEBREW_MODEL,
        fields=[fields.get(f["name"], "") for f in HEBREW_MODEL.fields],
    )


def main():
    decks = {}
    media_files = []

    main_deck_name = "Hebrew Duolingo 2023 🇮🇱"
    main_deck = create_deck(main_deck_name)
    decks[main_deck_name] = main_deck

    # Create a dictionary to store skills and their corresponding rows
    skills = {}

    with open(
        "Duolingo Hebrew Vocab COMPLETE - Words.csv", "r", encoding="utf-8"
    ) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            skill_order = int(row["#"])
            skill = row["Skill"]
            skill_key = f"{skill_order:02d}. {skill}"

            if skill_key not in skills:
                skills[skill_key] = []
            skills[skill_key].append(row)

    # Process skills in order
    for skill_key in sorted(skills.keys()):
        deck_name = f"{main_deck_name}::Skills::{skill_key}"
        decks[deck_name] = create_deck(deck_name)

        for row in skills[skill_key]:
            fields = {f["name"]: row.get(f["name"], "") for f in HEBREW_MODEL.fields}
            fields["Tags"] = skill_key  # Add the skill as a tag
            audio_file = f"audio/{row['Niqqud']}.mp3"
            if os.path.exists(audio_file):
                fields["Audio"] = f'[sound:{row["Niqqud"]}.mp3]'
                media_files.append(audio_file)

            note = create_note(fields)
            decks[deck_name].add_note(note)
            main_deck.add_note(note)  # Add the note to the main deck as well

    package = genanki.Package(list(decks.values()))
    package.media_files = media_files
    package.write_to_file("Hebrew_Vocabulary.apkg")
    print("Anki deck creation process completed!")


if __name__ == "__main__":
    main()
