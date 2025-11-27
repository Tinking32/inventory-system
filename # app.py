from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)

# 1. 主页
@app.route('/')
def index():
    all_products = Product.query.all()
    return render_template('index.html', items=all_products)

# 2. 添加
@app.route('/add', methods=['GET', 'POST'])
def add_item():
    if request.method == 'POST':
        p_name = request.form['name']
        p_qty = int(request.form['quantity'])
        p_price = float(request.form['price'])
        new_product = Product(name=p_name, quantity=p_qty, price=p_price)
        db.session.add(new_product)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('add_item.html')

# 3. 删除 (新功能)
@app.route('/delete/<int:id>')
def delete_item(id):
    # 根据 ID 查找商品，如果找不到会报错 404
    item_to_delete = Product.query.get_or_404(id)
    
    try:
        db.session.delete(item_to_delete) # 删掉它
        db.session.commit()               # 确认执行
        return redirect(url_for('index')) # 回主页
    except:
        return "删除时出错了"

# 4. 编辑 (新功能)
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_item(id):
    item_to_edit = Product.query.get_or_404(id)

    if request.method == 'POST':
        # 这里是保存修改的逻辑
        item_to_edit.name = request.form['name']
        item_to_edit.quantity = int(request.form['quantity'])
        item_to_edit.price = float(request.form['price'])
        
        db.session.commit() # 只需要 commit，不需要 add
        return redirect(url_for('index'))
    
    # 如果是刚点进来，就把旧数据传给网页
    return render_template('edit_item.html', item=item_to_edit)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)