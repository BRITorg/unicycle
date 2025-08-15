import os
import csv
from PIL import Image
from PIL import ImageOps
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
TARGET_BYTES = 10 * 1024 * 1024

def predict_cropped_bytes(original_bytes, crop_box, orig_size):
    # Predict new bytes ~ proportional to pixel area (good enough for a one-pass decision)
    ox, oy = orig_size
    cx = max(1, crop_box[2] - crop_box[0])
    cy = max(1, crop_box[3] - crop_box[1])
    area_ratio = (cx * cy) / float(ox * oy)
    return int(original_bytes * area_ratio)

def one_pass_resize_jpeg(img, max_bytes=TARGET_BYTES, base_quality=90):
    """
    Try a single encode; if still over limit, downscale once based on bytes ratio.
    Optionally probe quality once more via a tiny binary search.
    """
    buf = BytesIO()
    img.convert("RGB").save(buf, format="JPEG", quality=base_quality, optimize=True, progressive=True)
    size = buf.tell()
    if size <= max_bytes:
        buf.seek(0)
        return buf  # good

    # Estimate scale factor from bytes ratio (sqrt on area)
    scale = (max_bytes / size) ** 0.5
    if scale < 0.98:  # only bother if meaningful downscale
        new_size = (max(1, int(img.width * scale)), max(1, int(img.height * scale)))
        img = ImageOps.contain(img, new_size)  # fast multi-step shrink

    # Try again at same quality
    buf = BytesIO()
    img.convert("RGB").save(buf, format="JPEG", quality=base_quality, optimize=True, progressive=True)
    size = buf.tell()
    if size <= max_bytes:
        buf.seek(0)
        return buf

    # Final small binary search on quality (2 more tries)
    lo, hi = 70, base_quality  # don’t go lower than 70 by your original rule
    for _ in range(2):
        mid = (lo + hi) // 2
        buf = BytesIO()
        img.convert("RGB").save(buf, format="JPEG", quality=mid, optimize=True, progressive=True)
        if buf.tell() <= max_bytes:
            hi = mid
        else:
            lo = mid + 1
    buf.seek(0)
    return buf

def crop_images(folder_path, cropping_params):
    output_folder = folder_path + "-cropped"
    os.makedirs(output_folder, exist_ok=True)
    image_files = [f for f in os.scandir(folder_path)
                   if f.is_file() and f.name.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff'))]

    for entry in tqdm(image_files, desc="Cropping images"):
        image_path = entry.path
        with Image.open(image_path) as img:
            dimensions = img.size
            params = cropping_params.get(dimensions)
            if not params:
                continue

            crop_box = (
                int(dimensions[0] * params['left']),
                int(dimensions[1] * params['top']),
                int(dimensions[0] * (1 - params['right'])),
                int(dimensions[1] * (1 - params['bottom']))
            )
            cropped = img.crop(crop_box)

            original_bytes = entry.stat().st_size
            # If predicted cropped bytes already < 10MB, save once
            if predict_cropped_bytes(original_bytes, crop_box, dimensions) <= TARGET_BYTES:
                out = BytesIO()
                cropped.convert("RGB").save(out, format="JPEG", quality=90, optimize=True, progressive=True)
            else:
                out = one_pass_resize_jpeg(cropped, TARGET_BYTES, base_quality=90)

            output_path = os.path.join(output_folder, os.path.splitext(entry.name)[0] + ".jpg")
            with open(output_path, "wb") as f:
                f.write(out.getbuffer())

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
    run_precheck = input("Image dimensions precheck? (Y/N): ").strip().upper()
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
