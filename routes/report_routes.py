from flask import Blueprint, render_template, session, redirect, url_for
from models import Product, ActivityLog, User
import pytz

report_bp = Blueprint('report', __name__)

LOCAL_TIMEZONE = pytz.timezone('America/Sao_Paulo')

@report_bp.route('/relatorios')
def relatorios():
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
            'stock': product.stock,
            'price': f"{product.price:,.2f}",
            'stock_status': stock_status
        })
    all_activities = ActivityLog.query.join(User, ActivityLog.user_id == User.id)\
        .order_by(ActivityLog.created_at.desc()).all()
    activities_for_template = []
    for activity in all_activities:
        user = User.query.get(activity.user_id)
        local_time = activity.created_at.astimezone(LOCAL_TIMEZONE)
        activities_for_template.append({
            'username': user.username if user else '',
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