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
        from app.models import Sale, BatchExpense, SaleBatch, OrderItem
        all_products = Product.query.all()
        for p in all_products:
            if p.image_filename:
                delete_image(p.image_filename)

        OrderItem.query.delete()
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
    """Carga el catálogo completo de productos y presentaciones de Mundolimp."""
    try:
        sample_products = [
            # 1. Lavandinas y Cloro
            {'name': 'Lavandina Concentrada 55g/l', 'category': 'Lavandinas y Cloro', 'presentation': 'Bidón 5 Litros', 'price': Decimal('3200'), 'description': 'Lavandina de máxima pureza para desinfección profunda de superficies y sanitarios.', 'badge': 'mas-vendido'},
            {'name': 'Lavandina Concentrada 55g/l', 'category': 'Lavandinas y Cloro', 'presentation': 'Botella 1 Litro', 'price': Decimal('1100'), 'description': 'Lavandina concentrada 55g/l presentación 1 litro.', 'badge': ''},
            {'name': 'Lavandina Concentrada 55g/l', 'category': 'Lavandinas y Cloro', 'presentation': 'Bidón 20 Litros', 'price': Decimal('11500'), 'description': 'Bidón x 20 litros mayorista de lavandina concentrada.', 'badge': 'oferta'},
            {'name': 'Lavandina en Gel', 'category': 'Lavandinas y Cloro', 'presentation': 'Botella 1 Litro', 'price': Decimal('1600'), 'description': 'Lavandina en gel con mayor adherencia y poder blanqueador sin salpicaduras.', 'badge': 'nuevo'},
            {'name': 'Lavandina en Gel', 'category': 'Lavandinas y Cloro', 'presentation': 'Bidón 5 Litros', 'price': Decimal('4500'), 'description': 'Lavandina en gel presentación bidón 5 litros.', 'badge': ''},
            {'name': 'Lavandina Ropa Blanca', 'category': 'Lavandinas y Cloro', 'presentation': 'Botella 1 Litro', 'price': Decimal('1400'), 'description': 'Blanqueador formulado especialmente para el cuidado de prendas blancas.', 'badge': ''},
            {'name': 'Lavandina Ropa Blanca', 'category': 'Lavandinas y Cloro', 'presentation': 'Bidón 5 Litros', 'price': Decimal('3900'), 'description': 'Blanqueador para ropa blanca en bidón de 5 litros.', 'badge': ''},
            {'name': 'Lavandina Ropa Color', 'category': 'Lavandinas y Cloro', 'presentation': 'Botella 1 Litro', 'price': Decimal('1500'), 'description': 'Limpiador desinfectante a base de oxígeno activo que protege los colores.', 'badge': ''},
            {'name': 'Lavandina Ropa Color', 'category': 'Lavandinas y Cloro', 'presentation': 'Bidón 5 Litros', 'price': Decimal('4200'), 'description': 'Oxígeno activo para ropa color en bidón de 5 litros.', 'badge': 'mas-vendido'},
            {'name': 'Lavandina Ropa Color', 'category': 'Lavandinas y Cloro', 'presentation': 'Bidón 20 Litros', 'price': Decimal('15000'), 'description': 'Bidón de 20 litros para lavaderos y uso comercial.', 'badge': ''},
            {'name': 'Hipoclorito de Sodio Puro 100g/l', 'category': 'Lavandinas y Cloro', 'presentation': 'Bidón 5 Litros', 'price': Decimal('4800'), 'description': 'Cloro puro concentrado para desinfección rigurosa y tratamiento de aguas.', 'badge': 'oferta'},
            {'name': 'Hipoclorito de Sodio Puro 100g/l', 'category': 'Lavandinas y Cloro', 'presentation': 'Bidón 20 Litros', 'price': Decimal('17500'), 'description': 'Bidón de 20 litros de hipoclorito de sodio puro concentrado.', 'badge': ''},
            {'name': 'Cloro Granulado para Piletas', 'category': 'Lavandinas y Cloro', 'presentation': 'Botella 1 Litro', 'price': Decimal('7500'), 'description': 'Cloro granulado de disolución rápida para mantenimiento de piscinas.', 'badge': ''},
            {'name': 'Pastillas de Cloro Triple Acción x50gr', 'category': 'Lavandinas y Cloro', 'presentation': 'Botella 1 Litro', 'price': Decimal('8200'), 'description': 'Pastillas de cloro x 50g con alguicida y clarificador para boyas de pileta.', 'badge': ''},
            {'name': 'Pastillas de Cloro x200gr', 'category': 'Lavandinas y Cloro', 'presentation': 'Botella 1 Litro', 'price': Decimal('8200'), 'description': 'Pastillas grandes de 200 gramos para mantenimiento prolongado.', 'badge': ''},
            {'name': 'Alguicida Concentrado para Piscinas', 'category': 'Lavandinas y Cloro', 'presentation': 'Botella 1 Litro', 'price': Decimal('4200'), 'description': 'Previene y elimina formación de algas, hongos y verdín en el agua.', 'badge': ''},
            {'name': 'Alguicida Concentrado para Piscinas', 'category': 'Lavandinas y Cloro', 'presentation': 'Bidón 5 Litros', 'price': Decimal('14500'), 'description': 'Alguicida concentrado presentación profesional bidón 5 litros.', 'badge': ''},
            {'name': 'Clarificador Floculante para Piscinas', 'category': 'Lavandinas y Cloro', 'presentation': 'Botella 1 Litro', 'price': Decimal('3900'), 'description': 'Decanta partículas en suspensión dejando el agua transparente y cristalina.', 'badge': ''},
            {'name': 'Clarificador Floculante para Piscinas', 'category': 'Lavandinas y Cloro', 'presentation': 'Bidón 5 Litros', 'price': Decimal('13500'), 'description': 'Clarificador floculante presentación bidón 5 litros.', 'badge': ''},
            {'name': 'Regulador PH +', 'category': 'Lavandinas y Cloro', 'presentation': 'Botella 1 Litro', 'price': Decimal('3500'), 'description': 'Incrementador de pH para aguas de piscinas.', 'badge': ''},
            {'name': 'Regulador PH -', 'category': 'Lavandinas y Cloro', 'presentation': 'Botella 1 Litro', 'price': Decimal('3500'), 'description': 'Reductor de pH para aguas de piscinas.', 'badge': ''},

            # 2. Detergentes y Desengrasantes
            {'name': 'Detergente al 10% Ultra Espumoso', 'category': 'Detergentes y Desengrasantes', 'presentation': 'Bidón 5 Litros', 'price': Decimal('3800'), 'description': 'Detergente concentrado con gran poder desengrasante y agradable aroma.', 'badge': 'mas-vendido'},
            {'name': 'Detergente al 10% Ultra Espumoso', 'category': 'Detergentes y Desengrasantes', 'presentation': 'Botella 1 Litro', 'price': Decimal('1200'), 'description': 'Detergente al 10% presentación 1 litro.', 'badge': ''},
            {'name': 'Detergente al 10% Ultra Espumoso', 'category': 'Detergentes y Desengrasantes', 'presentation': 'Bidón 20 Litros', 'price': Decimal('13800'), 'description': 'Bidón x 20 litros mayorista de detergente al 10%.', 'badge': 'oferta'},
            {'name': 'Detergente Institucional Gastronómico', 'category': 'Detergentes y Desengrasantes', 'presentation': 'Bidón 5 Litros', 'price': Decimal('4600'), 'description': 'Fórmula espesa para gastronomía, rotiserías y cocinas profesionales.', 'badge': ''},
            {'name': 'Detergente Institucional Gastronómico', 'category': 'Detergentes y Desengrasantes', 'presentation': 'Bidón 20 Litros', 'price': Decimal('16500'), 'description': 'Detergente gastronómico institucional en bidón de 20 litros.', 'badge': ''},
            {'name': 'Desengrasante Amarillo Multiuso', 'category': 'Detergentes y Desengrasantes', 'presentation': 'Bidón 5 Litros', 'price': Decimal('4500'), 'description': 'Disuelve grasas vegetales y animales en mesadas, hornos y pisos.', 'badge': 'mas-vendido'},
            {'name': 'Desengrasante Amarillo Multiuso', 'category': 'Detergentes y Desengrasantes', 'presentation': 'Botella 1 Litro', 'price': Decimal('1400'), 'description': 'Desengrasante amarillo presentación 1 litro.', 'badge': ''},
            {'name': 'Desengrasante Amarillo Multiuso', 'category': 'Detergentes y Desengrasantes', 'presentation': 'Bidón 20 Litros', 'price': Decimal('16000'), 'description': 'Desengrasante amarillo en bidón de 20 litros.', 'badge': ''},
            {'name': 'Desengrasante BB Pesado Industrial', 'category': 'Detergentes y Desengrasantes', 'presentation': 'Bidón 5 Litros', 'price': Decimal('4900'), 'description': 'Máxima potencia para campanas extractoras, parrillas y suciedad pesada.', 'badge': 'oferta'},
            {'name': 'Desengrasante BB Pesado Industrial', 'category': 'Detergentes y Desengrasantes', 'presentation': 'Botella 1 Litro', 'price': Decimal('1500'), 'description': 'Desengrasante pesado BB presentación 1 litro.', 'badge': ''},
            {'name': 'Desengrasante BB Pesado Industrial', 'category': 'Detergentes y Desengrasantes', 'presentation': 'Bidón 20 Litros', 'price': Decimal('17500'), 'description': 'Bidón de 20 litros de desengrasante industrial BB.', 'badge': ''},
            {'name': 'Limpiador Multiuso Concentrado', 'category': 'Detergentes y Desengrasantes', 'presentation': 'Bidón 5 Litros', 'price': Decimal('3900'), 'description': 'Limpiador desengrasante apto para toda clase de superficies lavables.', 'badge': ''},
            {'name': 'Limpiador Multiuso Concentrado', 'category': 'Detergentes y Desengrasantes', 'presentation': 'Botella 1 Litro', 'price': Decimal('1200'), 'description': 'Limpiador multiuso presentación 1 litro.', 'badge': ''},
            {'name': 'Limpiador Cremoso Tipo CIF', 'category': 'Detergentes y Desengrasantes', 'presentation': 'Botella 1 Litro', 'price': Decimal('1800'), 'description': 'Limpiador cremoso con micropartículas para manchas difíciles.', 'badge': ''},
            {'name': 'Limpiador Cremoso Tipo CIF', 'category': 'Detergentes y Desengrasantes', 'presentation': 'Bidón 5 Litros', 'price': Decimal('5500'), 'description': 'Limpiador cremoso presentación bidón 5 litros.', 'badge': ''},
            {'name': 'Limpimax Desinfectante', 'category': 'Detergentes y Desengrasantes', 'presentation': 'Bidón 5 Litros', 'price': Decimal('4200'), 'description': 'Desinfectante y limpiador de alto rendimiento para instituciones.', 'badge': ''},
            {'name': 'Quita Sarro Concentrado', 'category': 'Detergentes y Desengrasantes', 'presentation': 'Botella 1 Litro', 'price': Decimal('2100'), 'description': 'Remueve incrustaciones de sarro y óxido en sanitarios y griferías.', 'badge': ''},
            {'name': 'Destapa Cañerías Potente', 'category': 'Detergentes y Desengrasantes', 'presentation': 'Botella 1 Litro', 'price': Decimal('2400'), 'description': 'Fórmula de rápida acción para disolver grasas, cabellos y residuos.', 'badge': 'oferta'},
            {'name': 'Soda Líquida al 25%', 'category': 'Detergentes y Desengrasantes', 'presentation': 'Bidón 5 Litros', 'price': Decimal('7200'), 'description': 'Solución cáustica para limpieza profunda y destapes difíciles.', 'badge': ''},
            {'name': 'Soda Cáustica en Escamas Pura', 'category': 'Detergentes y Desengrasantes', 'presentation': 'Botella 1 Litro', 'price': Decimal('3800'), 'description': 'Soda cáustica pura en escamas 1 kg.', 'badge': ''},
            {'name': 'Vinagre de Limpieza Concentrado', 'category': 'Detergentes y Desengrasantes', 'presentation': 'Botella 1 Litro', 'price': Decimal('1300'), 'description': 'Vinagre de alcohol concentrado natural para brillo y desodorización.', 'badge': ''},
            {'name': 'Vinagre de Limpieza Concentrado', 'category': 'Detergentes y Desengrasantes', 'presentation': 'Bidón 5 Litros', 'price': Decimal('3800'), 'description': 'Vinagre de limpieza en bidón de 5 litros.', 'badge': ''},

            # 3. Jabones y Suavizantes
            {'name': 'Jabón Líquido para Ropa Azul (Tipo Ariel)', 'category': 'Jabones y Suavizantes', 'presentation': 'Bidón 5 Litros', 'price': Decimal('4200'), 'description': 'Fórmula baja espuma para lavarropas automáticos con fragancia duradera.', 'badge': 'mas-vendido'},
            {'name': 'Jabón Líquido para Ropa Azul (Tipo Ariel)', 'category': 'Jabones y Suavizantes', 'presentation': 'Botella 1 Litro', 'price': Decimal('1300'), 'description': 'Jabón líquido azul presentación 1 litro.', 'badge': ''},
            {'name': 'Jabón Líquido para Ropa Azul (Tipo Ariel)', 'category': 'Jabones y Suavizantes', 'presentation': 'Bidón 20 Litros', 'price': Decimal('15500'), 'description': 'Jabón líquido azul para lavaderos bidón 20 litros.', 'badge': 'oferta'},
            {'name': 'Jabón Líquido para Ropa Verde (Tipo Skip)', 'category': 'Jabones y Suavizantes', 'presentation': 'Bidón 5 Litros', 'price': Decimal('4200'), 'description': 'Remueve suciedades profundas cuidando los tejidos y colores.', 'badge': 'nuevo'},
            {'name': 'Jabón Líquido para Ropa Verde (Tipo Skip)', 'category': 'Jabones y Suavizantes', 'presentation': 'Botella 1 Litro', 'price': Decimal('1300'), 'description': 'Jabón líquido verde presentación 1 litro.', 'badge': ''},
            {'name': 'Jabón Líquido para Ropa Verde (Tipo Skip)', 'category': 'Jabones y Suavizantes', 'presentation': 'Bidón 20 Litros', 'price': Decimal('15500'), 'description': 'Jabón líquido verde para ropa bidón 20 litros.', 'badge': ''},
            {'name': 'Jabón Líquido para Ropa Premium', 'category': 'Jabones y Suavizantes', 'presentation': 'Bidón 5 Litros', 'price': Decimal('4800'), 'description': 'Máxima concentración con enzimas activas quitamanchas.', 'badge': ''},
            {'name': 'Suavizante Textil Celeste Floral', 'category': 'Jabones y Suavizantes', 'presentation': 'Bidón 5 Litros', 'price': Decimal('3600'), 'description': 'Aroma clásico fresco con microcápsulas suavizantes.', 'badge': 'mas-vendido'},
            {'name': 'Suavizante Textil Celeste Floral', 'category': 'Jabones y Suavizantes', 'presentation': 'Botella 1 Litro', 'price': Decimal('1100'), 'description': 'Suavizante celeste presentación 1 litro.', 'badge': ''},
            {'name': 'Suavizante Textil Celeste Floral', 'category': 'Jabones y Suavizantes', 'presentation': 'Bidón 20 Litros', 'price': Decimal('13000'), 'description': 'Suavizante celeste mayorista bidón 20 litros.', 'badge': ''},
            {'name': 'Suavizante Textil Blanco Toque de Bebé', 'category': 'Jabones y Suavizantes', 'presentation': 'Bidón 5 Litros', 'price': Decimal('3600'), 'description': 'Suavizante hipoalergénico con aroma suave y delicado.', 'badge': ''},
            {'name': 'Suavizante Textil Blanco Toque de Bebé', 'category': 'Jabones y Suavizantes', 'presentation': 'Bidón 20 Litros', 'price': Decimal('13000'), 'description': 'Suavizante blanco bidón 20 litros.', 'badge': ''},
            {'name': 'Suavizante Textil Rosado Primavera', 'category': 'Jabones y Suavizantes', 'presentation': 'Bidón 5 Litros', 'price': Decimal('3600'), 'description': 'Suavizante con fragancia dulce floral de larga permanencia.', 'badge': ''},
            {'name': 'Suavizante Textil Rosado Primavera', 'category': 'Jabones y Suavizantes', 'presentation': 'Bidón 20 Litros', 'price': Decimal('13000'), 'description': 'Suavizante rosado bidón 20 litros.', 'badge': ''},
            {'name': 'Suavizante Celeste Doble Perfume', 'category': 'Jabones y Suavizantes', 'presentation': 'Bidón 5 Litros', 'price': Decimal('4200'), 'description': 'Edición especial con doble carga de aroma para ropa intensamente perfumada.', 'badge': 'nuevo'},
            {'name': 'Suavizante Blanco Doble Perfume', 'category': 'Jabones y Suavizantes', 'presentation': 'Bidón 5 Litros', 'price': Decimal('4200'), 'description': 'Doble concentración de fragancia suave para sábanas y toallas.', 'badge': ''},
            {'name': 'Shampoo para Manos Vainilla', 'category': 'Jabones y Suavizantes', 'presentation': 'Botella 1 Litro', 'price': Decimal('1800'), 'description': 'Jabón líquido humectante con exquisito aroma a vainilla.', 'badge': ''},
            {'name': 'Shampoo para Manos Vainilla', 'category': 'Jabones y Suavizantes', 'presentation': 'Bidón 5 Litros', 'price': Decimal('5200'), 'description': 'Shampoo de manos vainilla bidón 5 litros.', 'badge': ''},
            {'name': 'Shampoo para Manos Manzana', 'category': 'Jabones y Suavizantes', 'presentation': 'Botella 1 Litro', 'price': Decimal('1800'), 'description': 'Jabón líquido cremoso con aroma frutal a manzana verde.', 'badge': ''},
            {'name': 'Shampoo para Manos Rosas', 'category': 'Jabones y Suavizantes', 'presentation': 'Botella 1 Litro', 'price': Decimal('1800'), 'description': 'Jabón líquido con extracto de rosas y agentes suavizantes.', 'badge': ''},
            {'name': 'Shampoo para Manos Neutro', 'category': 'Jabones y Suavizantes', 'presentation': 'Bidón 5 Litros', 'price': Decimal('5200'), 'description': 'Jabón líquido neutro sin colorantes para uso gastronómico y clínico.', 'badge': ''},

            # 4. Pisos y Aromatizantes
            {'name': 'Limpiador de Pisos Lavanda', 'category': 'Pisos y Aromatizantes', 'presentation': 'Bidón 5 Litros', 'price': Decimal('2900'), 'description': 'Desodorizante aromatizante con fragancia fresca y relajante a lavanda.', 'badge': 'mas-vendido'},
            {'name': 'Limpiador de Pisos Lavanda', 'category': 'Pisos y Aromatizantes', 'presentation': 'Botella 1 Litro', 'price': Decimal('950'), 'description': 'Limpiador lavanda presentación 1 litro.', 'badge': ''},
            {'name': 'Limpiador de Pisos Lavanda', 'category': 'Pisos y Aromatizantes', 'presentation': 'Bidón 20 Litros', 'price': Decimal('10500'), 'description': 'Limpiador de pisos lavanda bidón 20 litros.', 'badge': 'oferta'},
            {'name': 'Limpiador de Pisos Citronella (Repelente)', 'category': 'Pisos y Aromatizantes', 'presentation': 'Bidón 5 Litros', 'price': Decimal('2900'), 'description': 'Eficaz repelente natural de insectos y mosquitos con rico aroma.', 'badge': 'mas-vendido'},
            {'name': 'Limpiador de Pisos Citronella (Repelente)', 'category': 'Pisos y Aromatizantes', 'presentation': 'Botella 1 Litro', 'price': Decimal('950'), 'description': 'Limpiador citronella presentación 1 litro.', 'badge': ''},
            {'name': 'Limpiador de Pisos Citronella (Repelente)', 'category': 'Pisos y Aromatizantes', 'presentation': 'Bidón 20 Litros', 'price': Decimal('10500'), 'description': 'Limpiador citronella bidón 20 litros.', 'badge': ''},
            {'name': 'Limpiador de Pisos Cherry Dulce', 'category': 'Pisos y Aromatizantes', 'presentation': 'Bidón 5 Litros', 'price': Decimal('2900'), 'description': 'Intensa fragancia dulce de cereza que perdura horas.', 'badge': ''},
            {'name': 'Limpiador de Pisos Cherry Dulce', 'category': 'Pisos y Aromatizantes', 'presentation': 'Botella 1 Litro', 'price': Decimal('950'), 'description': 'Limpiador cherry presentación 1 litro.', 'badge': ''},
            {'name': 'Limpiador de Pisos Lysoform Desinfectante', 'category': 'Pisos y Aromatizantes', 'presentation': 'Bidón 5 Litros', 'price': Decimal('2900'), 'description': 'Aroma desinfectante similar a lysoform para máxima sensación de limpieza.', 'badge': ''},
            {'name': 'Limpiador de Pisos Lysoform Desinfectante', 'category': 'Pisos y Aromatizantes', 'presentation': 'Botella 1 Litro', 'price': Decimal('950'), 'description': 'Limpiador lysoform presentación 1 litro.', 'badge': ''},
            {'name': 'Limpiador de Pisos Marino', 'category': 'Pisos y Aromatizantes', 'presentation': 'Bidón 5 Litros', 'price': Decimal('2900'), 'description': 'Brisa marina refrescante para ambientes ventilados.', 'badge': ''},
            {'name': 'Limpiador de Pisos Pino / Pinolux', 'category': 'Pisos y Aromatizantes', 'presentation': 'Bidón 5 Litros', 'price': Decimal('2900'), 'description': 'Aroma tradicional a pino silvestre desinfectante.', 'badge': ''},
            {'name': 'Limpiador de Pisos Procenex / Espadol', 'category': 'Pisos y Aromatizantes', 'presentation': 'Bidón 5 Litros', 'price': Decimal('2900'), 'description': 'Fragancia herbal antiséptica para todo tipo de pisos.', 'badge': ''},
            {'name': 'Limpiador de Pisos Primavera Floral', 'category': 'Pisos y Aromatizantes', 'presentation': 'Bidón 5 Litros', 'price': Decimal('2900'), 'description': 'Mezcla floral primaveral fresca.', 'badge': ''},
            {'name': 'Cera Autobrillo Incolora', 'category': 'Pisos y Aromatizantes', 'presentation': 'Bidón 5 Litros', 'price': Decimal('5200'), 'description': 'Cera autobrillante transparente antideslizante para mosaicos y cerámicas.', 'badge': 'mas-vendido'},
            {'name': 'Cera Autobrillo Incolora', 'category': 'Pisos y Aromatizantes', 'presentation': 'Botella 1 Litro', 'price': Decimal('1600'), 'description': 'Cera incolora presentación 1 litro.', 'badge': ''},
            {'name': 'Cera Autobrillo Roja', 'category': 'Pisos y Aromatizantes', 'presentation': 'Bidón 5 Litros', 'price': Decimal('5200'), 'description': 'Realza y unifica el tono en pisos cerámicos y baldosas rojas.', 'badge': ''},
            {'name': 'Cera Autobrillo Roja', 'category': 'Pisos y Aromatizantes', 'presentation': 'Botella 1 Litro', 'price': Decimal('1600'), 'description': 'Cera roja presentación 1 litro.', 'badge': ''},
            {'name': 'Cera Autobrillo Negra', 'category': 'Pisos y Aromatizantes', 'presentation': 'Bidón 5 Litros', 'price': Decimal('5200'), 'description': 'Protección y brillo uniforme para pisos oscuros y granito negro.', 'badge': ''},
            {'name': 'Esencia Pura Citronela Concentrada', 'category': 'Pisos y Aromatizantes', 'presentation': 'Botella 1 Litro', 'price': Decimal('2800'), 'description': 'Esencia concentrada para dilución y hornillos de aromatización.', 'badge': ''},
            {'name': 'Esencia Pura Lavanda Concentrada', 'category': 'Pisos y Aromatizantes', 'presentation': 'Botella 1 Litro', 'price': Decimal('2800'), 'description': 'Esencia pura para perfumar y aromatizar ambientes.', 'badge': ''},
            {'name': 'Esencia Pura Cherry Concentrada', 'category': 'Pisos y Aromatizantes', 'presentation': 'Botella 1 Litro', 'price': Decimal('2800'), 'description': 'Esencia concentrada de cereza dulce.', 'badge': ''},
            {'name': 'Perfume Textil y Ambientes Coniglio', 'category': 'Pisos y Aromatizantes', 'presentation': 'Botella 1 Litro', 'price': Decimal('3900'), 'description': 'Fragancia textil premium para cortinas, sillones y ropa.', 'badge': 'mas-vendido'},
            {'name': 'Perfume Textil y Ambientes Cocovai', 'category': 'Pisos y Aromatizantes', 'presentation': 'Botella 1 Litro', 'price': Decimal('3900'), 'description': 'Dulce fragancia tropical a coco y vainilla.', 'badge': ''},
            {'name': 'Perfume Textil y Ambientes Vivere', 'category': 'Pisos y Aromatizantes', 'presentation': 'Botella 1 Litro', 'price': Decimal('3900'), 'description': 'Aroma clásico a ropa recién lavada.', 'badge': ''},

            # 5. Automotor e Industria
            {'name': 'Shampoo Siliconado para Carrocerías', 'category': 'Automotor e Industria', 'presentation': 'Bidón 5 Litros', 'price': Decimal('4100'), 'description': 'Shampoo neutro para lavado de autos con siliconas que protegen la pintura.', 'badge': 'mas-vendido'},
            {'name': 'Shampoo Siliconado para Carrocerías', 'category': 'Automotor e Industria', 'presentation': 'Botella 1 Litro', 'price': Decimal('1300'), 'description': 'Shampoo siliconado para autos presentación 1 litro.', 'badge': ''},
            {'name': 'Shampoo Siliconado para Carrocerías', 'category': 'Automotor e Industria', 'presentation': 'Bidón 20 Litros', 'price': Decimal('14800'), 'description': 'Bidón x 20 litros especial para lavaderos de autos.', 'badge': 'oferta'},
            {'name': 'Shampoo Teflonado de Alto Brillo', 'category': 'Automotor e Industria', 'presentation': 'Bidón 5 Litros', 'price': Decimal('4900'), 'description': 'Efecto perlado anti-adhesivo para suciedad y agua.', 'badge': 'nuevo'},
            {'name': 'Limpia Tapizados y Alfombras', 'category': 'Automotor e Industria', 'presentation': 'Bidón 5 Litros', 'price': Decimal('5500'), 'description': 'Espuma activa para limpieza de butacas, tapizados de autos y colchones.', 'badge': ''},
            {'name': 'Limpia Tapizados y Alfombras', 'category': 'Automotor e Industria', 'presentation': 'Botella 1 Litro', 'price': Decimal('1700'), 'description': 'Limpia tapizados presentación 1 litro.', 'badge': ''},
            {'name': 'Mekasil Desengrasante Motores y Chasis', 'category': 'Automotor e Industria', 'presentation': 'Bidón 5 Litros', 'price': Decimal('6200'), 'description': 'Desengrasante emulsionable para hidrocarburos, motores y piezas mecánicas.', 'badge': 'mas-vendido'},
            {'name': 'Mekasil Desengrasante Motores y Chasis', 'category': 'Automotor e Industria', 'presentation': 'Botella 1 Litro', 'price': Decimal('1900'), 'description': 'Mekasil desengrasante presentación 1 litro.', 'badge': ''},
            {'name': 'Mekasil Desengrasante Motores y Chasis', 'category': 'Automotor e Industria', 'presentation': 'Bidón 20 Litros', 'price': Decimal('22000'), 'description': 'Mekasil bidón x 20 litros para talleres y lavaderos.', 'badge': ''},
            {'name': 'Mekasil Super Concentrado Industrial', 'category': 'Automotor e Industria', 'presentation': 'Bidón 5 Litros', 'price': Decimal('7500'), 'description': 'Ultra poder solvente para grasas petroleras pesadas.', 'badge': 'oferta'},
            {'name': 'Silicona en Crema para Tableros y Vinilos', 'category': 'Automotor e Industria', 'presentation': 'Botella 1 Litro', 'price': Decimal('3600'), 'description': 'Restaura y protege plásticos, cueros y tableros contra rayos UV.', 'badge': 'mas-vendido'},
            {'name': 'Silicona en Crema para Tableros y Vinilos', 'category': 'Automotor e Industria', 'presentation': 'Bidón 5 Litros', 'price': Decimal('11800'), 'description': 'Silicona en crema bidón 5 litros.', 'badge': ''},
            {'name': 'Renovador de Caucho y Cubiertas Premium', 'category': 'Automotor e Industria', 'presentation': 'Botella 1 Litro', 'price': Decimal('2900'), 'description': 'Abrillantador negro brillante para neumáticos y gomas.', 'badge': ''},
            {'name': 'Renovador de Caucho y Cubiertas Premium', 'category': 'Automotor e Industria', 'presentation': 'Bidón 5 Litros', 'price': Decimal('9800'), 'description': 'Renovador de cubiertas bidón 5 litros.', 'badge': ''},
            {'name': 'Limpia Vidrios y Parabrisas Desengrasante', 'category': 'Automotor e Industria', 'presentation': 'Botella 1 Litro', 'price': Decimal('1200'), 'description': 'Fórmula antiempañante que no deja marcas ni vetas.', 'badge': ''},
            {'name': 'Limpia Vidrios y Parabrisas Desengrasante', 'category': 'Automotor e Industria', 'presentation': 'Bidón 5 Litros', 'price': Decimal('3800'), 'description': 'Limpia vidrios bidón 5 litros.', 'badge': ''},
            {'name': 'Removedor de Cemento y Sarro de Obra', 'category': 'Automotor e Industria', 'presentation': 'Bidón 5 Litros', 'price': Decimal('6900'), 'description': 'Limpia restos de pastina, cemento y mortero en finales de obra.', 'badge': ''},
            {'name': 'Kaotrina Insecticida Concentrado', 'category': 'Automotor e Industria', 'presentation': 'Botella 1 Litro', 'price': Decimal('4800'), 'description': 'Control eficaz de insectos rastreros y voladores.', 'badge': ''},

            # 6. Accesorios y Varios
            {'name': 'Trapo de Piso Uruguayense Pesado', 'category': 'Accesorios y Varios', 'presentation': 'Unidad', 'price': Decimal('1400'), 'description': 'Trapo de algodón blanco tejido reforzado de gran absorción.', 'badge': 'mas-vendido'},
            {'name': 'Trapo de Piso Consorcio Gigante', 'category': 'Accesorios y Varios', 'presentation': 'Unidad', 'price': Decimal('2200'), 'description': 'Medida extra grande ideal para pasillos y consorcios.', 'badge': ''},
            {'name': 'Paño de Microfibra Especial para Autos 50x60', 'category': 'Accesorios y Varios', 'presentation': 'Unidad', 'price': Decimal('1800'), 'description': 'Microfibra de secado rápido que no raya la pintura.', 'badge': 'mas-vendido'},
            {'name': 'Franela de Algodón Suave', 'category': 'Accesorios y Varios', 'presentation': 'Unidad', 'price': Decimal('1200'), 'description': 'Franela clásica para lustre de muebles y vehículos.', 'badge': ''},
            {'name': 'Rejilla Doble de Algodón', 'category': 'Accesorios y Varios', 'presentation': 'Unidad', 'price': Decimal('950'), 'description': 'Rejilla tejida para cocina y limpieza general.', 'badge': ''},
            {'name': 'Esponja de Fibra Dorada/Verde', 'category': 'Accesorios y Varios', 'presentation': 'Unidad', 'price': Decimal('600'), 'description': 'Esponja multiuso doble cara para lavado.', 'badge': ''},
            {'name': 'Esponja Salvaúñas Reforzada', 'category': 'Accesorios y Varios', 'presentation': 'Unidad', 'price': Decimal('750'), 'description': 'Diseño ergonómico con protección de uñas.', 'badge': ''},
            {'name': 'Secador de Piso Doble Goma 40cm', 'category': 'Accesorios y Varios', 'presentation': 'Unidad', 'price': Decimal('3200'), 'description': 'Secador reforzado de doble labio de goma.', 'badge': ''},
            {'name': 'Secador de Piso Reforzado 50cm', 'category': 'Accesorios y Varios', 'presentation': 'Unidad', 'price': Decimal('4100'), 'description': 'Secador amplio para grandes superficies.', 'badge': ''},
            {'name': 'Escobillón Gondola Cerdas Suaves', 'category': 'Accesorios y Varios', 'presentation': 'Unidad', 'price': Decimal('3800'), 'description': 'Escobillón de excelente barrido para interiores.', 'badge': ''},
            {'name': 'Escoba de Paja Tradicional 5 Hilos', 'category': 'Accesorios y Varios', 'presentation': 'Unidad', 'price': Decimal('4500'), 'description': 'Escoba de paja reforzada para veredas y patios.', 'badge': ''},
            {'name': 'Cabo de Madera Reforzado 1.30m', 'category': 'Accesorios y Varios', 'presentation': 'Unidad', 'price': Decimal('1500'), 'description': 'Cabo con rosca universal para escobillón o secador.', 'badge': ''},
            {'name': 'Pulverizador con Gatillo Graduable 500cc', 'category': 'Accesorios y Varios', 'presentation': 'Unidad', 'price': Decimal('1800'), 'description': 'Botella con pistola atomizadora regulable.', 'badge': ''},
            {'name': 'Pulverizador con Gatillo Graduable 1 Litro', 'category': 'Accesorios y Varios', 'presentation': 'Unidad', 'price': Decimal('2400'), 'description': 'Pulverizador de 1 litro para aplicaciones continuas.', 'badge': ''},
            {'name': 'Papel Higiénico New Pel x 80 Metros', 'category': 'Accesorios y Varios', 'presentation': 'Unidad', 'price': Decimal('3400'), 'description': 'Pack de papel higiénico institucional de 80 metros.', 'badge': ''},
            {'name': 'Rollo de Cocina New Pel x 200 Paños', 'category': 'Accesorios y Varios', 'presentation': 'Unidad', 'price': Decimal('2600'), 'description': 'Rollo de cocina gigante alta absorción.', 'badge': ''},
        ]

        # Opcional: si el catálogo tenía solo celulares viejos o si se pide reset, limpiarlos antes
        from app.models import Sale, BatchExpense, SaleBatch, OrderItem
        existing_count = Product.query.count()
        first_p = Product.query.first()
        is_old_catalog = first_p and (
            'celular' in first_p.name.lower() or 
            'iphone' in first_p.name.lower() or 
            'samsung' in first_p.name.lower() or 
            'motorola' in first_p.name.lower() or 
            'xiaomi' in first_p.name.lower() or 
            existing_count > 80
        )
        if is_old_catalog or request.args.get('reset') == '1':
            all_products = Product.query.all()
            for p in all_products:
                if p.image_filename:
                    delete_image(p.image_filename)
            OrderItem.query.delete()
            Sale.query.delete()
            BatchExpense.query.delete()
            SaleBatch.query.delete()
            Product.query.delete()

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
        flash(f'¡Catálogo actualizado con éxito! Se cargaron {len(sample_products)} productos reales de Mundolimp.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al cargar catálogo de Mundolimp: {str(e)}', 'danger')
    return redirect(url_for('products.list_products'))
