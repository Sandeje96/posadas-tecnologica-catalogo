import os
import uuid
from datetime import datetime
from decimal import Decimal
from flask import Blueprint, render_template, request, jsonify, current_app, redirect, url_for
from app.routes.auth import login_required
from app.models import Product, Order, Setting
from app import db

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/')
@admin_bp.route('/dashboard')
@login_required
def dashboard():
    """Dashboard principal del panel de administración de Mundolimp."""
    total_products = Product.query.count()
    products_in_stock = Product.query.filter_by(stock=True).count()

    total_orders = Order.query.count()
    pending_orders = Order.query.filter_by(status='pendiente').count()
    confirmed_orders = Order.query.filter_by(status='confirmado').count()

    # Pedidos recientes
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()

    # Total ventas web
    orders_completed = Order.query.filter(Order.status.in_(['confirmado', 'en_camino', 'entregado'])).all()
    total_revenue_ars = sum(Decimal(str(o.total_amount or 0)) for o in orders_completed)

    return render_template(
        'admin/dashboard.html',
        total_products=total_products,
        products_in_stock=products_in_stock,
        total_orders=total_orders,
        pending_orders=pending_orders,
        confirmed_orders=confirmed_orders,
        total_revenue_ars=total_revenue_ars,
        recent_orders=recent_orders,
        now=datetime.utcnow()
    )


@admin_bp.route('/upload-image', methods=['POST'])
@login_required
def upload_image():
    product_id = request.form.get('product_id')
    if not product_id:
        return jsonify({'error': 'product_id required'}), 400
    product = Product.query.get(int(product_id))
    if not product:
        return jsonify({'error': 'product not found'}), 404
    if 'image' not in request.files or request.files['image'].filename == '':
        return jsonify({'error': 'no image'}), 400
    file = request.files['image']
    try:
        ext = file.filename.rsplit('.', 1)[-1].lower()
        filename = f"{uuid.uuid4().hex}.{ext}"
        upload_folder = current_app.config.get('UPLOAD_FOLDER')
        os.makedirs(upload_folder, exist_ok=True)
        file.save(os.path.join(upload_folder, filename))
        product.image_filename = filename
        db.session.commit()
        return jsonify({'ok': product.id, 'filename': filename})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
