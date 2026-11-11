/* ============================================================
   Mundolimp — Shopping Cart & Checkout System
   Client-side localStorage cart with seamless ordering
   ============================================================ */

'use strict';

const CART_STORAGE_KEY = 'mundolimp_cart_v1';

function getCart() {
  try {
    const raw = localStorage.getItem(CART_STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch (e) {
    console.error('Error loading cart from storage', e);
    return [];
  }
}

function saveCart(cart) {
  try {
    localStorage.setItem(CART_STORAGE_KEY, JSON.stringify(cart));
  } catch (e) {
    console.error('Error saving cart to storage', e);
  }
  updateCartUI();
}

function addToCart(product, qty = 1) {
  const cart = getCart();
  const existingIndex = cart.findIndex(item => item.id === product.id);

  if (existingIndex > -1) {
    cart[existingIndex].quantity += qty;
  } else {
    cart.push({
      id: product.id,
      name: product.name,
      presentation: product.presentation || 'Bidón 5 Litros',
      price: parseFloat(product.price) || 0,
      image: product.image || '',
      quantity: qty
    });
  }

  saveCart(cart);
  showToastFeedback(`"${product.name}" agregado a tu pedido.`);
}

function updateQuantity(productId, delta) {
  let cart = getCart();
  const item = cart.find(i => i.id === productId);
  if (!item) return;

  item.quantity += delta;
  if (item.quantity <= 0) {
    cart = cart.filter(i => i.id !== productId);
  }

  saveCart(cart);
  renderCartModal();
}

function removeFromCart(productId) {
  let cart = getCart();
  cart = cart.filter(i => i.id !== productId);
  saveCart(cart);
  renderCartModal();
}

function clearCart() {
  saveCart([]);
  renderCartModal();
}

function getCartTotal() {
  const cart = getCart();
  return cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
}

function getCartCount() {
  const cart = getCart();
  return cart.reduce((sum, item) => sum + item.quantity, 0);
}

function updateCartUI() {
  const count = getCartCount();
  const total = getCartTotal();

  // Badges in navbar and buttons
  document.querySelectorAll('.cart-count-badge').forEach(el => {
    el.textContent = count;
    el.style.display = count > 0 ? 'inline-block' : 'none';
  });

  // Floating bottom-bar or floating button if present
  const floatingBtn = document.getElementById('floatingCartBtn');
  if (floatingBtn) {
    if (count > 0) {
      floatingBtn.classList.remove('d-none');
      const countEl = floatingBtn.querySelector('.floating-cart-count');
      const totalEl = floatingBtn.querySelector('.floating-cart-total');
      if (countEl) countEl.textContent = `${count} ${count === 1 ? 'producto' : 'productos'}`;
      if (totalEl) totalEl.textContent = `$${total.toLocaleString('es-AR')}`;
    } else {
      floatingBtn.classList.add('d-none');
    }
  }
}

function renderCartModal() {
  const cart = getCart();
  const listContainer = document.getElementById('cartItemsList');
  const emptyState = document.getElementById('cartEmptyState');
  const cartContent = document.getElementById('cartContentSection');
  const totalEl = document.getElementById('cartTotalDisplay');
  const submitBtn = document.getElementById('btnSubmitOrder');

  if (!listContainer) return;

  if (cart.length === 0) {
    if (emptyState) emptyState.classList.remove('d-none');
    if (cartContent) cartContent.classList.add('d-none');
    if (submitBtn) submitBtn.disabled = true;
    return;
  }

  if (emptyState) emptyState.classList.add('d-none');
  if (cartContent) cartContent.classList.remove('d-none');
  if (submitBtn) submitBtn.disabled = false;

  let html = '';
  cart.forEach(item => {
    const subtotal = item.price * item.quantity;
    const imgTag = item.image
      ? `<img src="/static/uploads/${item.image}" alt="${item.name}" class="rounded-3 border" style="width: 48px; height: 48px; object-fit: cover;">`
      : `<div class="rounded-3 bg-light border d-flex align-items-center justify-content-center p-1" style="width: 48px; height: 48px;"><img src="/static/img/logo.png" alt="Mundolimp" style="width: 100%; height: 100%; object-fit: contain;"></div>`;

    html += `
      <div class="d-flex align-items-center justify-content-between p-2 mb-2 bg-white rounded-3 border">
        <div class="d-flex align-items-center gap-3">
          ${imgTag}
          <div>
            <div class="fw-bold text-dark small">${item.name}</div>
            <div class="text-muted" style="font-size: 0.75rem;">${item.presentation} · $${item.price.toLocaleString('es-AR')} c/u</div>
          </div>
        </div>

        <div class="d-flex align-items-center gap-3">
          <div class="input-group input-group-sm" style="width: 105px;">
            <button class="btn btn-outline-secondary px-2" type="button" onclick="updateQuantity(${item.id}, -1)">
              <i class="bi bi-dash"></i>
            </button>
            <span class="input-group-text bg-white px-2 fw-bold text-dark justify-content-center" style="min-width: 32px;">${item.quantity}</span>
            <button class="btn btn-outline-secondary px-2" type="button" onclick="updateQuantity(${item.id}, 1)">
              <i class="bi bi-plus"></i>
            </button>
          </div>

          <div class="text-end" style="min-width: 80px;">
            <span class="fw-bold text-dark small">$${subtotal.toLocaleString('es-AR')}</span>
          </div>

          <button class="btn btn-sm btn-link text-danger p-0 ms-1" onclick="removeFromCart(${item.id})" title="Quitar">
            <i class="bi bi-trash3"></i>
          </button>
        </div>
      </div>
    `;
  });

  listContainer.innerHTML = html;
  if (totalEl) totalEl.textContent = `$${getCartTotal().toLocaleString('es-AR')}`;
}

function openCartModal() {
  renderCartModal();
  const modalEl = document.getElementById('cartModal');
  if (modalEl) {
    const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
    modal.show();
  }
}

function showToastFeedback(message) {
  let toastContainer = document.getElementById('toastContainer');
  if (!toastContainer) {
    toastContainer = document.createElement('div');
    toastContainer.id = 'toastContainer';
    toastContainer.className = 'toast-container position-fixed bottom-0 start-50 translate-middle-x p-3';
    toastContainer.style.zIndex = '9999';
    document.body.appendChild(toastContainer);
  }

  const toastEl = document.createElement('div');
  toastEl.className = 'toast align-items-center text-white bg-dark border-0 shadow-lg rounded-pill px-2 py-1';
  toastEl.setAttribute('role', 'alert');
  toastEl.setAttribute('aria-live', 'assertive');
  toastEl.setAttribute('aria-atomic', 'true');
  toastEl.innerHTML = `
    <div class="d-flex align-items-center">
      <div class="toast-body d-flex align-items-center gap-2">
        <i class="bi bi-check-circle-fill text-success fs-5"></i>
        <span class="small fw-medium">${message}</span>
      </div>
      <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
    </div>
  `;

  toastContainer.appendChild(toastEl);
  const bsToast = new bootstrap.Toast(toastEl, { delay: 2800 });
  bsToast.show();
  toastEl.addEventListener('hidden.bs.toast', () => toastEl.remove());
}

async function submitOrder(e) {
  if (e) e.preventDefault();

  const cart = getCart();
  if (cart.length === 0) {
    alert('Tu carrito está vacío. Agrega productos antes de confirmar.');
    return;
  }

  const nameInput = document.getElementById('orderCustomerName');
  const phoneInput = document.getElementById('orderCustomerPhone');
  const addressInput = document.getElementById('orderCustomerAddress');
  const notesInput = document.getElementById('orderCustomerNotes');
  const submitBtn = document.getElementById('btnSubmitOrder');

  const customerName = nameInput ? nameInput.value.trim() : '';
  const customerPhone = phoneInput ? phoneInput.value.trim() : '';
  const customerAddress = addressInput ? addressInput.value.trim() : '';
  const customerNotes = notesInput ? notesInput.value.trim() : '';

  if (!customerName) {
    alert('Por favor ingresa tu Nombre o Comercio.');
    if (nameInput) nameInput.focus();
    return;
  }
  if (!customerPhone) {
    alert('Por favor ingresa un teléfono o WhatsApp de contacto.');
    if (phoneInput) phoneInput.focus();
    return;
  }
  if (!customerAddress) {
    alert('Por favor ingresa tu dirección de entrega.');
    if (addressInput) addressInput.focus();
    return;
  }

  const payload = {
    customer_name: customerName,
    customer_phone: customerPhone,
    customer_address: customerAddress,
    customer_notes: customerNotes,
    items: cart.map(item => ({
      product_id: item.id,
      product_name: item.name,
      presentation: item.presentation,
      quantity: item.quantity,
      unit_price: item.price
    }))
  };

  const originalBtnHtml = submitBtn ? submitBtn.innerHTML : '';
  if (submitBtn) {
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Enviando pedido...';
  }

  try {
    const res = await fetch('/checkout', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest'
      },
      body: JSON.stringify(payload)
    });

    const data = await res.json();

    if (res.ok && data.success) {
      // Pedido confirmado con éxito!
      const orderNumber = data.order_number || 'S/N';
      const totalAmount = data.total_amount ? `$${parseFloat(data.total_amount).toLocaleString('es-AR')}` : `$${getCartTotal().toLocaleString('es-AR')}`;

      // Limpiar carrito local
      saveCart([]);

      // Mostrar pantalla de confirmación limpia en el modal
      const modalBody = document.querySelector('#cartModal .modal-body');
      const modalFooter = document.querySelector('#cartModal .modal-footer');
      if (modalFooter) modalFooter.classList.add('d-none');

      if (modalBody) {
        modalBody.innerHTML = `
          <div class="text-center py-4 px-3">
            <div class="mb-3">
              <i class="bi bi-check-circle-fill text-success" style="font-size: 4rem;"></i>
            </div>
            <h3 class="fw-bold text-dark mb-1">¡Pedido Registrado con Éxito!</h3>
            <p class="text-muted small mb-3">Tu pedido ha sido recibido por el equipo de Mundolimp.</p>

            <div class="bg-light border rounded-4 p-3 text-start mb-4">
              <div class="d-flex justify-content-between border-bottom pb-2 mb-2">
                <span class="text-muted small">Número de Pedido:</span>
                <span class="fw-bold text-primary">${orderNumber}</span>
              </div>
              <div class="d-flex justify-content-between border-bottom pb-2 mb-2">
                <span class="text-muted small">Cliente / Comercio:</span>
                <span class="fw-bold text-dark">${customerName}</span>
              </div>
              <div class="d-flex justify-content-between border-bottom pb-2 mb-2">
                <span class="text-muted small">Teléfono:</span>
                <span class="text-dark">${customerPhone}</span>
              </div>
              <div class="d-flex justify-content-between border-bottom pb-2 mb-2">
                <span class="text-muted small">Entrega en:</span>
                <span class="text-dark">${customerAddress}</span>
              </div>
              <div class="d-flex justify-content-between pt-1">
                <span class="fw-bold text-dark">Total del Pedido:</span>
                <span class="fw-bold fs-5 text-success">${totalAmount}</span>
              </div>
            </div>

            <div class="alert alert-info border-0 rounded-4 text-start small mb-4">
              <i class="bi bi-info-circle-fill me-1"></i>
              Nos pondremos en contacto vía telefónica o WhatsApp para coordinar el horario de entrega y método de pago (Efectivo / Transferencia).
            </div>

            <button type="button" class="btn btn-primary rounded-pill px-4 py-2 fw-medium" data-bs-dismiss="modal" onclick="window.location.reload()">
              <i class="bi bi-arrow-left me-1"></i> Seguir Viendo Productos
            </button>
          </div>
        `;
      }
    } else {
      alert('Hubo un error al procesar tu pedido: ' + (data.error || 'Intente nuevamente más tarde.'));
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalBtnHtml;
      }
    }
  } catch (err) {
    console.error('Checkout error:', err);
    alert('No se pudo conectar con el servidor. Por favor verifica tu conexión e inténtalo nuevamente.');
    if (submitBtn) {
      submitBtn.disabled = false;
      submitBtn.innerHTML = originalBtnHtml;
    }
  }
}

// Inicializar al cargar el DOM
document.addEventListener('DOMContentLoaded', () => {
  updateCartUI();

  const checkoutForm = document.getElementById('checkoutForm');
  if (checkoutForm) {
    checkoutForm.addEventListener('submit', submitOrder);
  }
});
