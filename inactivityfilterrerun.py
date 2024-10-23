import requests
import time
import csv
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone, timedelta
import threading
import tkinter as tk


# APIKey class to manage key usage and rate limiting
class APIKey:
    def __init__(self, key, holder_name, sleep_value, call_number=0):
        """Initialize an API key with holder's name, sleep value, and call number."""
        self.key = key
        self.holder_name = holder_name
        self.sleep_value = sleep_value
        self.call_number = call_number

    def make_request(self, url):
        """Make an API request and apply sleep to respect the rate limit."""
        print(f"Making request with API key {self.key} (Holder: {self.holder_name})")
        response = requests.get(url)
        time.sleep(self.sleep_value)
        self.call_number += 1
        return response


# Initialize multiple API keys
api_keys = [
    APIKey(key="1CGin0RE5GqcHVsq", holder_name="billysnob", sleep_value=1.75),
    APIKey(key="eTsKvHBUa84tbulK", holder_name="l_valk", sleep_value=2),
    APIKey(key="fY2UwuW4uyscBAKx", holder_name="Sweetanimal", sleep_value=2),
    APIKey(key="Fu4EYMR57L0tSIMS", holder_name="Chainimal", sleep_value=2),
    APIKey(key="lQESuISveRhsiDIH", holder_name="An0nymous", sleep_value=2),
    APIKey(key="DexJF6HJwpDn68xN", holder_name="PierogiPirat", sleep_value=2),
    APIKey(key="AUVOHQHESSuonfjF", holder_name="Bhudda_Ghost", sleep_value=2),
    APIKey(key="Q1hIvWxom8Xa3dff", holder_name="3Ddas", sleep_value=2),

]

BASE_URL = 'https://api.torn.com/user/'
ONE_YEAR_DAYS = 365

file_lock = threading.Lock()
data_lock = threading.Lock()

# Tkinter GUI setup
root = tk.Tk()
root.title("User Processing Progress")

# Progress variables
total_processed_var = tk.IntVar()
blacklisted_var = tk.IntVar()
inactive_var = tk.IntVar()

# Internal counters (thread-safe updates)
total_processed_count = 0
blacklisted_count = 0
inactive_count = 0

# Labels to display progress
total_processed_label = tk.Label(root, text="Total Processed: 0")
total_processed_label.pack()

blacklisted_label = tk.Label(root, text="Blacklisted: 0")
blacklisted_label.pack()

inactive_label = tk.Label(root, text="Inactive: 0")
inactive_label.pack()


# Function to update the GUI from the internal thread-safe counters
def update_display():
    with data_lock:  # Ensure data consistency
        total_processed_var.set(total_processed_count)
        blacklisted_var.set(blacklisted_count)
        inactive_var.set(inactive_count)

    total_processed_label.config(text=f"Total Processed: {total_processed_var.get()}")
    blacklisted_label.config(text=f"Blacklisted: {blacklisted_var.get()}")
    inactive_label.config(text=f"Inactive: {inactive_var.get()}")

    root.update_idletasks()  # Refresh the display
    root.after(2000, update_display)  # Schedule to update again in 2 seconds


# Fetch profile data and extract last_action timestamp
def fetch_last_action(user_id, api_key_obj):
    url = f'{BASE_URL}{user_id}?selections=profile&key={api_key_obj.key}'
    response = api_key_obj.make_request(url)
    if response.status_code == 200:
        data = response.json()
        last_action = data.get('last_action', {})
        if 'timestamp' in last_action:
            return last_action['timestamp']
        elif 'relative' in last_action:
            print(f"User {user_id} has no exact timestamp, but their last action was {last_action['relative']}.")
            return None  # Handle this case differently if needed
        else:
            print(f"No last_action available for user {user_id}")
            return None
    else:
        print(f"Failed to fetch data for user {user_id}: {response.status_code}")
        return None



# Check if a user's last action was within the last 40 days
def is_active(last_action_timestamp):
    if last_action_timestamp:
        last_action_time = datetime.fromtimestamp(last_action_timestamp, tz=timezone.utc)
        current_time = datetime.now(timezone.utc)
        time_difference = current_time - last_action_time
        return time_difference <= timedelta(days=40)
    return False


# Load processed users from CSV
def load_processed_users(csv_file):
    processed_users = {}
    try:
        with open(csv_file, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                user_id = int(row['User ID'])
                last_action_timestamp = int(row['Last Action Timestamp']) if row['Last Action Timestamp'] else None
                processed_users[user_id] = last_action_timestamp
    except FileNotFoundError:
        print(f"{csv_file} not found. Starting fresh.")
    return processed_users


# Load blacklist of users with missing timestamps
def load_blacklist(csv_file):
    blacklist = set()
    try:
        with open(csv_file, 'r') as file:
            reader = csv.reader(file)
            for row in reader:
                if row:
                    blacklist.add(int(row[0]))
    except FileNotFoundError:
        print(f"{csv_file} not found. Starting fresh.")
    return blacklist


def load_recently_checked(csv_file):
    """Load recently checked inactive users from the CSV file."""
    recently_checked = set()
    try:
        with open(csv_file, 'r') as file:
            reader = csv.reader(file)
            for row in reader:
                if row:
                    recently_checked.add(int(row[0]))
    except FileNotFoundError:
        print(f"{csv_file} not found. Starting fresh.")
    return recently_checked

def save_recently_checked(recently_checked, csv_file):
    """Save the recently checked inactive users to a CSV file."""
    with open(csv_file, 'w', newline='') as file:
        writer = csv.writer(file)
        for user_id in recently_checked:
            writer.writerow([user_id])


def save_blacklist(blacklist, csv_file):
    """Save the blacklist of users to a CSV file."""
    with open(csv_file, 'w', newline='') as file:
        writer = csv.writer(file)
        for user_id in blacklist.copy():  # Iterate over a copy of the set
            writer.writerow([user_id])



# Process a list of user IDs for a specific APIKey
def check_public_statuses(user_ids, api_key_obj, writer, processed_users, blacklist, recently_checked, csvfile,
                          total_users):
    global total_processed_count, blacklisted_count, inactive_count

    for user_id in user_ids:
        if user_id in processed_users:
            print(f"User {user_id} already processed. Skipping.")
            continue

        if user_id in blacklist:
            print(f"User {user_id} is blacklisted. Skipping.")
            with data_lock:
                blacklisted_count += 1
            continue

        if user_id in recently_checked:
            print(f"User {user_id} was recently checked and is inactive. Skipping.")
            continue

        last_action_timestamp = fetch_last_action(user_id, api_key_obj)
        if last_action_timestamp is None:
            print(f"User {user_id} has no available timestamp. Adding to blacklist.")
            blacklist.add(user_id)
            save_blacklist(blacklist, 'blacklist.csv')
            with data_lock:
                blacklisted_count += 1
            continue

        if is_active(last_action_timestamp):
            with file_lock:
                writer.writerow([user_id, last_action_timestamp])
                csvfile.flush()
            print(f"User {user_id} is active and written to CSV.")
        else:
            with data_lock:
                inactive_count += 1
                recently_checked.add(user_id)  # Add to recently checked list
                save_recently_checked(recently_checked, 'recently_checked.csv')  # Save the recently checked list
            print(f"User {user_id} is not active.")

        with data_lock:
            total_processed_count += 1

        time.sleep(api_key_obj.sleep_value)


def process_with_multiple_keys(user_ids, api_keys, processed_users, blacklist, recently_checked):
    total_users = len(user_ids)
    users_per_key = total_users // len(api_keys)

    with open('active_users_filtered.csv', 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        if csvfile.tell() == 0:
            writer.writerow(['User ID', 'Last Action Timestamp'])

        with ThreadPoolExecutor(max_workers=len(api_keys)) as executor:
            futures = []
            for i, api_key in enumerate(api_keys):
                start_idx = i * users_per_key
                end_idx = (i + 1) * users_per_key
                if i == len(api_keys) - 1:
                    end_idx = total_users

                user_ids_chunk = user_ids[start_idx:end_idx]
                futures.append(executor.submit(
                    check_public_statuses, user_ids_chunk, api_key, writer, processed_users, blacklist, recently_checked, csvfile, total_users
                ))

            for future in futures:
                future.result()  # Ensure we catch any exceptions



# Main execution
# Main execution
if __name__ == "__main__":
    processed_users = load_processed_users('active_users_filtered.csv')
    blacklist = load_blacklist('blacklist.csv')
    recently_checked = load_recently_checked('recently_checked.csv')  # Load the recently checked users

    user_ids = []
    with open('active_users.csv', 'r') as infile:
        reader = csv.reader(infile)
        next(reader)
        for row in reader:
            user_ids.append(int(row[0]))

    def threaded_processing():
        process_with_multiple_keys(user_ids, api_keys, processed_users, blacklist, recently_checked)

    # Start the periodic GUI update
    root.after(2000, update_display)  # Update the display every 2 seconds

    # Start processing in a background thread
    threading.Thread(target=threaded_processing).start()

    # Start the Tkinter event loop
    root.mainloop()

    # Save the recently checked list at the end
    save_recently_checked(recently_checked, 'recently_checked.csv')
