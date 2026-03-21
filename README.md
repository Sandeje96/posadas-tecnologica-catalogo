# PosadasTecnologica — Catálogo Digital y Gestión de Ventas

Sistema de catálogo digital y gestión de ventas para negocio de electrónica, construido con Flask y PostgreSQL.

---

## 1. Configuración Local (Desarrollo)

### Requisitos previos
- Python 3.10 o superior
- pip
- PostgreSQL (o SQLite para desarrollo rápido)

### Pasos

```bash
# 1. Clonar o descargar el proyecto
cd ProgramaCatalogos

# 2. Crear entorno virtual
python -m venv venv

# 3. Activar el entorno virtual
# En Windows:
venv\Scripts\activate
# En Linux/Mac:
source venv/bin/activate

# 4. Instalar dependencias
pip install -r requirements.txt

# 5. Crear archivo .env
cp .env.example .env
# Editar .env con tus valores reales
```

---

## 2. Variables de Entorno

Edita el archivo `.env` con los siguientes valores:

```env
SECRET_KEY=una-clave-secreta-muy-larga-y-aleatoria
DATABASE_URL=postgresql://usuario:contraseña@localhost:5432/posadastecno
ADMIN_PASSWORD=tu-contraseña-admin
```

Para desarrollo rápido con SQLite (sin PostgreSQL):
```env
DATABASE_URL=sqlite:///posadas.db
```

---

## 3. Configuración de la Base de Datos

```bash
# 1. Inicializar Flask-Migrate (solo la primera vez)
flask db init

# 2. Crear la migración inicial
flask db migrate -m "Tablas iniciales"

# 3. Aplicar la migración a la base de datos
flask db upgrade
```

### Ejecutar la aplicación en desarrollo

```bash
python run.py
```

La aplicación estará disponible en: `http://localhost:5000`

- **Catálogo público:** `http://localhost:5000/`
- **Panel admin:** `http://localhost:5000/admin/login`

---

## 4. Despliegue en Railway

### Pasos de despliegue

1. Crear cuenta en [railway.app](https://railway.app)
2. Crear un nuevo proyecto desde GitHub o subir el código
3. Railway detectará automáticamente el `Procfile` y usará NIXPACKS

```bash
# Si usas Railway CLI:
railway login
railway init
railway up
```

---

## 5. Agregar PostgreSQL en Railway

1. En tu proyecto de Railway, hacer clic en **"New Service"**
2. Seleccionar **"Database" → "PostgreSQL"**
3. Railway generará automáticamente la variable `DATABASE_URL`
4. Esta variable se pasa automáticamente al servicio de la aplicación

---

## 6. Configurar Variables de Entorno en Railway

En el panel de Railway, ir a tu servicio → **Variables** y agregar:

| Variable | Valor |
|----------|-------|
| `SECRET_KEY` | Una clave aleatoria larga (ej: usar `python -c "import secrets; print(secrets.token_hex(32))"`) |
| `ADMIN_PASSWORD` | Tu contraseña de administrador segura |
| `DATABASE_URL` | Se asigna automáticamente por PostgreSQL de Railway |

### Ejecutar migraciones en Railway

Después del primer deploy, ejecutar en la consola de Railway:

```bash
flask db upgrade
```

O agregar al comando de inicio:
```
flask db upgrade && gunicorn run:app
```

---

## 7. Almacenamiento de Imágenes en Railway

**IMPORTANTE:** Railway usa almacenamiento efímero. Las imágenes subidas se perderán al reiniciar el servidor.

### Opciones recomendadas para producción:

1. **Cloudinary (recomendado):** Servicio gratuito de almacenamiento de imágenes. Modificar `save_image()` en `app/routes/products.py` para subir a Cloudinary.

2. **AWS S3 / Backblaze B2:** Almacenamiento de objetos persistente.

3. **URLs externas:** En lugar de subir imágenes, agregar un campo `image_url` al modelo y usar URLs de imágenes externas (ej: del proveedor del producto).

Para desarrollo local el almacenamiento de archivos funciona normalmente en `app/static/uploads/`.

---

## Estructura del Proyecto

```
ProgramaCatalogos/
├── app/
│   ├── __init__.py          # Application factory
│   ├── models.py            # SQLAlchemy models
│   ├── routes/
│   │   ├── auth.py          # Login/logout
│   │   ├── catalog.py       # Catálogo público
│   │   ├── admin.py         # Dashboard
│   │   ├── products.py      # CRUD productos
│   │   ├── sales.py         # CRUD ventas + simulador
│   │   ├── customers.py     # CRUD clientes
│   │   └── config_routes.py # Configuración
│   ├── templates/           # Plantillas Jinja2
│   └── static/              # CSS, JS, uploads
├── config.py                # Configuración Flask
├── run.py                   # Punto de entrada
├── requirements.txt
├── Procfile
└── railway.json
```
