import csv
import requests
import time
from concurrent.futures import ThreadPoolExecutor
import threading
import tkinter as tk


# APIKey class to manage key usage and rate limiting
class APIKey:
    def __init__(self, key, holder_name, calls_per_minute=60):
        """Initialize an API key with holder's name and calls per minute."""
        self.key = key
        self.holder_name = holder_name
        self.calls_per_minute = calls_per_minute

        # Calculate sleep value based on calls_per_minute
        self.sleep_value = 60 / self.calls_per_minute
        self.call_number = 0  # Tracks the number of calls made with this key

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
def fetch_and_write_bazaar_data(user_ids, api_key_obj, writer, output_file, progress_var, total_users):
    for user_id in user_ids:
        url = BAZAAR_URL.format(user_id=user_id, api_key=api_key_obj.key)
        response = api_key_obj.make_request(url)
        if response.status_code == 200:
            try:
                data = response.json()

                # Check if the 'bazaar' field is a list or a dictionary
                bazaar_data = data.get('bazaar')

                if isinstance(bazaar_data, list):
                    # Handle bazaar as a list
                    if len(bazaar_data) > 0:
                        with file_lock:  # Ensure only one thread writes at a time
                            for item in bazaar_data:
                                writer.writerow({
                                    'player_id': user_id,
                                    'item_name': item['name'],
                                    'price': item['price'],
                                    'quantity': item['quantity']
                                })
                                print(f"User {user_id}: Added item {item['name']} to CSV.")
                            output_file.flush()  # Force data to be written immediately
                    else:
                        print(f"User {user_id} has a bazaar but no items listed.")
                elif isinstance(bazaar_data, dict):
                    # Handle bazaar as a dictionary (if it ever returns this way)
                    with file_lock:  # Ensure only one thread writes at a time
                        for item_id, item_info in bazaar_data.items():
                            writer.writerow({
                                'player_id': user_id,
                                'item_name': item_info['name'],
                                'price': item_info['price'],
                                'quantity': item_info['quantity']
                            })
                            print(f"User {user_id}: Added item {item_info['name']} to CSV.")
                        output_file.flush()  # Force data to be written immediately
                else:
                    print(f"User {user_id}: Bazaar is of unexpected type {type(bazaar_data)}. Skipping.")

            except Exception as e:
                print(f"Error processing bazaar for user {user_id}: {e}")
        else:
            print(f"Failed to fetch bazaar data for user {user_id}. Status code: {response.status_code}")

        # Update the progress
        with file_lock:
            progress_var.set(progress_var.get() + 1)


# Function to distribute work across multiple API keys and save results to CSV
def process_with_multiple_keys(user_ids, api_keys, writer, output_file, progress_var):
    total_users = len(user_ids)
    users_per_key = total_users // len(api_keys)

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
                fetch_and_write_bazaar_data, user_ids_chunk, api_key, writer, output_file, progress_var, total_users
            ))

        # Wait for all threads to complete
        for future in futures:
            future.result()


# Function to start processing in the background
def start_processing(user_ids, api_keys, writer, output_file, progress_var):
    threading.Thread(target=process_with_multiple_keys,
                     args=(user_ids, api_keys, writer, output_file, progress_var)).start()


# Main function to run the entire process
def main():
    input_csv = 'active_users_filtered.csv'  # The input CSV with user IDs
    output_csv = 'sorted_bazaars.csv'  # The output CSV with sorted bazaar data

    # Create the Tkinter root window
    root = tk.Tk()
    root.title("Bazaar Search Progress")

    # Create a progress variable
    total_users = len(open(input_csv).readlines()) - 1  # Subtract header
    progress_var = tk.IntVar(value=0)

    # Create progress display labels
    progress_label = tk.Label(root, text=f"Bazaars searched: 0 of {total_users}")
    progress_label.pack()

    # Function to update the label dynamically
    def update_label():
        progress_label.config(text=f"Bazaars searched: {progress_var.get()} of {total_users}")
        root.after(1000, update_label)  # Refresh the label every 1 second

    update_label()  # Start updating the label

    # API keys
    api_keys = [
        APIKey(key="1CGin0RE5GqcHVsq", holder_name="billysnob", calls_per_minute=60),
        APIKey(key="eTsKvHBUa84tbulK", holder_name="l_valk", calls_per_minute=50),
        APIKey(key="fY2UwuW4uyscBAKx", holder_name="Sweetanimal", calls_per_minute=50),
        APIKey(key="Fu4EYMR57L0tSIMS", holder_name="Chainimal", calls_per_minute=50),
        APIKey(key="lQESuISveRhsiDIH", holder_name="An0nymous", calls_per_minute=50),
        APIKey(key="DexJF6HJwpDn68xN", holder_name="PierogiPirat", calls_per_minute=50),
        APIKey(key="AUVOHQHESSuonfjF", holder_name="Bhudda_Ghost", calls_per_minute=50),
        APIKey(key="Q1hIvWxom8Xa3dff", holder_name="3Ddas", calls_per_minute=50),
        APIKey(key="izR3QEtOtnU54ww3", holder_name="JessicaAnn", calls_per_minute=50),
        APIKey(key="6kH8fvS2upXJtMEV", holder_name="RepoMan", calls_per_minute=50),
        APIKey(key="5zIbX9LSwI1G4uVv", holder_name="Drilla", calls_per_minute=50),
        APIKey(key="BsqM9RlJSh5NOOH3", holder_name="i9i", calls_per_minute=50),
        APIKey(key="V7n8LmtqBqD3sO8w", holder_name="fatcow", calls_per_minute=50),
        APIKey(key="KSt1ZcoXJkMASXZ7", holder_name="KingDarius", calls_per_minute=50),
    ]

    # Open CSV for writing data in real-time
    with open(output_csv, 'w', newline='') as output_file:
        writer = csv.DictWriter(output_file, fieldnames=['player_id', 'item_name', 'price', 'quantity'])
        writer.writeheader()

        # Read user IDs from the existing CSV
        user_ids = []
        with open(input_csv, 'r') as infile:
            reader = csv.reader(infile)
            next(reader)  # Skip header row
            for row in reader:
                user_ids.append(row[0])  # Append user ID from the CSV

        # Start background processing
        start_processing(user_ids, api_keys, writer, output_file, progress_var)

        # Start Tkinter mainloop
        root.mainloop()


if __name__ == "__main__":
    main()
