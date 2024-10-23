import requests
import time
import csv
from concurrent.futures import ThreadPoolExecutor
import threading

#this step is time consuming and inefficient, but I didnt think to do it all with the inactivity filter and I havent had enough fucks to give to 
#edit that program to do what this one does yet and this one formats it in a way the other one needs to run so yeah

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

# Initialize multiple API keys
api_keys = [
]

BASE_URL = 'https://api.torn.com/user/'
START_ID = 1
END_ID = 3500000  # Ending at 3.5 million

# Create a thread lock for synchronized file writing
file_lock = threading.Lock()

# Function to fetch publicStatus data using a specific APIKey instance
def fetch_public_status(user_id, api_key_obj):
    """Fetches public status for a given user ID from the Torn API using the provided APIKey."""
    url = f'{BASE_URL}{user_id}?selections=publicStatus&key={api_key_obj.key}'
    response = api_key_obj.make_request(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch data for user {user_id}: {response.status_code}")
        return None

# Function to process a range of user IDs for a specific APIKey instance
def check_public_statuses(start_id, end_id, api_key_obj, writer):
    """Checks the public status of users in a given range and writes results immediately to CSV."""
    for user_id in range(start_id, end_id + 1):
        data = fetch_public_status(user_id, api_key_obj)
        if data:
            banned = data.get('banned', False)
            if not banned:
                with file_lock:  # Ensure only one thread writes at a time
                    writer.writerow([user_id])  # Write the user ID to the CSV file immediately
                print(f"User {user_id} written to CSV.")  # Optional: log progress
        time.sleep(api_key_obj.sleep_value)  # Respect rate limit between calls

# Function to distribute work across multiple API keys and save results to CSV
def process_with_multiple_keys(start_id, end_id, api_keys):
    total_users = end_id - start_id + 1
    users_per_key = total_users // len(api_keys)

    with open('active_users.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['User ID'])  # Only store User ID

        # Use ThreadPoolExecutor for parallel processing
        with ThreadPoolExecutor(max_workers=len(api_keys)) as executor:
            futures = []
            for i, api_key in enumerate(api_keys):
                key_start = start_id + i * users_per_key
                key_end = start_id + (i + 1) * users_per_key - 1
                if i == len(api_keys) - 1:
                    key_end = end_id  # Ensure the last key handles the remaining range

                # Submit each API key to handle its range
                futures.append(executor.submit(
                    check_public_statuses, key_start, key_end, api_key, writer
                ))

# Main execution
if __name__ == "__main__":
    process_with_multiple_keys(START_ID, END_ID, api_keys)
