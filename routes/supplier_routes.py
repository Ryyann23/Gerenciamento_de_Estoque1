from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from models import db, Supplier, ActivityLog
import pytz

supplier_bp = Blueprint('supplier', __name__)

LOCAL_TIMEZONE = pytz.timezone('America/Sao_Paulo')

@supplier_bp.route('/fornecedores')
def fornecedores():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
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

@supplier_bp.route('/add_supplier', methods=['POST'])
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
        db.session.add(ActivityLog(
            user_id=session['user_id'],
            action='create',
            details=f'Adicionou o fornecedor "{data["name"]}"'
        ))
        db.session.commit()
        return jsonify({'success': True, 'id': new_supplier.id, 'message': 'Fornecedor adicionado com sucesso'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Erro ao adicionar fornecedor', 'error': str(e)}), 500

@supplier_bp.route('/get_supplier')
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
        return jsonify({'success': False, 'message': 'Erro ao buscar fornecedor', 'error': str(e)}), 500

@supplier_bp.route('/update_supplier', methods=['POST'])
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
            db.session.add(ActivityLog(
                user_id=session['user_id'],
                action='update',
                details=f'Editou o fornecedor "{supplier.name}": ' + ', '.join(changes)
            ))
        db.session.commit()
        return jsonify({'success': True, 'message': 'Fornecedor atualizado com sucesso'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Erro ao atualizar fornecedor', 'error': str(e)}), 500

@supplier_bp.route('/delete_supplier', methods=['POST'])
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
        db.session.add(ActivityLog(
            user_id=session['user_id'],
            action='delete',
            details=f'Removeu o fornecedor "{supplier.name}"'
        ))
        db.session.delete(supplier)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Fornecedor excluído com sucesso'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Erro ao excluir fornecedor', 'error': str(e)}), 500