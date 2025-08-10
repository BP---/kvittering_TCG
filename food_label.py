"""Utility script to test thermal printer output including Nordic characters like ø.

Notes:
 - Thermal printers often default to code page CP437 (no 'ø'). We explicitly switch
   to a Western European/Nordic table (CP1252 or CP865) before printing.
 - python-escpos: p.charcode(name) sends ESC t n for the selected table AND sets
   the internal encoding used when calling p.text()/p.textln().
 - If your specific clone maps the tables differently, run cycle_codepages().
"""

from escpos.printer import Usb
from escpos import exceptions as escpos_exceptions

# --- Configuration ---
PRINTER_VENDOR_ID = 0x0fe6
PRINTER_PRODUCT_ID = 0x811e

# Candidate code pages that contain 'ø'. Order is preference.
PREFERRED_CODEPAGES = [
    "CP1252",   # Windows Western Europe – usually table 16 on many ESC/POS printers
    "ISO8859_1",# Latin-1 (sometimes listed as ISO-8859-1)
    "CP865",    # Nordic
    "CP858",    # Western Europe + Euro
]

def _init_printer():
    """Create & return the Usb printer instance."""
    return Usb(PRINTER_VENDOR_ID, PRINTER_PRODUCT_ID, 0, profile="simple", in_ep=0x82, out_ep=0x03)

def _select_codepage(p, verbose=True):
    """Attempt to set one of the preferred code pages so that 'ø' prints correctly.

    Falls back to sending raw ESC t if python-escpos name mapping fails.
    """
    for name in PREFERRED_CODEPAGES:
        try:
            p.charcode(name)
            if verbose:
                print(f"Selected code page: {name}")
            # Verify that encoding supports ø
            try:
                "ø".encode(p.encoding)
                return True
            except Exception:  # pragma: no cover - extremely unlikely
                continue
        except (AttributeError, escpos_exceptions.Error):
            continue

    # Fallback: manual ESC t (common table numbers; may vary by model)
    # Mapping attempts: CP1252->16, CP865->3
    raw_attempts = [(16, "manual CP1252 guess"), (3, "manual CP865 guess")]
    for code, label in raw_attempts:
        try:
            p._raw(b"\x1bt" + bytes([code]))  # ESC t n
            if verbose:
                print(f"Sent raw ESC t {code} ({label})")
            return True
        except Exception as e:
            if verbose:
                print(f"Raw ESC t {code} failed: {e}")
    if verbose:
        print("Failed to set a preferred code page; 'ø' may not print correctly.")
    return False

def test_print():
    """Print the ingredient list including characters 'ø' and 'å'."""
    try:
        p = _init_printer()
        usable = p.is_usable()
        print(f"Printer usable: {usable}")
        p.open()

        _select_codepage(p)

        p.set(align='center', bold=True)
        p.text("BPs jerky\n")
        p.textln("----------")

        p.set(align='left', bold=False)
        p.ln(1)
        # Lines containing Nordic letters to verify output
        ingredients = [
            "Oksekjøtt",
            "Worcestershire saus",
            "Soya saus",
            "Brunt sukker",
            "Løkpulver",
            "Hvitløkspulver",
            "Paprikapulver",
            "Gochugaru",
            "Kajennepepper",
        ]
        for line in ingredients:
            p.textln(line)

        p.ln(2)
        # p.cut()  # Uncomment if your printer supports cutting
        print("Test message (with ø) sent to printer.")
        p.close()
    except Exception as e:
        print(f"An error occurred: {e}")

def cycle_codepages():
    """Diagnostic: cycle several code pages and print a sample line to see which renders ø.

    After running, inspect paper to find the FIRST correct line. Use that code page name in
    PREFERRED_CODEPAGES ordering if needed.
    """
    samples = [
        "CP1252", "ISO8859_1", "CP865", "CP858", "CP437", "CP850", "CP852"
    ]
    sample_text = "Test ø Ø æ Æ å Å Sørensen"
    try:
        p = _init_printer()
        p.open()
        p.set(align='left')
        for name in samples:
            try:
                p.charcode(name)
                p.textln(f"[{name}] {sample_text}")
            except Exception as e:
                p.textln(f"[{name}] (failed: {e})")
        p.ln(3)
        # p.cut()
        p.close()
        print("Finished cycling code pages. Check the printout for the first correct line.")
    except Exception as e:
        print(f"Cycle failed: {e}")

if __name__ == "__main__":
    # Change to cycle_codepages() if you need to diagnose the correct table.
    test_print()