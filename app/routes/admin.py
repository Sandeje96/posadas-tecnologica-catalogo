from datetime import datetime, date
from decimal import Decimal
from flask import Blueprint, render_template
from app.routes.auth import login_required
from app.models import Product, Sale, Customer, Setting
from app import db
from sqlalchemy import func

admin_bp = Blueprint('admin', __name__)



@admin_bp.route('/update-image/<int:product_id>', methods=['POST'])
@login_required
def update_image(product_id):
    """Ruta temporal: actualiza solo la imagen de un producto."""
    from app.routes.products import save_image
    product = Product.query.get_or_404(product_id)
    if 'image' in request.files and request.files['image'].filename != '':
        new_image = save_image(request.files['image'])
        if new_image:
            if product.image_filename:
                from app.routes.products import delete_image
                delete_image(product.image_filename)
            product.image_filename = new_image
            db.session.commit()
            return f"OK:{product_id}"
    return f"FAIL:{product_id}", 400


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
