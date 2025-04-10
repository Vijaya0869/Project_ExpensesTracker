import json

# This could be replaced with actual user authentication logic
users = {
    "demo": "password123"  # default demo user
}

# Load expenses from the JSON file
def load_expenses(filepath='expenses_data.json', username="demo"):
    with open(filepath, "r") as file:
        raw_data = json.load(file)

    expenses = []
    for idx, entry in enumerate(raw_data, start=1):
        entry['id'] = idx
        entry['user'] = username
        expenses.append(entry)

    return expenses

