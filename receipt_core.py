"""
Headless core logic for the TCG Receipt Generator.

Contains the thermal printer handling, photo capture/processing, and the
full receipt generation flow, with no GUI dependencies. Used by the
FastAPI web server (webapp.py).
"""

import threading
import time
from datetime import datetime
from typing import Dict, Any, Optional

import requests

from getRandomPerson import get_random_person, check_pocketbase_connection

# Try to import camera and printer modules (may not be available on all systems)
try:
    from picamera2 import Picamera2
    CAMERA_AVAILABLE = True
except ImportError as e:
    print(f"Camera module not available: {e}")
    CAMERA_AVAILABLE = False

try:
    from escpos.printer import Usb
    PRINTER_AVAILABLE = True
except ImportError as e:
    print(f"Printer module not available: {e}")
    PRINTER_AVAILABLE = False

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError as e:
    print(f"PIL not available: {e}")
    PIL_AVAILABLE = False

# --- Configuration ---
POCKETBASE_URL = "http://localhost:8090"
API_URL = f"{POCKETBASE_URL}/api"
RECEIPTS_COLLECTION = "receipts"

# Printer configuration
PRINTER_VENDOR_ID = 0x0fe6
PRINTER_PRODUCT_ID = 0x811e

DEFAULT_TEXT_WIDTH = 24
DEFAULT_IMAGE_WIDTH = 256

CAPTURE_FILENAME = "capture.jpg"

# Only one request may talk to the printer (and camera) at a time
hardware_lock = threading.Lock()

# Norwegian character mapping to single-byte codepage values
NORWEGIAN_CHAR_MAP = {
    'ø': '\xF8',
    'Ø': '\xD8',
    'å': '\xE5',
    'Å': '\xC5',
    'æ': '\xE6',
    'Æ': '\xC6',
}


def replace_norwegian_chars(text: str) -> str:
    """Replace Norwegian characters with their codepage byte representations."""
    for norwegian_char, byte_char in NORWEGIAN_CHAR_MAP.items():
        text = text.replace(norwegian_char, byte_char)
    return text


def setup_printer_encoding(printer) -> bool:
    """Configure printer for Norwegian/Danish characters."""
    for charcode in ('CP865', 'CP850', 'CP437'):
        try:
            printer.charcode(charcode)
            return True
        except Exception:
            continue
    print("Warning: Could not set printer encoding for special characters")
    return False


def open_printer():
    """Initialize and open the USB thermal printer."""
    printer = Usb(PRINTER_VENDOR_ID, PRINTER_PRODUCT_ID, 0,
                  profile="simple", in_ep=0x82, out_ep=0x03)
    printer.open()
    try:
        setup_printer_encoding(printer)
    except Exception as encoding_error:
        print(f"Encoding setup failed, using character replacement: {encoding_error}")
    return printer


def print_free_text(text: str) -> None:
    """Print arbitrary user-supplied text to the thermal printer."""
    if not PRINTER_AVAILABLE:
        print("Printer not available - simulating print output:")
        print("=" * 40)
        print(text)
        print("=" * 40)
        return

    with hardware_lock:
        try:
            printer = open_printer()
            printer.set(align='left', bold=False)
            printer.text(replace_norwegian_chars(text))
            printer.ln(3)
            printer.close()
            print("Text printed successfully!")
        except Exception as e:
            raise RuntimeError(f"Printer error: {e}")


def take_and_process_photo(image_width: int = DEFAULT_IMAGE_WIDTH,
                           warmup_seconds: float = 2.0):
    """
    Capture a photo with the Pi camera and process it for thermal printing.
    Returns a dithered PIL image, or None if the camera is unavailable.
    """
    if not CAMERA_AVAILABLE or not PIL_AVAILABLE:
        return None

    picam2 = None
    try:
        print("Initializing camera...")
        picam2 = Picamera2()
        config = picam2.create_still_configuration()
        picam2.configure(config)
        picam2.start()
        print("Camera started, waiting for auto-adjustment...")
        time.sleep(warmup_seconds)
        picam2.capture_file(CAPTURE_FILENAME)
        print(f"Picture saved as {CAPTURE_FILENAME}")
    finally:
        if picam2 is not None:
            try:
                picam2.stop()
                picam2.close()
            except Exception as e:
                print(f"Warning: Error during camera cleanup: {e}")

    print(f"Processing image for thermal look (width: {image_width})...")
    with Image.open(CAPTURE_FILENAME) as img:
        original_width, original_height = img.size
        aspect_ratio = original_height / float(original_width)
        new_height = int(image_width * aspect_ratio)
        resized_img = img.resize((image_width, new_height))
        grayscale_img = resized_img.convert('L')
        dithered_img = grayscale_img.convert('1', dither=Image.Dither.FLOYDSTEINBERG)
        print("Image processing complete.")
        return dithered_img


def print_receipt(person: Dict[str, Any], image: Optional[object] = None) -> None:
    """Print the TCG receipt to the thermal printer. Caller must hold hardware_lock."""
    if not PRINTER_AVAILABLE:
        print("Printer not available - simulating print output:")
        simulate_print_output(person, image)
        return

    try:
        printer = open_printer()

        # Header
        printer.set(align='center', bold=True, double_height=True, font='b')
        printer.text("IKT RECEIPT\n")
        printer.ln(1)

        # Person info
        printer.set(align='center', bold=True, double_height=False)
        printer.text(f"{replace_norwegian_chars(person.get('name', 'Unknown'))}\n")

        printer.set(align='center', bold=False)
        printer.text(f"Rarity: {replace_norwegian_chars(person.get('rarity', 'Unknown'))}\n")
        printer.ln(1)

        # Description
        description = person.get('description', 'No description available')
        printer.set(align='left', bold=False)
        printer.text(replace_norwegian_chars(description))
        printer.ln(1)

        # Date and time
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        printer.set(align='center', bold=False)
        printer.text(f"Generated: {current_time}\n")
        printer.ln(2)

        # Image
        if image and PIL_AVAILABLE:
            printer.set(align='center')
            printer.image(image)
            printer.ln(2)

        printer.ln(2)
        printer.close()
        print("Receipt printed successfully!")

    except Exception as e:
        raise RuntimeError(f"Printer error: {e}")


def simulate_print_output(person: Dict[str, Any], image: Optional[object] = None) -> None:
    """Simulate printer output for testing without an actual printer."""
    print("\n" + "=" * 40)
    print("SIMULATED THERMAL PRINTER OUTPUT")
    print("=" * 40)
    print("         TCG RECEIPT")
    print()
    print(f"      {person.get('name', 'Unknown')}")
    print(f"    Rarity: {person.get('rarity', 'Unknown')}")
    print()
    print(person.get('description', 'No description available'))
    print()
    print(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if image:
        print("    [IMAGE WOULD BE HERE]")
    print("=" * 40)


def create_receipt_record(person: Dict[str, Any]) -> Dict[str, Any]:
    """Create a receipt record in the PocketBase database."""
    receipt_data = {
        "person": person.get('id'),
        "reason": "other",
        "created": datetime.now().isoformat() + "Z",
    }
    try:
        response = requests.post(
            f"{API_URL}/collections/{RECEIPTS_COLLECTION}/records",
            json=receipt_data,
            headers={"Content-Type": "application/json"},
        )
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Network error while creating receipt record: {e}")

    if response.status_code == 200:
        print("Receipt record created successfully!")
        return response.json()
    raise RuntimeError(
        f"Failed to create receipt record: {response.status_code} - {response.text}")


def generate_receipt(testing: bool = False,
                     image_width: int = DEFAULT_IMAGE_WIDTH) -> Dict[str, Any]:
    """
    Run the full TCG receipt flow: pick a random person, take a photo,
    print the receipt, and (unless testing) save a record to the database.
    Returns a summary dict describing what happened.
    """
    if not check_pocketbase_connection():
        raise RuntimeError("Cannot connect to PocketBase. Make sure it's running.")

    person = get_random_person()
    if not person:
        raise RuntimeError("Could not retrieve a random person from database.")

    with hardware_lock:
        photo_taken = False
        processed_image = None
        if CAMERA_AVAILABLE:
            try:
                processed_image = take_and_process_photo(image_width=image_width)
                photo_taken = processed_image is not None
            except Exception as e:
                print(f"Camera error: {e}")
        else:
            print("Camera not available on this system.")

        print_receipt(person, processed_image)

    if not testing:
        create_receipt_record(person)

    return {
        "name": person.get('name', 'Unknown'),
        "rarity": person.get('rarity', 'Unknown'),
        "photo_taken": photo_taken,
        "saved_to_database": not testing,
    }
