import os
import json
import time
import chardet
from openai import OpenAI

# Load secrets from PolyParse_secrets.py
try:
    import PolyParse_secrets as secrets
except ImportError:
    print("\n[ERROR] Missing 'PolyParse_secrets.py'. Please create this file with the necessary API keys.")
    exit(1)

# Retrieve available API keys
gpt_model = "gpt-4o-mini"  # Default GPT model
print(f"\n[INFO] GPT Model: {gpt_model}")

api_keys = {key: value for key, value in vars(secrets).items() if key.startswith("OPENAI_API_KEY_")}

if not api_keys:
    print("\n[ERROR] No API keys found in PolyParse_secrets.py.")
    exit(1)

# If multiple API keys exist, prompt the user to select one
if len(api_keys) > 1:
    print("Available API keys:")
    for idx, (key, _) in enumerate(api_keys.items(), start=1):
        print(f"{idx}. {key}")
    choice = int(input("Enter the number of the API key you want to use: ")) - 1
    if 0 <= choice < len(api_keys):
        selected_key = list(api_keys.keys())[choice]
    else:
        print("Invalid choice. Please enter a valid number.")
        exit(1)
else:
    selected_key = list(api_keys.keys())[0]

api_key = api_keys[selected_key]

# Initialize OpenAI client with the selected API key
client = OpenAI(api_key=api_key)

print(f"\n[INFO] Using API key: {selected_key}")

def detect_encoding(file_path):
    """Detect the encoding of a file."""
    with open(file_path, 'rb') as f:
        raw_data = f.read(1024)  # Read a small portion of the file
    result = chardet.detect(raw_data)
    return result['encoding']

def process_file(input_file, output_file, system_role_file):
    encoding = detect_encoding(input_file)
    print(f"[INFO] Detected encoding for {input_file}: {encoding}")
    
    with open(input_file, "r", encoding=encoding) as file:
        input_text = file.read()

    with open(system_role_file, "r", encoding="utf-8") as file:
        system_role = file.read()

    try:
        completion = client.chat.completions.create(
            model=gpt_model,
            messages=[
                {"role": "system", "content": system_role},
                {"role": "user", "content": input_text}
            ],
            temperature=0.2,
            response_format={"type": "json_object"}
        )
    except Exception as e:
        print(f"API request failed: {e}")
        return

    print('prompt_tokens:', completion.usage.prompt_tokens)
    print('completion_tokens:', completion.usage.completion_tokens)
    
    response_text = completion.choices[0].message.content
    try:
        response_dict = json.loads(response_text)
        response_dict['prompt_tokens'] = completion.usage.prompt_tokens
        response_dict['completion_tokens'] = completion.usage.completion_tokens
        
        with open(output_file, "w", encoding="utf-8") as file:
            file.write(json.dumps(response_dict, indent=4))
    except Exception as e:
        print('Error', e)

def select_system_role_file(directory):
    """Prompt the user to choose the system role file from the directory."""
    files = [f for f in os.listdir(directory) if f.endswith('.txt')]
    print("Available prompts:")
    for idx, file in enumerate(files, start=1):
        print(f"{idx}. {file}")
    choice = int(input("Enter the number of the prompt you want to use: ")) - 1
    if 0 <= choice < len(files):
        return os.path.join(directory, files[choice])
    else:
        print("Invalid choice. Please enter a valid number.")
        return select_system_role_file(directory)

def main():
    script_dir = os.path.dirname(os.path.realpath(__file__))
    system_role_directory = os.path.join(script_dir, "Prompt Library")
    if not os.path.exists(system_role_directory):
        print(f"\n[ERROR] The 'Prompt Library' folder was not found in: {script_dir}")
        return

    print(f"\n[INFO] 'Prompt Library' found in: {system_role_directory}")
    system_role_file = select_system_role_file(system_role_directory)

    input_dir = input("Enter the path to the directory containing input text files: ").strip()
    parent_dir, input_folder_name = os.path.split(os.path.abspath(input_dir))
    
    # Remove suffixes
    for suffix in ["-Textract", "-Textract-filtered"]:
        if input_folder_name.endswith(suffix):
            input_folder_name = input_folder_name[: -len(suffix)]
    
    output_dir = os.path.join(parent_dir, f"{input_folder_name}-PolyParse")
    os.makedirs(output_dir, exist_ok=True)

    # Ask user whether to overwrite existing output files
    while True:
        overwrite_choice = input("Overwrite existing files? (y = overwrite / n = skip): ").strip().lower()
        if overwrite_choice in ['y', 'n']:
            break
        print("Please enter 'y' or 'n'.")

    input_files = [f for f in os.listdir(input_dir) if f.endswith(".txt")]
    total_files = len(input_files)

    start_time = time.time()
    for count, filename in enumerate(input_files, start=1):
        print(f'Parsing {count}/{total_files}: {filename}')
        
        input_file = os.path.join(input_dir, filename)
        output_file = os.path.join(output_dir, filename.replace(".txt", ".json"))

        # Skip if file exists and user chose not to overwrite
        if os.path.exists(output_file) and overwrite_choice == 'n':
            print(f"[SKIPPED] Output file already exists: {output_file}\n")
            continue
        
        process_file(input_file, output_file, system_role_file)
        
        elapsed_time = time.time() - start_time
        avg_time_per_file = elapsed_time / count
        remaining_files = total_files - count
        est_time_remaining = avg_time_per_file * remaining_files
        
        print(f"Processed {count}/{total_files} files. Estimated time remaining: {int(est_time_remaining // 60)} minutes {int(est_time_remaining % 60)} seconds.\n")

if __name__ == "__main__":
    main()
