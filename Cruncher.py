import os
import json
import csv
import logging
from pathlib import Path


def setup_logging(log_file):
    """Set up logging configuration."""
    logging.basicConfig(filename=log_file, level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')


def read_json_file(file_path):
    """Reads JSON data from a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        return data
    except Exception as e:
        logging.error(f"Error reading {file_path}: {e}")
        return None


def clean_data(data):
    """Removes newline characters from data fields."""
    return {key: (value.replace('\n', '') if isinstance(value, str) else value) for key, value in data.items()}


def write_to_csv(csv_file, data, fieldnames):
    """Writes data to a CSV file."""
    cleaned_data = clean_data(data)
    with open(csv_file, 'a', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writerow(cleaned_data)


def json_to_csv(input_dir, output_csv, log_file):
    """Converts JSON files in the input directory to a CSV file."""
    if not os.path.exists(input_dir):
        logging.error(f"Input directory {input_dir} does not exist.")
        return

    logging.info("Starting conversion...")
    fieldnames = None  # Define fieldnames outside the loop

    # Iterate over JSON files in the input directory
    for filename in os.listdir(input_dir):
        if filename.endswith('.json'):
            file_path = os.path.join(input_dir, filename)
            logging.info(f"Processing {file_path}...")

            json_data = read_json_file(file_path)
            if not json_data:
                continue

            # Add filename to json_data without the .json extension
            json_data['filename'] = os.path.splitext(filename)[0]

            if fieldnames is None:  # Initialize fieldnames on the first file
                fieldnames = list(json_data.keys())
                if not os.path.exists(output_csv):
                    # Create CSV file and write header
                    with open(output_csv, 'w', newline='', encoding='utf-8') as file:
                        writer = csv.DictWriter(file, fieldnames=fieldnames)
                        writer.writeheader()

            # Check for new fields and update fieldnames dynamically
            new_fields = set(json_data.keys()) - set(fieldnames)
            if new_fields:
                logging.info(f"New fields detected: {new_fields}")
                fieldnames.extend(new_fields)

                # Rewrite the CSV file with updated fieldnames
                with open(output_csv, 'r', newline='', encoding='utf-8') as file:
                    rows = list(csv.DictReader(file))

                with open(output_csv, 'w', newline='', encoding='utf-8') as file:
                    writer = csv.DictWriter(file, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(rows)

            # Write JSON data to CSV file
            write_to_csv(output_csv, json_data, fieldnames)
            logging.info(f"Data from {file_path} added to CSV.")

    logging.info("Conversion completed.")


def main():
    input_dir = input("Enter the path to the directory containing JSON files: ").strip()
    base_dir = Path(input_dir)

    if not base_dir.exists() or not base_dir.is_dir():
        print(f"Error: The directory '{input_dir}' does not exist.")
        return

    folder_name = base_dir.name
    output_csv = base_dir / f"{folder_name}.csv"
    log_file = base_dir / f"{folder_name}_log.txt"

    setup_logging(log_file)

    # Convert JSON files to CSV
    json_to_csv(input_dir, output_csv, log_file)

    logging.info("Conversion completed. Data has been saved in the input directory.")
    print(f"Conversion complete. Output saved to: {output_csv}")
    print(f"Log saved to: {log_file}")


if __name__ == "__main__":
    main()
