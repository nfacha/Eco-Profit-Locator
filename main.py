import json
import os

import requests
import pandas as pd
from dotenv import load_dotenv

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)
pd.set_option('display.max_colwidth', None)

def fetch_data(url):
    response = requests.get(url)
    if response.status_code == 200:
        print("Data fetched successfully.")
        return response.json()
    else:
        print(f"Failed to fetch data: HTTP {response.status_code}")
        return None


def find_profit_opportunities(data, currency_filter, min_profit_per_item):
    if not data or "Stores" not in data:
        print("Invalid or empty data.")
        return []

    print(f"Analyzing opportunities for currency: {currency_filter} with minimum profit: {min_profit_per_item}")
    opportunities = []
    for i, store in enumerate(data["Stores"]):
        if store["CurrencyName"] != currency_filter or not store["Enabled"]:
            print(f"Skipping store {store['Name']} due to currency mismatch or it being disabled.")
            continue
        for j, other_store in enumerate(data["Stores"]):
            if i == j or other_store["CurrencyName"] != currency_filter or not other_store["Enabled"]:
                continue

            for offer in store.get("AllOffers", []):
                if offer["Buying"]:  # Skip if the store is buying, not selling
                    continue
                for other_offer in other_store.get("AllOffers", []):
                    if not other_offer["Buying"]:  # Skip if the other store is selling, not buying
                        continue
                    if offer["ItemName"] == other_offer["ItemName"]:
                        sell_price = other_offer["Price"]
                        buy_price = offer["Price"]
                        profit_per_item = sell_price - buy_price

                        # Determine the maximum quantity that can be sold, taking into account the seller's limit and buyer's maximum wanted
                        seller_limit = offer.get("Limit", float('inf'))  # Assume unlimited if not specified
                        buyer_max_wanted = other_offer.get("MaxNumWanted", float('inf'))  # Assume unlimited if not specified
                        if sell_price == 0:
                            max_sell_quantity = 0
                        else:
                            max_affordable_quantity = other_store["Balance"] // sell_price
                            max_sell_quantity = min(offer["Quantity"], seller_limit, buyer_max_wanted, max_affordable_quantity)

                        total_potential_profit = profit_per_item * max_sell_quantity

                        if buy_price < sell_price and profit_per_item >= min_profit_per_item and max_sell_quantity > 0 and other_store["Balance"] >= sell_price:
                            opportunity = {
                                "BuyFrom": store["Name"],
                                "SellTo": other_store["Name"],
                                "ItemName": offer["ItemName"],
                                "BuyPrice": buy_price,
                                "SellPrice": sell_price,
                                "ProfitPerItem": profit_per_item,
                                "PotentialQuantity": max_sell_quantity,
                                "TotalPotentialProfit": total_potential_profit
                            }
                            opportunities.append(opportunity)
                            print(f"Profit opportunity found: Buy {opportunity['ItemName']} from {opportunity['BuyFrom']} at {opportunity['BuyPrice']} and sell to {opportunity['SellTo']} at {opportunity['SellPrice']}. Profit per item: {opportunity['ProfitPerItem']}. Potential quantity: {opportunity['PotentialQuantity']}, Total potential profit: {opportunity['TotalPotentialProfit']}.")

    if not opportunities:
        print("No opportunities found after analysis.")
    else:
        save_opportunities_to_json(opportunities)

    return opportunities

def save_opportunities_to_json(opportunities, filename='profit_opportunities.json'):
    with open(filename, 'w') as file:
        json.dump(opportunities, file, indent=4)
        print(f"Opportunities saved to {filename}")
def save_opportunities_to_json(opportunities):
    with open('profit_opportunities.json', 'w') as file:
        json.dump(opportunities, file, indent=4)
        print("Opportunities saved to profit_opportunities.json")

def generate_profit_table_from_json(json_file):
    with open(json_file, 'r') as file:
        opportunities = json.load(file)

    # Convert the list of dictionaries to a DataFrame
    df = pd.DataFrame(opportunities)

    # Order the DataFrame by 'TotalPotentialProfit' in descending order
    df_sorted = df.sort_values(by='TotalPotentialProfit', ascending=False)

    # Return the sorted DataFrame
    return df_sorted
if __name__ == "__main__":
    load_dotenv()
    url = os.getenv("URL")
    currency_filter = os.getenv("CURRENCY_FILTER")
    min_profit_per_item = float(os.getenv("MIN_PROFIT_PER_ITEM", 0.01))

    if __name__ == "__main__":
        print(f"URL: {url}")
        print(f"Currency Filter: {currency_filter}")
        print(f"Minimum Profit Per Item: {min_profit_per_item}")
    data = fetch_data(url)
    opportunities = find_profit_opportunities(data, currency_filter, min_profit_per_item)
    if opportunities:
        for opp in opportunities:
            print(f"Buy {opp['ItemName']} from {opp['BuyFrom']} at {opp['BuyPrice']} and sell to {opp['SellTo']} at {opp['SellPrice']} for a profit of {opp['ProfitPerItem']} per item. Potential quantity: {opp['PotentialQuantity']}.")
    else:
        print("No profit opportunities found.")
    json_file = 'profit_opportunities.json'
    profit_table = generate_profit_table_from_json(json_file)
    print(profit_table)
