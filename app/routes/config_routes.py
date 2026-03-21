from decimal import Decimal, InvalidOperation
from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models import Setting
from app.routes.auth import login_required

config_bp = Blueprint('config_bp', __name__)


@config_bp.route('/', methods=['GET', 'POST'])
@login_required
def config():
    if request.method == 'POST':
        try:
            exchange_rate_str = request.form.get('exchange_rate', '').strip()
            if not exchange_rate_str:
                flash('El tipo de cambio no puede estar vacío.', 'danger')
                return redirect(url_for('config_bp.config'))

            exchange_rate = Decimal(exchange_rate_str)
            if exchange_rate <= 0:
                flash('El tipo de cambio debe ser un valor positivo.', 'danger')
                return redirect(url_for('config_bp.config'))

            Setting.set('exchange_rate', str(exchange_rate))
            flash(f'Tipo de cambio actualizado exitosamente: USD 1 = ARS {exchange_rate:,.2f}', 'success')
            return redirect(url_for('config_bp.config'))

        except InvalidOperation:
            flash('Por favor ingresa un valor numérico válido para el tipo de cambio.', 'danger')
        except Exception as e:
            flash(f'Error al guardar la configuración: {str(e)}', 'danger')

    try:
        exchange_rate = Decimal(Setting.get('exchange_rate', '1000'))
    except Exception:
        exchange_rate = Decimal('1000')

    return render_template('admin/config.html', exchange_rate=exchange_rate)
