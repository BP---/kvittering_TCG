from escpos.printer import Usb
from escpos.exceptions import DeviceNotFoundError

# --- IMPORTANT ---
# Replace these with your printer's vendor and product IDs.
# You can find them using 'lsusb' on Linux/macOS or Device Manager on Windows.
VENDOR_ID = 0x0fe6
PRODUCT_ID = 0x811e

try:
    # Initialize the printer
    p = Usb(VENDOR_ID, PRODUCT_ID, in_ep=0x82, out_ep=0x03)

    # --- Print a Title ---
    # Let's start with a nice, big, centered title.
    p.set(align='center', width=2, height=2)
    p.text("Font Size Demo\n\n")

    # --- Print Very Small Text (the default) ---
    # Resetting the printer state is good practice.
    # width=1 and height=1 is the smallest font.
    p.set(align='left', width=1, height=1)
    p.text("This is the smallest text (width=1, height=1).\n")
    p.text("The quick brown fox jumps over the lazy dog.\n\n")
    
    # --- Print a Bit Bigger Text ---
    # Set width and height to 2 to make characters twice as big.
    p.set(width=2, height=2)
    p.text("This is bigger text (width=2, height=2).\n\n")

    # --- Print an Even Bigger Text ---
    # You can use values up to 8.
    p.set(width=3, height=3)
    p.text("Even bigger!\n(3x3)\n")

    # Cut the paper
    #p.cut()

    # Close the connection to the printer
    p.close()

    print("Successfully printed the font size demo.")

except DeviceNotFoundError:
    print(f"Error: Printer not found. Please check your connection and ensure the Vendor ID (0x{VENDOR_ID:04x}) and Product ID (0x{PRODUCT_ID:04x}) are correct.")
except Exception as e:
    print(f"An error occurred: {e}")