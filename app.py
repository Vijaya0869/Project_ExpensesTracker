from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_session import Session
import math

app = Flask(__name__)

app.config["SECRET_KEY"] = "vijji"
app.config["SESSION_TYPE"] = "filesystem"

Session(app)

from database import users, load_expenses
expenses = load_expenses()
users = {}

@app.route('/')
def index():
    if 'user' not in session:
        return redirect(url_for('login'))

    # Get current page number
    page = int(request.args.get('page', 1))
    per_page = 10

    # Initial filtered list
    user_expenses = [e for e in expenses if e['user'] == session['user']]

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
    unique_subcategories = sorted(set(e['Sub-category'] for e in expenses if e['user'] == session['user']))
    unique_categories = sorted(set(e['Category'] for e in expenses if e['user'] == session['user']))
    unique_category_types = sorted(set(e['Category Type'] for e in expenses if e['user'] == session['user']))
    unique_months = sorted(set(e['Month Number'] for e in expenses))
    weekday_order = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    unique_weekdays = sorted(set(e['Weekday'] for e in expenses), key=lambda x: weekday_order.index(x))

    # Show category limit modal logic (same as before)
    total_amount_in_category = sum(e['Amount'] for e in user_expenses if e['Category'] == 'Food')
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

@app.route('/add_expense', methods=['GET', 'POST'])
def add_expense():
    if 'user' not in session:
        return redirect(url_for('login'))

    # Define category limits
    CATEGORY_LIMITS = {
        'Dining Out': 10000,
        'Groceries': 5000,
        'Discretionary': 2000  # Added discretionary category with limit
    }

    if request.method == 'POST':
        category = request.form['category']
        debit = float(request.form['debit'])
        month_number = int(request.form['month_number'])

        # Calculate the total debit for the selected category in the current month
        total_debit = sum(e['Debit'] for e in expenses if e['Category'] == category and e['Month Number'] == month_number)

        # Add the new expense debit to the total debit
        total_debit += debit

        # Check if the total debit exceeds the category limit
        if category in CATEGORY_LIMITS and total_debit > CATEGORY_LIMITS[category]:
            flash(f"You've exceeded the limit for {category} this month!")
            return render_template('add_expense.html', category_limit_exceeded=True, category=category, debit=debit, category_type=request.form['category_type'])

        # Add the expense to the list (or update the database, etc.)
        expenses.append({
            "Date": request.form['date'],
            "Description": request.form['description'],
            "Debit": debit,
            "Credit": request.form.get('credit', ''),
            "Sub-category": request.form['subcategory'],
            "Category": category,
            "Category Type": request.form['category_type'],
            "Month Number": month_number,
            "Weekday": request.form['weekday'],
            "Amount": request.form['amount'],  # Keep amount for reference
            "user": session['user']
        })
        flash("Expense added successfully!")
        return redirect(url_for('index'))

    return render_template('add_expense.html', category_limit_exceeded=False)


@app.route('/edit_expense/<int:expense_id>', methods=['GET', 'POST'])
def edit_expense(expense_id):
    if 'user' not in session:
        return redirect(url_for('login'))

    expense = next((e for e in expenses if e['id'] == expense_id and e['user'] == session['user']), None)
    if not expense:
        flash("Expense not found.")
        return redirect(url_for('index'))

    # Define category limits
    CATEGORY_LIMITS = {
        'Dining Out': 10000,
        'Groceries': 5000,
        'Discretionary': 2000  # Added discretionary category with limit
    }

    if request.method == 'POST':
        category = request.form['category']
        debit = float(request.form['debit'])
        month_number = int(request.form['month_number'])

        # Calculate the total debit for the selected category in the current month, excluding the current expense
        # Correcting the type conversion issue by ensuring 'Debit' is treated as a number (float)
        total_debit = sum(float(e['Debit']) for e in expenses if e['Category'] == category and e['Month Number'] == month_number) - float(expense['Debit'])

        # Add the updated debit to the total debit
        total_debit += debit

        # Check if the total debit exceeds the category limit
        if category in CATEGORY_LIMITS and total_debit > CATEGORY_LIMITS[category]:
            flash(f"You've exceeded the limit for {category} this month!")
            return render_template('edit_expense.html', expense=expense, category_limit_exceeded=True, category=category, debit=debit, category_type=request.form['category_type'])

        # Update the expense details
        expense.update({
            "Date": request.form['date'],
            "Description": request.form['description'],
            "Debit": debit,
            "Credit": request.form.get('credit', ''),
            "Sub-category": request.form['subcategory'],
            "Category": category,
            "Category Type": request.form['category_type'],
            "Month Number": month_number,
            "Weekday": request.form['weekday'],
            "Amount": request.form['amount']  # Keep amount for reference
        })

        flash("Expense updated successfully!")
        return redirect(url_for('index'))

    return render_template('edit_expense.html', expense=expense, category_limit_exceeded=False)

@app.route('/delete_expense/<int:expense_id>')
def delete_expense(expense_id):
    if 'user' not in session:
        return redirect(url_for('login'))

    global expenses
    expenses = [e for e in expenses if not (e['id'] == expense_id and e['user'] == session['user'])]
    flash("Expense deleted successfully!")
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

print(f"Loaded {len(expenses)} expenses")


if __name__ == '__main__':
    app.run(debug=True)