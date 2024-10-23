import csv


# Function to load user input data from a CSV (containing sell prices)
def load_user_input(user_input_csv):
    user_sell_prices = {}
    with open(user_input_csv, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            item_name = row['Item Name'].lower()  # Ensure matching is case-insensitive
            sell_price = float(row['Sell Price'])
            user_sell_prices[item_name] = sell_price
    return user_sell_prices


# Function to cross-reference the bazaars and find the most profitable items
def find_profitable_items(user_sell_prices, sorted_bazaars_csv):
    profitable_items = []

    # Open and read the sorted_bazaars CSV
    with open(sorted_bazaars_csv, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            item_name = row['item_name'].lower()
            if item_name in user_sell_prices:
                sell_price = user_sell_prices[item_name]  # User's target sell price
                try:
                    buy_price = float(row['price'])
                    quantity = int(row['quantity'])

                    # Filter out price-locked items at $1
                    if buy_price <= 1:
                        continue

                    # Calculate profitability
                    if sell_price > buy_price:
                        profit_per_item = sell_price - buy_price
                        total_profit = profit_per_item * quantity

                        # Generate bazaar link
                        player_id = row['player_id']
                        bazaar_link = f"https://www.torn.com/bazaar.php?userID={player_id}"

                        profitable_items.append({
                            'player_id': player_id,
                            'item_name': row['item_name'],
                            'buy_price': buy_price,
                            'sell_price': sell_price,
                            'quantity': quantity,
                            'total_profit': total_profit,
                            'bazaar_link': bazaar_link
                        })
                except ValueError:
                    continue  # Skip rows with conversion issues

    return profitable_items


# Function to sort and display the most profitable items
def display_most_profitable(profitable_items):
    # Sort by total profit in descending order
    profitable_items.sort(key=lambda x: x['total_profit'], reverse=True)

    print(f"Most Profitable Items:")
    for item in profitable_items:
        print(f"{item['player_id']}, {item['item_name']}, "
              f"Buy: ${item['buy_price']}, Sell: ${item['sell_price']}, "
              f"Quantity: {item['quantity']},  Profit: {item['total_profit']:.2f}, "
              f"Bazaar Link: {item['bazaar_link']}")


# Main function to orchestrate the process
def main():
    user_input_csv = 'items.csv'  # CSV with user's sell prices
    sorted_bazaars_csv = 'sorted_bazaars.csv'  # CSV with bazaar data

    # Load user input data
    user_sell_prices = load_user_input(user_input_csv)

    # Find profitable items by cross-referencing the bazaar data
    profitable_items = find_profitable_items(user_sell_prices, sorted_bazaars_csv)

    # Display the most profitable items
    display_most_profitable(profitable_items)


if __name__ == "__main__":
    main()
