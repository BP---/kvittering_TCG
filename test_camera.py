import time
from picamera2 import Picamera2
from PIL import Image

# --- Configuration ---
# The standard width for 58mm thermal printers is 384 pixels.
# We'll use this to simulate the final output size.
OUTPUT_IMAGE_WIDTH = 384

# The filename for the initial high-resolution capture.
CAPTURE_FILENAME = "capture.jpg"


def take_and_process_photo():
    """
    Captures an image, processes it for thermal printing,
    and returns the processed image object.
    """
    # 1. --- Initialize and capture with the camera ---
    print("Initializing camera...")
    picam2 = Picamera2()
    
    # Create a configuration for a still capture
    config = picam2.create_still_configuration()
    picam2.configure(config)
    
    picam2.start()
    # It's important to give the camera's sensor a moment to adjust
    # to light levels, auto-focus, etc.
    print("Taking picture in 2 seconds...")
    time.sleep(2)
    
    # Capture the image and save it to a file
    picam2.capture_file(CAPTURE_FILENAME)
    print(f"Picture saved as {CAPTURE_FILENAME}")
    picam2.stop()

    # 2. --- Process the image using Pillow ---
    print("Processing image for thermal look...")
    with Image.open(CAPTURE_FILENAME) as img:
        # Resize the image to the printer's width, maintaining aspect ratio
        original_width, original_height = img.size
        aspect_ratio = original_height / float(original_width)
        new_height = int(OUTPUT_IMAGE_WIDTH * aspect_ratio)
        resized_img = img.resize((OUTPUT_IMAGE_WIDTH, new_height))

        # Convert to grayscale ('L' mode in Pillow)
        grayscale_img = resized_img.convert('L')

        # DITHERING: This is the most important step!
        # It converts the grayscale image to pure black and white ('1' mode)
        # using a pattern of dots to simulate shades of gray. This looks
        # much better on a thermal printer than simple thresholding.
        # Floyd-Steinberg is a popular and effective dithering algorithm.
        dithered_img = grayscale_img.convert('1', dither=Image.Dither.FLOYDSTEINBERG)
        
        print("Image processing complete.")
        return dithered_img


# --- Main execution block ---
if __name__ == "__main__":
    # Run the main function
    processed_image = take_and_process_photo()

    # 3. --- Display the final image ---
    if processed_image:
        print("Displaying processed image for 5 seconds...")
        
        # .show() opens the image in the default image viewer on your Pi's desktop
        processed_image.show()
        
        # Wait for 5 seconds while the image viewer is open
        time.sleep(5)
        
        print("Script finished.")
        # The script will end here, and the image viewer will likely close
        # or you can close it manually.