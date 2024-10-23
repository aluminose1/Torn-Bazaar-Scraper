import requests
import time
import csv
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone, timedelta
import threading
import tkinter as tk


# APIKey class to manage key usage and rate limiting
class APIKey:
    def __init__(self, key, holder_name, calls_per_minute):
        self.key = key
        self.holder_name = holder_name
        self.sleep_value = 60 / calls_per_minute

    def make_request(self, url):
        response = requests.get(url)
        time.sleep(self.sleep_value)  # Sleep based on the API rate limit
        return response


def load_csv_to_set(csv_file):
    """Utility function to load user IDs from a CSV file into a set."""
    user_set = set()
    try:
        with open(csv_file, 'r') as file:
            reader = csv.reader(file)
            next(reader)  # Skip the header row
            for row in reader:
                if row and row[0].isdigit():  # Ensure it's a number
                    user_set.add(int(row[0]))
    except FileNotFoundError:
        print(f"{csv_file} not found. Starting fresh.")
    return user_set


def save_set_to_csv(data_set, csv_file):
    with open(csv_file, 'w', newline='') as file:
        csv.writer(file).writerows([[user_id] for user_id in data_set])


# Fetch last action timestamp from API
def fetch_last_action(user_id, api_key_obj):
    url = f'https://api.torn.com/user/{user_id}?selections=profile&key={api_key_obj.key}'
    response = api_key_obj.make_request(url)
    if response.status_code == 200:
        return response.json().get('last_action', {}).get('timestamp')
    return None


# Check if the last action is within 40 days
def is_active(last_action_timestamp):
    if last_action_timestamp:
        last_action_time = datetime.fromtimestamp(last_action_timestamp, tz=timezone.utc)
        return (datetime.now(timezone.utc) - last_action_time).days <= 40
    return False


# Process a batch of user IDs
def process_users(user_ids, api_key_obj, writer, processed_users, blacklist, recently_checked, csvfile):
    for user_id in user_ids:
        if user_id in processed_users or user_id in blacklist or user_id in recently_checked:
            continue

        last_action = fetch_last_action(user_id, api_key_obj)
        if last_action is None:
            blacklist.add(user_id)
            save_set_to_csv(blacklist, 'blacklist.csv')
        elif is_active(last_action):
            writer.writerow([user_id, last_action])
            csvfile.flush()
        else:
            recently_checked.add(user_id)
            save_set_to_csv(recently_checked, 'recently_checked.csv')


# Handle multi-threaded API processing
def process_with_multiple_keys(user_ids, api_keys, processed_users, blacklist, recently_checked):
    # Convert set to list for slicing
    user_ids_list = list(user_ids)  # Convert the set to a list here
    users_per_key = len(user_ids_list) // len(api_keys)

    with open('active_users_filtered.csv', 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        if csvfile.tell() == 0:  # Write the header only if the file is new
            writer.writerow(['User ID', 'Last Action Timestamp'])

        with ThreadPoolExecutor(max_workers=len(api_keys)) as executor:
            futures = [
                executor.submit(
                    process_users, user_ids_list[i * users_per_key: (i + 1) * users_per_key],
                    api_key, writer, processed_users, blacklist, recently_checked, csvfile
                ) for i, api_key in enumerate(api_keys)
            ]
            for future in futures:
                future.result()


# Tkinter display updater
def update_display():
    total_processed_label.config(text=f"Processed: {len(processed_users)}")
    blacklisted_label.config(text=f"Blacklisted: {len(blacklist)}")
    inactive_label.config(text=f"Inactive: {len(recently_checked)}")
    root.after(2000, update_display)


# Main program
if __name__ == "__main__":
    # Load data
    processed_users = load_csv_to_set('active_users_filtered.csv')
    blacklist = load_csv_to_set('blacklist.csv')
    recently_checked = load_csv_to_set('recently_checked.csv')

    user_ids = load_csv_to_set('active_users.csv')

    # Declare the API keys before processing
    api_keys = [
        APIKey(key="1CGin0RE5GqcHVsq", holder_name="billysnob", calls_per_minute=60),
        APIKey(key="eTsKvHBUa84tbulK", holder_name="l_valk", calls_per_minute=50),
        # Add more API keys as needed
    ]

    # Tkinter setup
    root = tk.Tk()
    root.title("Progress Tracker")
    total_processed_label = tk.Label(root, text="Processed: 0")
    total_processed_label.pack()
    blacklisted_label = tk.Label(root, text="Blacklisted: 0")
    blacklisted_label.pack()
    inactive_label = tk.Label(root, text="Inactive: 0")
    inactive_label.pack()

    # Start the GUI and background processing
    threading.Thread(target=lambda: process_with_multiple_keys(
        user_ids, api_keys, processed_users, blacklist, recently_checked)).start()

    root.after(2000, update_display)
    root.mainloop()
