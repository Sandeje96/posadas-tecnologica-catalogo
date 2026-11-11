from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app import db
from app.models import Order, OrderItem
from app.routes.auth import login_required

orders_bp = Blueprint('orders', __name__)


@orders_bp.route('/')
@login_required
def list_orders():
    """Listado de pedidos web recibidos."""
    estado = request.args.get('estado', '')
    buscar = request.args.get('buscar', '')

    query = Order.query

    if estado and estado != 'todos':
        query = query.filter(Order.status == estado)

    if buscar:
        termino = f"%{buscar}%"
        query = query.filter(
            db.or_(
                Order.order_number.ilike(termino),
                Order.customer_name.ilike(termino),
                Order.customer_phone.ilike(termino),
                Order.customer_address.ilike(termino)
            )
        )

    orders = query.order_by(Order.created_at.desc()).all()

    # Contadores rápidos
    total_pedidos = Order.query.count()
    pedidos_pendientes = Order.query.filter_by(status='pendiente').count()
    pedidos_confirmados = Order.query.filter_by(status='confirmado').count()

    return render_template(
        'admin/orders/index.html',
        orders=orders,
        estado_filtro=estado,
        buscar=buscar,
        total_pedidos=total_pedidos,
        pedidos_pendientes=pedidos_pendientes,
        pedidos_confirmados=pedidos_confirmados
    )


@orders_bp.route('/<int:order_id>')
@login_required
def view_order(order_id):
    """Detalle de un pedido específico."""
    order = Order.query.get_or_404(order_id)
    return render_template('admin/orders/view.html', order=order)


@orders_bp.route('/<int:order_id>/cambiar-estado', methods=['POST'])
@login_required
def change_status(order_id):
    """Actualiza el estado de un pedido (pendiente, confirmado, entregado, cancelado)."""
    order = Order.query.get_or_404(order_id)
    nuevo_estado = request.form.get('status', 'pendiente')

    estados_validos = ['pendiente', 'confirmado', 'en_camino', 'entregado', 'cancelado']
    if nuevo_estado in estados_validos:
        order.status = nuevo_estado
        db.session.commit()
        flash(f'Estado del pedido {order.order_number} actualizado a "{nuevo_estado}".', 'success')
    else:
        flash('Estado no válido.', 'danger')

    return redirect(request.referrer or url_for('orders.list_orders'))
