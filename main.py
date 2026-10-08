import csv
import sys
import shutil
from pathlib import Path

sys.dont_write_bytecode = True

from thermoml_parser import parse_file

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)
CSV_PATH = OUTPUT_DIR / "thermoml_dataset_1_3.csv"


def find_json_files():
    return sorted(DATA_DIR.rglob("*.json"))


def collect_columns(files):
    columns = []
    seen = set()

    for number, file_path in enumerate(files, start=1):
        try:
            rows = parse_file(file_path)

            for row in rows:
                for column in row:
                    if column not in seen:
                        seen.add(column)
                        columns.append(column)

        except Exception as error:
            print(
                f"Ошибка в {file_path}: "
                f"{type(error).__name__}: {error}"
            )

        if number % 100 == 0:
            print(
                f"Первый проход: "
                f"{number}/{len(files)} файлов"
            )

    return columns


def write_csv(files, columns):
    total_rows = 0

    with open(
        CSV_PATH,
        "w",
        encoding="utf-8-sig",
        newline=""
    ) as csv_file:

        writer = csv.DictWriter(
            csv_file,
            fieldnames=columns,
            delimiter=";",
            extrasaction="ignore"
        )

        writer.writeheader()

        for number, file_path in enumerate(files, start=1):
            try:
                rows = parse_file(file_path)

                for row in rows:
                    writer.writerow(row)
                    total_rows += 1

                del rows

            except Exception as error:
                print(
                    f"Ошибка в {file_path}: "
                    f"{type(error).__name__}: {error}"
                )

            if number % 100 == 0:
                print(
                    f"Второй проход: "
                    f"{number}/{len(files)} файлов, "
                    f"{total_rows} строк"
                )

    return total_rows


def remove_pycache():
    for path in BASE_DIR.rglob("__pycache__"):
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)


def main():
    files = find_json_files()

    if not files:
        print("JSON-файлы не найдены.")
        print(DATA_DIR)
        return

    print("Найдено JSON-файлов:", len(files))

    columns = collect_columns(files)

    print("Найдено колонок:", len(columns))

    total_rows = write_csv(files, columns)

    print()
    print("Готово.")
    print("Строк:", total_rows)
    print("CSV:", CSV_PATH)

    remove_pycache()


if __name__ == "__main__":
    main()
