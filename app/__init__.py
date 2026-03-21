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

    return app
