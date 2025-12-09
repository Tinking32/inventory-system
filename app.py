from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

# --- 1. App Configuration & Initialization ---
app = Flask(__name__)
# Database configuration: using a local SQLite file named inventory.db
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database extension
db = SQLAlchemy(app)

# --- 2. Database Model Definition ---
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)

# --- 3. Routes (Controller Logic) ---

# [Route 1] Home Page (Dashboard) with Search & Sort
@app.route('/')
def index():
    # 1. Get query parameters from URL
    q = request.args.get('q')              # Search keyword
    sort_by = request.args.get('sort', 'id') # Sort column (default: id)
    order = request.args.get('order', 'asc') # Sort order (default: asc)

    # 2. Start building the query
    query = Product.query

    # 3. Apply Search Filter if keyword exists
    if q:
        # Filter products where name contains the keyword
        query = query.filter(Product.name.contains(q))

    # 4. Apply Sorting Logic
    if sort_by == 'quantity':
        if order == 'asc':
            query = query.order_by(Product.quantity.asc())
        else:
            query = query.order_by(Product.quantity.desc())
    elif sort_by == 'price':
        if order == 'asc':
            query = query.order_by(Product.price.asc())
        else:
            query = query.order_by(Product.price.desc())
    else:
        # Default sort by ID
        if order == 'asc':
            query = query.order_by(Product.id.asc())
        else:
            query = query.order_by(Product.id.desc())

    # 5. Execute the query to get results
    items = query.all()

    # 6. Render the template
    return render_template('index.html', items=items, sort_by=sort_by, order=order)

# [Route 2] Add New Item
@app.route('/add', methods=['GET', 'POST'])
def add_item():
    if request.method == 'POST':
        # Retrieve form data
        p_name = request.form['name']
        p_qty = int(request.form['quantity'])
        p_price = float(request.form['price'])
        
        # Create new product object
        new_product = Product(name=p_name, quantity=p_qty, price=p_price)
        
        # Save to database
        db.session.add(new_product)
        db.session.commit()
        
        return redirect(url_for('index'))
    
    return render_template('add_item.html')

# [Route 3] Delete Item
@app.route('/delete/<int:id>')
def delete_item(id):
    # Attempt to fetch the item by ID, return 404 if not found
    item_to_delete = Product.query.get_or_404(id)
    
    try:
        db.session.delete(item_to_delete) # Delete the object
        db.session.commit()               # Commit changes to database
        return redirect(url_for('index')) # Redirect to dashboard
    except:
        return "There was an error deleting the item."

# [Route 4] Edit Item
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_item(id):
    item_to_edit = Product.query.get_or_404(id)

    if request.method == 'POST':
        # Logic to update existing item details
        item_to_edit.name = request.form['name']
        item_to_edit.quantity = int(request.form['quantity'])
        item_to_edit.price = float(request.form['price'])
        
        db.session.commit() # Only commit needed for updates
        return redirect(url_for('index'))
    
    # Render the edit form with existing data
    return render_template('edit_item.html', item=item_to_edit)

# --- 4. Application Entry Point ---
if __name__ == "__main__":
    with app.app_context():
        db.create_all() # Create database tables if they don't exist
    app.run(debug=True)