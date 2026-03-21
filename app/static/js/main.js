/* ============================================================
   PosadasTecnologica — Main JavaScript
   ============================================================ */

'use strict';

/* ----------------------------------------------------------
   Utility Functions
   ---------------------------------------------------------- */

function formatUSD(value) {
  const num = parseFloat(value) || 0;
  return 'USD $' + num.toLocaleString('es-AR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function formatARS(value) {
  const num = parseFloat(value) || 0;
  return 'ARS $' + num.toLocaleString('es-AR', { minimumFractionDigits: 0, maximumFractionDigits: 0 });
}

function formatNumber(value, decimals = 2) {
  const num = parseFloat(value) || 0;
  return num.toLocaleString('es-AR', { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
}

/* ----------------------------------------------------------
   Catalog: Client-side Search & Category Filter
   ---------------------------------------------------------- */

function initCatalogFilters() {
  const searchInput = document.getElementById('searchInput');
  const clearSearch = document.getElementById('clearSearch');
  const categoryButtons = document.querySelectorAll('.category-filter');
  const productCols = document.querySelectorAll('.product-card-col');
  const noResults = document.getElementById('noResults');

  if (!searchInput) return;

  let activeCategory = 'Todos';

  function filterProducts() {
    const searchTerm = searchInput.value.toLowerCase().trim();
    let visibleCount = 0;

    if (clearSearch) {
      clearSearch.style.display = searchTerm ? 'block' : 'none';
    }

    productCols.forEach(col => {
      const name = col.dataset.name || '';
      const brand = col.dataset.brand || '';
      const model = col.dataset.model || '';
      const desc = col.dataset.description || '';
      const category = col.dataset.category || '';

      const matchesSearch = !searchTerm ||
        name.includes(searchTerm) ||
        brand.includes(searchTerm) ||
        model.includes(searchTerm) ||
        desc.includes(searchTerm);

      const matchesCategory = activeCategory === 'Todos' || category === activeCategory;

      if (matchesSearch && matchesCategory) {
        col.style.display = '';
        visibleCount++;
      } else {
        col.style.display = 'none';
      }
    });

    if (noResults) {
      noResults.classList.toggle('d-none', visibleCount > 0);
    }
  }

  searchInput.addEventListener('input', filterProducts);

  if (clearSearch) {
    clearSearch.addEventListener('click', () => {
      searchInput.value = '';
      filterProducts();
      searchInput.focus();
    });
  }

  categoryButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      activeCategory = btn.dataset.category;
      categoryButtons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      filterProducts();
    });
  });

  // Run initial filter (in case of pre-filled search)
  filterProducts();
}

/* ----------------------------------------------------------
   Catalog: Product Detail Modal
   ---------------------------------------------------------- */

function openProductModal(productId) {
  const modal = new bootstrap.Modal(document.getElementById('productModal'));
  const modalBody = document.getElementById('modalBody');

  // Show spinner
  modalBody.innerHTML = `
    <div class="text-center p-5">
      <div class="spinner-border" style="color: var(--color-accent);" role="status">
        <span class="visually-hidden">Cargando...</span>
      </div>
    </div>`;

  modal.show();

  fetch('/producto/' + productId)
    .then(res => res.json())
    .then(data => {
      const stockBadge = data.stock
        ? `<span class="badge rounded-pill" style="background-color: rgba(22,163,74,0.1); color: var(--color-success);">
             <i class="bi bi-check-circle me-1"></i>Disponible
           </span>`
        : `<span class="badge rounded-pill" style="background-color: rgba(220,38,38,0.1); color: var(--color-danger);">
             <i class="bi bi-x-circle me-1"></i>Sin stock
           </span>`;

      const badgeHtml = data.badge ? (() => {
        const badges = {
          'mas-vendido': '<span class="badge badge-hot rounded-pill"><i class="bi bi-fire me-1"></i>Más vendido</span>',
          'nuevo': '<span class="badge badge-new rounded-pill"><i class="bi bi-stars me-1"></i>Nuevo</span>',
          'oferta': '<span class="badge badge-offer rounded-pill"><i class="bi bi-tag me-1"></i>Oferta</span>'
        };
        return badges[data.badge] || '';
      })() : '';

      const imgHtml = data.image_filename
        ? `<img src="/static/uploads/${data.image_filename}" alt="${data.name}" class="img-fluid rounded-3" style="max-height: 280px; object-fit: contain; width: 100%;">`
        : `<div class="d-flex align-items-center justify-content-center rounded-3" style="height: 200px; background-color: var(--color-surface);">
             <i class="bi bi-image" style="font-size: 4rem; color: var(--color-border);"></i>
           </div>`;

      const exchangeRate = typeof EXCHANGE_RATE !== 'undefined' ? EXCHANGE_RATE : data.exchange_rate;
      const arsPrice = (data.sale_price_usd * exchangeRate).toLocaleString('es-AR', {maximumFractionDigits: 0});

      modalBody.innerHTML = `
        <div class="row g-0">
          <div class="col-md-5 p-4" style="background-color: var(--color-surface);">
            ${imgHtml}
            <div class="text-center mt-3">
              <span class="badge rounded-pill me-1" style="background-color: rgba(0,174,239,0.15); color: var(--color-accent);">
                ${data.category}
              </span>
              ${badgeHtml}
            </div>
          </div>
          <div class="col-md-7 p-4">
            <h4 class="fw-bold mb-1" style="color: var(--color-text);">${data.name}</h4>
            <p class="mb-3" style="color: var(--color-muted);">${data.brand}${data.model ? ' · ' + data.model : ''}</p>

            ${data.description ? `<p class="mb-3 small" style="color: var(--color-text);">${data.description}</p>` : ''}

            ${(data.ram || data.storage || data.color) ? `
            <div class="d-flex flex-wrap gap-2 mb-3">
              ${data.ram ? `<span class="badge rounded-pill px-3 py-2" style="background-color: rgba(10,46,92,0.08); color: var(--color-primary); font-size: 0.8rem;"><i class="bi bi-memory me-1"></i><strong>RAM:</strong> ${data.ram}</span>` : ''}
              ${data.storage ? `<span class="badge rounded-pill px-3 py-2" style="background-color: rgba(10,46,92,0.08); color: var(--color-primary); font-size: 0.8rem;"><i class="bi bi-device-hdd me-1"></i><strong>Almacenamiento:</strong> ${data.storage}</span>` : ''}
              ${data.color ? `<span class="badge rounded-pill px-3 py-2" style="background-color: rgba(10,46,92,0.08); color: var(--color-primary); font-size: 0.8rem;"><i class="bi bi-palette me-1"></i><strong>Color:</strong> ${data.color}</span>` : ''}
            </div>` : ''}

            <div class="mb-3">
              <div class="fw-bold mb-1" style="color: var(--color-accent-alt); font-size: 1.6rem;">
                USD $${parseFloat(data.sale_price_usd).toLocaleString('es-AR', {minimumFractionDigits: 2})}
              </div>
              <div style="color: var(--color-muted);">
                ARS $${arsPrice}
              </div>
            </div>

            <div class="mb-4">${stockBadge}</div>

            <div class="p-3 rounded-3 small" style="background-color: var(--color-surface); color: var(--color-muted);">
              <i class="bi bi-currency-exchange me-1"></i>
              Precio en ARS calculado con USD 1 = ARS $${parseFloat(exchangeRate).toLocaleString('es-AR', {maximumFractionDigits: 0})}
            </div>
          </div>
        </div>`;
    })
    .catch(err => {
      modalBody.innerHTML = `
        <div class="text-center p-5">
          <i class="bi bi-exclamation-triangle" style="font-size: 2rem; color: var(--color-danger);"></i>
          <p class="mt-2" style="color: var(--color-muted);">Error al cargar el producto</p>
        </div>`;
    });
}

/* ----------------------------------------------------------
   Image Upload Preview (Product Form)
   ---------------------------------------------------------- */

function initImagePreview() {
  const imageInput = document.getElementById('imageInput');
  const previewImg = document.getElementById('previewImg');
  const previewPlaceholder = document.getElementById('previewPlaceholder');

  if (!imageInput || !previewImg) return;

  imageInput.addEventListener('change', function () {
    const file = this.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = function (e) {
      previewImg.src = e.target.result;
      previewImg.style.display = 'block';
      if (previewPlaceholder) previewPlaceholder.style.display = 'none';
    };
    reader.readAsDataURL(file);
  });

  // Click on preview container to trigger file input
  const previewContainer = document.getElementById('imagePreview');
  if (previewContainer) {
    previewContainer.addEventListener('click', () => imageInput.click());
  }
}

/* ----------------------------------------------------------
   Product Form: Live Profit Calculation
   ---------------------------------------------------------- */

function initProductProfitCalc() {
  const costInput = document.getElementById('costPrice');
  const saleInput = document.getElementById('salePrice');
  const profitUsdEl = document.getElementById('profitUsd');
  const marginEl = document.getElementById('marginPercent');
  const statusEl = document.getElementById('marginStatus');

  if (!costInput || !saleInput) return;

  function calculate() {
    const cost = parseFloat(costInput.value) || 0;
    const sale = parseFloat(saleInput.value) || 0;
    const profit = sale - cost;
    const margin = cost > 0 ? (profit / cost) * 100 : 0;

    if (profitUsdEl) {
      profitUsdEl.textContent = '$' + profit.toLocaleString('es-AR', { minimumFractionDigits: 2 });
      profitUsdEl.style.color = profit >= 0 ? 'var(--color-success)' : 'var(--color-danger)';
    }

    if (marginEl) {
      marginEl.textContent = margin.toFixed(1) + '%';
      marginEl.style.color = margin >= 20 ? 'var(--color-success)' : margin >= 10 ? 'var(--color-accent-alt)' : 'var(--color-danger)';
    }

    if (statusEl) {
      if (margin >= 20) {
        statusEl.innerHTML = '<span style="color: var(--color-success);">✓ Buen margen</span>';
      } else if (margin >= 10) {
        statusEl.innerHTML = '<span style="color: var(--color-accent-alt);">⚠ Margen bajo</span>';
      } else if (margin > 0) {
        statusEl.innerHTML = '<span style="color: var(--color-danger);">✗ Margen crítico</span>';
      } else if (profit < 0) {
        statusEl.innerHTML = '<span style="color: var(--color-danger);">✗ Pérdida</span>';
      } else {
        statusEl.textContent = '—';
      }
    }
  }

  costInput.addEventListener('input', calculate);
  saleInput.addEventListener('input', calculate);
  calculate();
}

/* ----------------------------------------------------------
   Sale Form: Product Select → Auto-fill cost, Recalculate
   ---------------------------------------------------------- */

function initSaleForm() {
  const productSelect = document.getElementById('productSelect');
  const costDisplay = document.getElementById('costPriceDisplay');
  const salePriceInput = document.getElementById('salePriceInput');

  const calcCost = document.getElementById('calcCost');
  const calcSaleUsd = document.getElementById('calcSaleUsd');
  const calcSaleArs = document.getElementById('calcSaleArs');
  const calcProfitUsd = document.getElementById('calcProfitUsd');
  const calcProfitArs = document.getElementById('calcProfitArs');
  const calcMargin = document.getElementById('calcMargin');

  if (!productSelect) return;

  const rate = typeof CURRENT_EXCHANGE_RATE !== 'undefined' ? CURRENT_EXCHANGE_RATE : 1000;

  function updateCalc() {
    const cost = parseFloat(costDisplay ? costDisplay.value : 0) || 0;
    const sale = parseFloat(salePriceInput ? salePriceInput.value : 0) || 0;
    const profit = sale - cost;
    const margin = cost > 0 ? (profit / cost) * 100 : 0;

    if (calcCost) calcCost.textContent = cost > 0 ? formatUSD(cost) : '—';
    if (calcSaleUsd) calcSaleUsd.textContent = sale > 0 ? formatUSD(sale) : '—';
    if (calcSaleArs) calcSaleArs.textContent = sale > 0 ? formatARS(sale * rate) : '—';
    if (calcProfitUsd) {
      calcProfitUsd.textContent = sale > 0 ? formatUSD(profit) : '—';
      calcProfitUsd.style.color = profit >= 0 ? 'var(--color-success)' : 'var(--color-danger)';
    }
    if (calcProfitArs) {
      calcProfitArs.textContent = sale > 0 ? formatARS(profit * rate) : '—';
      calcProfitArs.style.color = profit >= 0 ? 'var(--color-success)' : 'var(--color-danger)';
    }
    if (calcMargin && sale > 0) {
      calcMargin.textContent = margin.toFixed(1) + '%';
      if (margin >= 20) {
        calcMargin.style.cssText = 'background-color: rgba(22,163,74,0.15); color: var(--color-success); font-size: 0.9rem;';
      } else if (margin >= 10) {
        calcMargin.style.cssText = 'background-color: rgba(255,107,0,0.15); color: var(--color-accent-alt); font-size: 0.9rem;';
      } else {
        calcMargin.style.cssText = 'background-color: rgba(220,38,38,0.15); color: var(--color-danger); font-size: 0.9rem;';
      }
    } else if (calcMargin) {
      calcMargin.textContent = '—';
      calcMargin.style.cssText = 'background-color: var(--color-surface); color: var(--color-muted); font-size: 0.9rem;';
    }
  }

  productSelect.addEventListener('change', function () {
    const selected = this.options[this.selectedIndex];
    const cost = selected.dataset.cost || '';
    const sale = selected.dataset.sale || '';

    if (costDisplay) costDisplay.value = cost;
    if (salePriceInput && sale) salePriceInput.value = parseFloat(sale).toFixed(2);

    updateCalc();
  });

  if (salePriceInput) {
    salePriceInput.addEventListener('input', updateCalc);
  }
}

/* ----------------------------------------------------------
   Delete Modals: Product, Sale, Customer
   ---------------------------------------------------------- */

function initDeleteModals() {
  // Product delete modal
  const deleteModal = document.getElementById('deleteModal');
  if (deleteModal) {
    deleteModal.addEventListener('show.bs.modal', function (event) {
      const btn = event.relatedTarget;
      const productId = btn.dataset.productId;
      const productName = btn.dataset.productName;
      document.getElementById('deleteProductName').textContent = productName;
      document.getElementById('deleteForm').action = '/admin/productos/' + productId + '/eliminar';
    });
  }

  // Sale delete modal
  const deleteSaleModal = document.getElementById('deleteSaleModal');
  if (deleteSaleModal) {
    deleteSaleModal.addEventListener('show.bs.modal', function (event) {
      const btn = event.relatedTarget;
      const saleId = btn.dataset.saleId;
      document.getElementById('deleteSaleId').textContent = '#' + saleId;
      document.getElementById('deleteSaleForm').action = '/admin/ventas/' + saleId + '/eliminar';
    });
  }

  // Customer delete modal
  const deleteCustomerModal = document.getElementById('deleteCustomerModal');
  if (deleteCustomerModal) {
    deleteCustomerModal.addEventListener('show.bs.modal', function (event) {
      const btn = event.relatedTarget;
      const customerId = btn.dataset.customerId;
      const customerName = btn.dataset.customerName;
      document.getElementById('deleteCustomerName').textContent = customerName;
      document.getElementById('deleteCustomerForm').action = '/admin/clientes/' + customerId + '/eliminar';
    });
  }
}

/* ----------------------------------------------------------
   Stock Toggle (Product List)
   ---------------------------------------------------------- */

function initStockToggles() {
  document.querySelectorAll('.stock-toggle-btn').forEach(btn => {
    btn.addEventListener('click', function () {
      const url = this.dataset.url;
      const originalHtml = this.innerHTML;
      this.disabled = true;
      this.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';

      fetch(url, { method: 'POST', headers: { 'X-Requested-With': 'XMLHttpRequest' } })
        .then(res => res.json())
        .then(data => {
          if (data.success) {
            if (data.stock) {
              this.innerHTML = '<i class="bi bi-check-circle me-1"></i>En stock';
              this.style.cssText = 'background-color: rgba(22,163,74,0.15); color: var(--color-success); border: 1px solid rgba(22,163,74,0.3); font-size: 0.75rem;';
            } else {
              this.innerHTML = '<i class="bi bi-x-circle me-1"></i>Sin stock';
              this.style.cssText = 'background-color: rgba(220,38,38,0.15); color: var(--color-danger); border: 1px solid rgba(220,38,38,0.3); font-size: 0.75rem;';
            }
          } else {
            this.innerHTML = originalHtml;
            alert('Error: ' + (data.message || 'No se pudo actualizar'));
          }
          this.disabled = false;
        })
        .catch(() => {
          this.innerHTML = originalHtml;
          this.disabled = false;
        });
    });
  });
}

/* ----------------------------------------------------------
   Simulator
   ---------------------------------------------------------- */

function initSimulator() {
  const simProductSelect = document.getElementById('simProductSelect');
  const simCostUsd = document.getElementById('simCostUsd');
  const marginType = document.getElementById('marginType');
  const marginValue = document.getElementById('marginValue');
  const customRate = document.getElementById('customRate');
  const marginSuffix = document.getElementById('marginSuffix');

  if (!simCostUsd) return;

  const simUrl = typeof SIMULATOR_URL !== 'undefined' ? SIMULATOR_URL : '';
  const defaultRate = typeof SIMULATOR_EXCHANGE_RATE !== 'undefined' ? SIMULATOR_EXCHANGE_RATE : 1000;

  // Product select fills cost
  if (simProductSelect) {
    simProductSelect.addEventListener('change', function () {
      const selected = this.options[this.selectedIndex];
      const cost = selected.value;
      if (cost) {
        simCostUsd.value = parseFloat(cost).toFixed(2);
        // Show save button
        const saveSection = document.getElementById('saveAsPriceSection');
        const saveName = document.getElementById('selectedProductName');
        if (saveSection) saveSection.classList.remove('d-none');
        if (saveName) saveName.textContent = selected.dataset.name || '';
      } else {
        const saveSection = document.getElementById('saveAsPriceSection');
        if (saveSection) saveSection.classList.add('d-none');
      }
      runSimulation();
    });
  }

  // Margin type changes suffix
  if (marginType) {
    marginType.addEventListener('change', function () {
      if (marginSuffix) marginSuffix.textContent = this.value === 'percentage' ? '%' : 'USD';
      runSimulation();
    });
  }

  [simCostUsd, marginValue, customRate].forEach(el => {
    if (el) el.addEventListener('input', runSimulation);
  });

  function runSimulation() {
    const cost = parseFloat(simCostUsd ? simCostUsd.value : 0) || 0;
    const mType = marginType ? marginType.value : 'percentage';
    const mValue = parseFloat(marginValue ? marginValue.value : 0) || 0;
    const rate = parseFloat(customRate ? customRate.value : defaultRate) || defaultRate;

    if (cost <= 0) {
      clearResults();
      return;
    }

    fetch(simUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest' },
      body: JSON.stringify({ cost_usd: cost, margin_type: mType, margin_value: mValue, exchange_rate: rate })
    })
      .then(res => res.json())
      .then(data => {
        if (data.error) return;
        updateResults(data, cost, rate);
      })
      .catch(() => {});
  }

  function updateResults(data, cost, rate) {
    const set = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };

    set('resCostUsd', 'USD $' + formatNumber(cost));
    set('resCostArs', 'ARS $' + formatNumber(data.cost_ars, 0));
    set('resSaleUsd', 'USD $' + formatNumber(data.sale_price_usd));
    set('resSaleArs', 'ARS $' + formatNumber(data.sale_price_ars, 0));
    set('resProfitUsd', 'USD $' + formatNumber(data.profit_usd));
    set('resProfitArs', 'ARS $' + formatNumber(data.profit_ars, 0));

    const badge = document.getElementById('resMarginBadge');
    if (badge) {
      const m = data.margin_percent;
      badge.textContent = m.toFixed(1) + '%';
      if (m >= 20) {
        badge.style.cssText = 'background-color: rgba(22,163,74,0.15); color: var(--color-success); font-size: 1rem;';
      } else if (m >= 10) {
        badge.style.cssText = 'background-color: rgba(255,107,0,0.15); color: var(--color-accent-alt); font-size: 1rem;';
      } else {
        badge.style.cssText = 'background-color: rgba(220,38,38,0.15); color: var(--color-danger); font-size: 1rem;';
      }
    }

    // Store for save button
    window._simSalePriceUsd = data.sale_price_usd;
  }

  function clearResults() {
    ['resCostUsd', 'resCostArs', 'resSaleUsd', 'resSaleArs', 'resProfitUsd', 'resProfitArs'].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.textContent = '—';
    });
    const badge = document.getElementById('resMarginBadge');
    if (badge) {
      badge.textContent = '—';
      badge.style.cssText = 'background-color: var(--color-border); color: var(--color-muted); font-size: 1rem;';
    }
  }

  // Save as price button
  const saveBtn = document.getElementById('saveAsPriceBtn');
  if (saveBtn) {
    saveBtn.addEventListener('click', function () {
      const selected = simProductSelect ? simProductSelect.options[simProductSelect.selectedIndex] : null;
      const productId = selected ? selected.dataset.id : null;
      const salePrice = window._simSalePriceUsd;

      if (!productId || !salePrice) {
        alert('Selecciona un producto y calcula el precio primero.');
        return;
      }

      if (!confirm('¿Guardar USD $' + formatNumber(salePrice) + ' como precio de venta del producto?')) return;

      // Use the edit product form via fetch/redirect
      // We'll redirect the user to edit page with price prefilled via a query param isn't standard,
      // so instead update via a simple form submission
      const form = document.createElement('form');
      form.method = 'POST';
      form.action = '/admin/productos/' + productId + '/editar';
      form.style.display = 'none';

      // We need all current product data — redirect to edit page instead
      alert('Redirigiendo al formulario de edición del producto con el precio calculado.');
      window.location.href = '/admin/productos/' + productId + '/editar';
    });
  }

  // Scenario comparators
  document.querySelectorAll('.scenario-cost, .scenario-margin').forEach(input => {
    input.addEventListener('input', function () {
      const scenario = this.dataset.scenario;
      calcScenario(scenario);
    });
  });

  function calcScenario(num) {
    const costEl = document.querySelector(`.scenario-cost[data-scenario="${num}"]`);
    const marginEl = document.querySelector(`.scenario-margin[data-scenario="${num}"]`);
    const resultEl = document.getElementById('scenarioResult' + num);

    const cost = parseFloat(costEl ? costEl.value : 0) || 0;
    const margin = parseFloat(marginEl ? marginEl.value : 0) || 0;
    const rate = parseFloat(customRate ? customRate.value : defaultRate) || defaultRate;

    if (cost <= 0 || !resultEl) return;

    const profit = cost * (margin / 100);
    const saleUsd = cost + profit;
    const saleArs = saleUsd * rate;

    const saleUsdEl = resultEl.querySelector('.scenario-sale-usd');
    const saleArsEl = resultEl.querySelector('.scenario-sale-ars');
    const profitEl = resultEl.querySelector('.scenario-profit');

    if (saleUsdEl) saleUsdEl.textContent = 'USD $' + formatNumber(saleUsd);
    if (saleArsEl) saleArsEl.textContent = 'ARS $' + formatNumber(saleArs, 0);
    if (profitEl) profitEl.textContent = 'USD $' + formatNumber(profit);

    resultEl.classList.remove('d-none');
  }
}

/* ----------------------------------------------------------
   Initialize everything on DOMContentLoaded
   ---------------------------------------------------------- */

document.addEventListener('DOMContentLoaded', function () {
  initCatalogFilters();
  initImagePreview();
  initProductProfitCalc();
  initSaleForm();
  initDeleteModals();
  initStockToggles();
  initSimulator();

  // Auto-dismiss alerts after 5 seconds
  document.querySelectorAll('.alert.alert-dismissible').forEach(alert => {
    setTimeout(() => {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
      if (bsAlert) bsAlert.close();
    }, 5000);
  });
});
