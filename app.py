from flask import Flask
from models import db
import os

def create_app():
    app = Flask(__name__)
    app.secret_key = 'teste123'
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "database.db")}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    # Importa e registra blueprints das rotas
    from routes.auth_routes import auth_bp
    from routes.product_routes import product_bp
    from routes.supplier_routes import supplier_bp
    from routes.report_routes import report_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(product_bp)
    app.register_blueprint(supplier_bp)
    app.register_blueprint(report_bp)

    return app

def initialize_database(app):
    with app.app_context():
        db.create_all()
        from models import User
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', email='admin@quantumstock.com')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("Usuário admin criado com senha 'admin123'")

if __name__ == '__main__':
    app = create_app()
    initialize_database(app)
    app.run(debug=True)