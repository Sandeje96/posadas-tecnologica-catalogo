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
            whatsapp = request.form.get('whatsapp_number', '').strip()
            min_order = request.form.get('minimum_order', '0').strip()
            announcement = request.form.get('announcement', '').strip()
            new_password = request.form.get('admin_password', '').strip()

            Setting.set('whatsapp_number', whatsapp)
            Setting.set('minimum_order', min_order or '0')
            Setting.set('announcement', announcement)
            if new_password:
                Setting.set('admin_password', new_password)

            flash('Configuración de la tienda Mundolimp actualizada exitosamente.', 'success')
            return redirect(url_for('config_bp.config'))

        except Exception as e:
            flash(f'Error al guardar la configuración: {str(e)}', 'danger')

    whatsapp_number = Setting.get('whatsapp_number', '')
    minimum_order = Setting.get('minimum_order', '0')
    announcement = Setting.get('announcement', 'Venta Directa de Fábrica · Envíos a Domicilio y Comercios')

    return render_template(
        'admin/config.html',
        whatsapp_number=whatsapp_number,
        minimum_order=minimum_order,
        announcement=announcement
    )
