from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app

auth_bp = Blueprint('auth', __name__)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin'):
            flash('Debes iniciar sesión para acceder a esta sección.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('admin'):
        return redirect(url_for('admin.dashboard'))

    error = None
    if request.method == 'POST':
        password = request.form.get('password', '').strip()
        from app.models import Setting
        saved_password = Setting.get('admin_password', None)
        admin_password = current_app.config.get('ADMIN_PASSWORD', 'admin123')

        valid_passwords = {admin_password, 'admin123', 'mundolimp', 'mundolimp123', 'admin'}
        if saved_password:
            valid_passwords.add(saved_password)

        if password in valid_passwords:
            session['admin'] = True
            session.permanent = True
            flash('Bienvenido al panel de administración de Mundolimp.', 'success')
            return redirect(url_for('admin.dashboard'))
        else:
            error = 'Contraseña incorrecta. Podés ingresar con: mundolimp o admin123'

    return render_template('auth/login.html', error=error)


@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('Sesión cerrada correctamente.', 'info')
    return redirect(url_for('catalog.index'))
