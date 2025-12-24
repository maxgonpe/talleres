/* ==========================================================
   INGRESO FUSIONADO: CLIENTE + COMPONENTES + ACCIONES
   ========================================================== */

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

document.addEventListener("DOMContentLoaded", () => {
  // Buscar el root en cualquiera de los dos templates (fusionado o voz)
  const root = document.getElementById("ingreso-fusionado-root") || 
                document.getElementById("ingreso-voz-root");
  if (!root) return; // Solo ejecutar en los templates fusionados

  console.log("🚀 Flujo de ingreso fusionado cargado");

  /* --------------------
     Wizard de 3 pasos
     -------------------- */
  const panes = Array.from(document.querySelectorAll(".wizard-pane"));
  const steps = Array.from(document.querySelectorAll(".wizard-step"));
  const btnPrev = document.getElementById("wizard-prev");
  const btnNext = document.getElementById("wizard-next");
  const btnSubmit = document.getElementById("wizard-submit");
  const btnSkip = document.getElementById("wizard-skip");
  let currentStep = 1;
  const totalSteps = panes.length;

  function syncWizardUI() {
    panes.forEach(pane => {
      pane.classList.toggle("active", Number(pane.dataset.stepPane) === currentStep);
    });
    steps.forEach(step => {
      const stepNumber = Number(step.dataset.step);
      step.classList.remove("active", "done", "pending");
      if (stepNumber < currentStep) {
        step.classList.add("done");
      } else if (stepNumber === currentStep) {
        step.classList.add("active");
      } else {
        step.classList.add("pending");
      }
    });

    if (btnPrev) btnPrev.style.display = currentStep > 1 ? "inline-flex" : "none";
    if (btnNext) btnNext.style.display = currentStep < totalSteps ? "inline-flex" : "none";
    if (btnSubmit) btnSubmit.style.display = currentStep === totalSteps ? "inline-flex" : "none";
    if (btnSkip) btnSkip.style.display = currentStep === totalSteps ? "inline-flex" : "none";
  }

  function goToStep(targetStep) {
    currentStep = Math.max(1, Math.min(totalSteps, targetStep));
    syncWizardUI();
  }

  btnPrev?.addEventListener("click", () => goToStep(currentStep - 1));
  btnNext?.addEventListener("click", () => goToStep(currentStep + 1));
  goToStep(1);

  /* --------------------
     Cliente y vehículo
     -------------------- */
  const clienteSelect = document.getElementById("cliente_existente");
  const nuevoClienteCampos = document.getElementById("nuevo_cliente_campos");
  const vehiculoSelect = document.getElementById("vehiculo_select");
  const vehiculoFields = document.getElementById("vehiculo_fields");

  function toggleClienteCampos() {
    if (!nuevoClienteCampos) return;
    nuevoClienteCampos.style.display = clienteSelect && clienteSelect.value ? "none" : "block";
  }

  // Función para normalizar RUT: convertir 'k' final a MAYÚSCULA
  // IMPORTANTE: En la BD siempre se guarda con 'K' mayúscula, por lo que
  // debemos normalizar a mayúscula para que coincida con la BD
  function normalizarRut(rut) {
    if (!rut) return rut;
    rut = String(rut).trim();
    // Si termina en 'k' o 'K', convertir a MAYÚSCULA para que coincida con la BD
    if (rut && rut.slice(-1).toLowerCase() === 'k') {
      rut = rut.slice(0, -1) + 'K';
    }
    return rut;
  }

  async function cargarVehiculos(clienteId, selectedVehiculoId = null) {
    if (!vehiculoSelect) return;
    vehiculoSelect.innerHTML = '<option value="">-- Nuevo vehículo --</option>';

    const cleanedId = normalizarRut((clienteId || "").trim());
    console.log('🚗 cargarVehiculos - clienteId recibido:', clienteId, 'cleanedId:', cleanedId);
    if (!cleanedId) {
      toggleVehiculoCampos();
      return;
    }

    try {
      const encodedId = encodeURIComponent(cleanedId);
      const url = `/api/vehiculos/${encodedId}/`;
      console.log('📡 Fetching URL:', url);
      const res = await fetch(url);
      console.log('📡 Response status:', res.status, res.ok);
      if (!res.ok) {
        console.error('❌ Error en respuesta:', res.status, res.statusText);
        throw new Error(`HTTP ${res.status}`);
      }
      const data = await res.json();
      console.log('✅ Vehículos recibidos:', data.length, 'vehículos');
      data.forEach(v => {
        const opt = document.createElement("option");
        opt.value = v.id;
        const placa = (v.placa || "").trim() || "(sin patente)";
        const marca = (v.marca || "").trim();
        const modelo = (v.modelo || "").trim();
        const anio = v.anio ? String(v.anio) : "";
        opt.textContent = `${placa} • ${[marca, modelo].filter(Boolean).join(" ")}` + (anio ? ` (${anio})` : "");
        if (selectedVehiculoId && String(v.id) === String(selectedVehiculoId)) {
          opt.selected = true;
        }
        vehiculoSelect.appendChild(opt);
      });
    } catch (error) {
      console.error("❌ Error cargando vehículos:", error);
      console.error("Error details:", {
        message: error.message,
        clienteId: clienteId,
        cleanedId: cleanedId
      });
    }
    toggleVehiculoCampos();
  }

  function toggleVehiculoCampos() {
    if (!vehiculoFields) return;
    vehiculoFields.style.display = vehiculoSelect && vehiculoSelect.value ? "none" : "block";
  }

  if (clienteSelect) {
    clienteSelect.addEventListener("change", () => {
      toggleClienteCampos();
      // Normalizar el RUT antes de cargar vehículos (importante para RUTs con 'k')
      const rutOriginal = clienteSelect.value;
      const rutNormalizado = normalizarRut(rutOriginal);
      console.log('🔍 Cliente seleccionado - RUT original:', rutOriginal, 'RUT normalizado:', rutNormalizado);
      cargarVehiculos(rutNormalizado);
      if (vehiculoSelect) vehiculoSelect.value = "";
      toggleVehiculoCampos();
    });
    toggleClienteCampos();
  }

  if (vehiculoSelect) {
    vehiculoSelect.addEventListener("change", toggleVehiculoCampos);
    if (clienteSelect && clienteSelect.value) {
      const selectedAttr = vehiculoSelect.dataset.selected;
      const selectedVehiculoId = selectedAttr && selectedAttr !== "None" ? selectedAttr : null;
      // Normalizar el RUT antes de cargar vehículos (importante para RUTs con 'k')
      const rutNormalizado = normalizarRut(clienteSelect.value);
      cargarVehiculos(rutNormalizado, selectedVehiculoId);
    } else {
      toggleVehiculoCampos();
    }
  }

  /* --------------------
     Búsqueda de vehículo por placa (API externa)
     -------------------- */
  async function buscarVehiculoPorPlaca(rawPlaca, opts = { showAlerts: true }) {
    const placa = String(rawPlaca || "").trim().toUpperCase();
    if (!placa) {
      if (opts.showAlerts) console.warn("buscarVehiculoPorPlaca: placa vacía");
      return null;
    }

    try {
      const url = `/car/vehiculo_lookup/?placa=${encodeURIComponent(placa)}`;
      const resp = await fetch(url);
      if (!resp.ok) {
        const msg = `Error HTTP ${resp.status}`;
        if (opts.showAlerts) alert(msg);
        return null;
      }
      const dataRaw = await resp.json();
      const payload = (dataRaw && dataRaw.success && dataRaw.data) ? dataRaw.data : dataRaw;

      const marca = payload.marca || (payload.model && (payload.model.brand?.name || payload.model.brand_name)) || payload.brand?.name || "";
      const modelo = payload.modelo || payload.model?.name || payload.version || payload.modelName || "";
      const anio = payload.anio || payload.year || payload.yearRT || payload.model?.year || "";
      const vin = payload.vin || payload.vinNumber || payload.vin_number || payload.vin_no || "";
      const placaRes = payload.placa || payload.licensePlate || placa;
      const descripcionMotor = payload.descripcion_motor || (payload.engine ? `Motor ${payload.engine} • ${payload.version || ""}` : (payload.engineNumber || ""));

      const datos = {
        marca: marca || "",
        modelo: modelo || "",
        anio: anio || "",
        vin: vin || "",
        placa: placaRes || placa,
        descripcion_motor: descripcionMotor || ""
      };

      function setField(nameSuffix, value) {
        if (value === undefined || value === null) value = "";
        const candidates = [
          `id_vehiculo-${nameSuffix}`,
          `id_vehiculo_${nameSuffix}`,
          `vehiculo-${nameSuffix}`,
          `vehiculo_${nameSuffix}`,
          `id_${nameSuffix}`,
          nameSuffix
        ];
        for (const sel of candidates) {
          const byId = document.getElementById(sel);
          if (byId) {
            byId.value = value;
            byId.dispatchEvent(new Event("input", { bubbles: true }));
            return true;
          }
          const byName = document.querySelector(`[name="${sel}"]`);
          if (byName) {
            byName.value = value;
            byName.dispatchEvent(new Event("input", { bubbles: true }));
            return true;
          }
        }
        return false;
      }

      setField("marca", datos.marca);
      setField("modelo", datos.modelo);
      setField("anio", datos.anio);
      setField("vin", datos.vin);
      setField("placa", datos.placa);
      setField("descripcion_motor", datos.descripcion_motor);

      if (opts.showAlerts) {
        const placaInput = document.querySelector('#id_vehiculo-placa, #id_vehiculo_placa, [name="vehiculo-placa"], [name="vehiculo_placa"], [name="placa"]');
        if (placaInput) {
          let badge = document.getElementById("vehiculo-lookup-badge");
          if (!badge) {
            badge = document.createElement("div");
            badge.id = "vehiculo-lookup-badge";
            badge.style.fontSize = "0.9rem";
            badge.style.marginTop = "0.35rem";
            placaInput.closest(".mb-3")?.appendChild(badge) || placaInput.parentNode.appendChild(badge);
          }
          badge.textContent = `Vehículo encontrado: ${datos.marca} ${datos.modelo} ${datos.anio}`;
          badge.style.color = "#0b5ed7";
          setTimeout(() => badge?.remove(), 4500);
        }
      }

      return datos;
    } catch (error) {
      console.error("Error en buscarVehiculoPorPlaca:", error);
      if (opts.showAlerts) alert("Error al consultar la API del vehículo. Revisa la consola.");
      return null;
    }
  }

  const placaInput = document.querySelector('#id_vehiculo-placa, #id_vehiculo_placa, [name="vehiculo-placa"], [name="vehiculo_placa"], [name="placa"]');
  if (placaInput) {
    const btnBuscarVehiculo = document.getElementById("btn-buscar-vehiculo");
    if (btnBuscarVehiculo) {
      btnBuscarVehiculo.addEventListener("click", () => {
        const val = placaInput.value || placaInput.textContent || "";
        buscarVehiculoPorPlaca(val);
      });
    }

    placaInput.addEventListener("blur", () => {
      const val = placaInput.value || "";
      if (val && String(val).trim().length >= 3) buscarVehiculoPorPlaca(val, { showAlerts: false });
    });
    placaInput.addEventListener("keydown", e => {
      if (e.key === "Enter") {
        e.preventDefault();
        buscarVehiculoPorPlaca(placaInput.value);
      }
    });
  } else {
    console.warn("No se encontró el input de placa para habilitar búsqueda por API.");
  }

  window.buscarVehiculoPorPlaca = buscarVehiculoPorPlaca;

  /* --------------------
     Componentes + Acciones
     -------------------- */
  const componentesList = document.getElementById("lista-seleccionados");
  const accionesCount = document.getElementById("acciones-count");
  const accionesTableBody = document.querySelector("#acciones-resumen-table tbody");
  const totalManoObraEl = document.getElementById("total_mano_obra");
  const accionesHiddenInput = document.getElementById("acciones_componentes_json");
  const accionesUrlTemplate = root.dataset.accionesTemplate ||
    document.getElementById("acciones-endpoints")?.dataset.accionesUrlTemplate ||
    "/car/acciones-por-componente/0/";

  const CLP = new Intl.NumberFormat("es-CL", {
    style: "currency",
    currency: "CLP",
    maximumFractionDigits: 0
  });

  const accionesState = new Map();

  function buildAccionesUrl(componenteId) {
    return accionesUrlTemplate.replace(/0\/?$/, `${componenteId}/`);
  }

  function renderComponentesList() {
    if (!componentesList) return;
    const seleccionados = Array.from(document.querySelectorAll('input[name="componentes_seleccionados"]:checked'));
    if (seleccionados.length === 0) {
      componentesList.innerHTML = '<li class="text-muted">Aún no hay componentes seleccionados.</li>';
      return;
    }
    componentesList.innerHTML = "";
    seleccionados.forEach(cb => {
      const li = document.createElement("li");
      li.textContent = cb.dataset.nombre || cb.value;
      li.className = "d-flex align-items-center justify-content-between gap-2";
      componentesList.appendChild(li);
    });
  }

  function updateAccionSubtotal(state, subtotalEl) {
    if (!subtotalEl) return;
    const precio = parseFloat(state.precio || state.precio_base || 0) || 0;
    const cantidad = parseInt(state.cantidad, 10) || 1;
    const subtotal = state.seleccionado ? precio * cantidad : 0;
    subtotalEl.textContent = CLP.format(subtotal);
    subtotalEl.className = "accion-subtotal " + (state.seleccionado ? "text-success" : "text-muted");
  }

  function updateHiddenPayloadAndResumen() {
    let total = 0;
    let seleccionadas = 0;
    const payload = [];

    if (accionesTableBody) accionesTableBody.innerHTML = "";

    accionesState.forEach(state => {
      if (!state.seleccionado) return;

      const precio = parseFloat(state.precio || state.precio_base || 0) || 0;
      const cantidad = parseInt(state.cantidad, 10) || 1;
      const subtotal = precio * cantidad;

      payload.push({
        componente_id: parseInt(state.componente_id, 10),
        accion_id: parseInt(state.accion_id, 10),
        precio_mano_obra: (state.precio || state.precio_base || "").toString(),
        cantidad
      });

      total += subtotal;
      seleccionadas += 1;

      if (accionesTableBody) {
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td>${escapeHtml(state.componente_nombre || state.componente_id)}</td>
          <td>${escapeHtml(state.accion_nombre || state.accion_id)}</td>
          <td class="text-end fw-semibold">${CLP.format(subtotal)}</td>
        `;
        accionesTableBody.appendChild(tr);
      }
    });

    if (accionesTableBody && seleccionadas === 0) {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td colspan="3" class="text-muted text-center small">
          Selecciona acciones para ver el resumen.
        </td>
      `;
      accionesTableBody.appendChild(tr);
    }

    if (accionesHiddenInput) {
      accionesHiddenInput.value = JSON.stringify(payload);
    }
    if (totalManoObraEl) {
      totalManoObraEl.textContent = CLP.format(total);
    }
    if (accionesCount) {
      accionesCount.textContent = `${seleccionadas} acción${seleccionadas === 1 ? "" : "es"}`;
    }
  }

  async function fetchAcciones(componenteId) {
    const urls = [buildAccionesUrl(componenteId), buildAccionesUrl(componenteId).replace(/\/$/, "")];
    for (const url of urls) {
      try {
        const res = await fetch(url);
        if (!res.ok) continue;
        const data = await res.json();
        if (data && (data.ok || Array.isArray(data))) {
          return data.acciones || data || [];
        }
      } catch (error) {
        console.error("Error cargando acciones:", error);
      }
    }
    return [];
  }

  function ensureAccionState({ key, componenteId, componenteNombre, accion }) {
    if (!accionesState.has(key)) {
      accionesState.set(key, {
        componente_id: componenteId,
        componente_nombre: componenteNombre,
        accion_id: accion.accion_id,
        accion_nombre: accion.accion_nombre,
        precio_base: accion.precio_base || "",
        precio: "",
        cantidad: 1,
        seleccionado: false
      });
    }
    return accionesState.get(key);
  }

  function attachAccionEvents({ item, state }) {
    const checkbox = item.querySelector(".accion-checkbox");
    const precioInput = item.querySelector(".accion-precio");
    const cantidadInput = item.querySelector(".accion-cantidad");
    const subtotalEl = item.querySelector(".accion-subtotal");

    if (checkbox) {
      checkbox.checked = Boolean(state.seleccionado);
      checkbox.addEventListener("change", () => {
        state.seleccionado = checkbox.checked;
        if (checkbox.checked && !state.precio && state.precio_base) {
          state.precio = state.precio_base;
          if (precioInput) precioInput.value = state.precio_base;
        }
        item.classList.toggle("seleccionada", checkbox.checked);
        updateAccionSubtotal(state, subtotalEl);
        updateHiddenPayloadAndResumen();
      });
    }

    if (precioInput) {
      if (state.precio) {
        precioInput.value = state.precio;
      } else {
        precioInput.placeholder = state.precio_base || "0";
      }
      precioInput.addEventListener("input", () => {
        state.precio = precioInput.value;
        updateAccionSubtotal(state, subtotalEl);
        updateHiddenPayloadAndResumen();
      });
    }

    if (cantidadInput) {
      cantidadInput.value = state.cantidad || 1;
      cantidadInput.addEventListener("input", () => {
        const cantidad = Math.max(1, parseInt(cantidadInput.value, 10) || 1);
        cantidadInput.value = cantidad;
        state.cantidad = cantidad;
        updateAccionSubtotal(state, subtotalEl);
        updateHiddenPayloadAndResumen();
      });
    }

    updateAccionSubtotal(state, subtotalEl);
    item.classList.toggle("seleccionada", Boolean(state.seleccionado));
  }

  async function activateComponent(checkbox, { initial = false } = {}) {
    const componenteId = checkbox.value;
    const componenteNombre = checkbox.dataset.nombre || checkbox.value;
    const item = checkbox.closest(".componente-item");
    const panel = item?.querySelector(".acciones-panel");
    const placeholder = panel?.querySelector(".acciones-placeholder");
    const contenido = panel?.querySelector(".acciones-contenido");

    item?.classList.add("active");
    if (panel) {
      panel.classList.add("show");
    }
    renderComponentesList();

    if (!panel || !contenido) return;

    if (panel.dataset.loaded === "1") {
      // Ya cargado: sincronizar estado visual
      contenido.querySelectorAll(".accion-item").forEach(existingItem => {
        const key = existingItem.dataset.accionKey;
        if (!key) return;
        const state = accionesState.get(key);
        if (!state) return;
        attachAccionEvents({ item: existingItem, state });
      });
      updateHiddenPayloadAndResumen();
      return;
    }

    if (placeholder) {
      placeholder.textContent = "Cargando acciones disponibles…";
    }
    contenido.innerHTML = "";

    const acciones = await fetchAcciones(componenteId);

    if (!acciones || acciones.length === 0) {
      if (placeholder) {
        placeholder.textContent = "No hay acciones sugeridas para este componente.";
      }
      panel.dataset.loaded = "1";
      return;
    }

    if (placeholder) {
      placeholder.style.display = "none";
    }

    // Ordenar acciones por nombre ascendente (A-Z)
    const accionesOrdenadas = [...acciones].sort((a, b) => {
      const nombreA = (a.accion_nombre || "").toLowerCase();
      const nombreB = (b.accion_nombre || "").toLowerCase();
      return nombreA.localeCompare(nombreB, 'es', { sensitivity: 'base' });
    });

    accionesOrdenadas.forEach(accion => {
      const key = `${componenteId}-${accion.accion_id}`;
      const state = ensureAccionState({
        key,
        componenteId,
        componenteNombre,
        accion
      });

      const itemAccion = document.createElement("div");
      itemAccion.className = "accion-item";
      itemAccion.dataset.accionKey = key;
      itemAccion.innerHTML = `
        <div class="accion-head">
          <div>
            <div class="form-check form-switch">
              <input class="form-check-input accion-checkbox" type="checkbox"
                     id="accion-${key}">
              <label class="form-check-label fw-semibold" for="accion-${key}">
                ${escapeHtml(accion.accion_nombre)}
              </label>
            </div>
            <div class="small text-muted">Acción ID: ${accion.accion_id}</div>
          </div>
          <span class="badge bg-light text-dark">${escapeHtml(componenteNombre)}</span>
        </div>
        <div class="accion-controls">
          <div>
            <label class="form-label small mb-1">Precio unitario</label>
            <input type="number" step="0.01" min="0" class="form-control form-control-sm accion-precio">
            <small class="text-muted">Base: ${accion.precio_base ? CLP.format(Number(accion.precio_base)) : "Sin precio base"}</small>
          </div>
          <div>
            <label class="form-label small mb-1">Cantidad</label>
            <input type="number" min="1" step="1" class="form-control form-control-sm accion-cantidad" value="1">
          </div>
          <div class="d-flex flex-column justify-content-end">
            <div class="small text-muted">Subtotal</div>
            <div class="accion-subtotal">$0</div>
          </div>
        </div>
      `;

      contenido.appendChild(itemAccion);
      attachAccionEvents({ item: itemAccion, state });
    });

    panel.dataset.loaded = "1";

    if (!initial) {
      updateHiddenPayloadAndResumen();
    }
  }

  function deactivateComponent(checkbox) {
    const componenteId = checkbox.value;
    const item = checkbox.closest(".componente-item");
    const panel = item?.querySelector(".acciones-panel");

    item?.classList.remove("active");
    if (panel) {
      panel.classList.remove("show");
      panel.querySelectorAll(".accion-checkbox").forEach(cb => {
        cb.checked = false;
      });
      panel.querySelectorAll(".accion-item").forEach(accionItem => {
        accionItem.classList.remove("seleccionada");
      });
    }

    accionesState.forEach((state, key) => {
      if (String(state.componente_id) === String(componenteId)) {
        state.seleccionado = false;
      }
    });

    renderComponentesList();
    updateHiddenPayloadAndResumen();
  }

  document.querySelectorAll('input[name="componentes_seleccionados"]').forEach(cb => {
    cb.addEventListener("change", () => {
      if (cb.checked) {
        activateComponent(cb);
      } else {
        deactivateComponent(cb);
      }
    });
  });

  // Inicializar componentes marcados (por ejemplo, cuando se re-renderiza el formulario con errores)
  document.querySelectorAll('input[name="componentes_seleccionados"]:checked').forEach(cb => {
    activateComponent(cb, { initial: true });
  });
  renderComponentesList();
  updateHiddenPayloadAndResumen();

  /* --------------------
     Interacción con SVG
     -------------------- */
  const planoContainer = document.getElementById("plano-container");

  if (planoContainer) {
    planoContainer.addEventListener("click", ev => {
      const target = ev.target.closest("[id]");
      if (!target || !planoContainer.contains(target)) return;
      const codigo = target.id;

      fetch(`/car/componentes-lookup/?part=${encodeURIComponent(codigo)}`)
        .then(r => r.json())
        .then(data => {
          if (!data || !data.found) return;
          const compId = data.parent.id;
          const compNombre = data.parent.nombre;
          let checkbox = document.querySelector(`input[name="componentes_seleccionados"][value="${compId}"]`);

          if (!checkbox) {
            checkbox = document.createElement("input");
            checkbox.type = "checkbox";
            checkbox.name = "componentes_seleccionados";
            checkbox.value = compId;
            checkbox.dataset.nombre = compNombre;
            checkbox.checked = true;
            checkbox.style.display = "none";
            document.getElementById("form-ingreso")?.appendChild(checkbox);
          } else {
            checkbox.checked = !checkbox.checked;
          }

          checkbox.dispatchEvent(new Event("change", { bubbles: true }));

          if (checkbox.checked) {
            target.style.fill = "orange";
          } else {
            target.style.fill = "";
          }
        })
        .catch(err => console.error("componentes-lookup error:", err));
    });
  }

  const btnResetPlano = document.getElementById("btn-reset-plano");
  if (btnResetPlano) {
    btnResetPlano.addEventListener("click", () => {
      const cont = document.getElementById("plano-container");
      if (!cont) return;
      const url = cont.dataset.inicialUrl;
      cont.innerHTML = `<object type="image/svg+xml" data="${url}" class="w-100"></object>`;
    });
  }

  /* --------------------
     Repuestos e insumos
     -------------------- */
  const meta = document.getElementById("diagnostico-meta");
  const diagnosticoId = meta?.dataset.diagnosticoId?.trim() || "";
  const CSRF = meta?.dataset.csrf || "";
  let buscarInsumosTimeout;

  function getRepuestosHiddenItems() {
    const hidden = document.getElementById("repuestos-json");
    if (!hidden || !hidden.value) return [];
    try {
      const data = JSON.parse(hidden.value);
      return Array.isArray(data) ? data : [];
    } catch (error) {
      console.warn("⚠️ Error parseando repuestos-json:", error);
      return [];
    }
  }

  function setRepuestosHiddenItems(items) {
    const hidden = document.getElementById("repuestos-json");
    if (!hidden) return;
    hidden.value = JSON.stringify(items);
  }

  function renderRepuestosPreviewFromHidden() {
    if (diagnosticoId) return;
    const cont = document.getElementById("tabla-contenido");
    if (!cont) return;

    const items = getRepuestosHiddenItems();
    if (!items.length) {
      cont.innerHTML = "<p class='text-muted'>Los repuestos e insumos agregados aparecerán aquí.</p>";
      return;
    }

    let total = 0;
    const filas = items.map(item => {
      const cantidad = parseInt(item.cantidad, 10) || 1;
      const precio = parseFloat(item.precio_unitario || 0) || 0;
      const subtotal = cantidad * precio;
      total += subtotal;
      return `
        <tr>
          <td>${escapeHtml(item.nombre || item.id)}</td>
          <td class="text-center">${cantidad}</td>
          <td class="text-end">${CLP.format(precio)}</td>
          <td class="text-end fw-semibold">${CLP.format(subtotal)}</td>
        </tr>
      `;
    }).join("");

    cont.innerHTML = `
      <table class="table table-sm table-bordered align-middle">
        <thead class="table-light">
          <tr>
            <th>Nombre</th>
            <th style="width: 90px;" class="text-center">Cant.</th>
            <th style="width: 130px;" class="text-end">Precio unit.</th>
            <th style="width: 130px;" class="text-end">Subtotal</th>
          </tr>
        </thead>
        <tbody>${filas}</tbody>
        <tfoot>
          <tr class="table-success">
            <td colspan="3" class="text-end fw-bold">Total estimado</td>
            <td class="text-end fw-bold">${CLP.format(total)}</td>
          </tr>
        </tfoot>
      </table>
    `;
  }

  function prepararRepuestosParaEnvio() {
    const repuestosNuevos = [];
    document.querySelectorAll("#repuestos-list input.repuesto-check:checked").forEach(chk => {
      const cantidadInput = document.querySelector(
        `#repuestos-list input.repuesto-cantidad[data-id="${chk.dataset.id}"]`
      );
      const cantidad = cantidadInput ? parseInt(cantidadInput.value, 10) || 1 : 1;
      repuestosNuevos.push({
        id: chk.dataset.id,
        repuesto_stock_id: chk.dataset.stockId || null,
        cantidad,
        precio_unitario: parseFloat(chk.dataset.precio || 0),
        nombre: chk.dataset.nombre || "",
        oem: chk.dataset.oem || ""
      });
    });

    const existentes = getRepuestosHiddenItems();
    const idsExistentes = new Set(existentes.map(item => item.id));
    const combinados = [...existentes];

    repuestosNuevos.forEach(rep => {
      if (!idsExistentes.has(rep.id)) {
        combinados.push(rep);
      }
    });

    setRepuestosHiddenItems(combinados);
    console.log("✅ repuestos-json actualizado:", combinados.length, "items");
    renderRepuestosPreviewFromHidden();
  }

  window.prepararRepuestosParaEnvio = prepararRepuestosParaEnvio;

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

    fetch(url)
      .then(r => {
        if (!r.ok) throw new Error("HTTP " + r.status);
        return r.json();
      })
      .then(data => {
        cont.innerHTML = "";
        if (!data.repuestos || data.repuestos.length === 0) {
          cont.innerHTML = "<p class='text-muted'>No hay repuestos sugeridos.</p>";
          return;
        }
        data.repuestos.forEach(r => {
          const div = document.createElement("div");
          div.classList.add("card", "mb-2", "p-2");

          let compatibilidadClass = "border-secondary";
          if (r.compatibilidad >= 80) compatibilidadClass = "border-success";
          else if (r.compatibilidad >= 60) compatibilidadClass = "border-warning";
          else if (r.compatibilidad >= 40) compatibilidadClass = "border-info";
          else if (r.compatibilidad >= 20) compatibilidadClass = "border-danger";
          div.classList.add(compatibilidadClass);

          div.innerHTML = `
            <label class="form-check">
              <input type="checkbox"
                     class="form-check-input repuesto-check"
                     data-id="${r.id}"
                     data-stock-id="${r.repuesto_stock_id || ""}"
                     data-precio="${r.precio_venta || 0}"
                     data-nombre="${escapeHtml(r.nombre)}"
                     data-oem="${escapeHtml(r.oem || "")}">
              <b>${escapeHtml(r.nombre)}</b> (${escapeHtml(r.oem || "sin OEM")})<br>
              <small>${escapeHtml(r.sku || "")} • ${escapeHtml(r.posicion || "")}</small><br>
              Stock: ${r.disponible} – 💰 $${(r.precio_venta || 0).toFixed(0)}<br>
              ${r.compatibilidad_texto ? `<small class="text-muted">${r.compatibilidad_texto} (${r.compatibilidad}%)</small>` : ""}
            </label>
            <div class="mt-1 d-flex justify-content-between align-items-center">
              <div>
                <label class="form-label small mb-0">Cantidad</label>
                <input type="number"
                       class="form-control form-control-sm repuesto-cantidad"
                       data-id="${r.id}"
                       min="1"
                       value="1"
                       style="max-width:80px;">
              </div>
              <button type="button" class="btn btn-sm btn-outline-danger" onclick="descartarRepuesto(this)">
                ✕
              </button>
            </div>
          `;
          cont.appendChild(div);
        });
      })
      .catch(err => {
        cont.innerHTML = `<div class="alert alert-warning">Error cargando repuestos: ${escapeHtml(err.message)}</div>`;
      });
  };

  window.agregarRepuesto = function (repuestoId, stockId) {
    if (!diagnosticoId) {
      alert("⚠️ Guarda el diagnóstico antes de agregar repuestos.");
      return;
    }
    const cont = document.getElementById("repuestos-list");
    fetch(`/diagnostico/${diagnosticoId}/agregar-repuesto/`, {
      method: "POST",
      headers: {
        "X-CSRFToken": CSRF,
        "Content-Type": "application/json",
        "Accept": "application/json"
      },
      body: JSON.stringify({
        repuesto_id: repuestoId,
        repuesto_stock_id: stockId,
        cantidad: 1
      })
    })
      .then(res => res.json())
      .then(data => {
        if (data.error) {
          alert("❌ " + data.error);
          return;
        }
        cargarTablaRepuestos();
        if (cont) {
          const flash = document.createElement("div");
          flash.className = "alert alert-success small mt-2";
          flash.textContent = "Repuesto agregado al diagnóstico";
          cont.prepend(flash);
          setTimeout(() => flash.remove(), 2000);
        }
      })
      .catch(err => {
        alert("Error al agregar repuesto: " + err.message);
      });
  };

  window.cargarTablaRepuestos = function () {
    if (!diagnosticoId) {
      document.getElementById("tabla-contenido").innerHTML =
        "<p class='text-muted'>Guarda el diagnóstico y vuelve para ver repuestos agregados.</p>";
      return;
    }
    fetch(`/diagnostico/${diagnosticoId}/repuestos/`, { headers: { "Accept": "application/json" } })
      .then(res => res.json())
      .then(data => {
        const cont = document.getElementById("tabla-contenido");
        cont.innerHTML = "";
        if (!data.repuestos || data.repuestos.length === 0) {
          cont.innerHTML = "<p class='text-muted'>No hay repuestos agregados.</p>";
          return;
        }
        let tabla = `
          <table class="table table-sm table-bordered align-middle text-center">
            <thead class="table-light">
              <tr>
                <th>Nombre</th>
                <th>OEM</th>
                <th>Cantidad</th>
                <th>Precio</th>
                <th>Subtotal</th>
              </tr>
            </thead>
            <tbody>
        `;
        data.repuestos.forEach(r => {
          tabla += `
            <tr>
              <td>${escapeHtml(r.nombre)}</td>
              <td>${escapeHtml(r.oem || "-")}</td>
              <td>${Number(r.cantidad)}</td>
              <td>$${Number(r.precio_unitario || 0).toFixed(0)}</td>
              <td>$${Number(r.subtotal || 0).toFixed(0)}</td>
            </tr>
          `;
        });
        tabla += `
            </tbody>
          </table>
          <h5 class="text-end">💰 Total: $${Number(data.total || 0).toFixed(0)}</h5>
        `;
        cont.innerHTML = tabla;
      })
      .catch(err => {
        const cont = document.getElementById("tabla-contenido");
        cont.innerHTML = `<div class="alert alert-danger">Error cargando repuestos: ${escapeHtml(err.message)}</div>`;
      });
  };

  window.buscarInsumos = function () {
    const buscarInput = document.getElementById("buscar-insumo");
    const cont = document.getElementById("lista-insumos-disponibles");
    if (!buscarInput || !cont) return;

    const termino = buscarInput.value.trim();
    if (termino.length < 2) {
      cont.innerHTML = '<div class="alert alert-info small mb-0">Escribe al menos 2 caracteres para buscar.</div>';
      return;
    }

    cont.innerHTML = '<div class="alert alert-info small mb-0"><i class="fas fa-spinner fa-spin"></i> Buscando insumos…</div>';

    fetch(`/car/repuestos/buscar-insumos/?q=${encodeURIComponent(termino)}`)
      .then(res => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then(data => {
        const insumos = data.insumos || [];
        if (!insumos.length) {
          cont.innerHTML = '<div class="alert alert-warning small mb-0">No se encontraron insumos para ese término.</div>';
          return;
        }

        cont.innerHTML = "";
        insumos.forEach(insumo => {
          const item = document.createElement("div");
          item.className = "list-group-item";
          item.innerHTML = `
            <div class="d-flex justify-content-between align-items-center gap-3">
              <div class="form-check flex-grow-1">
                <input class="form-check-input insumo-check" type="checkbox"
                       id="insumo-${insumo.id}"
                       data-id="${insumo.id}"
                       data-nombre="${escapeHtml(insumo.nombre)}"
                       data-precio="${insumo.precio || 0}">
                <label class="form-check-label" for="insumo-${insumo.id}">
                  <strong>${escapeHtml(insumo.nombre)}</strong><br>
                  <small class="text-muted">
                    SKU: ${escapeHtml(insumo.sku || "N/A")}
                    ${insumo.marca ? "• Marca: " + escapeHtml(insumo.marca) : ""}
                    • Precio: ${CLP.format(insumo.precio || 0)}
                    • Stock: ${insumo.stock || 0}
                  </small>
                </label>
              </div>
              <div>
                <input type="number" class="form-control form-control-sm insumo-cantidad"
                       data-id="${insumo.id}" value="1" min="1" style="width: 80px;">
              </div>
            </div>
          `;
          cont.appendChild(item);
        });
      })
      .catch(error => {
        console.error("❌ Error buscando insumos:", error);
        cont.innerHTML = `<div class="alert alert-danger small mb-0">Error buscando insumos: ${escapeHtml(error.message)}</div>`;
      });
  };

  window.buscarInsumosDebounced = function () {
    clearTimeout(buscarInsumosTimeout);
    buscarInsumosTimeout = setTimeout(window.buscarInsumos, 300);
  };

  window.agregarInsumos = function () {
    const checkboxes = document.querySelectorAll("#lista-insumos-disponibles input.insumo-check:checked");
    if (!checkboxes.length) {
      alert("⚠️ Selecciona al menos un insumo para agregar.");
      return;
    }

    const items = getRepuestosHiddenItems();
    let nuevos = 0;

    checkboxes.forEach(chk => {
      const id = chk.dataset.id;
      const nombre = chk.dataset.nombre || id;
      const precio = parseFloat(chk.dataset.precio || 0) || 0;
      const cantidadInput = document.querySelector(
        `#lista-insumos-disponibles input.insumo-cantidad[data-id="${id}"]`
      );
      const cantidad = Math.max(1, parseInt(cantidadInput?.value || "1", 10));

      const existente = items.find(item => String(item.id) === String(id));
      if (existente) {
        existente.cantidad = (parseInt(existente.cantidad, 10) || 0) + cantidad;
      } else {
        items.push({
          id: parseInt(id, 10),
          nombre,
          cantidad,
          precio_unitario: precio
        });
        nuevos += 1;
      }
    });

    setRepuestosHiddenItems(items);
    renderRepuestosPreviewFromHidden();

    const mensaje = document.getElementById("insumos-agregados-mensaje");
    if (mensaje) {
      mensaje.style.display = "block";
      mensaje.textContent = nuevos
        ? `✅ ${nuevos} insumo(s) agregado(s).`
        : "ℹ️ Los insumos seleccionados ya estaban agregados, se actualizaron las cantidades.";
      setTimeout(() => {
        mensaje.style.display = "none";
      }, 3000);
    }

    checkboxes.forEach(chk => {
      chk.checked = false;
    });
  };

  window.descartarRepuesto = function (boton) {
    boton.closest(".card")?.remove();
  };

  window.skipRepuestosAndSubmit = function () {
    prepararRepuestosParaEnvio();
    document.getElementById("form-ingreso")?.submit();
  };

  const form = document.getElementById("form-ingreso");
  if (form) {
    form.addEventListener("submit", () => {
      prepararRepuestosParaEnvio();
      updateHiddenPayloadAndResumen();
    });
  }

  renderRepuestosPreviewFromHidden();

  const buscarInput = document.getElementById("buscar-insumo");
  if (buscarInput) {
    buscarInput.addEventListener("input", window.buscarInsumosDebounced);
    buscarInput.addEventListener("keypress", event => {
      if (event.key === "Enter") {
        event.preventDefault();
        window.buscarInsumos();
      }
    });
  }
});

