import os
import csv
import urllib.request
import logging
from datetime import datetime

# Configure logging to save in the selected output directory
def configure_logging(output_dir):
    timestamp = datetime.today().strftime('%Y_%m_%d')  # Generate timestamp in YYYY_MM_DD format
    log_file = os.path.join(output_dir, f'img-get_{timestamp}.log')  # Set log file path
    logging.basicConfig(
        filename=log_file,
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s',
        filemode='w'  # Overwrite log file each run (use 'a' to append instead)
    )

def download_images_from_csv(csv_file, output_dir, column_name, start_row=None, end_row=None):
    try:
        configure_logging(output_dir)  # Set up logging inside the selected output directory

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        file_count = 0
        dir_count = 1  # Start counting from dir_1

        while os.path.exists(os.path.join(output_dir, f'dir_{dir_count}')):
            current_dir = os.path.join(output_dir, f'dir_{dir_count}')
            file_count = len(os.listdir(current_dir))
            if file_count < 5000:
                break
            dir_count += 1  # Move to the next directory if the current one is full

        current_dir = os.path.join(output_dir, f'dir_{dir_count}')
        os.makedirs(current_dir, exist_ok=True)

        with open(csv_file, 'r') as file:
            reader = csv.DictReader(file)
            if column_name not in reader.fieldnames:
                raise ValueError(f"Column '{column_name}' not found in the CSV file.")

            rows = list(reader)
            if start_row is not None and end_row is not None:
                rows = rows[start_row-1:end_row]

            for row in rows:
                url = row[column_name].strip()
                if not url:
                    continue

                image_name = url.split('/')[-1]
                output_path = os.path.join(current_dir, image_name)

                logging.info(f'Downloading image from {url}')
                urllib.request.urlretrieve(url, output_path)
                logging.info(f'Image downloaded to {output_path}')

                file_count += 1
                if file_count >= 5000:
                    dir_count += 1
                    current_dir = os.path.join(output_dir, f'dir_{dir_count}')
                    os.makedirs(current_dir, exist_ok=True)
                    file_count = 0

    except Exception as e:
        logging.error(f'An error occurred: {e}')

if __name__ == "__main__":
    # Prompt for CSV file and output directory
    csv_file = input("Enter the path to the CSV file: ")

    # Report column names and allow the user to select from a numbered list
    try:
        with open(csv_file, 'r') as file:
            reader = csv.DictReader(file)
            fieldnames = reader.fieldnames
            if not fieldnames:
                raise ValueError("The CSV file does not contain any headers.")

            print("Available columns:")
            for idx, field in enumerate(fieldnames, start=1):
                print(f"{idx}: {field}")

            column_index = int(input("Enter the number corresponding to the column containing the image URLs: ")) - 1
            if column_index < 0 or column_index >= len(fieldnames):
                raise ValueError("Invalid column selection.")
            column_name = fieldnames[column_index]
    except Exception as e:
        print(f"Failed to read CSV file or select a column: {e}")
        exit(1)

    output_dir = input("Enter the path to the output directory: ")

    # Ensure logging is set up before proceeding
    configure_logging(output_dir)

    # Prompt user for download range
    print("Download options:")
    print("1: Download all records")
    print("2: Download a range of records")
    
    try:
        choice = int(input("Enter your choice (1 or 2): "))
        if choice == 1:
            start_row = None
            end_row = None
        elif choice == 2:
            start_row = int(input("Enter the starting row number: "))
            end_row = int(input("Enter the ending row number: "))
            if start_row <= 0 or end_row <= 0 or start_row > end_row:
                raise ValueError("Invalid range of rows.")
        else:
            raise ValueError("Invalid choice.")
    except Exception as e:
        print(f"Failed to parse input: {e}")
        exit(1)

    # Download images
    download_images_from_csv(csv_file, output_dir, column_name, start_row, end_row)
