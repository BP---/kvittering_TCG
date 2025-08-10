from escpos.printer import Usb

# --- Configuration ---
PRINTER_VENDOR_ID = 0x0fe6
PRINTER_PRODUCT_ID = 0x811e

def test_encoding_options():
    """Test different encoding options for Norwegian characters."""
    encodings_to_test = [
        ('CP865', 'Norwegian/Danish'),
        ('CP850', 'Western European'),  
        ('CP437', 'Original IBM PC'),
        ('ISO8859-1', 'Latin-1'),
        ('UTF-8', 'Unicode UTF-8')
    ]
    
    test_text = "Oksekjøtt - Løkpulver - Hvitløkspulver"
    
    try:
        p = Usb(PRINTER_VENDOR_ID, PRINTER_PRODUCT_ID, 0, profile="simple", in_ep=0x82, out_ep=0x03)
        p.open()
        
        p.set(align='center', bold=True)
        p.text("ENCODING TEST\n")
        p.text("=" * 32 + "\n")
        
        for encoding, description in encodings_to_test:
            try:
                p.set(align='left', bold=False)
                p.text(f"\n{encoding} ({description}):\n")
                
                if encoding in ['UTF-8']:
                    # For UTF-8, we might need to handle differently
                    p.text(test_text.encode('utf-8').decode('utf-8') + "\n")
                else:
                    # Set the codepage for the printer
                    if hasattr(p, 'charcode'):
                        p.charcode(encoding)
                    p.text(test_text + "\n")
                    
            except Exception as e:
                p.text(f"Error with {encoding}: {str(e)[:20]}...\n")
        
        p.text("\n" + "=" * 32 + "\n")
        p.text("End of encoding test\n")
        p.ln(3)
        
        p.close()
        print("Encoding test completed!")
        
    except Exception as e:
        print(f"Test failed: {e}")

def test_print():
    """Initializes the printer with a specific output endpoint."""
    try:
        # THE KEY CHANGE IS HERE: we add out_ep=0x02
        p = Usb(PRINTER_VENDOR_ID, PRINTER_PRODUCT_ID, 0, profile="simple", in_ep=0x82,  out_ep=0x03)
        print(p.is_usable())
        p.open()
        
        # Set encoding to handle Norwegian characters
        p.charcode('ISO8859-1')  # Norwegian/Danish codepage
        
        p.set(align='center', bold=True)
        p.text("BPs jerky\n")
        p.textln("----------")
        
        p.set(align='left', bold=False)
        p.ln(2)
        # Encode Norwegian characters properly
        p.text("Oksekjøtt\n")
        p.text("Worcestershire saus\n")
        p.text("Soya saus\n")
        p.text("Brunt sukker\n")
        p.text("Løkpulver\n")
        p.text("Hvitløkspulver\n")
        p.text("Paprikapulver\n")
        p.text("Gochugaru\n")
        p.text("Kajennepepper\n")
        p.ln(2)
        #p.cut()
        
        print("Test message sent to printer successfully!")
        p.close()

    except Exception as e:
        print(f"An error occurred: {e}")

# --- Run the test print ---
if __name__ == "__main__":
    print("Running encoding test...")
    #test_encoding_options()
    print("\nRunning regular print test...")
    test_print()