import cv2
import numpy as np

def draw_annotations(image_path):
    # Load the image
    image = cv2.imread(image_path)

    if image is None:
        print(f"Error: Unable to load image {image_path}")
        return

    # Get image dimensions
    height, width, _ = image.shape

    # Set a scaling factor based on the image dimensions (adjust as needed)
    scale_factor = min(width, height) / 500  # You can adjust this value for desired scaling

    # Calculate positions for vertical lines and labels
    line_positions = [int(width * (i / 10)) for i in range(1, 10)]
    vertical_labels = [f'{i * 10}%' for i in range(1, 10)]

    # Draw vertical blue lines and labels
    for x, label in zip(line_positions, vertical_labels):
        cv2.line(image, (x, 0), (x, height), (255, 0, 0), int(2 * scale_factor))  # Scaled line thickness
        cv2.putText(image, label, (x + int(5 * scale_factor), int(20 * scale_factor)), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5 * scale_factor, (255, 0, 0), int(2 * scale_factor))  # Scaled text size

    # Calculate positions for horizontal lines and labels
    horizontal_positions = [int(height * (i / 10)) for i in range(1, 10)]
    horizontal_labels = [f'{i * 10}%' for i in range(1, 10)]

    # Draw horizontal red lines and labels
    for y, label in zip(horizontal_positions, horizontal_labels):
        cv2.line(image, (0, y), (width, y), (0, 0, 255), int(2 * scale_factor))  # Scaled line thickness
        cv2.putText(image, label, (int(10 * scale_factor), y - int(5 * scale_factor)), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5 * scale_factor, (0, 0, 255), int(2 * scale_factor))  # Scaled text size

    # Save annotated image with annotations
    annotated_image_path = image_path.replace('.jpg', '_annotated.jpg')  # Adjust as needed for other image formats
    cv2.imwrite(annotated_image_path, image)
    print(f"Annotated image saved as {annotated_image_path}")

# Prompt user for image path
image_path = input("Enter the path to your image file: ")
draw_annotations(image_path)
