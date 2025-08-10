from escpos.printer import Usb
import re

# --- Configuration ---
PRINTER_VENDOR_ID = 0x0fe6
PRINTER_PRODUCT_ID = 0x811e

# Norwegian character mapping to UTF-8 byte sequences
NORWEGIAN_CHAR_MAP = {
    'ø': '\xF8',  # UTF-8 byte for ø
    'Ø': '\xD8',  # UTF-8 byte for Ø
    'å': '\xE5',  # UTF-8 byte for å
    'Å': '\xC5',  # UTF-8 byte for Å
    'æ': '\xE6',  # UTF-8 byte for æ
    'Æ': '\xC6',  # UTF-8 byte for Æ
}

def replace_norwegian_chars(text):
    """Replace Norwegian characters with their UTF-8 byte representations."""
    for norwegian_char, utf8_byte in NORWEGIAN_CHAR_MAP.items():
        text = text.replace(norwegian_char, utf8_byte)
    return text

def replace_norwegian_chars_regex(text):
    """Alternative regex-based approach to replace Norwegian characters."""
    # Create a regex pattern that matches any Norwegian character
    pattern = '[øØåÅæÆ]'
    
    def replace_match(match):
        char = match.group(0)
        return NORWEGIAN_CHAR_MAP.get(char, char)
    
    return re.sub(pattern, replace_match, text)

def process_ingredients(ingredients_list):
    """Process a list of ingredients, replacing Norwegian characters."""
    processed_ingredients = []
    for ingredient in ingredients_list:
        # You can use either method:
        processed_ingredient = replace_norwegian_chars(ingredient)
        # Or: processed_ingredient = replace_norwegian_chars_regex(ingredient)
        processed_ingredients.append(processed_ingredient)
    return processed_ingredients

def test_encoding_approaches():
    """Test different approaches for Norwegian characters without using charcode."""
    test_ingredients = ["Oksekjøtt", "Løkpulver", "Hvitløkspulver"]
    
    print("=== Testing Different Encoding Approaches ===")
    
    # Approach 1: Direct UTF-8 byte replacement
    print("\nApproach 1: UTF-8 byte replacement")
    for ingredient in test_ingredients:
        processed = replace_norwegian_chars(ingredient)
        print(f"  {ingredient} -> {processed}")
    
    # Approach 2: Regex-based replacement
    print("\nApproach 2: Regex replacement")
    for ingredient in test_ingredients:
        processed = replace_norwegian_chars_regex(ingredient)
        print(f"  {ingredient} -> {processed}")
    
    # Approach 3: Try different encoding/decoding
    print("\nApproach 3: Encoding attempts")
    for ingredient in test_ingredients:
        try:
            # Try latin-1 encoding
            encoded = ingredient.encode('latin-1')
            print(f"  {ingredient} -> latin-1: {encoded}")
        except:
            print(f"  {ingredient} -> latin-1: Failed")
        
        try:
            # Try cp850 encoding  
            encoded = ingredient.encode('cp850')
            print(f"  {ingredient} -> cp850: {encoded}")
        except:
            print(f"  {ingredient} -> cp850: Failed")

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
    """Test printing with Norwegian character replacement."""
    # List of ingredients with Norwegian characters
    ingredients = [
        "Oksekjøtt",
        "Worcestershire saus", 
        "Soya saus",
        "Brunt sukker",
        "Løkpulver",
        "Hvitløkspulver",
        "Paprikapulver",
        "Gochugaru",
        "Kajennepepper"
    ]
    
    try:
        p = Usb(PRINTER_VENDOR_ID, PRINTER_PRODUCT_ID, 0, profile="simple", in_ep=0x82, out_ep=0x03)
        print(p.is_usable())
        p.open()
        
        # Don't set any special charcode - use default
        p.set(align='center', bold=True)
        p.text("BPs jerky\n")
        p.text("----------\n")
        
        p.set(align='left', bold=False)
        p.ln(2)
        
        # Process and print ingredients
        processed_ingredients = process_ingredients(ingredients)
        for ingredient in processed_ingredients:
            p.text(f"{ingredient}\n")
            
        p.ln(2)
        #p.cut()
        
        print("Test message sent to printer successfully!")
        print("\nOriginal ingredients:")
        for ingredient in ingredients:
            print(f"  {ingredient}")
        print("\nProcessed ingredients:")
        for ingredient in processed_ingredients:
            print(f"  {ingredient}")
            
        p.close()

    except Exception as e:
        print(f"An error occurred: {e}")

# --- Run the test print ---
if __name__ == "__main__":
    print("Testing encoding approaches...")
    test_encoding_approaches()
    print("\n" + "="*50)
    print("Running printer test...")
    test_print()