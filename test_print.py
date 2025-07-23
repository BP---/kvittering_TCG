from escpos.printer import Usb

# --- Configuration ---
# These are correct! Do not change them.
PRINTER_VENDOR_ID = 0x0fe6
PRINTER_PRODUCT_ID = 0x811e

def test_print():
    """Initializes the printer and prints a simple test message using the CORRECT syntax."""
    try:
        # This part is correct and should now work without a permissions error
        p = Usb(PRINTER_VENDOR_ID, PRINTER_PRODUCT_ID)

        # Let's print something!
        # This is the corrected section:
        p.set(align='center', bold=True)
        p.text("Hello World!\n")
        
        p.set(align='left', bold=False) # Turn off bold and set align to left
        p.text("The printer is connected!\n")
        p.text(f"Vendor: {PRINTER_VENDOR_ID:#06x}, Product: {PRINTER_PRODUCT_ID:#06x}\n\n")

        # You can also change text size
        p.set(align='center', bold=True, width=2, height=2)
        p.text("BIG TEXT\n")
        p.set() # Resets all text settings to default

        p.text("\n")
        p.cut() # Cut the paper
        
        print("Test message sent to printer successfully!")

    except Exception as e:
        # This part is just for catching any other potential errors
        print(f"An error occurred: {e}")

# --- Run the test print ---
if __name__ == "__main__":
    test_print()