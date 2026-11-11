import os
import uuid
from decimal import Decimal
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from werkzeug.utils import secure_filename
from app import db
from app.models import Product
from app.routes.auth import login_required

products_bp = Blueprint('products', __name__)

CATEGORIES = [
    'Lavandinas y Cloro',
    'Detergentes y Desengrasantes',
    'Jabones y Suavizantes',
    'Pisos y Aromatizantes',
    'Automotor e Industria',
    'Accesorios y Varios'
]
BADGES = ['', 'mas-vendido', 'oferta', 'nuevo']
PRESENTACIONES = ['Bidón 5 Litros', 'Botella 1 Litro', 'Bidón 10 Litros', 'Bidón 20 Litros', 'Suelto / Litro', 'Unidad']


def allowed_file(filename):
    allowed = current_app.config.get('ALLOWED_EXTENSIONS', {'png', 'jpg', 'jpeg', 'gif', 'webp'})
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed


def save_image(file):
    """Guarda imagen subida con nombre único. Retorna el nombre de archivo o None."""
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
    """Elimina imagen de la carpeta de uploads."""
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
    search = request.args.get('buscar', '').strip()
    categoria = request.args.get('categoria', '')

    query = Product.query

    if search:
        term = f'%{search}%'
        query = query.filter(
            db.or_(
                Product.name.ilike(term),
                Product.description.ilike(term),
                Product.category.ilike(term)
            )
        )

    if categoria:
        query = query.filter(Product.category == categoria)

    products = query.order_by(Product.created_at.desc()).all()

    return render_template(
        'admin/products/list.html',
        products=products,
        categories=CATEGORIES,
        search=search,
        selected_category=categoria
    )


@products_bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
def new_product():
    if request.method == 'POST':
        try:
            name = request.form.get('name', '').strip()
            description = request.form.get('description', '').strip()
            category = request.form.get('category', 'Lavandinas y Cloro')
            presentation = request.form.get('presentation', 'Bidón 5 Litros').strip()
            price_str = request.form.get('price', '0').replace('.', '').replace(',', '.').strip()
            price = Decimal(price_str or '0')
            badge = request.form.get('badge', '').strip()
            stock = request.form.get('stock') == 'on'

            if not name:
                flash('El nombre del producto es obligatorio.', 'danger')
                return render_template('admin/products/form.html', categories=CATEGORIES, badges=BADGES, presentaciones=PRESENTACIONES, product=None)

            # Subida de imagen
            image_filename = None
            if 'image' in request.files:
                image_filename = save_image(request.files['image'])

            product = Product(
                name=name,
                brand='Mundolimp',
                description=description or None,
                category=category,
                presentation=presentation or 'Bidón 5 Litros',
                price=price,
                sale_price_usd=price,  # compatibilidad
                badge=badge if badge else None,
                stock=stock,
                image_filename=image_filename
            )
            db.session.add(product)
            db.session.commit()
            flash(f'Producto "{name}" agregado exitosamente al catálogo.', 'success')
            return redirect(url_for('products.list_products'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear el producto: {str(e)}', 'danger')

    return render_template('admin/products/form.html', categories=CATEGORIES, badges=BADGES, presentaciones=PRESENTACIONES, product=None)


@products_bp.route('/<int:product_id>/editar', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)

    if request.method == 'POST':
        try:
            name = request.form.get('name', '').strip()
            description = request.form.get('description', '').strip()
            category = request.form.get('category', 'Lavandinas y Cloro')
            presentation = request.form.get('presentation', 'Bidón 5 Litros').strip()
            price_str = request.form.get('price', '0').replace('.', '').replace(',', '.').strip()
            price = Decimal(price_str or '0')
            badge = request.form.get('badge', '').strip()
            stock = request.form.get('stock') == 'on'

            if not name:
                flash('El nombre del producto es obligatorio.', 'danger')
                return render_template('admin/products/form.html', categories=CATEGORIES, badges=BADGES, presentaciones=PRESENTACIONES, product=product)

            product.name = name
            product.description = description or None
            product.category = category
            product.presentation = presentation or 'Bidón 5 Litros'
            product.price = price
            product.sale_price_usd = price
            product.badge = badge if badge else None
            product.stock = stock

            # Manejo de nueva foto
            if 'image' in request.files and request.files['image'].filename != '':
                new_image = save_image(request.files['image'])
                if new_image:
                    if product.image_filename:
                        delete_image(product.image_filename)
                    product.image_filename = new_image

            db.session.commit()
            flash(f'Producto "{product.name}" actualizado correctamente.', 'success')
            return redirect(url_for('products.list_products'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar el producto: {str(e)}', 'danger')

    return render_template('admin/products/form.html', categories=CATEGORIES, badges=BADGES, presentaciones=PRESENTACIONES, product=product)


@products_bp.route('/<int:product_id>/eliminar', methods=['POST'])
@login_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    name = product.name
    try:
        from app.models import Sale
        Sale.query.filter_by(product_id=product.id).delete()
        if product.image_filename:
            delete_image(product.image_filename)
        db.session.delete(product)
        db.session.commit()
        flash(f'Producto "{name}" eliminado del catálogo.', 'info')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar el producto: {str(e)}', 'danger')
    return redirect(url_for('products.list_products'))


@products_bp.route('/<int:product_id>/toggle-stock', methods=['POST'])
@login_required
def toggle_stock(product_id):
    product = Product.query.get_or_404(product_id)
    product.stock = not product.stock
    db.session.commit()
    estado = "Disponible" if product.stock else "Agotado"
    flash(f'Stock de "{product.name}" actualizado a {estado}.', 'success')
    return redirect(request.referrer or url_for('products.list_products'))


@products_bp.route('/vaciar-catalogo-viejo', methods=['POST'])
@login_required
def clear_old_catalog():
    """Elimina todos los productos viejos del catálogo y sus imágenes asociadas."""
    try:
        from app.models import Sale, BatchExpense, SaleBatch
        all_products = Product.query.all()
        for p in all_products:
            if p.image_filename:
                delete_image(p.image_filename)

        Sale.query.delete()
        BatchExpense.query.delete()
        SaleBatch.query.delete()
        Product.query.delete()
        db.session.commit()
        flash('Se eliminaron todos los productos viejos del catálogo correctamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al vaciar el catálogo: {str(e)}', 'danger')
    return redirect(url_for('products.list_products'))


@products_bp.route('/cargar-productos-mundolimp', methods=['POST'])
@login_required
def seed_mundolimp():
    """Carga productos iniciales típicos de Mundolimp en el catálogo."""
    try:
        sample_products = [
            {
                'name': 'Lavandina Concentrada 55g/l Mundolimp',
                'category': 'Lavandinas y Cloro',
                'presentation': 'Bidón 5 Litros',
                'price': Decimal('3200'),
                'description': 'Lavandina concentrada de máximo poder desinfectante. Ideal para superficies, pisos y sanitarios.',
                'badge': 'mas-vendido'
            },
            {
                'name': 'Cloro Líquido Puro Concentrado 100g/l',
                'category': 'Lavandinas y Cloro',
                'presentation': 'Bidón 5 Litros',
                'price': Decimal('4500'),
                'description': 'Cloro concentrado para desinfección profunda y mantenimiento de piletas.',
                'badge': ''
            },
            {
                'name': 'Detergente Ultra Desengrasante Limón',
                'category': 'Detergentes y Desengrasantes',
                'presentation': 'Bidón 5 Litros',
                'price': Decimal('3800'),
                'description': 'Fórmula espesa con alto poder desengrasante para vajilla, gastronomía y superficies grasas.',
                'badge': 'mas-vendido'
            },
            {
                'name': 'Desengrasante Multiuso Industrial',
                'category': 'Detergentes y Desengrasantes',
                'presentation': 'Bidón 5 Litros',
                'price': Decimal('4900'),
                'description': 'Removedor de grasas pesadas, aceites de cocina, campanas y talleres.',
                'badge': 'oferta'
            },
            {
                'name': 'Jabón Líquido para Ropa Tipo Ariel',
                'category': 'Jabones y Suavizantes',
                'presentation': 'Bidón 5 Litros',
                'price': Decimal('4200'),
                'description': 'Jabón baja espuma con agradable fragancia fresca. Protege las fibras textiles.',
                'badge': 'nuevo'
            },
            {
                'name': 'Suavizante Textil Celeste Floral',
                'category': 'Jabones y Suavizantes',
                'presentation': 'Bidón 5 Litros',
                'price': Decimal('3600'),
                'description': 'Deja las prendas suaves y perfumadas con microcápsulas de larga duración.',
                'badge': ''
            },
            {
                'name': 'Limpiador Desodorizante de Pisos Lavanda',
                'category': 'Pisos y Aromatizantes',
                'presentation': 'Bidón 5 Litros',
                'price': Decimal('2900'),
                'description': 'Limpiador líquido aromatizante para pisos cerámicos, mosaicos y porcelanatos.',
                'badge': ''
            },
            {
                'name': 'Cera Autobrillo Incolora',
                'category': 'Pisos y Aromatizantes',
                'presentation': 'Bidón 5 Litros',
                'price': Decimal('5200'),
                'description': 'Cera autobrillo antideslizante para pisos de alto tránsito.',
                'badge': ''
            },
            {
                'name': 'Silicona Perfumada para Automotor',
                'category': 'Automotor e Industria',
                'presentation': 'Bidón 5 Litros',
                'price': Decimal('6500'),
                'description': 'Brillo y protección para tableros, plásticos y vinilos automotores.',
                'badge': ''
            },
            {
                'name': 'Shampoo Siliconado para Autos',
                'category': 'Automotor e Industria',
                'presentation': 'Bidón 5 Litros',
                'price': Decimal('4100'),
                'description': 'Fórmula neutra de alto brillo para lavado de carrocerías.',
                'badge': ''
            }
        ]

        for p_data in sample_products:
            p = Product(
                name=p_data['name'],
                brand='Mundolimp',
                category=p_data['category'],
                presentation=p_data['presentation'],
                price=p_data['price'],
                sale_price_usd=p_data['price'],
                description=p_data['description'],
                badge=p_data['badge'] or None,
                stock=True
            )
            db.session.add(p)

        db.session.commit()
        flash('Se cargaron 10 productos base de Mundolimp exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al cargar productos iniciales: {str(e)}', 'danger')
    return redirect(url_for('products.list_products'))
