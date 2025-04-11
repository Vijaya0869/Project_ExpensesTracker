from pymongo import MongoClient

# MongoDB connection string with the correct credentials (MongoDB Atlas)
connection_string = "mongodb+srv://sadineniharshitha07:harshi@cluster0.wddsxwj.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

client = MongoClient(connection_string)  # Connect to MongoDB Atlas
db = client['Expense']  # Database name
collection = db['Data1']  # Collection name
