import json
from pathlib import Path
import glob
import boto3
import aws_secrets

# Prompt the user for an input folder
input_path = input("Please enter the full path of the input folder: ").strip()

# Validate input path
input_directory = Path(input_path)
if not input_directory.is_dir():
    print("The specified path is not a valid directory.")
    exit()

# Define output directory
output_name = input_directory.stem.replace("-cropped", "") + "-Textract"
output_directory = input_directory.parent / output_name
output_directory.mkdir(exist_ok=True)

images = glob.glob(str(input_directory / '*.jpg'))

if not images:
    print("No .jpg images found in the specified directory.")
    exit()

# Amazon Textract client
textract = boto3.client('textract',
                        region_name='us-west-2',
                        aws_access_key_id=aws_secrets.aws_access_key_id,
                        aws_secret_access_key=aws_secrets.aws_secret_access_key)

# Prompt user once for overwrite behavior
overwrite_decision = input("Overwrite existing files? (y = overwrite / n = skip): ").strip().lower()
overwrite = overwrite_decision == 'y'

for image in images:
    image_path = Path(image)
    key = image_path.stem

    json_output_path = output_directory / f'{key}.json'
    text_output_path = output_directory / f'{key}.txt'

    if not overwrite and json_output_path.exists() and text_output_path.exists():
        print(f"Skipping {image_path.name} (already processed)")
        continue

    print(f"Processing: {image_path.name}")

    try:
        # Read document content
        with open(image, 'rb') as document:
            imageBytes = document.read()

        # Call Amazon Textract
        response = textract.detect_document_text(Document={'Bytes': imageBytes})

        # Save JSON response
        with open(json_output_path, 'w') as json_file:
            json.dump(response, json_file)

        # Save raw text results
        with open(text_output_path, 'w', encoding='utf-8') as txt_file:
            for item in response["Blocks"]:
                if item["BlockType"] == "LINE":
                    print(item['Text'])
                    txt_file.write(item['Text'] + '\n')

    except Exception as e:
        print(f"Skipping {image_path.name} due to error: {e}")