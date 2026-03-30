from decimal import Decimal, InvalidOperation
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app import db
from app.models import Product, Sale, Customer, Setting
from app.routes.auth import login_required

sales_bp = Blueprint('sales', __name__)

ITEMS_PER_PAGE = 20


@sales_bp.route('/')
@login_required
def list_sales():
    page = request.args.get('page', 1, type=int)
    sales_pagination = Sale.query.order_by(Sale.created_at.desc()).paginate(
        page=page, per_page=ITEMS_PER_PAGE, error_out=False
    )
    all_sales = Sale.query.all()
    total_revenue_usd = sum(Decimal(str(s.sale_price_usd)) for s in all_sales)
    total_revenue_ars = sum(Decimal(str(s.sale_price_ars)) for s in all_sales)
    total_profit_usd = sum(Decimal(str(s.profit_usd)) for s in all_sales)
    total_profit_ars = sum(Decimal(str(s.profit_ars)) for s in all_sales)

    return render_template(
        'admin/sales/list.html',
        sales=sales_pagination.items,
        pagination=sales_pagination,
        total_sales=len(all_sales),
        total_revenue_usd=total_revenue_usd,
        total_revenue_ars=total_revenue_ars,
        total_profit_usd=total_profit_usd,
        total_profit_ars=total_profit_ars
    )


@sales_bp.route('/nueva', methods=['GET', 'POST'])
@login_required
def new_sale():
    products = Product.query.order_by(Product.name).all()
    customers = Customer.query.order_by(Customer.name).all()

    try:
        exchange_rate = Decimal(Setting.get('exchange_rate', '1000'))
    except Exception:
        exchange_rate = Decimal('1000')

    if request.method == 'POST':
        try:
            product_id = int(request.form.get('product_id'))
            customer_id = request.form.get('customer_id')
            sale_price_usd = Decimal(request.form.get('sale_price_usd', '0') or '0')
            notes = request.form.get('notes', '').strip()

            product = Product.query.get_or_404(product_id)

            # Recalculate exchange rate at time of sale
            try:
                current_rate = Decimal(Setting.get('exchange_rate', '1000'))
            except Exception:
                current_rate = Decimal('1000')

            # Usar el costo enviado desde el form (puede haber sido modificado manualmente)
            form_cost = request.form.get('cost_price_usd', '').strip()
            try:
                cost_price_usd = Decimal(form_cost) if form_cost else Decimal(str(product.cost_price_usd))
            except Exception:
                cost_price_usd = Decimal(str(product.cost_price_usd))
            sale_price_ars = sale_price_usd * current_rate
            profit_usd = sale_price_usd - cost_price_usd
            profit_ars = profit_usd * current_rate

            sale = Sale(
                product_id=product_id,
                customer_id=int(customer_id) if customer_id and customer_id.isdigit() else None,
                sale_price_usd=sale_price_usd,
                exchange_rate=current_rate,
                sale_price_ars=sale_price_ars,
                cost_price_usd=cost_price_usd,
                profit_usd=profit_usd,
                profit_ars=profit_ars,
                notes=notes
            )
            db.session.add(sale)
            db.session.commit()
            flash('Venta registrada exitosamente.', 'success')
            return redirect(url_for('sales.list_sales'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error al registrar la venta: {str(e)}', 'danger')

    return render_template(
        'admin/sales/form.html',
        products=products,
        customers=customers,
        exchange_rate=exchange_rate
    )


@sales_bp.route('/<int:sale_id>')
@login_required
def sale_detail(sale_id):
    sale = Sale.query.get_or_404(sale_id)
    return render_template('admin/sales/detail.html', sale=sale)


@sales_bp.route('/<int:sale_id>/editar', methods=['GET', 'POST'])
@login_required
def edit_sale(sale_id):
    sale = Sale.query.get_or_404(sale_id)
    products = Product.query.order_by(Product.name).all()
    customers = Customer.query.order_by(Customer.name).all()

    try:
        exchange_rate = Decimal(Setting.get('exchange_rate', '1000'))
    except Exception:
        exchange_rate = Decimal('1000')

    if request.method == 'POST':
        try:
            product_id = int(request.form.get('product_id'))
            customer_id = request.form.get('customer_id')
            sale_price_usd = Decimal(request.form.get('sale_price_usd', '0') or '0')
            notes = request.form.get('notes', '').strip()

            product = Product.query.get_or_404(product_id)

            try:
                current_rate = Decimal(Setting.get('exchange_rate', '1000'))
            except Exception:
                current_rate = Decimal('1000')

            form_cost = request.form.get('cost_price_usd', '').strip()
            try:
                cost_price_usd = Decimal(form_cost) if form_cost else Decimal(str(product.cost_price_usd))
            except Exception:
                cost_price_usd = Decimal(str(product.cost_price_usd))

            sale.product_id = product_id
            sale.customer_id = int(customer_id) if customer_id and customer_id.isdigit() else None
            sale.sale_price_usd = sale_price_usd
            sale.exchange_rate = current_rate
            sale.sale_price_ars = sale_price_usd * current_rate
            sale.cost_price_usd = cost_price_usd
            sale.profit_usd = sale_price_usd - cost_price_usd
            sale.profit_ars = (sale_price_usd - cost_price_usd) * current_rate
            sale.notes = notes

            db.session.commit()
            flash('Venta actualizada exitosamente.', 'success')
            return redirect(url_for('sales.list_sales'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar la venta: {str(e)}', 'danger')

    return render_template(
        'admin/sales/edit.html',
        sale=sale,
        products=products,
        customers=customers,
        exchange_rate=exchange_rate
    )


@sales_bp.route('/<int:sale_id>/eliminar', methods=['POST'])
@login_required
def delete_sale(sale_id):
    sale = Sale.query.get_or_404(sale_id)
    try:
        db.session.delete(sale)
        db.session.commit()
        flash('Venta eliminada exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar la venta: {str(e)}', 'danger')
    return redirect(url_for('sales.list_sales'))


@sales_bp.route('/simulador', methods=['GET', 'POST'])
@login_required
def simulator():
    products = Product.query.order_by(Product.name).all()

    try:
        exchange_rate = Decimal(Setting.get('exchange_rate', '1000'))
    except Exception:
        exchange_rate = Decimal('1000')

    if request.method == 'POST':
        try:
            data = request.get_json()
            cost_usd = Decimal(str(data.get('cost_usd', 0)))
            margin_type = data.get('margin_type', 'percentage')
            margin_value = Decimal(str(data.get('margin_value', 0)))
            rate = Decimal(str(data.get('exchange_rate', str(exchange_rate))))

            if margin_type == 'percentage':
                profit_usd = cost_usd * (margin_value / Decimal('100'))
                sale_price_usd = cost_usd + profit_usd
            else:
                # Fixed USD value
                profit_usd = margin_value
                sale_price_usd = cost_usd + profit_usd

            sale_price_ars = sale_price_usd * rate
            profit_ars = profit_usd * rate
            cost_ars = cost_usd * rate

            if cost_usd > 0:
                margin_percent = (profit_usd / cost_usd) * Decimal('100')
            else:
                margin_percent = Decimal('0')

            return jsonify({
                'sale_price_usd': float(sale_price_usd),
                'sale_price_ars': float(sale_price_ars),
                'profit_usd': float(profit_usd),
                'profit_ars': float(profit_ars),
                'cost_ars': float(cost_ars),
                'margin_percent': float(margin_percent)
            })
        except (InvalidOperation, ValueError, TypeError) as e:
            return jsonify({'error': str(e)}), 400

    return render_template(
        'admin/sales/simulator.html',
        products=products,
        exchange_rate=exchange_rate
    )


@sales_bp.route('/api/producto/<int:product_id>')
@login_required
def get_product_cost(product_id):
    product = Product.query.get_or_404(product_id)
    return jsonify({
        'id': product.id,
        'name': product.name,
        'cost_price_usd': float(product.cost_price_usd),
        'sale_price_usd': float(product.sale_price_usd),
        'brand': product.brand,
        'model': product.model
    })
