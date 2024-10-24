from PIL import Image
from pathlib import Path

def resize_image_aspect_ratio(input_path, output_path, base_size, maintain_width=True):
    """Resize the image while maintaining the aspect ratio."""
    # Open the image file
    img = Image.open(input_path)
    
    # Get the original dimensions
    original_width, original_height = img.size
    
    # Calculate new dimensions based on maintaining either width or height
    if maintain_width:
        # Resize based on width
        new_width = base_size
        new_height = int((new_width / original_width) * original_height)
    else:
        # Resize based on height
        new_height = base_size
        new_width = int((new_height / original_height) * original_width)
    
    # Resize the image while maintaining the aspect ratio
    resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # Save the resized image
    resized_img.save(output_path)
    print(f"Image saved to {output_path} with size {new_width}x{new_height}")

def main():
    # Input parameters
    input_image = input("Enter the path to the image: ")
    output_image = input("Enter the path for the resized image (e.g., resized_image.jpg): ")
    base_size = int(input("Enter the base size (width or height): "))
    maintain_width = input("Resize based on width? (yes/no): ").strip().lower() == 'yes'

    # Ensure the input path exists
    input_path = Path(input_image)
    if not input_path.exists():
        print(f"Error: The file {input_image} does not exist.")
        return

    # Call the function to resize the image while maintaining the aspect ratio
    resize_image_aspect_ratio(input_image, output_image, base_size, maintain_width)

if __name__ == "__main__":
    main()
