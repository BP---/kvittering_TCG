import tkinter as tk
from tkinter import messagebox, ttk
import requests
from datetime import datetime
import threading
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

class TCGApp:
    def __init__(self, root):
        self.root = root
        self.root.title("TCG Receipt Generator")
        self.root.geometry("400x300")
        self.root.resizable(False, False)
        
        # Center the window
        self.center_window()
        
        # Setup UI
        self.setup_ui()
        
        # Bind Enter key to generate receipt
        self.root.bind('<Return>', lambda event: self.generate_receipt_threaded())
        self.root.bind('<KP_Enter>', lambda event: self.generate_receipt_threaded())  # Numpad Enter
        
        # Check initial connections
        self.check_connections()
    
    def center_window(self):
        """Center the window on the screen."""
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
        title_label = ttk.Label(main_frame, text="TCG Receipt Generator", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Status indicators
        self.db_status_label = ttk.Label(main_frame, text="Database: Checking...", 
                                        foreground="orange")
        self.db_status_label.grid(row=1, column=0, columnspan=2, pady=(0, 10))
        
        self.printer_status_label = ttk.Label(main_frame, text="Printer: Not tested", 
                                            foreground="gray")
        self.printer_status_label.grid(row=2, column=0, columnspan=2, pady=(0, 20))
        
        # Main action button
        self.generate_button = ttk.Button(main_frame, text="Generate Receipt", 
                                        command=self.generate_receipt_threaded,
                                        style="Accent.TButton")
        self.generate_button.grid(row=3, column=0, columnspan=2, pady=(0, 20), 
                                ipadx=20, ipady=10)
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), 
                          pady=(0, 10))
        
        # Status text
        self.status_label = ttk.Label(main_frame, text="Ready", 
                                    foreground="green")
        self.status_label.grid(row=5, column=0, columnspan=2)
        
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
        self.progress.start()
        
        thread = threading.Thread(target=self.generate_receipt)
        thread.daemon = True
        thread.start()
    
    def generate_receipt(self):
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
                    processed_image = take_and_process_photo()
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
            self.update_status("Printing receipt...", "blue")
            self.print_receipt(person, processed_image)
            
            # Step 5: Create receipt record in database
            self.update_status("Saving receipt record...", "blue")
            self.create_receipt_record(person)
            
            # Success
            self.update_status("Receipt generated successfully! ✓", "green")
            messagebox.showinfo("Success", 
                              f"Receipt generated for {person.get('name', 'Unknown')} "
                              f"({person.get('rarity', 'Unknown')} rarity)")
            
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            self.update_status(error_msg, "red")
            messagebox.showerror("Error", error_msg)
            print(f"Full error: {e}")
        
        finally:
            # Re-enable button and stop progress
            self.progress.stop()
            self.generate_button.config(state="normal")
    
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
            printer.set(align='center', bold=True, double_height=True)
            printer.text("TCG RECEIPT\n")
            printer.ln(1)
            
            # Print person info
            printer.set(align='center', bold=True, double_height=False)
            printer.text(f"{person.get('name', 'Unknown')}\n")
            
            printer.set(align='center', bold=False)
            printer.text(f"Rarity: {person.get('rarity', 'Unknown')}\n")
            printer.ln(1)
            
            # Print description
            printer.set(align='left', bold=False)
            description = person.get('description', 'No description available')
            # Wrap text for thermal printer (usually ~32 characters wide)
            wrapped_description = self.wrap_text(description, 32)
            for line in wrapped_description:
                printer.text(f"{line}\n")
            printer.ln(1)
            
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
            printer.set(align='center', bold=False)
            printer.text("Thank you!\n")
            printer.ln(4)
            
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
        
        description = person.get('description', 'No description available')
        wrapped_description = self.wrap_text(description, 32)
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
    root = tk.Tk()
    app = TCGApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
