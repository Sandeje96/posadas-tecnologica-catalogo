from decimal import Decimal
from flask import Blueprint, render_template, request, jsonify
from app.models import Product, Setting

catalog_bp = Blueprint('catalog', __name__)

CATEGORIES = ['Smartphones', 'Impresoras', 'Tablets', 'Laptops', 'Accesorios']


def _render_catalog(public_view=False):
    categoria = request.args.get('categoria', '')
    buscar = request.args.get('buscar', '')

    query = Product.query

    if categoria and categoria != 'Todos':
        query = query.filter(Product.category == categoria)

    if buscar:
        search_term = f'%{buscar}%'
        query = query.filter(
            db.or_(
                Product.name.ilike(search_term),
                Product.brand.ilike(search_term),
                Product.model.ilike(search_term),
                Product.description.ilike(search_term)
            )
        )

    products = query.order_by(Product.created_at.desc()).all()

    try:
        exchange_rate = Decimal(Setting.get('exchange_rate', '1000'))
    except Exception:
        exchange_rate = Decimal('1000')

    products_with_ars = []
    for product in products:
        ars_price = product.sale_price_ars(exchange_rate)
        products_with_ars.append({
            'product': product,
            'ars_price': ars_price
        })

    return render_template(
        'catalog/index.html',
        products_data=products_with_ars,
        categories=CATEGORIES,
        selected_category=categoria,
        search_query=buscar,
        exchange_rate=exchange_rate,
        public_view=public_view
    )


@catalog_bp.route('/')
def index():
    return _render_catalog(public_view=False)


@catalog_bp.route('/catalogo')
def public_catalog():
    """Vista pública del catálogo — sin links de admin."""
    return _render_catalog(public_view=True)


@catalog_bp.route('/producto/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    try:
        exchange_rate = Decimal(Setting.get('exchange_rate', '1000'))
    except Exception:
        exchange_rate = Decimal('1000')

    ars_price = product.sale_price_ars(exchange_rate)

    return jsonify({
        'id': product.id,
        'name': product.name,
        'brand': product.brand,
        'model': product.model,
        'description': product.description,
        'category': product.category,
        'sale_price_usd': float(product.sale_price_usd),
        'sale_price_ars': float(ars_price),
        'stock': product.stock,
        'badge': product.badge,
        'image_filename': product.image_filename,
        'exchange_rate': float(exchange_rate),
        'ram': product.ram,
        'storage': product.storage,
        'color': product.color
    })


# Import db for the or_ filter
from app import db
