# TCG Receipt Generator 🎯📸🖨️

A unique **Trading Card Game (TCG) receipt generator** that combines photography with thermal printing to create collectible receipts featuring historical figures. This Python application uses a camera to capture photos and generates receipts with random historical people of different rarities, creating a physical TCG-like collecting experience.

## 🎮 What This App Does

This application creates a unique collecting experience where:
- **Take a photo** with the integrated camera
- **Generate a receipt** featuring a random historical figure with TCG-style rarities
- **Print physical receipts** using a thermal printer (like those used in shops)
- **Collect historical figures** with different rarity levels (S-Rank to E-Rank)
- **Store all receipts** in a PocketBase database for tracking your collection

Think of it as a **real-world gacha/TCG system** where instead of digital cards, you get physical thermal-printed receipts!

## 🏆 Rarity System

The app uses a weighted TCG rarity system:

| Rarity | Name | Probability | Examples |
|--------|------|-------------|----------|
| **S** | Mythic | 0.5% | Leonardo da Vinci, Marie Curie, Albert Einstein |
| **A** | Legendary | 2.5% | William Shakespeare, Isaac Newton |
| **B** | Epic | 7% | Famous scientists, artists, leaders |
| **C** | Rare | 20% | Notable historical figures |
| **D** | Uncommon | 30% | Well-known personalities |
| **E** | Common | 40% | Historical figures |

## 🛠️ Hardware Requirements

### Required Hardware
- **Raspberry Pi** (recommended) or Windows/Linux computer
- **USB Camera** or **Pi Camera** (for photo capture)
- **58mm Thermal Printer** (USB connection)
  - Tested with printer using Vendor ID: `0x0fe6`, Product ID: `0x811e` The specific model I used is a CASHINO CSN-A4L 58mm
  - Compatible with ESC/POS thermal printers

### Optional Hardware
- **3.5" Touchscreen** for better user experience
- Custom enclosure/kiosk setup

## 📋 Software Requirements

### Python Dependencies
```
pillow
escpos
requests
python-escpos
numpy
picamera2  # For Raspberry Pi camera
```

### System Requirements
- **Python 3.7+**
- **PocketBase** (included in `pb/` folder)
- **Windows/Linux/Raspberry Pi OS**

## 🚀 Installation & Setup

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd kvittering_TCG
```

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 3. Setup PocketBase Database

#### Start PocketBase:
```bash
cd pb
./pocketbase serve  # Linux/Mac
# or
pocketbase.exe serve  # Windows
```

PocketBase will run on `http://localhost:8090`

#### Populate the Database:
```bash
python populatedb.py
```

This will load all historical figures from `files/people.json` into the database.

### 4. Hardware Setup
- Connect your USB thermal printer
- Connect your camera (USB or Pi Camera)
- Ensure proper driver installation for your printer

### 5. Test Your Setup
```bash
# Test camera
python test_camera.py

# Test printer
python test_print.py

# Test the main application
python main.py
```

## 🎯 Usage

### Web Server Mode (recommended for networked setups)

Run the FastAPI server on the Raspberry Pi and control the printer from any laptop connected to the same network (e.g. via an ethernet switch):

```bash
# Start PocketBase first (see above), then:
python webapp.py
# or with uvicorn directly:
uvicorn webapp:app --host 0.0.0.0 --port 8000
```

Then open `http://<pi-ip>:8000` in a browser on any connected laptop. The web interface lets you:
- **Print text**: type anything into the text box and hit *Print*
- **Generate TCG Receipt**: triggers the full receipt flow (random person + camera photo + thermal print + database record)

#### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Web interface |
| `POST` | `/api/print-text` | Print arbitrary text. Body: `{"text": "..."}` |
| `POST` | `/api/receipt` | Run the TCG receipt flow. Optional body: `{"testing": true}` skips the database save |
| `GET` | `/api/health` | Reports printer/camera/database availability |

> **Note:** The endpoints are intentionally unauthenticated — this is designed for a closed network with no public internet connection. To serve on port 80 on the Pi (so the bare IP works without a port), run uvicorn with `sudo` or via a systemd service: `uvicorn webapp:app --host 0.0.0.0 --port 80`.

### GUI Mode (original tkinter app)
```bash
python main.py
```

### Advanced Options
```bash
# Customize text size (smaller number = smaller text)
python main.py --text-width 20

# Customize image width for receipts
python main.py --image-width 200

# Both options
python main.py --text-width 28 --image-width 384
```

### Controls
- **Enter Key / Click Button**: Generate new receipt
- **Escape Key**: Toggle fullscreen mode
- **Camera**: Automatically captures photo when generating receipt

## 📁 Project Structure

```
kvittering_TCG/
├── main.py                 # Main application with GUI
├── getRandomPerson.py      # Handles person selection and rarity system
├── test_camera.py          # Camera interface and photo processing
├── populatedb.py           # Database population script
├── requirements.txt        # Python dependencies
├── files/
│   └── people.json        # Historical figures database
└── pb/                    # PocketBase database
    ├── pocketbase.exe     # PocketBase executable
    ├── pb_data/           # Database files
    └── pb_migrations/     # Database schema migrations
```

## 🔧 Configuration

### Printer Configuration
Edit the printer settings in `main.py`:
```python
PRINTER_VENDOR_ID = 0x0fe6  # Your printer's vendor ID
PRINTER_PRODUCT_ID = 0x811e  # Your printer's product ID
```

### Camera Settings
Modify camera settings in `test_camera.py`:
```python
OUTPUT_IMAGE_WIDTH = 384  # Image width for thermal printer
```

### PocketBase URL
Change database URL if needed in `main.py` and `getRandomPerson.py`:
```python
POCKETBASE_URL = "http://localhost:8090"
```

## 🎨 Features

- **📸 Photo Capture**: Integrated camera support with image processing
- **🖨️ Thermal Printing**: Direct printing to ESC/POS thermal printers ( I used a CASHINO CSN-A4L 58mm)
- **📊 Rarity System**: Weighted randomization for collecting rare figures
- **🗄️ Database Storage**: All receipts saved with timestamps
- **🌍 Multi-language**: Support for Norwegian characters
- **📱 Touch-Friendly GUI**: Optimized for touchscreen interfaces
- **⌨️ Keyboard Shortcuts**: Quick generation with Enter key
- **🖥️ Fullscreen Mode**: Perfect for kiosk setups

## 🐛 Troubleshooting

### Common Issues

**Camera not working:**
- Check camera permissions
- Ensure `picamera2` is installed for Pi Camera
- Verify camera is properly connected

**Printer not found:**
- Check USB connection
- Verify printer vendor/product IDs
- Install proper printer drivers

**PocketBase connection failed:**
- Ensure PocketBase is running on port 8090
- Check firewall settings
- Verify database is populated

**Norwegian/Special characters not printing:**
- The app includes special character encoding
- Try different printer character sets (CP865, CP850, CP437)

## 🎮 How to Play/Collect

1. **Take a photo** by pressing Enter or clicking the generate button
2. **Wait for processing** - the app selects a random historical figure
3. **Receive your receipt** - printed with photo and figure information
4. **Collect different rarities** - try to get all the legendary figures!
5. **Track your collection** - all receipts are stored in the database

## 🔮 Future Enhancements

Potential improvements for the project:
- **Collection tracking GUI** - view all collected figures
- **Trading system** - share/trade receipts with others
- **Achievement system** - rewards for collecting sets
- **Custom figure additions** - easy way to add new historical figures
- **Statistics dashboard** - collection completion rates
- **Mobile app companion** - digital collection viewer

## 🤝 Contributing

Feel free to contribute by:
- Adding new historical figures to `files/people.json`
- Improving the GUI design
- Adding support for different printer types
- Enhancing the rarity system
- Adding new features

## 📄 License

MIT

## 🙋‍♂️ Questions?

If you have questions about setup, hardware compatibility, or extending the project, feel free to open an issue!

---

**Happy Collecting! 🎯📸🖨️**