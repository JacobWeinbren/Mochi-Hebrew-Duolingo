import csv


def find_invalid_integers(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            try:
                int(row["שבדית"])
            except ValueError:
                print(f"Invalid integer in row {reader.line_num}: {row['שבדית']}")


find_invalid_integers("Duolingo Hebrew Vocab COMPLETE - Words.csv")
