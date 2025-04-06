from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_session import Session

app = Flask(__name__)

app.config["SECRET_KEY"] = "vijji"
app.config["SESSION_TYPE"] = "filesystem"

Session(app)

# In-memory data for demo purposes
users = {}
expenses = []

@app.route('/')
def index():
    if 'user' not in session:
        return redirect(url_for('login'))

    # Filter expenses for the logged-in user
    user_expenses = [e for e in expenses if e['user'] == session['user']]
    return render_template('index.html', expenses=user_expenses)

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

    if request.method == 'POST':
        expense = {
            "id": len(expenses) + 1,
            "user": session['user'],
            "Date": request.form['date'],
            "Description": request.form['description'],
            "Debit": request.form.get('debit', ''),
            "Credit": request.form.get('credit', ''),
            "Sub-category": request.form['subcategory'],
            "Category": request.form['category'],
            "Category Type": request.form['category_type'],
            "Month Number": request.form['month_number'],
            "Weekday": request.form['weekday'],
            "Amount": request.form['amount']
        }
        expenses.append(expense)
        flash("Expense added successfully!")
        return redirect(url_for('index'))

    return render_template('add_expense.html')

@app.route('/edit_expense/<int:expense_id>', methods=['GET', 'POST'])
def edit_expense(expense_id):
    if 'user' not in session:
        return redirect(url_for('login'))

    expense = next((e for e in expenses if e['id'] == expense_id and e['user'] == session['user']), None)
    if not expense:
        flash("Expense not found.")
        return redirect(url_for('index'))

    if request.method == 'POST':
        expense.update({
            "Date": request.form['date'],
            "Description": request.form['description'],
            "Debit": request.form.get('debit', ''),
            "Credit": request.form.get('credit', ''),
            "Sub-category": request.form['subcategory'],
            "Category": request.form['category'],
            "Category Type": request.form['category_type'],
            "Month Number": request.form['month_number'],
            "Weekday": request.form['weekday'],
            "Amount": request.form['amount']
        })
        flash("Expense updated successfully!")
        return redirect(url_for('index'))

    return render_template('edit_expense.html', expense=expense)

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

if __name__ == '__main__':
    app.run(debug=True)