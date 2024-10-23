import requests
import time
import csv
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone, timedelta
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


# Initialize multiple API keys
api_keys = [
    APIKey(key="1CGin0RE5GqcHVsq", holder_name="billysnob", sleep_value=2),
    APIKey(key="eTsKvHBUa84tbulK", holder_name="l_valk", sleep_value=2),
    APIKey(key="fY2UwuW4uyscBAKx", holder_name="Sweetanimal",sleep_value=2),
    APIKey(key="Fu4EYMR57L0tSIMS", holder_name="Chainimal", sleep_value=2),
    APIKey(key="lQESuISveRhsiDIH", holder_name="An0nymous", sleep_value=2),
    APIKey(key="DexJF6HJwpDn68xN", holder_name="PierogiPirat", sleep_value=2),
]

BASE_URL = 'https://api.torn.com/user/'
REQUEST_INTERVAL = 1.5  # Adjust according to Torn API rate limit

# Create a thread lock for synchronized file writing
file_lock = threading.Lock()


# Function to fetch profile data using a specific APIKey instance and extract last_action timestamp
def fetch_last_action(user_id, api_key_obj):
    """Fetches last action timestamp for a given user ID using the profile API."""
    url = f'{BASE_URL}{user_id}?selections=profile&key={api_key_obj.key}'
    response = api_key_obj.make_request(url)

    if response.status_code == 200:
        # Parse the response and extract last action timestamp
        data = response.json()
        last_action = data.get('last_action', {})
        if 'timestamp' in last_action:
            return last_action['timestamp']
        else:
            print(f"No last_action timestamp for user {user_id}")
            return None
    else:
        print(f"Failed to fetch data for user {user_id}: {response.status_code}")
        return None


# Function to check if a user's last action was within the last 40 days
def is_active(last_action_timestamp):
    """Check if the user's last action was within the last 40 days."""
    if last_action_timestamp:
        last_action_time = datetime.fromtimestamp(last_action_timestamp, tz=timezone.utc)
        current_time = datetime.now(timezone.utc)
        time_difference = current_time - last_action_time
        print(
            f"User last action: {last_action_time}, Current time: {current_time}, Difference: {time_difference.days} days")

        return time_difference <= timedelta(days=40)
    return False


# Function to process a list of user IDs for a specific APIKey instance
def check_public_statuses(user_ids, api_key_obj, writer):
    """Checks the public status of a list of user IDs and writes results immediately to CSV."""
    for user_id in user_ids:
        last_action_timestamp = fetch_last_action(user_id, api_key_obj)
        if last_action_timestamp and is_active(last_action_timestamp):
            with file_lock:  # Ensure only one thread writes at a time
                writer.writerow([user_id])  # Write the user ID to the CSV file immediately
            print(f"User {user_id} is active and written to CSV.")  # Optional: log progress
        time.sleep(api_key_obj.sleep_value)  # Respect rate limit between calls


# Function to distribute work across multiple API keys and save results to CSV
def process_with_multiple_keys(user_ids, api_keys):
    total_users = len(user_ids)
    users_per_key = total_users // len(api_keys)

    with open('active_users_filtered.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['User ID'])  # Only store User ID

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
                    check_public_statuses, user_ids_chunk, api_key, writer
                ))


# Main execution
#if __name__ == "__main__":
    # Read user IDs from the existing CSV
    user_ids = []
    with open('active_users.csv', 'r') as infile:
        reader = csv.reader(infile)
        next(reader)  # Skip header
        for row in reader:
            user_ids.append(row[0])  # Append user ID from the CSV

    # Process the user IDs with multiple API keys
    process_with_multiple_keys(user_ids, api_keys)