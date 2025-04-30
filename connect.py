import json
from pymongo import MongoClient

# Connect to MongoDB Atlas
MONGO_URI = "mongodb+srv://vijayadurgakilaru:vijji@expensestracker.bzhfuoy.mongodb.net/?retryWrites=true&w=majority&appName=ExpensesTracker"
client = MongoClient(MONGO_URI)

# Choose the database and collection
db = client['ExpensesTracker']
expenses_collection = db['expenses']

# Read your JSON file
with open('expenses_data.json', 'r') as file:
    expenses = json.load(file)

# Insert into MongoDB (if collection is empty)
if expenses_collection.count_documents({}) == 0:
    expenses_collection.insert_many(expenses)
    print("✅ Expenses inserted successfully!")
else:
    print("⚠️ Collection already has data. Skipping insert.")
