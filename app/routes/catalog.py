from decimal import Decimal
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify
from app import db
from app.models import Product, Order, OrderItem, Setting

catalog_bp = Blueprint('catalog', __name__)

CATEGORIES = [
    'Lavandinas y Cloro',
    'Detergentes y Desengrasantes',
    'Jabones y Suavizantes',
    'Pisos y Aromatizantes',
    'Automotor e Industria',
    'Accesorios y Varios'
]


def _render_catalog(public_view=False):
    categoria = request.args.get('categoria', '')
    buscar = request.args.get('buscar', '').strip()

    query = Product.query.filter(
        db.or_(Product.is_active == True, Product.is_active == None)
    )

    if categoria and categoria != 'Todos':
        query = query.filter(Product.category == categoria)

    if buscar:
        search_term = f'%{buscar}%'
        query = query.filter(
            db.or_(
                Product.name.ilike(search_term),
                Product.brand.ilike(search_term),
                Product.description.ilike(search_term),
                Product.category.ilike(search_term)
            )
        )

    products = query.order_by(Product.stock.desc(), Product.created_at.desc()).all()

    products_data = []
    for product in products:
        products_data.append({
            'product': product,
            'ars_price': float(product.price_ars)
        })

    return render_template(
        'catalog/index.html',
        products_data=products_data,
        categories=CATEGORIES,
        selected_category=categoria,
        search_query=buscar,
        public_view=public_view
    )


@catalog_bp.route('/')
def index():
    return _render_catalog(public_view=False)


@catalog_bp.route('/catalogo')
def public_catalog():
    """Vista pública del catálogo para clientes."""
    return _render_catalog(public_view=True)


@catalog_bp.route('/producto/<int:product_id>')
def product_detail(product_id):
    """Devuelve datos de un producto en formato JSON para el modal."""
    product = Product.query.get_or_404(product_id)

    return jsonify({
        'id': product.id,
        'name': product.name,
        'brand': product.brand or 'Mundolimp',
        'description': product.description or '',
        'category': product.category,
        'presentation': getattr(product, 'presentation', 'Bidón 5 Litros') or 'Bidón 5 Litros',
        'price_ars': float(product.price_ars),
        'stock': bool(product.stock),
        'badge': product.badge or '',
        'image_filename': product.image_filename or ''
    })


@catalog_bp.route('/checkout', methods=['POST'])
def checkout():
    """
    Recibe el pedido del carrito del cliente y lo guarda en la base de datos.
    """
    data = request.get_json(silent=True)
    if not data:
        data = request.form

    if not data:
        return jsonify({'success': False, 'error': 'No se recibieron datos del pedido.'}), 400

    customer_name = (data.get('customer_name') or '').strip()
    customer_phone = (data.get('customer_phone') or '').strip()
    customer_address = (data.get('customer_address') or '').strip()
    customer_city = (data.get('customer_city') or '').strip()
    notes = (data.get('customer_notes') or data.get('notes') or '').strip()
    items_data = data.get('items', [])

    if not customer_name:
        return jsonify({'success': False, 'error': 'El nombre o comercio es obligatorio.'}), 400
    if not customer_phone:
        return jsonify({'success': False, 'error': 'El teléfono de contacto es obligatorio.'}), 400
    if not customer_address:
        return jsonify({'success': False, 'error': 'La dirección de entrega es obligatoria.'}), 400
    if not items_data:
        return jsonify({'success': False, 'error': 'El pedido no tiene ningún producto cargado.'}), 400

    try:
        # Generar número de pedido único con formato ML-AAAA-XXXX
        year_now = datetime.utcnow().year
        total_prev = Order.query.count() + 1
        order_number = f"ML-{year_now}-{total_prev:04d}"

        total_pedido = Decimal('0')

        nuevo_pedido = Order(
            order_number=order_number,
            customer_name=customer_name,
            customer_phone=customer_phone,
            customer_address=customer_address,
            customer_city=customer_city or 'Posadas',
            notes=notes or None,
            total_amount=Decimal('0'),
            status='pendiente'
        )
        db.session.add(nuevo_pedido)
        db.session.flush()

        for item in items_data:
            p_id = item.get('product_id')
            if p_id:
                real_product = Product.query.get(p_id)
                if not real_product:
                    p_id = None
            p_name = item.get('product_name') or 'Producto Mundolimp'
            presentation = item.get('presentation') or 'Bidón 5 Litros'
            qty = Decimal(str(item.get('quantity', 1)))
            u_price = Decimal(str(item.get('unit_price', 0)))
            subtotal = qty * u_price
            total_pedido += subtotal

            order_item = OrderItem(
                order_id=nuevo_pedido.id,
                product_id=p_id if p_id else None,
                product_name=p_name,
                presentation=presentation,
                quantity=qty,
                unit_price=u_price,
                subtotal=subtotal
            )
            db.session.add(order_item)

        nuevo_pedido.total_amount = total_pedido
        db.session.commit()

        return jsonify({
            'success': True,
            'order_id': nuevo_pedido.id,
            'order_number': nuevo_pedido.order_number,
            'total_amount': float(total_pedido),
            'customer_name': customer_name
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'Error al guardar pedido: {str(e)}'}), 500
