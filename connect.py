from pymongo import MongoClient

# MongoDB connection string with the correct credentials
connection_string = "mongodb+srv://vijayadurgakilaru:vijji@expensestracker.bzhfuoy.mongodb.net/?retryWrites=true&w=majority&appName=ExpensesTracker"

# Connect to MongoDB
client = MongoClient(connection_string)

# Access the "Expense_data" database
db = client.Expense_data

# Access the "Data1" collection
collection = db.Data1

# Example: Fetch all documents from the "Data1" collection
documents = collection.find()

# Print all documents in the collection
for doc in documents:
    print(doc)
