import random
import requests
from typing import Dict, Any, Optional

# PocketBase configuration
POCKETBASE_URL = "http://localhost:8090"
API_URL = f"{POCKETBASE_URL}/api"
COLLECTION_NAME = "people"

# Rarity weights (higher weight = more common)
# These weights create a typical TCG rarity distribution
RARITY_WEIGHTS = {
    "E": 40,  # Common
    "D": 30,  # Uncommon
    "C": 20,  # Rare
    "B": 7,   # Epic
    "A": 2.5, # Legendary
    "S": 0.5  # Mythic
}

def get_weighted_rarity() -> str:
    """
    Randomly select a rarity based on weighted probabilities.
    
    Returns:
        str: The selected rarity (E, D, C, B, A, or S)
    """
    rarities = list(RARITY_WEIGHTS.keys())
    weights = list(RARITY_WEIGHTS.values())
    print(f"Rarities: {rarities} \nweights: {weights}")
    
    return random.choices(rarities, weights=weights, k=1)[0]

def get_people_by_rarity(rarity: str) -> list:
    """
    Fetch all people from PocketBase with the specified rarity.
    
    Args:
        rarity (str): The rarity to filter by
        
    Returns:
        list: List of person records with the specified rarity
    """
    try:
        # Create filter for the specific rarity
        filter_param = f'rarity="{rarity}"'
        
        response = requests.get(
            f"{API_URL}/collections/{COLLECTION_NAME}/records",
            params={"filter": filter_param},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("items", [])
        else:
            print(f"Error fetching people with rarity {rarity}: {response.status_code}")
            return []
            
    except requests.exceptions.RequestException as e:
        print(f"Network error while fetching people: {e}")
        return []

def get_random_person() -> Optional[Dict[str, Any]]:
    """
    Get a random person from the database based on weighted rarity selection.
    
    Returns:
        dict or None: A person record as a dictionary, or None if no person found
    """
    # First, select a rarity based on weights
    selected_rarity = get_weighted_rarity()
    print(f"Selected rarity: {selected_rarity}")
    
    # Get all people with that rarity
    people_with_rarity = get_people_by_rarity(selected_rarity)
    
    if not people_with_rarity:
        print(f"No people found with rarity {selected_rarity}")
        return None
    
    # Randomly select one person from the list
    selected_person = random.choice(people_with_rarity)
    
    print(f"Found {len(people_with_rarity)} people with rarity {selected_rarity}")
    print(f"Selected: {selected_person.get('name', 'Unknown')}")
    
    return selected_person

def check_pocketbase_connection() -> bool:
    """Check if PocketBase is running and accessible."""
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def display_person_info(person: Dict[str, Any]) -> None:
    """Display formatted person information."""
    if not person:
        print("No person to display.")
        return
    
    print("\n" + "=" * 50)
    print("RANDOM PERSON SELECTED")
    print("=" * 50)
    print(f"Name: {person.get('name', 'Unknown')}")
    print(f"Rarity: {person.get('rarity', 'Unknown')}")
    print(f"Description: {person.get('description', 'No description available')}")
    print(f"ID: {person.get('id', 'Unknown')}")
    print("=" * 50)

def main():
    """Main function for testing the random person selection."""
    print("Random Person Selector")
    print("-" * 30)
    
    # Check PocketBase connection
    if not check_pocketbase_connection():
        print("❌ Cannot connect to PocketBase at http://localhost:8090")
        print("Make sure PocketBase is running.")
        return
    
    print("✅ Connected to PocketBase")
    
    # Display rarity weights for reference
    print("\nRarity Distribution:")
    total_weight = sum(RARITY_WEIGHTS.values())
    for rarity, weight in RARITY_WEIGHTS.items():
        percentage = (weight / total_weight) * 100
        print(f"  {rarity}: {percentage:.1f}%")
    
    print(f"\nSelecting random person...")
    
    # Get a random person
    person = get_random_person()
    
    if person:
        display_person_info(person)
    else:
        print("❌ No person could be selected.")
    
    # Option to select multiple people for testing
    print(f"\n--- Testing Multiple Selections ---")
    rarity_counts = {rarity: 0 for rarity in RARITY_WEIGHTS.keys()}
    
    num_tests = 20
    print(f"Selecting {num_tests} random people to test distribution:")
    
    for i in range(num_tests):
        person = get_random_person()
        if person:
            rarity = person.get('rarity', 'Unknown')
            if rarity in rarity_counts:
                rarity_counts[rarity] += 1
        print(f"  {i+1}/{num_tests} - {person.get('name', 'Unknown') if person else 'None'} ({person.get('rarity', 'Unknown') if person else 'Unknown'})")
    
    print(f"\nActual distribution in {num_tests} selections:")
    for rarity, count in rarity_counts.items():
        percentage = (count / num_tests) * 100
        print(f"  {rarity}: {count} ({percentage:.1f}%)")

if __name__ == "__main__":
    main()
