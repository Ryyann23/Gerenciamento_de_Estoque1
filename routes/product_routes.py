from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from models import db, Product, ActivityLog, User
import pytz
from datetime import datetime

product_bp = Blueprint('product', __name__)

LOCAL_TIMEZONE = pytz.timezone('America/Sao_Paulo')

@product_bp.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    total_products = Product.query.count() or 0
    low_stock = Product.query.filter(Product.stock < 10).count() or 0
    stock_value = db.session.query(db.func.sum(Product.price * Product.stock)).scalar() or 0
    recent_activities = db.session.query(ActivityLog, User)\
        .join(User, ActivityLog.user_id == User.id)\
        .order_by(ActivityLog.created_at.desc())\
        .limit(5).all()
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

@product_bp.route('/produtos')
def produtos():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
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

@product_bp.route('/add_product', methods=['POST'])
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
        db.session.add(ActivityLog(
            user_id=session['user_id'],
            action='create',
            details=f'Adicionou o produto "{data["name"]}" ao estoque'
        ))
        db.session.commit()
        return jsonify({'success': True, 'id': new_product.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@product_bp.route('/update_product', methods=['POST'])
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
            db.session.add(ActivityLog(
                user_id=session['user_id'],
                action='update',
                details=f'Editou o produto "{product.name}": ' + ', '.join(changes)
            ))
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@product_bp.route('/delete_product', methods=['POST'])
def delete_product():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Não autorizado'}), 401
    data = request.get_json()
    try:
        product = Product.query.get(data['id'])
        if not product:
            return jsonify({'success': False, 'message': 'Produto não encontrado'}), 404
        db.session.add(ActivityLog(
            user_id=session['user_id'],
            action='delete',
            details=f'Removeu o produto "{product.name}" do estoque'
        ))
        db.session.delete(product)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500