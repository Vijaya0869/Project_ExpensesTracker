from flask import Flask, render_template, request, redirect, session, url_for, flash
from bson.objectid import ObjectId
from flask_bcrypt import Bcrypt
import connect  # Importing the connect.py to use the MongoClient setup

app = Flask(__name__)

# Set the secret key for sessions
app.config['SECRET_KEY'] = 'harshi'

# Initialize Flask-Bcrypt
bcrypt = Bcrypt(app)

# Database initialization from connect.py
db = connect.db  # Access the db object from connect.py
collection = db['Data1']  # Reference to the collection you're using

@app.route('/')
def index():
    if 'user' not in session:
        return redirect(url_for('login'))

    # Fetch only 10-15 records from MongoDB for the logged-in user
    user_expenses = collection.find({'user': session['user']}).limit(15)  # Limit to 15 records
    return render_template('index.html', expenses=user_expenses)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Access MongoDB collection using your custom connection
        user = db.users.find_one({'username': username})

        if user and bcrypt.check_password_hash(user['password'], password):
            session['user'] = username
            return redirect(url_for('index'))
        else:
            flash("Invalid login credentials", 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Access MongoDB collection using your custom connection
        user = db.users.find_one({'username': username})

        if user:
            flash('Username already exists!', 'danger')
        else:
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            db.users.insert_one({'username': username, 'password': hashed_password})
            flash('Registration successful!', 'success')
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/add_expense', methods=['GET', 'POST'])
def add_expense():
    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        expense = {
            "user": session['user'],
            "date": request.form['date'],
            "description": request.form['description'],
            "debit": request.form.get('debit', ''),
            "credit": request.form.get('credit', ''),
            "subcategory": request.form['subcategory'],
            "category": request.form['category'],
            "category_type": request.form['category_type'],
            "month_number": request.form['month_number'],
            "weekday": request.form['weekday'],
            "amount": request.form['amount']
        }
        collection.insert_one(expense)
        flash("Expense added successfully!")
        return redirect(url_for('index'))

    return render_template('add_expense.html')

@app.route('/edit_expense/<expense_id>', methods=['GET', 'POST'])
def edit_expense(expense_id):
    if 'user' not in session:
        return redirect(url_for('login'))

    expense = collection.find_one({'_id': ObjectId(expense_id), 'user': session['user']})
    if not expense:
        flash("Expense not found.")
        return redirect(url_for('index'))

    if request.method == 'POST':
        collection.update_one(
            {'_id': ObjectId(expense_id)},
            {'$set': {
                "date": request.form['date'],
                "description": request.form['description'],
                "debit": request.form.get('debit', ''),
                "credit": request.form.get('credit', ''),
                "subcategory": request.form['subcategory'],
                "category": request.form['category'],
                "category_type": request.form['category_type'],
                "month_number": request.form['month_number'],
                "weekday": request.form['weekday'],
                "amount": request.form['amount']
            }}
        )
        flash("Expense updated successfully!")
        return redirect(url_for('index'))

    return render_template('edit_expense.html', expense=expense)

@app.route('/delete_expense/<expense_id>')
def delete_expense(expense_id):
    if 'user' not in session:
        return redirect(url_for('login'))

    # Convert string to ObjectId
    collection.delete_one({'_id': ObjectId(expense_id)})
    flash("Expense deleted successfully!")
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
