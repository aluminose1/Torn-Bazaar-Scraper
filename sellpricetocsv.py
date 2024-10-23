import tkinter as tk
from tkinter import messagebox
import csv
import os


# Function to save the input to CSV
def save_to_csv():
    item_name = item_name_entry.get()
    sell_price = price_entry.get()

    if not item_name or not sell_price:
        messagebox.showerror("Input Error", "Please enter both item name and price.")
        return

    try:
        sell_price = float(sell_price)
    except ValueError:
        messagebox.showerror("Input Error", "Please enter a valid price.")
        return

    file_exists = os.path.isfile('items.csv')

    # Append data to the CSV file
    with open('items.csv', 'a', newline='') as csvfile:
        fieldnames = ['Item Name', 'Sell Price']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()  # Write header only if file is new

        writer.writerow({'Item Name': item_name, 'Sell Price': sell_price})

    # Show success message
    messagebox.showinfo("Success", f"Item '{item_name}' with price '{sell_price}' saved!")

    # Clear input fields
    item_name_entry.delete(0, tk.END)
    price_entry.delete(0, tk.END)


# Function to close the window
def close_window():
    root.destroy()


# Create the main window
root = tk.Tk()
root.title("Item Sell Price Input")

# Create and place labels and entry fields
tk.Label(root, text="Item Name:").grid(row=0, column=0, padx=10, pady=5)
item_name_entry = tk.Entry(root)
item_name_entry.grid(row=0, column=1, padx=10, pady=5)

tk.Label(root, text="Sell Price:").grid(row=1, column=0, padx=10, pady=5)
price_entry = tk.Entry(root)
price_entry.grid(row=1, column=1, padx=10, pady=5)

# Create buttons to save item and price
save_button = tk.Button(root, text="Save Item", command=save_to_csv)
save_button.grid(row=2, column=0, columnspan=2, pady=10)

# Create a close button
close_button = tk.Button(root, text="Close", command=close_window)
close_button.grid(row=3, column=0, columnspan=2, pady=5)

# Run the main loop
root.mainloop()
