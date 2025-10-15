/* ======= Helpers ======= */
function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

/* ======= Main DOM logic ======= */
document.addEventListener('DOMContentLoaded', function () {
  console.log("📌 ingreso.html cargado");

  // --- Meta ---
  const meta = document.getElementById("diagnostico-meta");
  const diagnosticoId = meta?.dataset.diagnosticoId?.trim() || "";
  const CSRF = meta?.dataset.csrf || "";

  // ==================== CLIENTE ====================
  const clienteSelect  = document.getElementById('cliente_existente');
  const nuevoClienteCampos = document.getElementById('nuevo_cliente_campos');
  function toggleClienteCampos() {
    if (!nuevoClienteCampos) return;
    nuevoClienteCampos.style.display = clienteSelect && clienteSelect.value ? 'none' : 'block';
  }
  if (clienteSelect) {
    clienteSelect.addEventListener('change', () => {
      toggleClienteCampos();
      cargarVehiculos(clienteSelect.value);
      const vehSel = document.getElementById('vehiculo_select');
      if (vehSel) vehSel.value = '';
      toggleVehiculoCampos();
    });
    toggleClienteCampos();
  }

  // ==================== VEHÍCULO ====================
  const vehiculoSelect = document.getElementById('vehiculo_select');
  const vehiculoFields = document.getElementById('vehiculo_fields');
  function toggleVehiculoCampos() {
    if (!vehiculoFields) return;
    vehiculoFields.style.display = vehiculoSelect && vehiculoSelect.value ? 'none' : 'block';
  }

  async function cargarVehiculos(clienteId, selectedVehiculoId = null) {
    if (!vehiculoSelect) return;
    vehiculoSelect.innerHTML = '<option value="">-- Nuevo vehículo --</option>';
    if (!clienteId) { toggleVehiculoCampos(); return; }
    try {
      const res = await fetch(`/api/vehiculos/${clienteId}/`);
      if (!res.ok) return;
      const data = await res.json();
      data.forEach(v => {
        const opt = document.createElement('option');
        opt.value = v.id;
        opt.textContent = `${v.placa} • ${v.marca} ${v.modelo} (${v.anio})`;
        if (selectedVehiculoId && String(v.id) === String(selectedVehiculoId)) {
          opt.selected = true;
        }
        vehiculoSelect.appendChild(opt);
      });
    } catch (err) {
      console.error("Error cargando vehículos:", err);
    }
    toggleVehiculoCampos();
  }

  if (vehiculoSelect) {
    vehiculoSelect.addEventListener('change', toggleVehiculoCampos);
    if (clienteSelect && clienteSelect.value) {
      cargarVehiculos(clienteSelect.value, vehiculoSelect.dataset.selected);
    } else {
      toggleVehiculoCampos();
    }
  }

  // ==================== COMPONENTES seleccionados ====================
  const lista = document.getElementById("lista-seleccionados");
  
  function agregarALista(compId, compNombre, codigoSvg = null) {
    if (!lista) return;
    if (!document.getElementById(`comp-li-${compId}`)) {
      const col = document.createElement("div");
      col.className = "col-md-6 col-lg-4";
      col.id = `comp-li-${compId}`;
      
      col.innerHTML = `
        <div class="card mb-2">
          <div class="card-body p-3">
            <div class="d-flex justify-content-between align-items-start mb-2">
              <h6 class="card-title mb-0">${escapeHtml(compNombre)}</h6>
              <button type="button" class="btn btn-sm btn-outline-danger" onclick="quitarComponente(${compId})">
                ✕
              </button>
            </div>
            
            <!-- Selector de acciones -->
            <div class="mb-2">
              <label class="form-label small">Acciones:</label>
              <div id="acciones-${compId}" class="acciones-container">
                <div class="d-flex gap-1 mb-1">
                  <select class="form-select form-select-sm accion-select" data-componente="${compId}">
                    <option value="">Cargando acciones...</option>
                  </select>
                  <button type="button" class="btn btn-sm btn-outline-success" onclick="agregarAccion(${compId})">
                    +
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      `;
      
      lista.appendChild(col);
      
      // Cargar acciones para este componente con un pequeño delay
      setTimeout(() => {
        cargarAccionesParaComponente(compId);
      }, 100);
    }
  }

  function quitarComponente(compId) {
    const col = document.getElementById(`comp-li-${compId}`);
    if (col) {
      col.remove();
      // Desmarcar checkbox
        const cb = document.querySelector(`input[name="componentes_seleccionados"][value="${compId}"]`);
        if (cb) cb.checked = false;
      // Limpiar SVG si aplica
      const codigoSvg = col.dataset.codigoSvg;
        if (codigoSvg) {
          const elSvg = document.getElementById(codigoSvg);
          if (elSvg) elSvg.style.fill = "";
        }
    }
  }

  function actualizarListaSeleccionados() {
    if (!lista) return;
    lista.innerHTML = "";
    document.querySelectorAll('input[name="componentes_seleccionados"]:checked').forEach(cb => {
      const nombre = cb.dataset.nombre || cb.value;
      agregarALista(cb.value, nombre);
    });
    
    // Reconfigurar event listeners después de actualizar la lista
    configurarEventListeners();
  }

  // ==================== ACCIONES ====================
  async function cargarAccionesParaComponente(componenteId) {
    try {
      const url = `/car/acciones-lookup/${componenteId}/`;
      console.log('🔍 Cargando acciones para componente:', componenteId, 'URL:', url);
      
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
        },
        credentials: 'same-origin'
      });
      
      console.log('📡 Respuesta recibida:', response.status, response.statusText);
      
      if (!response.ok) {
        console.error('❌ Error en respuesta:', response.status, response.statusText);
        if (response.status === 302) {
          console.error('🔄 Redirección detectada - posible problema de autenticación');
        }
        return;
      }
      
      const data = await response.json();
      console.log('📦 Datos recibidos:', data);
      
      const select = document.querySelector(`select[data-componente="${componenteId}"]`);
      if (!select) {
        console.error('❌ No se encontró el selector para componente:', componenteId);
        console.log('🔍 Selectores disponibles:', document.querySelectorAll('select[data-componente]'));
        return;
      }
      
      console.log('✅ Selector encontrado:', select);
      
      // Limpiar opciones existentes (excepto la primera)
      select.innerHTML = '<option value="">Seleccionar acción...</option>';
      
      if (data.ok && data.acciones && data.acciones.length > 0) {
        console.log('✅ Agregando', data.acciones.length, 'acciones al selector');
        data.acciones.forEach((accion, index) => {
          const option = document.createElement('option');
          option.value = accion.accion_id;
          const precio = parseFloat(accion.precio_base) || 0;
          option.textContent = `${accion.accion_nombre} - $${precio.toLocaleString()}`;
          option.dataset.precio = precio;
          select.appendChild(option);
          console.log(`  ${index + 1}. ${accion.accion_nombre} - $${precio.toLocaleString()}`);
        });
        console.log('✅ Acciones agregadas al selector');
      } else {
        console.log('No hay acciones disponibles para este componente');
        const option = document.createElement('option');
        option.value = '';
        option.textContent = 'No hay acciones disponibles';
        option.disabled = true;
        select.appendChild(option);
      }
    } catch (error) {
      console.error('❌ Error cargando acciones:', error);
      console.error('❌ Stack trace:', error.stack);
    }
  }

  function agregarAccion(componenteId) {
    const select = document.querySelector(`select[data-componente="${componenteId}"]`);
    if (!select || !select.value) return;
    
    const accionId = select.value;
    const selectedOption = select.options[select.selectedIndex];
    const accionNombre = selectedOption.textContent.split(' - ')[0];
    const precio = parseFloat(selectedOption.dataset.precio) || 0;
    
    // Verificar si ya existe esta acción para este componente
    const contenedor = document.getElementById(`acciones-${componenteId}`);
    const accionExistente = contenedor.querySelector(`[data-accion-id="${accionId}"]`);
    if (accionExistente) {
      alert('Esta acción ya está agregada para este componente');
      return;
    }
    
    // Crear elemento de acción
    const accionDiv = document.createElement('div');
    accionDiv.className = 'accion-item d-flex justify-content-between align-items-center p-2 bg-light rounded mb-1';
    accionDiv.dataset.accionId = accionId;
    accionDiv.dataset.precio = precio;
    
    accionDiv.innerHTML = `
      <div>
        <span class="accion-nombre">${escapeHtml(accionNombre)}</span>
        <small class="text-muted d-block">$${precio.toLocaleString()}</small>
      </div>
      <button type="button" class="btn btn-sm btn-outline-danger" onclick="quitarAccion(this)">
        ✕
      </button>
    `;
    
    // Agregar al contenedor de acciones
    contenedor.appendChild(accionDiv);
    
    // Limpiar selector
    select.value = '';
    
    // Actualizar totales
    actualizarTotales();
  }

  function quitarAccion(boton) {
    boton.closest('.accion-item').remove();
    actualizarTotales();
  }

  // ==================== REPUESTOS ====================
  window.cargarRepuestos = function () {
    const cont = document.getElementById("repuestos-list");
    if (!cont) return;

    let url = "";
    if (diagnosticoId) {
      url = cont.dataset.withIdTemplate.replace("0", diagnosticoId);
    } else {
      const compIds = Array.from(document.querySelectorAll('input[name="componentes_seleccionados"]:checked'))
                           .map(cb => cb.value);
      const marca = document.getElementById("id_marca")?.value || "";
      const modelo = document.getElementById("id_modelo")?.value || "";
      const anio = document.getElementById("id_anio")?.value || "";
      const motor = document.getElementById("id_descripcion_motor")?.value || "";

      const params = new URLSearchParams();
      compIds.forEach(c => params.append("componentes_ids", c));
      if (marca) params.append("marca", marca);
      if (modelo) params.append("modelo", modelo);
      if (anio) params.append("anio", anio);
      if (motor) params.append("motor", motor);

      url = cont.dataset.previewUrl + "?" + params.toString();
    }

    // Mostrar loading
    cont.innerHTML = `
      <div class="text-center py-4">
        <div class="spinner-border text-primary" role="status">
          <span class="visually-hidden">Buscando repuestos...</span>
        </div>
        <p class="mt-2 text-muted">Buscando repuestos compatibles...</p>
      </div>
    `;

    fetch(url)
      .then(r => {
        if (!r.ok) throw new Error("HTTP " + r.status);
        return r.json();
      })
      .then(data => {
        cont.innerHTML = "";
        if (!data.repuestos || data.repuestos.length === 0) {
          cont.innerHTML = `
            <div class="text-center text-muted py-4">
              <i class="fas fa-search fa-2x mb-2"></i>
              <p>No se encontraron repuestos sugeridos</p>
            </div>
          `;
          return;
        }
        
        data.repuestos.forEach(r => {
          const div = document.createElement("div");
          div.classList.add("card", "mb-2", "p-3");
          
          // Determinar clase CSS basada en compatibilidad
          let compatibilidadClass = "border-secondary";
          if (r.compatibilidad >= 80) compatibilidadClass = "border-success";
          else if (r.compatibilidad >= 60) compatibilidadClass = "border-warning";
          else if (r.compatibilidad >= 40) compatibilidadClass = "border-info";
          else if (r.compatibilidad >= 20) compatibilidadClass = "border-danger";
          
          div.classList.add(compatibilidadClass);
          
          div.innerHTML = `
            <div class="d-flex justify-content-between align-items-start mb-2">
              <div class="flex-grow-1">
                <div class="form-check">
                  <input type="checkbox"
                         class="form-check-input repuesto-check"
                         data-id="${r.id}"
                         data-stock-id="${r.repuesto_stock_id || ''}"
                         data-precio="${r.precio_venta || 0}"
                         data-nombre="${escapeHtml(r.nombre)}"
                         data-oem="${escapeHtml(r.oem || '')}">
                  <label class="form-check-label">
                    <strong>${escapeHtml(r.nombre)}</strong>
                    <br><small class="text-muted">${escapeHtml(r.oem || "sin OEM")}</small>
                  </label>
                </div>
                <div class="mt-1">
                  <small class="text-muted">
                    ${escapeHtml(r.sku || "")} • ${escapeHtml(r.posicion || "")}
                    ${r.marca_veh ? `• Marca: ${escapeHtml(r.marca_veh)}` : ''}
                    ${r.tipo_motor ? `• Motor: ${escapeHtml(r.tipo_motor)}` : ''}
                  </small>
                </div>
                <div class="mt-1">
                  <small>Stock: ${r.disponible} – 💰 $${(r.precio_venta || 0).toLocaleString()}</small>
                </div>
              </div>
              <div class="text-end">
                <button type="button" class="btn btn-sm btn-outline-danger" onclick="descartarRepuesto(this)">
                  ✕
                </button>
                <div class="mt-1">
                  <small class="badge ${r.compatibilidad >= 80 ? 'bg-success' : r.compatibilidad >= 60 ? 'bg-warning' : r.compatibilidad >= 40 ? 'bg-info' : r.compatibilidad >= 20 ? 'bg-danger' : 'bg-secondary'}">
                    ${r.compatibilidad}%
                  </small>
                  <br><small class="text-muted">${r.compatibilidad_texto || ''}</small>
                </div>
              </div>
            </div>
            <div class="row align-items-center">
              <div class="col-6">
                <label class="form-label small mb-0">Cantidad:</label>
                <input type="number"
                       class="form-control form-control-sm repuesto-cantidad"
                       data-id="${r.id}"
                       min="1"
                       value="1">
              </div>
              <div class="col-6 text-end">
                <small class="text-muted">Subtotal:</small>
                <div class="fw-bold" id="subtotal-${r.id}">$${(r.precio_venta || 0).toLocaleString()}</div>
              </div>
            </div>
          `;
          cont.appendChild(div);
        });
        
        // Agregar event listeners para actualizar subtotales
        cont.querySelectorAll('.repuesto-check, .repuesto-cantidad').forEach(el => {
          el.addEventListener('change', actualizarSubtotales);
        });
      })
      .catch(err => {
        cont.innerHTML = `<div class="alert alert-warning">Error cargando repuestos: ${escapeHtml(err.message)}</div>`;
      });
  };

  function descartarRepuesto(boton) {
    boton.closest('.card').remove();
  }

  function actualizarSubtotales() {
    document.querySelectorAll('#repuestos-list .repuesto-check:checked').forEach(checkbox => {
      const repuestoId = checkbox.dataset.id;
      const cantidadInput = document.querySelector(`#repuestos-list input.repuesto-cantidad[data-id="${repuestoId}"]`);
      const cantidad = cantidadInput ? parseInt(cantidadInput.value) || 1 : 1;
      const precio = parseFloat(checkbox.dataset.precio) || 0;
      const subtotal = precio * cantidad;
      
      const subtotalEl = document.getElementById(`subtotal-${repuestoId}`);
      if (subtotalEl) {
        subtotalEl.textContent = `$${subtotal.toLocaleString()}`;
      }
    });
  }

  // ==================== TOTALES ====================
  // Función actualizarTotales movida a window para acceso global

  // ==================== EVENT LISTENERS ====================
  function configurarEventListeners() {
  document.querySelectorAll('input[name="componentes_seleccionados"]').forEach(cb => {
      // Remover listener existente si lo tiene
      cb.removeEventListener("change", actualizarListaSeleccionados);
      // Agregar nuevo listener
    cb.addEventListener("change", actualizarListaSeleccionados);
  });
  }
  
  // Configurar listeners iniciales
  configurarEventListeners();
  actualizarListaSeleccionados();

  // ==================== INTERACTIVIDAD SVG ====================
  const planoContainer = document.getElementById('plano-container');
  if (planoContainer) {
    planoContainer.addEventListener('click', function (ev) {
      const target = ev.target.closest('[id]');
      if (!target || !planoContainer.contains(target)) return;
      const codigo = target.id;
      fetch(`/car/componentes-lookup/?part=${encodeURIComponent(codigo)}`)
        .then(r => r.json())
        .then(data => {
          if (!data) return;
          if (data.found) {
            const compId = data.parent.id;
            const compNombre = data.parent.nombre;
            let cb = document.querySelector(`input[name="componentes_seleccionados"][value="${compId}"]`);
            if (!cb) {
              cb = document.createElement("input");
              cb.type = "checkbox";
              cb.name = "componentes_seleccionados";
              cb.value = compId;
              cb.id = `hidden-comp-${compId}`;
              cb.checked = true;
              cb.dataset.nombre = compNombre;
              cb.style.display = "none";
              document.body.appendChild(cb);
            } else {
              cb.checked = true;
            }
            actualizarListaSeleccionados();
            target.style.fill = "#ffc107";
          }
        })
        .catch(err => console.error("Error en lookup:", err));
    });
  }

  // ==================== PREPARAR DATOS PARA ENVÍO ====================
  function prepararRepuestosParaEnvio() {
  const repuestos = [];
  document.querySelectorAll("#repuestos-list input.repuesto-check:checked").forEach(chk => {
    const cantidadInput = document.querySelector(
      `#repuestos-list input.repuesto-cantidad[data-id="${chk.dataset.id}"]`
    );
    const cantidad = cantidadInput ? parseInt(cantidadInput.value) || 1 : 1;
    repuestos.push({
      id: chk.dataset.id,
      repuesto_stock_id: chk.dataset.stockId || null,
      cantidad: cantidad,
      precio_unitario: parseFloat(chk.dataset.precio || 0),
      nombre: chk.dataset.nombre || '',
      oem: chk.dataset.oem || ''
    });
  });
  const hidden = document.getElementById("repuestos-json");
  if (hidden) {
    hidden.value = JSON.stringify(repuestos);
    console.log("✅ repuestos-json listo:", hidden.value);
  } else {
    console.warn("⚠️ No se encontró el input hidden #repuestos-json");
  }
  }

  // Preparar acciones para envío
  function prepararAccionesParaEnvio() {
    const acciones = [];
    document.querySelectorAll('.accion-item').forEach(item => {
      const componenteId = item.closest('[id^="acciones-"]').id.replace('acciones-', '');
      const precio = parseFloat(item.dataset.precio) || 0;
      acciones.push({
        componente_id: componenteId,
        accion_id: item.dataset.accionId,
        precio_mano_obra: precio.toString() // El backend espera 'precio_mano_obra' en el JSON
      });
    });
    
    const hidden = document.getElementById("acciones_componentes_json");
    if (hidden) {
      hidden.value = JSON.stringify(acciones);
      console.log("✅ acciones-json listo:", hidden.value);
    } else {
      console.warn("⚠️ No se encontró el input hidden #acciones_componentes_json");
    }
  }

  // Interceptar envío del formulario
  document.getElementById('form-ingreso').addEventListener('submit', function(e) {
    prepararRepuestosParaEnvio();
    prepararAccionesParaEnvio();
  });

  // Actualizar totales cada 3 segundos
  setInterval(actualizarTotales, 3000);
});

// ==================== FUNCIONES GLOBALES ====================
window.quitarComponente = function(compId) {
  const col = document.getElementById(`comp-li-${compId}`);
  if (col) {
    col.remove();
    const cb = document.querySelector(`input[name="componentes_seleccionados"][value="${compId}"]`);
    if (cb) cb.checked = false;
  }
};

window.agregarAccion = function(componenteId) {
  const select = document.querySelector(`select[data-componente="${componenteId}"]`);
  if (!select || !select.value) return;
  
  const accionId = select.value;
  const selectedOption = select.options[select.selectedIndex];
  const accionNombre = selectedOption.textContent.split(' - ')[0];
  const precio = parseFloat(selectedOption.dataset.precio) || 0;
  
  // Verificar si ya existe esta acción para este componente
  const contenedor = document.getElementById(`acciones-${componenteId}`);
  const accionExistente = contenedor.querySelector(`[data-accion-id="${accionId}"]`);
  if (accionExistente) {
    alert('Esta acción ya está agregada para este componente');
    return;
  }
  
  const accionDiv = document.createElement('div');
  accionDiv.className = 'accion-item d-flex justify-content-between align-items-center p-2 bg-light rounded mb-1';
  accionDiv.dataset.accionId = accionId;
  accionDiv.dataset.precio = precio;
  
  accionDiv.innerHTML = `
    <div>
      <span class="accion-nombre">${escapeHtml(accionNombre)}</span>
      <small class="text-muted d-block">$${precio.toLocaleString()}</small>
            </div>
    <button type="button" class="btn btn-sm btn-outline-danger" onclick="quitarAccion(this)">
      ✕
    </button>
  `;
  
  contenedor.appendChild(accionDiv);
  
  select.value = '';
  
  // Actualizar totales
  actualizarTotales();
};

window.quitarAccion = function(boton) {
  boton.closest('.accion-item').remove();
  actualizarTotales();
};

window.actualizarTotales = function() {
  console.log('🔄 Actualizando totales...');
  
  // Total mano de obra
  let totalManoObra = 0;
  const accionItems = document.querySelectorAll('.accion-item');
  console.log('📋 Acciones encontradas:', accionItems.length);
  
  accionItems.forEach((item, index) => {
    const precio = parseFloat(item.dataset.precio) || 0;
    totalManoObra += precio;
    console.log(`  ${index + 1}. Precio: $${precio.toLocaleString()}`);
  });
  
  // Total repuestos
  let totalRepuestos = 0;
  const repuestosChecked = document.querySelectorAll('#repuestos-list .repuesto-check:checked');
  console.log('🔧 Repuestos seleccionados:', repuestosChecked.length);
  
  repuestosChecked.forEach((checkbox, index) => {
    const cantidadInput = document.querySelector(`#repuestos-list input.repuesto-cantidad[data-id="${checkbox.dataset.id}"]`);
    const cantidad = cantidadInput ? parseInt(cantidadInput.value) || 1 : 1;
    const precio = parseFloat(checkbox.dataset.precio) || 0;
    const subtotal = precio * cantidad;
    totalRepuestos += subtotal;
    console.log(`  ${index + 1}. ${checkbox.dataset.nombre} - Cant: ${cantidad} x $${precio.toLocaleString()} = $${subtotal.toLocaleString()}`);
  });
  
  const totalGeneral = totalManoObra + totalRepuestos;
  
  console.log('💰 Totales calculados:');
  console.log(`  Mano de obra: $${totalManoObra.toLocaleString()}`);
  console.log(`  Repuestos: $${totalRepuestos.toLocaleString()}`);
  console.log(`  Total general: $${totalGeneral.toLocaleString()}`);
  
  // Actualizar elementos
  const totalManoObraEl = document.getElementById('total_mano_obra');
  const totalGeneralEl = document.getElementById('total_general');
  
  if (totalManoObraEl) {
    totalManoObraEl.textContent = `$${totalManoObra.toLocaleString()}`;
    console.log('✅ Total mano de obra actualizado en DOM');
  } else {
    console.warn('⚠️ No se encontró elemento #total_mano_obra');
  }
  
  if (totalGeneralEl) {
    totalGeneralEl.textContent = `$${totalGeneral.toLocaleString()}`;
    console.log('✅ Total general actualizado en DOM');
  } else {
    console.warn('⚠️ No se encontró elemento #total_general');
  }
};

window.descartarRepuesto = function(boton) {
  boton.closest('.card').remove();
};