import csv
import requests
import time
from concurrent.futures import ThreadPoolExecutor
import threading

# APIKey class to manage key usage and rate limiting
class APIKey:
    def __init__(self, key, holder_name, sleep_value, call_number=0):
        """Initialize an API key with holder's name, sleep value, and call number."""
        self.key = key
        self.holder_name = holder_name
        self.sleep_value = sleep_value  # Time to sleep between calls to avoid rate limiting
        self.call_number = call_number  # Tracks the number of calls made with this key

    def make_request(self, url):
        """Make an API request and apply sleep to respect the rate limit."""
        print(f"Making request with API key {self.key} (Holder: {self.holder_name})")
        response = requests.get(url)
        time.sleep(self.sleep_value)  # Apply the sleep value to respect the rate limit
        self.call_number += 1
        return response

# Torn API URL to fetch bazaar data
BAZAAR_URL = "https://api.torn.com/user/{user_id}?selections=bazaar&key={api_key}"

# Create a thread lock for synchronized file writing
file_lock = threading.Lock()

# Function to fetch bazaar data for a user and write to the CSV immediately
def fetch_and_write_bazaar_data(user_ids, api_key_obj, writer):
    for user_id in user_ids:
        url = BAZAAR_URL.format(user_id=user_id, api_key=api_key_obj.key)
        response = api_key_obj.make_request(url)
        if response.status_code == 200:
            data = response.json()
            if 'bazaar' in data and data['bazaar']:
                with file_lock:  # Ensure only one thread writes at a time
                    for item_id, item_info in data['bazaar'].items():
                        writer.writerow({
                            'player_id': user_id,
                            'item_name': item_info['name'],
                            'price': item_info['price'],
                            'quantity': item_info['quantity']
                        })
                        print(f"User {user_id}: Added item {item_info['name']} to CSV.")
            else:
                print(f"User {user_id} has no bazaar or no items listed.")
        else:
            print(f"Failed to fetch bazaar data for user {user_id}. Status code: {response.status_code}")

# Function to distribute work across multiple API keys and save results to CSV
def process_with_multiple_keys(user_ids, api_keys, output_file):
    total_users = len(user_ids)
    users_per_key = total_users // len(api_keys)

    # Open CSV for writing data in real-time
    with open(output_file, 'w', newline='') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=['player_id', 'item_name', 'price', 'quantity'])
        writer.writeheader()

        # Use ThreadPoolExecutor for parallel processing
        with ThreadPoolExecutor(max_workers=len(api_keys)) as executor:
            futures = []
            for i, api_key in enumerate(api_keys):
                start_idx = i * users_per_key
                end_idx = (i + 1) * users_per_key
                if i == len(api_keys) - 1:
                    end_idx = total_users  # Ensure the last key handles the remaining users

                # Submit each API key to handle its range of user IDs
                user_ids_chunk = user_ids[start_idx:end_idx]
                futures.append(executor.submit(
                    fetch_and_write_bazaar_data, user_ids_chunk, api_key, writer
                ))

            # Wait for all threads to complete
            for future in futures:
                future.result()

# Main function to run the entire process
def main():
    input_csv = 'active_users_filtered.csv'  # The input CSV with user IDs
    output_csv = 'sorted_bazaars.csv'  # The output CSV with sorted bazaar data
    api_keys = [
        APIKey(key="1CGin0RE5GqcHVsq", holder_name="billysnob", sleep_value=2),
        APIKey(key="eTsKvHBUa84tbulK", holder_name="l_valk", sleep_value=2),
        APIKey(key="fY2UwuW4uyscBAKx", holder_name="Sweetanimal", sleep_value=2),
        APIKey(key="Fu4EYMR57L0tSIMS", holder_name="Chainimal", sleep_value=2),
        APIKey(key="lQESuISveRhsiDIH", holder_name="An0nymous", sleep_value=2),
        APIKey(key="DexJF6HJwpDn68xN", holder_name="PierogiPirat", sleep_value=2),
    ]

    # Read user IDs from the existing CSV
    user_ids = []
    with open(input_csv, 'r') as infile:
        reader = csv.reader(infile)
        next(reader)  # Skip header row
        for row in reader:
            user_ids.append(row[0])  # Append user ID from the CSV

    # Process the user IDs with multiple API keys
    process_with_multiple_keys(user_ids, api_keys, output_csv)
    print(f"Sorted bazaar data has been written to {output_csv}")

if __name__ == "__main__":
    main()
