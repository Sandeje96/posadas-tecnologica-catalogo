import os
import uuid
from datetime import datetime, date
from decimal import Decimal
from flask import Blueprint, render_template, request, jsonify, current_app
from app.routes.auth import login_required
from app.models import Product, Sale, Customer, Setting
from app import db
from sqlalchemy import func

admin_bp = Blueprint('admin', __name__)




@admin_bp.route('/')
@admin_bp.route('/dashboard')
@login_required
def dashboard():
    # Total products
    total_products = Product.query.count()
    products_in_stock = Product.query.filter_by(stock=True).count()

    # Current month stats
    now = datetime.utcnow()
    start_of_month = datetime(now.year, now.month, 1)

    monthly_sales = Sale.query.filter(Sale.created_at >= start_of_month).all()
    total_sales_month = len(monthly_sales)

    total_revenue_usd = sum(Decimal(str(s.sale_price_usd)) for s in monthly_sales)
    total_revenue_ars = sum(Decimal(str(s.sale_price_ars)) for s in monthly_sales)
    total_profit_usd = sum(Decimal(str(s.profit_usd)) for s in monthly_sales)

    # Recent 5 sales
    recent_sales = Sale.query.order_by(Sale.created_at.desc()).limit(5).all()

    # Exchange rate
    try:
        exchange_rate = Decimal(Setting.get('exchange_rate', '1000'))
    except Exception:
        exchange_rate = Decimal('1000')

    # Total customers
    total_customers = Customer.query.count()

    return render_template(
        'admin/dashboard.html',
        total_products=total_products,
        products_in_stock=products_in_stock,
        total_sales_month=total_sales_month,
        total_revenue_usd=total_revenue_usd,
        total_revenue_ars=total_revenue_ars,
        total_profit_usd=total_profit_usd,
        recent_sales=recent_sales,
        exchange_rate=exchange_rate,
        total_customers=total_customers,
        now=now
    )


@admin_bp.route('/diag-images')
@login_required
def diag_images():
    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'N/A')
    folder_exists = os.path.isdir(upload_folder)
    files_on_disk = os.listdir(upload_folder) if folder_exists else []

    products = Product.query.all()
    db_info = []
    for p in products:
        fn = p.image_filename
        exists = os.path.isfile(os.path.join(upload_folder, fn)) if fn and folder_exists else False
        db_info.append({'id': p.id, 'name': p.name, 'image_filename': fn, 'file_exists': exists})

    return jsonify({
        'upload_folder': upload_folder,
        'folder_exists': folder_exists,
        'files_on_disk_count': len(files_on_disk),
        'files_on_disk': files_on_disk[:20],
        'products': db_info
    })


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


@admin_bp.route('/update-motorola-prices', methods=['POST'])
@login_required
def update_motorola_prices():
    from decimal import Decimal
    try:
        motorola_products = Product.query.filter(Product.brand.ilike('motorola')).all()
        updated = []
        for p in motorola_products:
            old_sale = float(p.sale_price_usd)
            p.sale_price_usd = Decimal(str(p.cost_price_usd)) + Decimal('20.5')
            updated.append({'id': p.id, 'name': p.name, 'cost': float(p.cost_price_usd), 'old_sale': old_sale, 'new_sale': float(p.sale_price_usd)})
        db.session.commit()
        return jsonify({'updated': len(updated), 'products': updated})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
