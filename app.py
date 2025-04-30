from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_session import Session
import math
from datetime import datetime

app = Flask(__name__)

app.config["SECRET_KEY"] = "vijji"
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

#MongoDB setup here
from pymongo import MongoClient
MONGO_URI = "mongodb+srv://vijayadurgakilaru:vijji@expensestracker.bzhfuoy.mongodb.net/?retryWrites=true&w=majority&appName=ExpensesTracker"
client = MongoClient(MONGO_URI)
db = client['ExpensesTracker']
expenses_collection = db['expenses']

#My database loading
from database import users, load_expenses
expenses = load_expenses()
users = {}

@app.route('/')
def index():
    if 'user' not in session:
        return redirect(url_for('login'))

    # Fetch expenses for current user from MongoDB live
    user_expenses = list(expenses_collection.find({'user': session['user']}))

    # Convert the _id field to a string before passing it to the template
    for expense in user_expenses:
        expense['_id'] = str(expense['_id'])

    # Get current page number
    page = int(request.args.get('page', 1))
    per_page = 10

    # Get filter values from request
    subcategory = request.args.get('subcategory')
    category = request.args.get('category')
    category_type = request.args.get('category_type')
    month_number = request.args.get('month_number')
    weekday = request.args.get('weekday')

    # Apply filters if provided
    if subcategory:
        user_expenses = [e for e in user_expenses if e['Sub-category'] == subcategory]
    if category:
        user_expenses = [e for e in user_expenses if e['Category'] == category]
    if category_type:
        user_expenses = [e for e in user_expenses if e['Category Type'] == category_type]
    if month_number:
        user_expenses = [e for e in user_expenses if str(e['Month Number']) == month_number]
    if weekday:
        user_expenses = [e for e in user_expenses if e['Weekday'] == weekday]

    total = len(user_expenses)
    start = (page - 1) * per_page
    end = start + per_page
    paginated_expenses = user_expenses[start:end]
    total_pages = math.ceil(total / per_page)
    page_range_start = max(1, page - 1)
    page_range_end = min(total_pages + 1, page + 2)

    # For filter dropdowns: get unique values
    unique_subcategories = sorted(set(e['Sub-category'] for e in user_expenses))
    unique_categories = sorted(set(e['Category'] for e in user_expenses))
    unique_category_types = sorted(set(e['Category Type'] for e in user_expenses))
    unique_months = sorted(set(e['Month Number'] for e in user_expenses))
    weekday_order = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    unique_weekdays = sorted(set(e['Weekday'] for e in user_expenses), key=lambda x: weekday_order.index(x))

    # Show category limit modal logic
    total_amount_in_category = sum(float(e['Amount']) for e in user_expenses if e['Category'] == 'Food')
    category_limit = 1000
    show_limit_modal = total_amount_in_category > category_limit

    return render_template(
        'index.html',
        expenses=paginated_expenses,
        page=page,
        total_pages=total_pages,
        page_range_start=page_range_start,
        page_range_end=page_range_end,
        show_limit_modal=show_limit_modal,
        unique_subcategories=unique_subcategories,
        unique_categories=unique_categories,
        unique_category_types=unique_category_types,
        unique_months=unique_months,
        unique_weekdays=unique_weekdays
    )


@app.route('/dashboard')
def dashboard():
    expenses = load_expenses()
    
    # Category-wise data
    category_data = {}
    for e in expenses:
        cat = e['Category']
        amt = float(e['Amount'])
        category_data[cat] = category_data.get(cat, 0) + amt

    # Total expenses
    total_expense = sum(category_data.values())

    # Monthly trend data
    monthly_data = {}
    for e in expenses:
        # Try to parse the date with both 'd/m/yy' and 'm/d/yy' formats
        try:
            # Try parsing in 'd/m/yy' format first
            date = datetime.strptime(e['Date'], '%d/%m/%y')
        except ValueError:
            try:
                # If the first fails, try parsing in 'm/d/yy' format
                date = datetime.strptime(e['Date'], '%m/%d/%y')
            except ValueError:
                # Log or handle invalid dates, like skipping or defaulting to a specific value
                print(f"Invalid date format: {e['Date']}")
                continue  # Skip this entry if date is invalid

        month_year = date.strftime('%B %Y')  # Get month and year (e.g., "April 2021")
        amt = float(e['Amount'])
        monthly_data[month_year] = monthly_data.get(month_year, 0) + amt
    
    # Sort months for the trend chart
    sorted_months = sorted(monthly_data.items(), key=lambda x: datetime.strptime(x[0], '%B %Y'))
    monthly_labels = [item[0] for item in sorted_months]
    monthly_values = [item[1] for item in sorted_months]

    # Pass the data to the template
    return render_template("dashboard.html",
                           category_labels=list(category_data.keys()),
                           category_values=list(category_data.values()),
                           total_expense=total_expense,
                           monthly_labels=monthly_labels,
                           monthly_values=monthly_values)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username in users and users[username] == password:
            session['user'] = username
            return redirect(url_for('index'))
        else:
            flash("Invalid login credentials")

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        users[username] = password
        flash("Registration successful! Please log in.")
        return redirect(url_for('login'))

    return render_template('register.html')

CATEGORY_LIMITS = {
    'Living Expenses': 400,
    'Dining Out': 10000,
    'Groceries': 5000,
    'Discretionary': 2000
}

@app.route('/add_expense', methods=['GET', 'POST'])
def add_expense():
    if 'user' not in session:
        return redirect(url_for('login'))

    # Fetch expenses for current user from MongoDB
    user_expenses = list(expenses_collection.find({'user': session['user']}))

    # Calculate total amount for a specific category (example: Food)
    total_amount_in_category = sum(float(e['Amount']) for e in user_expenses if e['Category'] == 'Food')

    # Define a category limit
    category_limit = 1000  # Example limit

    # Check if the category limit is exceeded
    category_limit_exceeded = total_amount_in_category > category_limit

    if request.method == 'POST':
        # Capture form data
        date = request.form['date']
        description = request.form['description']
        debit = float(request.form['debit'])
        credit = float(request.form['credit'])
        subcategory = request.form['subcategory']
        category = request.form['category']
        category_type = request.form['category_type']
        month_number = int(request.form['month_number'])
        weekday = request.form['weekday']
        amount = debit - credit

        # Create the new expense document
        new_expense = {
            'user': session['user'],
            'Date': date,
            'Description': description,
            'Debit': debit,
            'Credit': credit,
            'Sub-category': subcategory,
            'Category': category,
            'Category Type': category_type,
            'Month Number': month_number,
            'Weekday': weekday,
            'Amount': amount
        }

        # Insert into MongoDB
        result = expenses_collection.insert_one(new_expense)
        print(f"Inserted document ID: {result.inserted_id}")

        # Redirect to main page
        return redirect(url_for('index'))

    return render_template('add_expense.html', category_limit_exceeded=category_limit_exceeded)

from bson.objectid import ObjectId

@app.route('/edit_expense/<expense_id>', methods=['GET', 'POST'])
def edit_expense(expense_id):
    if 'user' not in session:
        return redirect(url_for('login'))

    # Fetch the expense from MongoDB
    expense = expenses_collection.find_one({'_id': ObjectId(expense_id), 'user': session['user']})
    if not expense:
        flash("Expense not found.")
        return redirect(url_for('index'))

    category_limit_exceeded = False

    if request.method == 'POST':
        # Get updated data from form
        updated_fields = {
            'Date': request.form['date'],
            'Description': request.form['description'],
            'Debit': float(request.form['debit']),
            'Credit': float(request.form['credit']),
            'Sub-category': request.form['subcategory'],
            'Category': request.form['category'],
            'Category Type': request.form['category_type'],
            'Month Number': int(request.form['month_number']),
            'Weekday': request.form['weekday'],
            'Amount': float(request.form['debit']) - float(request.form['credit'])
        }

        # Check category limit
        category = updated_fields['Category']
        month_number = updated_fields['Month Number']
        new_debit = updated_fields['Debit']

        CATEGORY_LIMITS = {
            'Living Expenses': 400,
            'Dining Out': 10000,
            'Groceries': 5000,
            'Discretionary': 2000
        }

        total_category_debit = sum(
            e['Debit'] for e in expenses_collection.find({
                'user': session['user'],
                'Category': category,
                'Month Number': month_number,
                '_id': {'$ne': ObjectId(expense_id)}
            })
        )

        if category in CATEGORY_LIMITS and total_category_debit + new_debit > CATEGORY_LIMITS[category]:
            category_limit_exceeded = True
            flash(f"You've exceeded the limit for {category} this month!")
            return render_template('edit_expense.html', expense=expense, category_limit_exceeded=category_limit_exceeded)

        # Perform update
        expenses_collection.update_one({'_id': ObjectId(expense_id)}, {'$set': updated_fields})
        flash("Expense updated successfully!")
        return redirect(url_for('index'))

    return render_template('edit_expense.html', expense=expense, category_limit_exceeded=category_limit_exceeded)

@app.route("/delete_expense/<expense_id>")
def delete_expense(expense_id):
    if 'user' not in session:
        return redirect(url_for('login'))

    expenses_collection.delete_one({'_id': ObjectId(expense_id), 'user': session['user']})
    flash("Expense deleted successfully!")
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

print(f"Loaded {len(expenses)} expenses")


if __name__ == '__main__':
    app.run(debug=True)
