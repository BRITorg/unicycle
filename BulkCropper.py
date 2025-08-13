import os
import csv
from PIL import Image
from tqdm import tqdm
import warnings
from io import BytesIO

# Suppress DecompressionBombWarning
warnings.filterwarnings("ignore", category=Image.DecompressionBombWarning)

# Function to get folder path by prompting user
def get_folder_path():
    folder_path = input("Enter the path to the folder containing images: ").strip()
    while not os.path.isdir(folder_path):
        print(f"Error: {folder_path} is not a valid directory.")
        folder_path = input("Please enter a valid folder path: ").strip()
    return folder_path

# Function to read cropping parameters from a CSV file
def read_cropping_parameters(csv_file):
    cropping_params = {}
    with open(csv_file, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            dimensions = tuple(map(int, row['dimensions'].split('x')))
            cropping_params[dimensions] = {
                'top': float(row['top']),
                'bottom': float(row['bottom']),
                'left': float(row['left']),
                'right': float(row['right']),
            }
    return cropping_params

# Function to check if all image dimensions are listed in the CSV file
def check_dimensions_in_csv(folder_path, cropping_params):
    dimension_counts = {}
    image_files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff'))]

    for filename in tqdm(image_files, desc="Checking image dimensions"):
        image_path = os.path.join(folder_path, filename)
        with Image.open(image_path) as img:
            dimensions = img.size
            if dimensions not in dimension_counts:
                dimension_counts[dimensions] = {'count': 0, 'in_csv': dimensions in cropping_params}
            dimension_counts[dimensions]['count'] += 1
    return dimension_counts

# Resize image iteratively to stay under 10MB
def resize_to_fit_limit(img, target_bytes=10 * 1024 * 1024, step=0.9, min_scale=0.3, min_quality=70):
    scale = 1.0
    quality = 95

    while scale >= min_scale:
        buffer = BytesIO()
        new_size = (int(img.width * scale), int(img.height * scale))
        resized = img.resize(new_size, Image.LANCZOS)

        # Save with current quality to buffer
        resized.convert('RGB').save(buffer, format='JPEG', quality=quality)
        size = buffer.tell()

        if size <= target_bytes:
            return resized

        # Reduce scale and quality progressively
        scale *= step
        quality = max(min_quality, int(quality * 0.95))

    # Last resort: return smallest version even if still oversized
    return resized


# Function to crop and resize images based on parameters
def crop_images(folder_path, cropping_params):
    parent_dir = os.path.dirname(folder_path)
    output_folder = folder_path + "-cropped"
    os.makedirs(output_folder, exist_ok=True)

    image_files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff'))]

    for filename in tqdm(image_files, desc="Cropping images"):
        image_path = os.path.join(folder_path, filename)
        with Image.open(image_path) as img:
            dimensions = img.size

            if dimensions in cropping_params:
                params = cropping_params[dimensions]
                crop_box = (
                    int(dimensions[0] * params['left']),
                    int(dimensions[1] * params['top']),
                    int(dimensions[0] * (1 - params['right'])),
                    int(dimensions[1] * (1 - params['bottom']))
                )
                cropped_img = img.crop(crop_box)

                original_size = os.path.getsize(image_path)
                if original_size > 10 * 1024 * 1024:
                    cropped_img = resize_to_fit_limit(cropped_img)

                output_path = os.path.join(output_folder, os.path.splitext(filename)[0] + ".jpg")
                cropped_img.convert('RGB').save(output_path, format='JPEG', quality=95)

    print(f"Processing completed. Cropped images saved in: {output_folder}")

# Main script
if __name__ == "__main__":
    # Get folder path by prompting user
    folder_path = get_folder_path()

    # Locate the CSV file containing cropping parameters
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_file = os.path.join(script_dir, "crop_parameters.csv")

    if not os.path.exists(csv_file):
        print(f"CSV file not found: {csv_file}. Exiting.")
        exit()

    # Read cropping parameters
    cropping_params = read_cropping_parameters(csv_file)

    # Prompt user to run precheck or skip it
    run_precheck = input("Image dimensions precheck? This takes about a minute per 1000 images. (Y/N): ").strip().upper()
    if run_precheck == 'Y':
        # Check if all dimensions are listed in the CSV
        dimension_counts = check_dimensions_in_csv(folder_path, cropping_params)
        print("\nImage dimensions found in the folder:")
        for dim, info in dimension_counts.items():
            status = "In CSV" if info['in_csv'] else "<<<Not in CSV>>>"
            print(f"Dimensions: {dim}, Count: {info['count']}, Status: {status}")

        # Prompt user to continue or cancel
        proceed = input("\nDo you want to proceed with cropping? (Y/N): ").strip().upper()
        if proceed != 'Y':
            print("Operation canceled by the user.")
            exit()

    # Crop images
    crop_images(folder_path, cropping_params)
