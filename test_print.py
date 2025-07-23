from escpos.printer import Usb

# --- Configuration ---
PRINTER_VENDOR_ID = 0x0fe6
PRINTER_PRODUCT_ID = 0x811e

def test_print():
    """Initializes the printer with a specific output endpoint."""
    try:
        # THE KEY CHANGE IS HERE: we add out_ep=0x02
        p = Usb(PRINTER_VENDOR_ID, PRINTER_PRODUCT_ID, out_ep=0x03)

        p.set(align='center', bold=True)
        p.text("Hello Again!\n")
        
        p.set(align='left', bold=False)
        p.text("This should work now...\n\n")
        p.ln(5)

        #p.cut()
        
        print("Test message sent to printer successfully!")

    except Exception as e:
        print(f"An error occurred: {e}")

# --- Run the test print ---
if __name__ == "__main__":
    test_print()