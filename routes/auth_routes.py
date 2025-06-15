from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import db, User, ActivityLog

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('product.dashboard'))
    return redirect(url_for('auth.login'))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('product.dashboard'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if not user or not user.check_password(password):
            flash('Usuário ou senha incorretos', 'error')
            return redirect(url_for('auth.login'))
        session['user_id'] = user.id
        session['username'] = user.username
        session['email'] = user.email
        db.session.add(ActivityLog(user_id=user.id, action='login', details='Usuário fez login no sistema'))
        db.session.commit()
        return redirect(url_for('product.dashboard'))
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('product.dashboard'))
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        if password != confirm_password:
            flash('As senhas não coincidem', 'error')
            return redirect(url_for('auth.register'))
        if User.query.filter_by(username=username).first():
            flash('Nome de usuário já está em uso', 'error')
            return redirect(url_for('auth.register'))
        if User.query.filter_by(email=email).first():
            flash('E-mail já está cadastrado', 'error')
            return redirect(url_for('auth.register'))
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash('Registro realizado com sucesso! Faça login.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('register.html')

@auth_bp.route('/logout')
def logout():
    if 'user_id' in session:
        db.session.add(ActivityLog(user_id=session['user_id'], action='logout', details='Usuário saiu do sistema'))
        db.session.commit()
        session.clear()
    return redirect(url_for('auth.login'))