# CLAUDE.md — Catálogo para Vendedores · PosadasTecnologica

## Descripción del proyecto

Aplicación web interna para vendedores de **PosadasTecnologica**. Permite consultar el catálogo de productos con precios actualizados, filtrar por categoría, buscar por nombre/modelo, y compartir productos rápidamente con clientes vía WhatsApp. No es pública: está pensada para uso exclusivo del equipo de ventas.

---

## Stack tecnológico

- **Frontend:** React + Vite
- **Estilos:** Tailwind CSS (sin librerías de componentes externas salvo iconos)
- **Iconos:** Lucide React
- **Datos:** JSON local (`/src/data/productos.json`) — sin backend por ahora
- **Despliegue:** GitHub Pages o Netlify (build estático)

---

## Identidad visual

### Paleta de colores

| Variable CSS         | Valor       | Uso                                      |
|----------------------|-------------|------------------------------------------|
| `--color-bg`         | `#FFFFFF`   | Fondo general de la app                  |
| `--color-surface`    | `#F4F6F9`   | Fondo de cards y secciones internas      |
| `--color-primary`    | `#0A2E5C`   | Azul oscuro principal (navbar, títulos)  |
| `--color-accent`     | `#00AEEF`   | Azul eléctrico (botones, badges activos) |
| `--color-accent-alt` | `#FF6B00`   | Naranja (precio, ofertas, CTA urgente)   |
| `--color-text`       | `#1A1A2E`   | Texto principal                          |
| `--color-muted`      | `#6B7280`   | Texto secundario / descripciones         |
| `--color-border`     | `#E5E7EB`   | Bordes de cards                          |
| `--color-success`    | `#16A34A`   | Stock disponible                         |
| `--color-danger`     | `#DC2626`   | Sin stock                                |

> **Importante:** El fondo general es **blanco** (`#FFFFFF`), no azul. Nunca usar fondos azules oscuros en el body o en secciones principales.

### Tipografía

- **Fuente principal:** `Inter` (Google Fonts)
- Títulos de producto: `font-semibold`, tamaño `text-base` o `text-lg`
- Precio: `font-bold`, color `--color-accent-alt` (`#FF6B00`)
- Precio tachado / anterior: `line-through`, color `--color-muted`
- Categoría badge: `text-xs`, `font-medium`, fondo `--color-accent` con texto blanco

### Logo

- Usar `/public/images/logo.png` (mismo logo del sitio principal)
- En navbar: logo a la izquierda, altura máxima `h-8`
- Fondo navbar: `--color-primary` (`#0A2E5C`) con texto blanco

---

## Estructura de carpetas

```
catalogo-vendedores/
├── public/
│   └── images/
│       └── logo.png
├── src/
│   ├── components/
│   │   ├── Navbar.jsx
│   │   ├── SearchBar.jsx
│   │   ├── CategoryFilter.jsx
│   │   ├── ProductCard.jsx
│   │   ├── ProductModal.jsx
│   │   └── WhatsAppButton.jsx
│   ├── data/
│   │   └── productos.json
│   ├── hooks/
│   │   └── useProductos.js
│   ├── App.jsx
│   ├── main.jsx
│   └── index.css
├── CLAUDE.md
├── index.html
├── tailwind.config.js
└── vite.config.js
```

---

## Estructura de datos — `productos.json`

Cada producto debe tener los siguientes campos:

```json
[
  {
    "id": "smart-001",
    "nombre": "Samsung Galaxy A55 5G",
    "categoria": "smartphones",
    "marca": "Samsung",
    "modelo": "Galaxy A55 5G",
    "descripcion": "6.6\" Super AMOLED, 8GB RAM, 256GB, cámara triple 50MP, batería 5000mAh.",
    "precio": 479999,
    "precioAnterior": 520000,
    "imagen": "/images/productos/samsung-a55.png",
    "badge": "mas-vendido",
    "stock": true,
    "tags": ["android", "5g", "garantia-oficial"],
    "whatsappTexto": "Hola! Me interesa el Samsung Galaxy A55 5G a $479.999. ¿Tiene disponibilidad?"
  }
]
```

**Categorías válidas:** `smartphones` | `impresoras` | `tablets` | `laptops` | `accesorios`

**Badges válidos:** `mas-vendido` | `nuevo` | `oferta` | `sin-badge`

---

## Funcionalidades requeridas

### 1. Listado de productos
- Grid responsivo: 1 columna en mobile, 2 en tablet, 3–4 en desktop
- Cada card muestra: imagen, badge (si aplica), categoría, nombre, descripción corta, precio actual, precio anterior tachado (si aplica), botón WhatsApp
- Cards con sombra suave (`shadow-sm`) y borde `--color-border`

### 2. Filtro por categoría
- Tabs horizontales en la parte superior: Todos / Smartphones / Impresoras / Tablets / Laptops / Accesorios
- Tab activo: fondo `--color-accent` (`#00AEEF`), texto blanco
- Tab inactivo: fondo blanco, texto `--color-primary`

### 3. Buscador
- Input con ícono de lupa (Lucide `Search`)
- Búsqueda en tiempo real por nombre, marca o modelo
- Placeholder: `"Buscar producto, marca o modelo..."`

### 4. Modal de detalle
- Al hacer clic en una card se abre un modal con:
  - Imagen grande
  - Nombre completo
  - Descripción completa
  - Precio con badge de oferta si aplica
  - Tags del producto
  - Estado de stock (verde = disponible, rojo = sin stock)
  - Botón grande de WhatsApp para consultar

### 5. Botón WhatsApp
- Ícono de WhatsApp + texto `"Consultar por WhatsApp"`
- Color: `#25D366` (verde WhatsApp estándar)
- Abre `https://wa.me/5493764XXXXXX?text=` con el `whatsappTexto` del producto (URL-encoded)
- Reemplazar `XXXXXX` con el número real del negocio

### 6. Indicador de stock
- Si `stock: true` → badge verde `"En stock"`
- Si `stock: false` → badge rojo `"Sin stock"` y card con opacidad reducida (`opacity-60`)

---

## Componentes — guía de implementación

### `Navbar.jsx`
- Fondo `bg-[#0A2E5C]`, texto blanco
- Logo izquierda, título `"Catálogo Interno"` derecha en texto pequeño muted
- Sin links de navegación (es app interna de una sola página)

### `ProductCard.jsx`
- Esquinas redondeadas `rounded-xl`
- Hover: `hover:shadow-md hover:-translate-y-0.5 transition-all`
- Precio en naranja `text-[#FF6B00] font-bold text-xl`
- Badge posicionado `absolute top-2 left-2`

### `CategoryFilter.jsx`
- Scroll horizontal en mobile (`overflow-x-auto`)
- Emojis opcionales en las tabs para identificación rápida: 📱 🖨️ 📟 💻 🎧

### `SearchBar.jsx`
- Input full-width con borde `--color-border`
- Focus: `ring-2 ring-[#00AEEF]`
- Botón limpiar (X) cuando hay texto

### `ProductModal.jsx`
- Overlay oscuro semitransparente (`bg-black/50`)
- Panel blanco centrado, máximo `max-w-lg`, `rounded-2xl`
- Cerrar con ESC o clic fuera del panel

---

## Comportamiento responsive

| Breakpoint | Columnas grid | Sidebar filtros |
|------------|---------------|-----------------|
| < 640px    | 1             | Tabs horizontales scroll |
| 640–1024px | 2             | Tabs horizontales |
| > 1024px   | 3–4           | Tabs horizontales fijas |

---

## Convenciones de código

- Componentes en **PascalCase**, archivos `.jsx`
- Hooks personalizados con prefijo `use`, archivos `.js`
- Props siempre destructuradas en la firma del componente
- No usar `any` implícito ni inline styles salvo para colores que Tailwind no cubre
- Comentarios en **español** (el equipo es hispanohablante)
- Formatear precios con `Intl.NumberFormat('es-AR', { style: 'currency', currency: 'ARS' })`

---

## Comandos del proyecto

```bash
# Instalar dependencias
npm install

# Desarrollo local
npm run dev

# Build para producción
npm run build

# Preview del build
npm run preview
```

---

## Notas para Claude Code

- Cuando se pidan cambios de colores, respetar siempre la paleta definida arriba. No inventar colores nuevos sin justificación.
- El fondo es **blanco**, no azul. El azul oscuro (`#0A2E5C`) es solo para navbar y encabezados.
- Si se agrega un nuevo campo al JSON de productos, actualizar también el tipo en `useProductos.js` y la card/modal correspondiente.
- Mantener el archivo `productos.json` como única fuente de datos hasta que se implemente un backend.
- El botón de WhatsApp es la acción principal de conversión: siempre debe ser visible y funcional.
- Al generar texto de WhatsApp para un producto, usar el campo `whatsappTexto` del JSON. Si no existe, generarlo con el formato: `"Hola! Me interesa el [nombre] a $[precio]. ¿Tiene disponibilidad?"`.
