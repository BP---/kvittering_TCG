"""
TCG Receipt Generator

A GUI application that generates receipts with random person data, photos, and thermal printing.

Usage:
    python main.py                                    # Use default settings (text size: 24, image width: 256)
    python main.py --text-width 20                   # Smaller text size for descriptions
    python main.py --image-width 200                 # Custom image width in pixels
    python main.py --text-width 28 --image-width 384 # Larger text and image size

Arguments:
    --text-width: Controls text size - smaller values create smaller text (default: 24)
    --image-width: Width for processed images in pixels (default: 256)
"""

import tkinter as tk
from tkinter import messagebox, ttk
import requests
from datetime import datetime
import threading
import argparse
import sys
from typing import Dict, Any, Optional

# Import functions from other modules
from getRandomPerson import get_random_person, check_pocketbase_connection

# Try to import camera and printer modules (may not be available on all systems)
try:
    from test_camera import take_and_process_photo
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
    from PIL import Image, ImageTk
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

# Default settings (can be overridden by command line arguments)
DEFAULT_TEXT_WIDTH = 24  # Controls text size - smaller values = smaller text
DEFAULT_IMAGE_WIDTH = 256  # Smaller default image size

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='TCG Receipt Generator')
    parser.add_argument('--text-width', type=int, default=DEFAULT_TEXT_WIDTH,
                       help=f'Text size control - smaller values = smaller text (default: {DEFAULT_TEXT_WIDTH})')
    parser.add_argument('--image-width', type=int, default=DEFAULT_IMAGE_WIDTH,
                       help=f'Width for processed images (default: {DEFAULT_IMAGE_WIDTH})')
    return parser.parse_args()

class TCGApp:
    def __init__(self, root, text_width=DEFAULT_TEXT_WIDTH, image_width=DEFAULT_IMAGE_WIDTH):
        self.root = root
        self.text_width = text_width
        self.image_width = image_width
        
        self.root.title("TCG Receipt Generator")
        # Get screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Option 1: Full screen minus taskbar (recommended for 3.5" screen)
        # Adjust height to account for taskbar (usually 40-60 pixels)
        taskbar_height = 50  # Adjust this value if needed
        self.root.geometry(f"{screen_width}x{screen_height - taskbar_height}+0+0")
        
        # Option 2: True fullscreen (uncomment to use instead)
        self.root.attributes('-fullscreen', True)
        self.root.bind('<Escape>', lambda e: self.root.attributes('-fullscreen', False))
        
        self.root.resizable(True, True)  # Allow resizing for better flexibility
        
        # Setup UI
        self.setup_ui()
        
        # Bind Enter key to generate receipt
        self.root.bind('<Return>', lambda event: self.generate_receipt_threaded())
        self.root.bind('<KP_Enter>', lambda event: self.generate_receipt_threaded())  # Numpad Enter
        
        # Add escape key binding to exit fullscreen mode
        self.root.bind('<Escape>', self.toggle_fullscreen)
        
        # Check initial connections
        self.check_connections()
    
    def toggle_fullscreen(self, event=None):
        """Toggle between fullscreen and windowed mode."""
        current_state = self.root.attributes('-fullscreen')
        self.root.attributes('-fullscreen', not current_state)
        
    def center_window(self):
        """Center the window on the screen (for windowed mode)."""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def setup_ui(self):
        """Setup the user interface."""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="IKT Receipt Generator", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 10))
        
        # Settings display
        settings_label = ttk.Label(main_frame, 
                                 text=f"Settings: Text size: {self.text_width}, Image width: {self.image_width}",
                                 font=("Arial", 8))
        settings_label.grid(row=1, column=0, columnspan=2, pady=(0, 15))
        
        # Status indicators
        self.db_status_label = ttk.Label(main_frame, text="Database: Checking...", 
                                        foreground="orange")
        self.db_status_label.grid(row=2, column=0, columnspan=2, pady=(0, 10))
        
        self.printer_status_label = ttk.Label(main_frame, text="Printer: Not tested", 
                                            foreground="gray")
        self.printer_status_label.grid(row=3, column=0, columnspan=2, pady=(0, 20))
        
        # Main action buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=4, column=0, columnspan=2, pady=(0, 20))
        
        # Main action button
        self.generate_button = ttk.Button(buttons_frame, text="Generate Receipt", 
                                        command=self.generate_receipt_threaded,
                                        style="Accent.TButton")
        self.generate_button.grid(row=0, column=0, padx=(0, 10), 
                                ipadx=20, ipady=10)
        
        # Test button
        self.test_button = ttk.Button(buttons_frame, text="Test", 
                                    command=self.test_receipt_threaded)
        self.test_button.grid(row=0, column=1, 
                            ipadx=10, ipady=5)
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), 
                          pady=(0, 10))
        
        # Status text
        self.status_label = ttk.Label(main_frame, text="Ready", 
                                    foreground="green")
        self.status_label.grid(row=6, column=0, columnspan=2)
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
    
    def check_connections(self):
        """Check database and printer connections."""
        # Check database
        if check_pocketbase_connection():
            self.db_status_label.config(text="Database: Connected ✓", 
                                      foreground="green")
        else:
            self.db_status_label.config(text="Database: Disconnected ✗", 
                                      foreground="red")
    
    def update_status(self, message, color="black"):
        """Update the status label."""
        self.status_label.config(text=message, foreground=color)
        self.root.update_idletasks()
    
    def generate_receipt_threaded(self):
        """Run the receipt generation in a separate thread to prevent UI freezing."""
        self.generate_button.config(state="disabled")
        self.test_button.config(state="disabled")
        self.progress.start()
        
        thread = threading.Thread(target=self.generate_receipt, args=(False,))
        thread.daemon = True
        thread.start()
    
    def test_receipt_threaded(self):
        """Run the test receipt generation in a separate thread to prevent UI freezing."""
        self.generate_button.config(state="disabled")
        self.test_button.config(state="disabled")
        self.progress.start()
        
        thread = threading.Thread(target=self.generate_receipt, args=(True,))
        thread.daemon = True
        thread.start()
    
    def generate_receipt(self, testing=False):
        """Main function to generate a receipt with photo and person data."""
        try:
            # Step 1: Check database connection
            self.update_status("Checking database connection...", "blue")
            if not check_pocketbase_connection():
                raise Exception("Cannot connect to PocketBase. Make sure it's running.")
            
            # Step 2: Get random person
            self.update_status("Selecting random person...", "blue")
            person = get_random_person()
            if not person:
                raise Exception("Could not retrieve a random person from database.")
            
            # Step 3: Take and process photo
            self.update_status("Taking photo...", "blue")
            processed_image = None
            if CAMERA_AVAILABLE:
                try:
                    processed_image = self.take_and_process_photo_custom()
                    if not processed_image:
                        print("Failed to capture and process photo.")
                except Exception as e:
                    # If camera fails, we'll continue without photo
                    print(f"Camera error: {e}")
                    processed_image = None
                    self.update_status("Photo capture failed, continuing without photo...", "orange")
            else:
                print("Camera not available on this system.")
                self.update_status("Camera not available, continuing without photo...", "orange")
            
            # Step 4: Print receipt
            print_status = "Printing test receipt..." if testing else "Printing receipt..."
            self.update_status(print_status, "blue")
            self.print_receipt(person, processed_image)
            
            # Step 5: Create receipt record in database (skip if testing)
            if testing:
                self.update_status("Test mode - skipping database save", "orange")
            else:
                self.update_status("Saving receipt record...", "blue")
                self.create_receipt_record(person)
            
            # Success
            if testing:
                self.update_status("Test receipt generated successfully! ✓", "green")
                messagebox.showinfo("Test Success", 
                                  f"Test receipt generated for {person.get('name', 'Unknown')} "
                                  f"({person.get('rarity', 'Unknown')} rarity)\n\n"
                                  f"Note: No database entry was created.")
            else:
                self.update_status("Receipt generated successfully! ✓", "green")
                messagebox.showinfo("Success", 
                                  f"Receipt generated for {person.get('name', 'Unknown')} "
                                  f"({person.get('rarity', 'Unknown')} rarity)")
            
        except Exception as e:
            error_prefix = "Test Error" if testing else "Error"
            error_msg = f"{error_prefix}: {str(e)}"
            self.update_status(error_msg, "red")
            messagebox.showerror(error_prefix, error_msg)
            print(f"Full {error_prefix.lower()}: {e}")
        
        finally:
            # Re-enable buttons and stop progress
            self.progress.stop()
            self.generate_button.config(state="normal")
            self.test_button.config(state="normal")
    
    def print_receipt(self, person: Dict[str, Any], image: Optional[object] = None):
        """Print the receipt to thermal printer."""
        if not PRINTER_AVAILABLE:
            print("Printer not available - simulating print output:")
            self.simulate_print_output(person, image)
            return
            
        try:
            # Initialize printer
            printer = Usb(PRINTER_VENDOR_ID, PRINTER_PRODUCT_ID, 0, 
                         profile="simple", in_ep=0x82, out_ep=0x03)
            printer.open()
            
            # Print header
            printer.set(align='center', bold=True, double_height=True, font='b')
            printer.text("IKT RECEIPT\n")
            printer.ln(1)
            
            # Print person info
            printer.set(align='center', bold=True, double_height=False)
            printer.text(f"{person.get('name', 'Unknown')}\n")
            
            printer.set(align='center', bold=False)
            printer.text(f"Rarity: {person.get('rarity', 'Unknown')}\n")
            printer.ln(1)
            
            # Print description with configurable text size
            description = person.get('description', 'No description available')
            printer.set(align='left', bold=False)
            printer.text(description)
            printer.ln(1)
            
            # Calculate height and width multipliers based on text_width setting
            # Smaller text_width values will result in smaller text
            # Default (24) = normal size (1x), smaller values = smaller text
            # size_multiplier = max(1, self.text_width // 12)  # Scale down for smaller widths
            # if self.text_width <= 12:
            #     height_mult = 1
            #     width_mult = 1
            # elif self.text_width <= 18:
            #     height_mult = 1
            #     width_mult = 1
            # elif self.text_width <= 24:
            #     height_mult = 1
            #     width_mult = 1
            # else:
            #     height_mult = min(2, self.text_width // 20)
            #     width_mult = min(2, self.text_width // 20)
            
            # printer.set(align='left', bold=False, height=height_mult, width=width_mult)
            
            # # Adjust wrapping width based on actual text size
            # # Larger text takes more space, so we need fewer characters per line
            # effective_width = self.text_width // max(1, (height_mult + width_mult) // 2)
            # wrapped_description = self.wrap_text(description, effective_width)
            # for line in wrapped_description:
            #     printer.text(f"{line}\n")
            # printer.ln(1)
            
            # Print date and time
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            printer.set(align='center', bold=False)
            printer.text(f"Generated: {current_time}\n")
            printer.ln(2)
            
            # Print image if available
            if image and PIL_AVAILABLE:
                printer.set(align='center')
                printer.image(image)
                printer.ln(2)
            
            # Print footer
            # printer.set(align='center', bold=False)
            # printer.text("Thank you!\n")
            printer.ln(2)
            
            printer.close()
            print("Receipt printed successfully!")
            
        except Exception as e:
            raise Exception(f"Printer error: {str(e)}")
    
    def simulate_print_output(self, person: Dict[str, Any], image: Optional[object] = None):
        """Simulate printer output for testing without actual printer."""
        print("\n" + "="*40)
        print("SIMULATED THERMAL PRINTER OUTPUT")
        print("="*40)
        print("         TCG RECEIPT")
        print()
        print(f"      {person.get('name', 'Unknown')}")
        print(f"    Rarity: {person.get('rarity', 'Unknown')}")
        print()
        
        # Calculate and show text size settings
        if self.text_width <= 12:
            height_mult = 1
            width_mult = 1
        elif self.text_width <= 18:
            height_mult = 1
            width_mult = 1
        elif self.text_width <= 24:
            height_mult = 1
            width_mult = 1
        else:
            height_mult = min(2, self.text_width // 20)
            width_mult = min(2, self.text_width // 20)
        
        effective_width = self.text_width // max(1, (height_mult + width_mult) // 2)
        
        print(f"[Text size: {width_mult}x width, {height_mult}x height, effective wrap: {effective_width}]")
        
        description = person.get('description', 'No description available')
        wrapped_description = self.wrap_text(description, effective_width)
        for line in wrapped_description:
            print(line)
        print()
        
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"  Generated: {current_time}")
        print()
        
        if image:
            print("    [IMAGE WOULD BE HERE]")
            print()
        
        print("       Thank you!")
        print()
        print("="*40)
    
    def take_and_process_photo_custom(self):
        """
        Custom version of take_and_process_photo that uses configurable image width
        and shows a preview before capturing.
        """
        if not CAMERA_AVAILABLE or not PIL_AVAILABLE:
            return None
            
        import time
        from picamera2 import Picamera2
        import tkinter as tk
        from tkinter import messagebox
        from PIL import ImageTk
        import numpy as np
        
        # The filename for the initial high-resolution capture.
        CAPTURE_FILENAME = "capture.jpg"
        
        picam2 = None
        captured_image = None
        
        try:
            # 1. --- Initialize camera and show preview ---
            print("Initializing camera...")
            picam2 = Picamera2()
            
            # Create a configuration for a still capture
            config = picam2.create_still_configuration()
            picam2.configure(config)
            
            picam2.start()
            print("Camera started, waiting for auto-adjustment...")
            time.sleep(2)  # Let camera adjust to lighting conditions
            
            # Show preview window
            preview_result = self.show_camera_preview(picam2)
            
            if preview_result:
                # User clicked "Take Photo"
                print("Capturing photo...")
                picam2.capture_file(CAPTURE_FILENAME)
                print(f"Picture saved as {CAPTURE_FILENAME}")
                captured_image = CAPTURE_FILENAME
            else:
                # User cancelled
                print("Photo capture cancelled by user")
                return None
            
        finally:
            # Ensure proper cleanup of camera resources
            if picam2 is not None:
                try:
                    picam2.stop()
                    picam2.close()
                    print("Camera properly closed")
                except Exception as e:
                    print(f"Warning: Error during camera cleanup: {e}")

        # 2. --- Process the captured image ---
        if captured_image:
            print(f"Processing image for thermal look (width: {self.image_width})...")
            with Image.open(captured_image) as img:
                # Resize the image to the configured width, maintaining aspect ratio
                original_width, original_height = img.size
                aspect_ratio = original_height / float(original_width)
                new_height = int(self.image_width * aspect_ratio)
                resized_img = img.resize((self.image_width, new_height))

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
        
        return None
    
    def show_camera_preview(self, picam2):
        """
        Show a preview window with the camera feed and capture controls.
        Returns True if photo should be taken, False if cancelled.
        """
        # Create preview window
        preview_window = tk.Toplevel(self.root)
        preview_window.title("Camera Preview")
        preview_window.geometry("640x480")
        preview_window.transient(self.root)
        preview_window.grab_set()  # Modal dialog
        
        # Center the preview window
        preview_window.update_idletasks()
        x = (preview_window.winfo_screenwidth() // 2) - (640 // 2)
        y = (preview_window.winfo_screenheight() // 2) - (480 // 2)
        preview_window.geometry(f"640x480+{x}+{y}")
        
        # Variables to track user choice
        user_choice = {"take_photo": False}
        
        # Create UI elements
        main_frame = ttk.Frame(preview_window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Instructions
        instruction_label = ttk.Label(main_frame, 
                                    text="Position your subject and click 'Take Photo' when ready",
                                    font=("Arial", 10))
        instruction_label.pack(pady=(0, 10))
        
        # Image display label
        image_label = ttk.Label(main_frame)
        image_label.pack(expand=True)
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))
        
        # Buttons
        def take_photo():
            user_choice["take_photo"] = True
            preview_window.destroy()
        
        def cancel():
            user_choice["take_photo"] = False
            preview_window.destroy()
        
        take_button = ttk.Button(button_frame, text="Take Photo", 
                               command=take_photo, style="Accent.TButton")
        take_button.pack(side=tk.LEFT, padx=(0, 10), ipadx=20, ipady=5)
        
        cancel_button = ttk.Button(button_frame, text="Cancel", 
                                 command=cancel)
        cancel_button.pack(side=tk.LEFT, ipadx=20, ipady=5)
        
        # Update preview image function
        def update_preview():
            try:
                if preview_window.winfo_exists():
                    # Capture a preview frame (low resolution for speed)
                    array = picam2.capture_array()
                    
                    # Convert to PIL Image
                    if len(array.shape) == 3:  # Color image
                        pil_image = Image.fromarray(array, 'RGB')
                    else:  # Grayscale
                        pil_image = Image.fromarray(array, 'L')
                    
                    # Resize for display (maintain aspect ratio)
                    display_size = (400, 300)  # Preview size
                    pil_image.thumbnail(display_size, Image.Resampling.LANCZOS)
                    
                    # Convert to PhotoImage for tkinter
                    photo = ImageTk.PhotoImage(pil_image)
                    
                    # Update the label
                    image_label.configure(image=photo)
                    image_label.image = photo  # Keep a reference
                    
                    # Schedule next update
                    preview_window.after(100, update_preview)  # Update every 100ms
            except Exception as e:
                print(f"Preview update error: {e}")
                # Continue trying to update
                if preview_window.winfo_exists():
                    preview_window.after(200, update_preview)
        
        # Start preview updates
        preview_window.after(100, update_preview)
        
        # Handle window close
        def on_closing():
            user_choice["take_photo"] = False
            preview_window.destroy()
        
        preview_window.protocol("WM_DELETE_WINDOW", on_closing)
        
        # Bind Enter key to take photo, Escape to cancel
        preview_window.bind('<Return>', lambda e: take_photo())
        preview_window.bind('<KP_Enter>', lambda e: take_photo())
        preview_window.bind('<Escape>', lambda e: cancel())
        
        preview_window.focus_set()
        
        # Wait for user to make a choice
        preview_window.wait_window()
        
        return user_choice["take_photo"]
    
    def wrap_text(self, text: str, width: int) -> list:
        """Wrap text to specified width."""
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            if len(current_line + " " + word) <= width:
                if current_line:
                    current_line += " " + word
                else:
                    current_line = word
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        return lines
    
    def create_receipt_record(self, person: Dict[str, Any]):
        """Create a receipt record in the database."""
        try:
            # Prepare the data for the receipt record
            receipt_data = {
                "person": person.get('id'),  # Relation to the person
                "reason": "other",  # Default reason as requested
                "created": datetime.now().isoformat() + "Z"  # ISO format timestamp
            }
            
            # Make POST request to create the receipt record
            response = requests.post(
                f"{API_URL}/collections/{RECEIPTS_COLLECTION}/records",
                json=receipt_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                print("Receipt record created successfully!")
                return response.json()
            else:
                raise Exception(f"Failed to create receipt record: {response.status_code} - {response.text}")
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error while creating receipt record: {e}")

def main():
    """Main function to run the application."""
    # Parse command line arguments
    args = parse_arguments()
    
    print(f"Starting TCG Receipt Generator with settings:")
    print(f"  Text width: {args.text_width} characters")
    print(f"  Image width: {args.image_width} pixels")
    
    root = tk.Tk()
    app = TCGApp(root, text_width=args.text_width, image_width=args.image_width)
    root.mainloop()

if __name__ == "__main__":
    main()
