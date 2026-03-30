import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config

db = SQLAlchemy()
migrate = Migrate()


def create_app():
    app = Flask(__name__)

    # Load configuration
    config = Config()
    app.config.from_object(config)

    # Fix DATABASE_URL for Railway (postgres:// -> postgresql://)
    db_url = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    if db_url.startswith('postgres://'):
        app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace('postgres://', 'postgresql://', 1)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Ensure upload folder exists
    upload_folder = app.config.get('UPLOAD_FOLDER')
    if upload_folder and not os.path.exists(upload_folder):
        os.makedirs(upload_folder, exist_ok=True)

    # Register blueprints
    from app.routes.catalog import catalog_bp
    from app.routes.auth import auth_bp
    from app.routes.admin import admin_bp
    from app.routes.products import products_bp
    from app.routes.sales import sales_bp
    from app.routes.customers import customers_bp
    from app.routes.config_routes import config_bp

    app.register_blueprint(catalog_bp)
    app.register_blueprint(auth_bp, url_prefix='/admin')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(products_bp, url_prefix='/admin/productos')
    app.register_blueprint(sales_bp, url_prefix='/admin/ventas')
    app.register_blueprint(customers_bp, url_prefix='/admin/clientes')
    app.register_blueprint(config_bp, url_prefix='/admin/configuracion')

    # Filtro Jinja2: formato numérico argentino (punto=miles, coma=decimales)
    @app.template_filter('fmt')
    def format_ar_number(value, decimals=2):
        try:
            formatted = f"{float(value):,.{decimals}f}"
            return formatted.replace(',', 'X').replace('.', ',').replace('X', '.')
        except (ValueError, TypeError):
            return str(value)

    # Crear tablas automáticamente si no existen (primer deploy)
    with app.app_context():
        from app.models import Product, Customer, Sale, Setting  # noqa: F401
        db.create_all()
        # Agregar columnas nuevas si la tabla ya existía (migración manual)
        try:
            from sqlalchemy import text
            with db.engine.connect() as conn:
                for col, tipo in [('ram', 'VARCHAR(50)'), ('storage', 'VARCHAR(50)'), ('color', 'VARCHAR(50)'), ('mercadolibre_active', 'BOOLEAN DEFAULT FALSE')]:
                    conn.execute(text(f'ALTER TABLE products ADD COLUMN IF NOT EXISTS {col} {tipo}'))
                conn.commit()
        except Exception:
            pass

    return app
