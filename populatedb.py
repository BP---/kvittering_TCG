import json
import requests
import os
from typing import Dict, Any

# PocketBase configuration
POCKETBASE_URL = "http://localhost:8090"  # Default PocketBase URL
API_URL = f"{POCKETBASE_URL}/api"
COLLECTION_NAME = "people"

def load_historical_figures() -> list:
    """Load historical figures from the JSON file."""
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        json_file_path = os.path.join(script_dir, "files", "people.json")
        
        with open(json_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            return data.get("historical_figures", [])
    except FileNotFoundError:
        print(f"Error: Could not find people.json file at {json_file_path}")
        return []
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format - {e}")
        return []

def create_person_record(person: Dict[str, Any]) -> bool:
    """Create a person record in PocketBase."""
    try:
        # Extract description (use English version)
        description = person.get("description", "")
        if isinstance(description, dict):
            description = description.get("no", "")
        
        # Prepare the data for PocketBase
        record_data = {
            "name": person.get("name", ""),
            "rarity": person.get("rarity", ""),
            "description": description
        }
        
        # Make POST request to create the record
        response = requests.post(
            f"{API_URL}/collections/{COLLECTION_NAME}/records",
            json=record_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            print(f"✓ Successfully added: {record_data['name']} (Rarity: {record_data['rarity']})")
            return True
        else:
            print(f"✗ Failed to add {record_data['name']}: {response.status_code} - {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"✗ Network error while adding {person.get('name', 'Unknown')}: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error while adding {person.get('name', 'Unknown')}: {e}")
        return False

def check_pocketbase_connection() -> bool:
    """Check if PocketBase is running and accessible."""
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code == 200:
            print(f"✓ Connected to PocketBase at {POCKETBASE_URL}")
            return True
        else:
            print(f"✗ PocketBase responded with status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"✗ Cannot connect to PocketBase at {POCKETBASE_URL}: {e}")
        print("Make sure PocketBase is running on localhost:8090")
        return False

def main():
    """Main function to populate the database."""
    print("Starting database population...")
    print("=" * 50)
    
    # Check PocketBase connection
    if not check_pocketbase_connection():
        return
    
    # Load historical figures
    historical_figures = load_historical_figures()
    if not historical_figures:
        print("No historical figures found to add.")
        return
    
    print(f"Found {len(historical_figures)} historical figures to add.")
    print("-" * 50)
    
    # Add each person to the database
    success_count = 0
    failed_count = 0
    
    for person in historical_figures:
        if create_person_record(person):
            success_count += 1
        else:
            failed_count += 1
    
    # Summary
    print("-" * 50)
    print(f"Database population completed!")
    print(f"Successfully added: {success_count} records")
    print(f"Failed to add: {failed_count} records")
    print(f"Total processed: {len(historical_figures)} records")

if __name__ == "__main__":
    main()
