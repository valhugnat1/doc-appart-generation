from rembg import remove
from PIL import Image

def smart_remove_background(input_path, output_path):
    input_image = Image.open(input_path)
    
    # The 'remove' function uses AI to detect the object
    output_image = remove(input_image)
    
    output_image.save(output_path)
    print(f"Success! Saved to {output_path}")

if __name__ == "__main__":
    smart_remove_background("logo.png", "logo_clean.png")