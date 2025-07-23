from escpos.printer import Usb

# --- Configuration ---
# These are the IDs 
PRINTER_VENDOR_ID = 0x0fe6
PRINTER_PRODUCT_ID = 0x811e

# --- The function to print ---
def test_print():
    """Initializes the printer and prints a simple test message."""
    try:
        # Initialize the USB printer object with your IDs
        p = Usb(PRINTER_VENDOR_ID, PRINTER_PRODUCT_ID)

        # Let's print something!
        p.set(align='center', text_type='B') # Set to bold and centered
        p.text("Hello World!\n")
        p.set(text_type='NORMAL')
        p.text("The printer is connected!\n")
        p.text("Vendor: 0x0fe6, Product: 0x811e\n\n")

        p.cut() # Cut the paper
        print("Test message sent to printer successfully!")

    except Exception as e:
        print(f"An error occurred: {e}")
        print("This might be a permissions issue. See notes on 'udev rules'.")

# --- Run the test print ---
if __name__ == "__main__":
    test_print()