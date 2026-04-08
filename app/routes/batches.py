from datetime import datetime
from decimal import Decimal
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app import db
from app.models import SaleBatch, BatchExpense, Sale, Setting
from app.routes.auth import login_required

batches_bp = Blueprint('batches', __name__)


@batches_bp.route('/')
@login_required
def list_batches():
    batches = SaleBatch.query.order_by(SaleBatch.created_at.desc()).all()
    # Ventas sin lote asignado
    sin_lote = Sale.query.filter_by(batch_id=None).count()
    return render_template('admin/batches/list.html', batches=batches, sin_lote=sin_lote)


@batches_bp.route('/nuevo', methods=['POST'])
@login_required
def new_batch():
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    if not name:
        flash('El nombre del lote es obligatorio.', 'danger')
        return redirect(url_for('batches.list_batches'))
    batch = SaleBatch(name=name, description=description or None)
    db.session.add(batch)
    db.session.commit()
    flash(f'Lote "{name}" creado exitosamente.', 'success')
    return redirect(url_for('batches.batch_detail', batch_id=batch.id))


@batches_bp.route('/<int:batch_id>')
@login_required
def batch_detail(batch_id):
    batch = SaleBatch.query.get_or_404(batch_id)
    # Ventas sin lote para poder agregarlas
    ventas_sin_lote = Sale.query.filter_by(batch_id=None).order_by(Sale.created_at.desc()).all()
    try:
        exchange_rate = Decimal(Setting.get('exchange_rate', '1000'))
    except Exception:
        exchange_rate = Decimal('1000')
    return render_template(
        'admin/batches/detail.html',
        batch=batch,
        ventas_sin_lote=ventas_sin_lote,
        exchange_rate=exchange_rate
    )


@batches_bp.route('/<int:batch_id>/agregar-ventas', methods=['POST'])
@login_required
def add_sales(batch_id):
    batch = SaleBatch.query.get_or_404(batch_id)
    sale_ids = request.form.getlist('sale_ids')
    if not sale_ids:
        flash('No seleccionaste ninguna venta.', 'warning')
        return redirect(url_for('batches.batch_detail', batch_id=batch_id))
    agregadas = 0
    for sid in sale_ids:
        try:
            sale = Sale.query.get(int(sid))
            if sale and sale.batch_id is None:
                sale.batch_id = batch_id
                agregadas += 1
        except (ValueError, TypeError):
            pass
    db.session.commit()
    flash(f'{agregadas} venta(s) agregada(s) al lote.', 'success')
    return redirect(url_for('batches.batch_detail', batch_id=batch_id))


@batches_bp.route('/<int:batch_id>/quitar-venta/<int:sale_id>', methods=['POST'])
@login_required
def remove_sale(batch_id, sale_id):
    sale = Sale.query.get_or_404(sale_id)
    if sale.batch_id == batch_id:
        sale.batch_id = None
        db.session.commit()
        flash('Venta quitada del lote.', 'success')
    return redirect(url_for('batches.batch_detail', batch_id=batch_id))


@batches_bp.route('/<int:batch_id>/gastos/nuevo', methods=['POST'])
@login_required
def add_expense(batch_id):
    batch = SaleBatch.query.get_or_404(batch_id)
    description = request.form.get('description', '').strip()
    category = request.form.get('category', 'otros').strip()

    try:
        exchange_rate = Decimal(Setting.get('exchange_rate', '1000'))
    except Exception:
        exchange_rate = Decimal('1000')

    # Aceptar monto en USD o ARS; si viene en ARS se convierte
    currency = request.form.get('currency', 'usd')
    raw_amount = request.form.get('amount', '0').strip().replace(',', '.')
    try:
        raw_amount = Decimal(raw_amount)
    except Exception:
        raw_amount = Decimal('0')

    if currency == 'ars':
        amount_ars = raw_amount
        amount_usd = raw_amount / exchange_rate if exchange_rate else Decimal('0')
    else:
        amount_usd = raw_amount
        amount_ars = raw_amount * exchange_rate

    if not description:
        flash('La descripción del gasto es obligatoria.', 'danger')
        return redirect(url_for('batches.batch_detail', batch_id=batch_id))

    expense = BatchExpense(
        batch_id=batch_id,
        description=description,
        category=category,
        amount_usd=amount_usd,
        amount_ars=amount_ars
    )
    db.session.add(expense)
    db.session.commit()
    flash('Gasto registrado.', 'success')
    return redirect(url_for('batches.batch_detail', batch_id=batch_id))


@batches_bp.route('/<int:batch_id>/gastos/<int:expense_id>/eliminar', methods=['POST'])
@login_required
def delete_expense(batch_id, expense_id):
    expense = BatchExpense.query.get_or_404(expense_id)
    if expense.batch_id == batch_id:
        db.session.delete(expense)
        db.session.commit()
        flash('Gasto eliminado.', 'success')
    return redirect(url_for('batches.batch_detail', batch_id=batch_id))


@batches_bp.route('/<int:batch_id>/cerrar', methods=['POST'])
@login_required
def toggle_close(batch_id):
    batch = SaleBatch.query.get_or_404(batch_id)
    if batch.is_closed:
        batch.closed_at = None
        flash('Lote reabierto.', 'success')
    else:
        batch.closed_at = datetime.utcnow()
        flash('Lote cerrado exitosamente.', 'success')
    db.session.commit()
    return redirect(url_for('batches.batch_detail', batch_id=batch_id))


@batches_bp.route('/<int:batch_id>/eliminar', methods=['POST'])
@login_required
def delete_batch(batch_id):
    batch = SaleBatch.query.get_or_404(batch_id)
    # Desasignar ventas del lote antes de eliminarlo
    for sale in batch.sales:
        sale.batch_id = None
    db.session.delete(batch)
    db.session.commit()
    flash('Lote eliminado. Las ventas quedaron sin lote asignado.', 'success')
    return redirect(url_for('batches.list_batches'))
