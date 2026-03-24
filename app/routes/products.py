import os
import uuid
from decimal import Decimal
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from werkzeug.utils import secure_filename
from app import db
from app.models import Product
from app.models import Product, Setting
from decimal import Decimal as _Decimal
from app.routes.auth import login_required

products_bp = Blueprint('products', __name__)

CATEGORIES = ['Smartphones', 'Impresoras', 'Tablets', 'Laptops', 'Accesorios']
BADGES = ['', 'mas-vendido', 'nuevo', 'oferta']


def allowed_file(filename):
    allowed = current_app.config.get('ALLOWED_EXTENSIONS', {'png', 'jpg', 'jpeg', 'gif', 'webp'})
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed


def save_image(file):
    """Save uploaded image with unique filename. Returns filename or None."""
    if not file or file.filename == '':
        return None
    if not allowed_file(file.filename):
        return None
    try:
        ext = file.filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}.{ext}"
        upload_folder = current_app.config.get('UPLOAD_FOLDER')
        os.makedirs(upload_folder, exist_ok=True)
        file_path = os.path.join(upload_folder, unique_filename)
        file.save(file_path)
        return unique_filename
    except Exception as e:
        current_app.logger.error(f"Error saving image: {e}")
        return None


def delete_image(filename):
    """Delete image file from uploads folder."""
    if not filename:
        return
    try:
        upload_folder = current_app.config.get('UPLOAD_FOLDER')
        file_path = os.path.join(upload_folder, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        current_app.logger.error(f"Error deleting image: {e}")


@products_bp.route('/')
@login_required
def list_products():
    search = request.args.get('buscar', '')
    categoria = request.args.get('categoria', '')

    query = Product.query

    if search:
        term = f'%{search}%'
        query = query.filter(
            db.or_(
                Product.name.ilike(term),
                Product.brand.ilike(term),
                Product.model.ilike(term)
            )
        )

    if categoria:
        query = query.filter(Product.category == categoria)

    products = query.order_by(Product.created_at.desc()).all()

    try:
        exchange_rate = _Decimal(Setting.get('exchange_rate', '1000'))
    except Exception:
        exchange_rate = _Decimal('1000')

    return render_template(
        'admin/products/list.html',
        products=products,
        categories=CATEGORIES,
        search=search,
        selected_category=categoria,
        exchange_rate=exchange_rate
    )


@products_bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
def new_product():
    if request.method == 'POST':
        try:
            name = request.form.get('name', '').strip()
            brand = request.form.get('brand', '').strip()
            model = request.form.get('model', '').strip()
            description = request.form.get('description', '').strip()
            category = request.form.get('category', 'Accesorios')
            badge = request.form.get('badge', '')
            cost_price_usd = Decimal(request.form.get('cost_price_usd', '0') or '0')
            sale_price_usd = Decimal(request.form.get('sale_price_usd', '0') or '0')
            stock = request.form.get('stock') == 'on'
            ram = request.form.get('ram', '').strip() or None
            storage = request.form.get('storage', '').strip() or None
            color = request.form.get('color', '').strip() or None

            if not name:
                flash('El nombre del producto es obligatorio.', 'danger')
                return render_template('admin/products/form.html', categories=CATEGORIES, badges=BADGES, product=None)

            # Handle image upload
            image_filename = None
            if 'image' in request.files:
                image_filename = save_image(request.files['image'])

            product = Product(
                name=name,
                brand=brand,
                model=model,
                description=description,
                category=category,
                badge=badge if badge else None,
                cost_price_usd=cost_price_usd,
                sale_price_usd=sale_price_usd,
                stock=stock,
                image_filename=image_filename,
                ram=ram,
                storage=storage,
                color=color
            )
            db.session.add(product)
            db.session.commit()
            flash(f'Producto "{name}" creado exitosamente.', 'success')
            return redirect(url_for('products.list_products'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear el producto: {str(e)}', 'danger')

    return render_template('admin/products/form.html', categories=CATEGORIES, badges=BADGES, product=None)


@products_bp.route('/<int:product_id>/editar', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)

    if request.method == 'POST':
        try:
            product.name = request.form.get('name', '').strip()
            product.brand = request.form.get('brand', '').strip()
            product.model = request.form.get('model', '').strip()
            product.description = request.form.get('description', '').strip()
            product.category = request.form.get('category', 'Accesorios')
            badge = request.form.get('badge', '')
            product.badge = badge if badge else None
            product.cost_price_usd = Decimal(request.form.get('cost_price_usd', '0') or '0')
            product.sale_price_usd = Decimal(request.form.get('sale_price_usd', '0') or '0')
            product.stock = request.form.get('stock') == 'on'
            product.ram = request.form.get('ram', '').strip() or None
            product.storage = request.form.get('storage', '').strip() or None
            product.color = request.form.get('color', '').strip() or None

            if not product.name:
                flash('El nombre del producto es obligatorio.', 'danger')
                return render_template('admin/products/form.html', categories=CATEGORIES, badges=BADGES, product=product)

            # Handle new image upload
            if 'image' in request.files and request.files['image'].filename != '':
                new_image = save_image(request.files['image'])
                if new_image:
                    # Delete old image
                    if product.image_filename:
                        delete_image(product.image_filename)
                    product.image_filename = new_image

            db.session.commit()
            flash(f'Producto "{product.name}" actualizado exitosamente.', 'success')
            return redirect(url_for('products.list_products'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar el producto: {str(e)}', 'danger')

    return render_template('admin/products/form.html', categories=CATEGORIES, badges=BADGES, product=product)


@products_bp.route('/<int:product_id>/eliminar', methods=['POST'])
@login_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    try:
        name = product.name
        # Delete image file
        if product.image_filename:
            delete_image(product.image_filename)
        db.session.delete(product)
        db.session.commit()
        flash(f'Producto "{name}" eliminado exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar el producto: {str(e)}', 'danger')
    return redirect(url_for('products.list_products'))


@products_bp.route('/<int:product_id>/toggle-stock', methods=['POST'])
@login_required
def toggle_stock(product_id):
    product = Product.query.get_or_404(product_id)
    try:
        product.stock = not product.stock
        db.session.commit()
        status = 'disponible' if product.stock else 'sin stock'
        return jsonify({'success': True, 'stock': product.stock, 'message': f'Producto marcado como {status}.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
