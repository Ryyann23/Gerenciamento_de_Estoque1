from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone, timedelta
import pytz
import os

app = Flask(__name__)
app.secret_key = 'teste123'

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "database.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

LOCAL_TIMEZONE = pytz.timezone('America/Sao_Paulo')

def get_local_time():
    return datetime.now(LOCAL_TIMEZONE)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: get_local_time())
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50))
    brand = db.Column(db.String(50))
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    added_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=lambda: get_local_time())

class Supplier(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50))
    contact = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(200))
    city = db.Column(db.String(50))
    state = db.Column(db.String(2))
    status = db.Column(db.String(10), default='Ativo')
    added_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=lambda: get_local_time())

class ActivityLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    action = db.Column(db.String(50), nullable=False)
    details = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=lambda: get_local_time())
    
    user = db.relationship('User', backref='activities')

@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        remember = 'remember' in request.form
        
        user = User.query.filter_by(username=username).first()
        
        if not user or not user.check_password(password):
            flash('Usuário ou senha incorretos', 'error')
            return redirect(url_for('login'))
        
        session['user_id'] = user.id
        session['username'] = user.username
        session['email'] = user.email
        
        new_activity = ActivityLog(
            user_id=user.id,
            action='login',
            details='Usuário fez login no sistema'
        )
        db.session.add(new_activity)
        db.session.commit()
        
        return redirect(url_for('dashboard'))
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            flash('As senhas não coincidem', 'error')
            return redirect(url_for('register'))
        
        if User.query.filter_by(username=username).first():
            flash('Nome de usuário já está em uso', 'error')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('E-mail já está cadastrado', 'error')
            return redirect(url_for('register'))
        
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registro realizado com sucesso! Faça login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    if 'user_id' in session:
        new_activity = ActivityLog(
            user_id=session['user_id'],
            action='logout',
            details='Usuário saiu do sistema'
        )
        db.session.add(new_activity)
        db.session.commit()
        
        session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    total_products = Product.query.count() or 0
    low_stock = Product.query.filter(Product.stock < 10).count() or 0
    stock_value = db.session.query(db.func.sum(Product.price * Product.stock)).scalar() or 0
    
    recent_activities = db.session.query(ActivityLog, User)\
        .join(User, ActivityLog.user_id == User.id)\
        .order_by(ActivityLog.created_at.desc())\
        .limit(5)\
        .all()
    
    activities_for_template = []
    for activity, user in recent_activities:
        local_time = activity.created_at.astimezone(LOCAL_TIMEZONE)
        activities_for_template.append({
            'username': user.username,
            'action': activity.action,
            'details': activity.details,
            'time': local_time.strftime('%d/%m/%Y %H:%M')
        })
    
    return render_template('dashboard.html',
                         current_user={
                             'name': session['username'],
                             'email': session['email'],
                             'initial': session['username'][0].upper()
                         },
                         total_products=total_products,
                         low_stock_count=low_stock,
                         stock_value=f"{stock_value:,.2f}",
                         activities=activities_for_template)

@app.route('/produtos')
def produtos():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    all_products = Product.query.all()
    
    products_for_template = []
    for product in all_products:
        if product.stock == 0:
            stock_status = "Esgotado"
        elif product.stock < 10:
            stock_status = "Estoque baixo"
        else:
            stock_status = "Em estoque"
        
        products_for_template.append({
            'id': product.id,
            'code': f"PROD{product.id:04d}",
            'name': product.name,
            'category': product.category or "Sem categoria",
            'brand': product.brand or "Sem marca",
            'stock': product.stock,
            'price': f"{product.price:,.2f}",
            'stock_status': stock_status
        })
    
    return render_template('produtos.html',
                         current_user={
                             'name': session['username'],
                             'email': session['email'],
                             'initial': session['username'][0].upper()
                         },
                         products=products_for_template)

@app.route('/fornecedores')
def fornecedores():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    all_suppliers = Supplier.query.all()
    
    suppliers_for_template = []
    for supplier in all_suppliers:
        suppliers_for_template.append({
            'id': supplier.id,
            'code': f"FORN{supplier.id:04d}",
            'name': supplier.name,
            'category': supplier.category or "Sem categoria",
            'contact': supplier.contact,
            'email': supplier.email,
            'phone': supplier.phone,
            'address': supplier.address,
            'city': supplier.city,
            'state': supplier.state,
            'status': supplier.status
        })
    
    return render_template('fornecedores.html',
                         current_user={
                             'name': session['username'],
                             'email': session['email'],
                             'initial': session['username'][0].upper()
                         },
                         suppliers=suppliers_for_template)

@app.route('/add_supplier', methods=['POST'])
def add_supplier():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Não autorizado'}), 401
    
    try:
        data = request.get_json()
        
        required_fields = ['name', 'contact', 'email', 'phone']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'message': f'O campo {field} é obrigatório'}), 400
        
        phone = ''.join(filter(str.isdigit, data.get('phone', '')))
        if len(phone) not in [10, 11]:  
            return jsonify({'success': False, 'message': 'Telefone inválido. Deve conter 10 ou 11 dígitos.'}), 400
        
        formatted_phone = f"({phone[:2]}) {phone[2:6]}-{phone[6:]}" if len(phone) == 10 else f"({phone[:2]}) {phone[2:7]}-{phone[7:]}"
        
        new_supplier = Supplier(
            name=data['name'],
            category=data.get('category', ''),
            contact=data['contact'],
            email=data['email'],
            phone=formatted_phone,
            address=data.get('address', ''),
            city=data.get('city', ''),
            state=data.get('state', ''),
            status=data.get('status', 'Ativo'),
            added_by=session['user_id']
        )
        
        db.session.add(new_supplier)
        
        new_activity = ActivityLog(
            user_id=session['user_id'],
            action='create',
            details=f'Adicionou o fornecedor "{data["name"]}"'
        )
        db.session.add(new_activity)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'id': new_supplier.id,
            'message': 'Fornecedor adicionado com sucesso'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Erro ao adicionar fornecedor',
            'error': str(e)
        }), 500

@app.route('/get_supplier')
def get_supplier():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Não autorizado'}), 401
    
    try:
        supplier_id = request.args.get('id')
        if not supplier_id:
            return jsonify({'success': False, 'message': 'ID do fornecedor não fornecido'}), 400
        
        supplier = Supplier.query.get(supplier_id)
        if not supplier:
            return jsonify({'success': False, 'message': 'Fornecedor não encontrado'}), 404
        
        return jsonify({
            'success': True,
            'supplier': {
                'id': supplier.id,
                'name': supplier.name,
                'category': supplier.category,
                'contact': supplier.contact,
                'email': supplier.email,
                'phone': supplier.phone,
                'address': supplier.address,
                'city': supplier.city,
                'state': supplier.state,
                'status': supplier.status
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Erro ao buscar fornecedor',
            'error': str(e)
        }), 500

@app.route('/update_supplier', methods=['POST'])
def update_supplier():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Não autorizado'}), 401
    
    try:
        data = request.get_json()
        
        required_fields = ['id', 'name', 'contact', 'email', 'phone']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'message': f'O campo {field} é obrigatório'}), 400
        
        supplier = Supplier.query.get(data['id'])
        if not supplier:
            return jsonify({'success': False, 'message': 'Fornecedor não encontrado'}), 404
        
        phone = ''.join(filter(str.isdigit, data.get('phone', '')))
        if len(phone) not in [10, 11]:
            return jsonify({'success': False, 'message': 'Telefone inválido. Deve conter 10 ou 11 dígitos.'}), 400
        
        formatted_phone = f"({phone[:2]}) {phone[2:6]}-{phone[6:]}" if len(phone) == 10 else f"({phone[:2]}) {phone[2:7]}-{phone[7:]}"
        
        changes = []
        if supplier.name != data['name']:
            changes.append(f'nome: {supplier.name} → {data["name"]}')
        if supplier.category != data.get('category', ''):
            changes.append(f'categoria: {supplier.category} → {data.get("category", "")}')
        if supplier.contact != data['contact']:
            changes.append(f'contato: {supplier.contact} → {data["contact"]}')
        if supplier.email != data['email']:
            changes.append(f'email: {supplier.email} → {data["email"]}')
        if supplier.phone != formatted_phone:
            changes.append(f'telefone: {supplier.phone} → {formatted_phone}')
        if supplier.status != data.get('status', 'Ativo'):
            changes.append(f'status: {supplier.status} → {data.get("status", "Ativo")}')
        
        supplier.name = data['name']
        supplier.category = data.get('category', '')
        supplier.contact = data['contact']
        supplier.email = data['email']
        supplier.phone = formatted_phone
        supplier.address = data.get('address', '')
        supplier.city = data.get('city', '')
        supplier.state = data.get('state', '')
        supplier.status = data.get('status', 'Ativo')
        
        if changes:
            new_activity = ActivityLog(
                user_id=session['user_id'],
                action='update',
                details=f'Editou o fornecedor "{supplier.name}": ' + ', '.join(changes)
            )
            db.session.add(new_activity)
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Fornecedor atualizado com sucesso'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Erro ao atualizar fornecedor',
            'error': str(e)
        }), 500

@app.route('/delete_supplier', methods=['POST'])
def delete_supplier():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Não autorizado'}), 401
    
    try:
        data = request.get_json()
        if not data or 'id' not in data:
            return jsonify({'success': False, 'message': 'ID do fornecedor não fornecido'}), 400
        
        supplier = Supplier.query.get(data['id'])
        if not supplier:
            return jsonify({'success': False, 'message': 'Fornecedor não encontrado'}), 404
        
        new_activity = ActivityLog(
            user_id=session['user_id'],
            action='delete',
            details=f'Removeu o fornecedor "{supplier.name}"'
        )
        db.session.add(new_activity)
        
        db.session.delete(supplier)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Fornecedor excluído com sucesso'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Erro ao excluir fornecedor',
            'error': str(e)
        }), 500

@app.route('/add_product', methods=['POST'])
def add_product():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Não autorizado'}), 401
    
    try:
        data = request.get_json()
        
        new_product = Product(
            name=data['name'],
            category=data['category'],
            brand=data.get('brand', ''),
            price=data['price'],
            stock=data['stock'],
            added_by=session['user_id']
        )
        db.session.add(new_product)
        
        new_activity = ActivityLog(
            user_id=session['user_id'],
            action='create',
            details=f'Adicionou o produto "{data["name"]}" ao estoque'
        )
        db.session.add(new_activity)
        
        db.session.commit()
        return jsonify({'success': True, 'id': new_product.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/update_product', methods=['POST'])
def update_product():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Não autorizado'}), 401
    
    data = request.get_json()
    
    try:
        product = Product.query.get(data['id'])
        if not product:
            return jsonify({'success': False, 'message': 'Produto não encontrado'}), 404
        
        changes = []
        if product.name != data['name']:
            changes.append(f'nome: {product.name} → {data["name"]}')
        if product.category != data['category']:
            changes.append(f'categoria: {product.category} → {data["category"]}')
        if product.brand != data.get('brand', ''):
            changes.append(f'marca: {product.brand} → {data.get("brand", "")}')
        if float(product.price) != float(data['price']):
            changes.append(f'preço: {product.price} → {data["price"]}')
        if product.stock != int(data['stock']):
            changes.append(f'estoque: {product.stock} → {data["stock"]}')
        
        product.name = data['name']
        product.category = data['category']
        product.brand = data.get('brand', '')
        product.price = data['price']
        product.stock = data['stock']
        
        if changes:
            new_activity = ActivityLog(
                user_id=session['user_id'],
                action='update',
                details=f'Editou o produto "{product.name}": ' + ', '.join(changes)
            )
            db.session.add(new_activity)
        
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/delete_product', methods=['POST'])
def delete_product():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Não autorizado'}), 401
    
    data = request.get_json()
    
    try:
        product = Product.query.get(data['id'])
        if not product:
            return jsonify({'success': False, 'message': 'Produto não encontrado'}), 404
        
        new_activity = ActivityLog(
            user_id=session['user_id'],
            action='delete',
            details=f'Removeu o produto "{product.name}" do estoque'
        )
        db.session.add(new_activity)
        
        db.session.delete(product)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/relatorios')
def relatorios():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    all_products = Product.query.all()
    
    products_for_template = []
    for product in all_products:
        if product.stock == 0:
            stock_status = "Esgotado"
        elif product.stock < 10:
            stock_status = "Estoque baixo"
        else:
            stock_status = "Em estoque"
        
        products_for_template.append({
            'id': product.id,
            'code': f"PROD{product.id:04d}",
            'name': product.name,
            'category': product.category or "Sem categoria",
            'stock': product.stock,
            'price': f"{product.price:,.2f}",
            'stock_status': stock_status
        })
    
    all_activities = db.session.query(ActivityLog, User)\
        .join(User, ActivityLog.user_id == User.id)\
        .order_by(ActivityLog.created_at.desc())\
        .all()
    
    activities_for_template = []
    for activity, user in all_activities:
        local_time = activity.created_at.astimezone(LOCAL_TIMEZONE)
        activities_for_template.append({
            'username': user.username,
            'action': activity.action,
            'details': activity.details,
            'time': local_time.strftime('%d/%m/%Y %H:%M')
        })
    
    return render_template('relatorios.html',
                         current_user={
                             'name': session['username'],
                             'email': session['email'],
                             'initial': session['username'][0].upper()
                         },
                         products=products_for_template,
                         activities=activities_for_template)

def initialize_database():
    with app.app_context():
        db.create_all()
        
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', email='admin@quantumstock.com')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            
            print("Usuário admin criado com senha 'admin123'")

if __name__ == '__main__':
    initialize_database()
    app.run(debug=True)