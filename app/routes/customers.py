from decimal import Decimal
from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.models import Customer, Sale
from app.routes.auth import login_required

customers_bp = Blueprint('customers', __name__)


@customers_bp.route('/')
@login_required
def list_customers():
    search = request.args.get('buscar', '')
    query = Customer.query

    if search:
        term = f'%{search}%'
        query = query.filter(
            db.or_(
                Customer.name.ilike(term),
                Customer.phone.ilike(term),
                Customer.email.ilike(term)
            )
        )

    customers = query.order_by(Customer.name).all()

    # Add sale count and last purchase date
    customers_data = []
    for customer in customers:
        sales = Sale.query.filter_by(customer_id=customer.id).order_by(Sale.created_at.desc()).all()
        last_sale = sales[0] if sales else None
        total_spent_usd = sum(Decimal(str(s.sale_price_usd)) for s in sales)
        customers_data.append({
            'customer': customer,
            'sale_count': len(sales),
            'last_purchase': last_sale.created_at if last_sale else None,
            'total_spent_usd': total_spent_usd
        })

    return render_template(
        'admin/customers/list.html',
        customers_data=customers_data,
        search=search
    )


@customers_bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
def new_customer():
    if request.method == 'POST':
        try:
            name = request.form.get('name', '').strip()
            phone = request.form.get('phone', '').strip()
            email = request.form.get('email', '').strip()
            notes = request.form.get('notes', '').strip()

            if not name:
                flash('El nombre del cliente es obligatorio.', 'danger')
                return render_template('admin/customers/form.html', customer=None)

            customer = Customer(
                name=name,
                phone=phone if phone else None,
                email=email if email else None,
                notes=notes if notes else None
            )
            db.session.add(customer)
            db.session.commit()
            flash(f'Cliente "{name}" creado exitosamente.', 'success')
            return redirect(url_for('customers.list_customers'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear el cliente: {str(e)}', 'danger')

    return render_template('admin/customers/form.html', customer=None)


@customers_bp.route('/<int:customer_id>')
@login_required
def customer_detail(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    sales = Sale.query.filter_by(customer_id=customer_id).order_by(Sale.created_at.desc()).all()
    total_spent_usd = sum(Decimal(str(s.sale_price_usd)) for s in sales)
    total_spent_ars = sum(Decimal(str(s.sale_price_ars)) for s in sales)
    total_profit_usd = sum(Decimal(str(s.profit_usd)) for s in sales)

    return render_template(
        'admin/customers/detail.html',
        customer=customer,
        sales=sales,
        total_spent_usd=total_spent_usd,
        total_spent_ars=total_spent_ars,
        total_profit_usd=total_profit_usd
    )


@customers_bp.route('/<int:customer_id>/editar', methods=['GET', 'POST'])
@login_required
def edit_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)

    if request.method == 'POST':
        try:
            customer.name = request.form.get('name', '').strip()
            customer.phone = request.form.get('phone', '').strip() or None
            customer.email = request.form.get('email', '').strip() or None
            customer.notes = request.form.get('notes', '').strip() or None

            if not customer.name:
                flash('El nombre del cliente es obligatorio.', 'danger')
                return render_template('admin/customers/form.html', customer=customer)

            db.session.commit()
            flash(f'Cliente "{customer.name}" actualizado exitosamente.', 'success')
            return redirect(url_for('customers.customer_detail', customer_id=customer.id))

        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar el cliente: {str(e)}', 'danger')

    return render_template('admin/customers/form.html', customer=customer)


@customers_bp.route('/<int:customer_id>/eliminar', methods=['POST'])
@login_required
def delete_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    try:
        name = customer.name
        # Set customer_id to NULL for related sales
        Sale.query.filter_by(customer_id=customer_id).update({'customer_id': None})
        db.session.delete(customer)
        db.session.commit()
        flash(f'Cliente "{name}" eliminado exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar el cliente: {str(e)}', 'danger')
    return redirect(url_for('customers.list_customers'))
