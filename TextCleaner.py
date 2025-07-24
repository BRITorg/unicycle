import os
import csv
import re

def process_files(input_folder):
    # Create the filtered folder in the same directory as the input folder
    parent_directory = os.path.dirname(input_folder)
    filtered_folder = os.path.join(parent_directory, os.path.basename(input_folder) + "-filtered")
    os.makedirs(filtered_folder, exist_ok=True)

    # Locate the replace.csv file in the script's directory
    script_directory = os.path.dirname(os.path.abspath(__file__))
    csv_file = os.path.join(script_directory, "replace.csv")

    if not os.path.isfile(csv_file):
        print(f"Error: 'replace.csv' not found in the script's directory: {script_directory}")
        return

    # Load find-and-replace pairs from the CSV file
    replacements = []
    with open(csv_file, 'r', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            if len(row) >= 2:
                replacements.append((row[0], row[1]))

    # Set of lines to be removed if they are the only text on the line
    unwanted_lines = {
        "Botanical Research Institute of Texas",
        "Botanical Research",
        "Institute of Texas",
        "BRIT",
        "BRIT,",
        "BOTANICAL RESEARCH",
        "INSTITUTE",
        "DALLAS TEXAS",
        "DALLAS, TEXAS",
        "HERBARIUM",
        "Southern Methodist University",
        "HERBARIUM OF SOUTHERN METHODIST UNIVERSITY",
        "PLANTS OF OKLAHOMA",
        "HERBARIUM OF SOUTHERN METHODIST UNIVERSITY",
        "ANNOTATION LABEL",
        "annotation LABEL",
        "PLANTS ",
        "PLANTS"

    }

    # Regex for date-only lines: DD MMM YYYY, year > 2014
    date_pattern = re.compile(r"\s*\d{2} [A-Z]{3} 20(1[5-9]|[2-9]\d)\s*")

    # Loop through all files in the input folder
    for file_name in os.listdir(input_folder):
        file_path = os.path.join(input_folder, file_name)

        if os.path.isfile(file_path) and file_name.endswith(".txt"):
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    file_content = file.read()
            except UnicodeDecodeError:
                try:
                    with open(file_path, 'r', encoding='latin-1') as file:
                        file_content = file.read()
                except Exception as e:
                    print(f"Error reading file {file_name}: {e}")
                    continue

            # Apply all find-and-replace operations
            for find_text, replace_text in replacements:
                file_content = file_content.replace(find_text, replace_text)

            # Extract the base filename without extension (e.g., "BRIT00869")
            base_name = os.path.splitext(file_name)[0]

            # Extract the numeric portion from the base name (e.g., "00869")
            numeric_part = ''.join(re.findall(r'\d+', base_name))

            # Remove exact matches of base_name and numeric_part
            if base_name:
                file_content = file_content.replace(base_name, "")
            if numeric_part:
                file_content = file_content.replace(numeric_part, "")


            # Clean and filter lines
            cleaned_lines = []
            for line in file_content.splitlines():
                stripped = line.strip()
                if not stripped:
                    continue  # Skip blank lines
                if stripped in unwanted_lines:
                    continue  # Skip known unwanted lines
                if date_pattern.fullmatch(stripped):
                    continue  # Skip date lines
                cleaned_lines.append(line)

            file_content = '\n'.join(cleaned_lines)

            # Save the filtered content
            filtered_file_path = os.path.join(filtered_folder, file_name)
            with open(filtered_file_path, 'w', encoding='utf-8') as filtered_file:
                filtered_file.write(file_content)

    print(f"Processed files are saved in the folder: {filtered_folder}")


# Example usage
if __name__ == "__main__":
    print("""
This script processes all .txt files in a specified folder. It performs the following actions:
  - Applies find-and-replace operations based on a replace.csv file in the script's directory.
  - Removes lines containing text like "BRIT" followed by numbers.
  - Removes blank lines and unnecessary whitespace.
  - Filters out lines with dates in the format DD MMM YYYY for years greater than 2014 (case-sensitive).
  - Removes lines containing only "Botanical Research Institute of Texas."

You can cancel the operation now by pressing Ctrl+C.
    """)
    proceed = input("Do you want to proceed? (yes/no): ").strip().lower()

    if proceed != "yes":
        print("Operation cancelled.")
    else:
        folder_path = input("Enter the folder path containing TXT files: ").strip()

        if os.path.isdir(folder_path):
            process_files(folder_path)
        else:
            print("The specified folder path does not exist. Please check and try again.")
