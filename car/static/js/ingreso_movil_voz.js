/* ==========================================================
   CONTROL POR VOZ PARA INGRESO MÓVIL
   ========================================================== */

document.addEventListener('DOMContentLoaded', function() {
  'use strict';

  // Verificar si estamos en el template de voz
  const root = document.getElementById('ingreso-voz-root');
  if (!root) return;

  console.log('🎤 Control por voz cargado');

  // Elementos del DOM
  const voiceBtn = document.getElementById('voice-btn');
  const voiceStatusBanner = document.getElementById('voice-status-banner');
  const voiceStatusText = document.getElementById('voice-status-text');
  const voiceFeedbackToast = document.getElementById('voice-feedback-toast');
  const voiceFeedbackText = document.getElementById('voice-feedback-text');

  // Estado del reconocimiento
  let recognition = null;
  let isListening = false;
  let currentStep = 1;
  let isRestarting = false; // Bandera para evitar múltiples reinicios simultáneos
  let networkErrorCount = 0; // Contador de errores de red consecutivos
  const MAX_NETWORK_RETRIES = 3; // Máximo de reintentos antes de detener

  // Verificar soporte de Web Speech API
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    console.error('❌ Web Speech API no está disponible en este navegador');
    if (voiceBtn) {
      voiceBtn.disabled = true;
      voiceBtn.title = 'Reconocimiento de voz no disponible';
      voiceBtn.style.opacity = '0.5';
    }
    showFeedback('⚠️ Tu navegador no soporta reconocimiento de voz', 'error');
    return;
  }

  // Función auxiliar para reiniciar reconocimiento de forma segura
  function safeRestart() {
    if (isRestarting) {
      console.log('⏸️ Reinicio ya en progreso, ignorando...');
      return;
    }
    
    if (!isListening) {
      console.log('⏸️ No se reinicia porque isListening es false');
      return;
    }
    
    isRestarting = true;
    
    // Intentar detener primero (ignorar errores si ya está detenido)
    try {
      recognition.stop();
    } catch (e) {
      // Ignorar errores al detener (puede que ya esté detenido)
      console.log('Info: No se pudo detener (probablemente ya estaba detenido)');
    }
    
    // Esperar un momento antes de reiniciar
    setTimeout(() => {
      try {
        recognition.start();
        console.log('🔄 Reconocimiento reiniciado');
        isRestarting = false;
        networkErrorCount = 0; // Resetear contador en reinicio exitoso
      } catch (e) {
        isRestarting = false;
        if (e.message && e.message.includes('already started')) {
          console.log('✅ Reconocimiento ya estaba iniciado');
          // Si ya está iniciado, está bien, solo resetear la bandera
        } else {
          console.error('❌ Error al reiniciar:', e);
          // Si falla múltiples veces, detener
          networkErrorCount++;
          if (networkErrorCount >= MAX_NETWORK_RETRIES) {
            isListening = false;
            updateVoiceUI('idle');
            hideStatusBanner();
            showFeedback('❌ Error de conexión persistente. Presiona el botón de micrófono para intentar de nuevo.', 'error');
          }
        }
      }
    }, 500);
  }

  // Inicializar reconocimiento de voz
  try {
    recognition = new SpeechRecognition();
    recognition.lang = 'es-ES'; // Español de España (también funciona para Chile)
    recognition.continuous = false; // Cambiar a false para mejor control
    recognition.interimResults = false; // Solo resultados finales

    recognition.onstart = function() {
      console.log('🎤 Reconocimiento iniciado');
      isListening = true;
      isRestarting = false; // Resetear bandera
      networkErrorCount = 0; // Resetear contador
      updateVoiceUI('listening');
      showStatusBanner('🎤 Escuchando... Di tu comando');
    };

    recognition.onresult = function(event) {
      // Obtener el último resultado (el más reciente)
      const lastResult = event.results[event.results.length - 1];
      const transcript = lastResult[0].transcript.trim();
      
      // Solo procesar si es un resultado final
      if (lastResult.isFinal && transcript.length > 0) {
        console.log('📝 Texto reconocido:', transcript);
        
        updateVoiceUI('processing');
        showStatusBanner('⚙️ Procesando comando...');
        
        // Procesar el comando después de un breve delay
        setTimeout(() => {
          processVoiceCommand(transcript);
          // Reiniciar para seguir escuchando
          if (isListening) {
            updateVoiceUI('listening');
            showStatusBanner('🎤 Escuchando... Di tu comando');
            safeRestart();
          }
        }, 300);
      }
    };

    recognition.onerror = function(event) {
      console.error('❌ Error en reconocimiento:', event.error);
      
      // No detener si es un error menor
      if (event.error === 'no-speech') {
        // Reiniciar automáticamente si no hay voz (solo si no hay otro reinicio en progreso)
        if (isListening && !isRestarting) {
          setTimeout(() => {
            safeRestart();
          }, 1000);
        }
        return;
      }
      
      // Manejo especial para errores de red - intentar reconectar con límite
      if (event.error === 'network') {
        networkErrorCount++;
        console.warn(`⚠️ Error de red en reconocimiento (intento ${networkErrorCount}/${MAX_NETWORK_RETRIES})`);
        
        if (networkErrorCount >= MAX_NETWORK_RETRIES) {
          // Demasiados errores, detener
          isListening = false;
          updateVoiceUI('idle');
          hideStatusBanner();
          showFeedback('❌ Error de conexión persistente. Presiona el botón de micrófono para intentar de nuevo.', 'error');
          return;
        }
        
        showFeedback(`⚠️ Error de conexión. Reintentando (${networkErrorCount}/${MAX_NETWORK_RETRIES})...`, 'error');
        
        // Intentar reiniciar después de un delay (solo si no hay otro reinicio en progreso)
        if (isListening && !isRestarting) {
          setTimeout(() => {
            safeRestart();
          }, 2000);
        }
        return;
      }
      
      // Para otros errores, detener
      if (event.error !== 'aborted') {
        isListening = false;
        isRestarting = false;
        updateVoiceUI('idle');
        hideStatusBanner();
        
        let errorMsg = 'Error en el reconocimiento de voz';
        if (event.error === 'not-allowed') {
          errorMsg = 'Permiso de micrófono denegado. Actívalo en la configuración del navegador.';
        } else if (event.error === 'audio-capture') {
          errorMsg = 'No se detectó ningún micrófono. Verifica que tu dispositivo tenga un micrófono conectado.';
        } else if (event.error === 'service-not-allowed') {
          errorMsg = 'Servicio de reconocimiento no disponible. Intenta más tarde.';
        }
        
        showFeedback(errorMsg, 'error');
      }
    };

    recognition.onend = function() {
      console.log('🛑 Reconocimiento finalizado');
      isRestarting = false; // Resetear bandera cuando termina
      
      // Reiniciar automáticamente si el usuario quiere seguir escuchando
      // Solo si no hay errores de red persistentes
      if (isListening && networkErrorCount < MAX_NETWORK_RETRIES) {
        setTimeout(() => {
          safeRestart();
        }, 500);
      } else if (!isListening) {
        updateVoiceUI('idle');
        hideStatusBanner();
      }
    };

  } catch (error) {
    console.error('❌ Error al inicializar reconocimiento:', error);
    if (voiceBtn) voiceBtn.disabled = true;
    showFeedback('Error al inicializar el reconocimiento de voz', 'error');
    return;
  }

  // Actualizar UI del botón de voz
  function updateVoiceUI(state) {
    if (!voiceBtn) return;
    
    voiceBtn.classList.remove('listening', 'processing');
    voiceStatusBanner.classList.remove('listening', 'processing', 'show');
    
    if (state === 'listening') {
      voiceBtn.classList.add('listening');
      voiceBtn.textContent = '🔴';
      voiceStatusBanner.classList.add('listening', 'show');
    } else if (state === 'processing') {
      voiceBtn.classList.add('processing');
      voiceBtn.textContent = '⏳';
      voiceStatusBanner.classList.add('processing', 'show');
    } else {
      voiceBtn.textContent = '🎤';
    }
  }

  // Mostrar/ocultar banner de estado
  function showStatusBanner(text) {
    if (voiceStatusText) voiceStatusText.textContent = text;
    if (voiceStatusBanner) voiceStatusBanner.classList.add('show');
  }

  function hideStatusBanner() {
    setTimeout(() => {
      if (voiceStatusBanner) voiceStatusBanner.classList.remove('show');
    }, 500);
  }

  // Mostrar feedback toast
  function showFeedback(message, type = 'success') {
    if (!voiceFeedbackToast || !voiceFeedbackText) return;
    
    voiceFeedbackText.textContent = message;
    voiceFeedbackToast.classList.remove('success', 'error');
    voiceFeedbackToast.classList.add(type, 'show');
    
    setTimeout(() => {
      voiceFeedbackToast.classList.remove('show');
    }, 3000);
  }

  // Lista completa de comandos disponibles (para mostrar ayuda)
  const COMANDOS_DISPONIBLES = {
    'Control del micrófono': [
      'Desactivar micrófono',
      'Apagar micrófono',
      'Detener micrófono',
      'Cerrar micrófono',
      'Silenciar micrófono',
      'Stop',
      'Parar'
    ],
    'Navegación': [
      'Siguiente paso',
      'Paso siguiente',
      'Adelante',
      'Avanzar',
      'Anterior',
      'Paso anterior',
      'Atrás',
      'Volver',
      'Ir a paso uno',
      'Ir a paso dos',
      'Ir a paso tres'
    ],
    'Datos del cliente': [
      'RUT [número]',
      'Ruth [número]',
      'Nombre [nombre completo]',
      'Cliente [nombre]',
      'Teléfono [número]',
      '2teléfono [número]',
      'Email [dirección de correo]',
      'Correo [dirección de correo]',
      'Dirección [dirección completa]',
      'Domicilio [dirección completa]',
      'Abrir clientes / Mostrar clientes / Listar clientes (muestra la lista completa)',
      'Seleccionar cliente [nombre o RUT]',
      'Cliente existente'
    ],
    'Vehículo': [
      'Placa [patente]',
      'Patente [patente]',
      'Buscar',
      'Buscar placa',
      'Buscar vehículo',
      'Buscar en API',
      'Buscar API',
      'Abrir vehículos / Mostrar vehículos / Listar vehículos (muestra la lista completa)',
      'Seleccionar vehículo [placa o descripción]',
      'Vehículo existente'
    ],
    'Descripción del problema': [
      'Descripción [texto del problema]',
      'Problema [texto del problema]',
      'Descripción del problema [texto]'
    ],
    'Componentes': [
      'Seleccionar [nombre componente]',
      'Activar [nombre componente]',
      'Marcar [nombre componente]',
      'Deseleccionar [nombre componente]',
      'Desactivar [nombre componente]',
      'Desmarcar [nombre componente]'
    ],
    'Acciones de componentes': [
      'Acción [nombre acción] para [componente]',
      'Seleccionar acción [nombre] en [componente]',
      'Para [componente] acción [nombre acción]',
      'Ejemplo: "Acción limpiar para bujías"',
      'Ejemplo: "Para motor acción revisar"'
    ],
    'Acciones finales': [
      'Guardar',
      'Guardar diagnóstico',
      'Finalizar',
      'Terminar',
      'Omitir repuestos',
      'Saltar repuestos',
      'Cancelar',
      'Salir'
    ],
    'Ayuda': [
      'Mostrar comandos',
      'Comandos disponibles',
      'Ayuda',
      'Qué puedo decir',
      'Lista de comandos'
    ]
  };

  // Función para mostrar todos los comandos disponibles
  function mostrarComandosDisponibles() {
    let mensaje = '📋 COMANDOS DE VOZ DISPONIBLES:\n\n';
    
    for (const [categoria, comandos] of Object.entries(COMANDOS_DISPONIBLES)) {
      mensaje += `\n🔹 ${categoria}:\n`;
      comandos.forEach(cmd => {
        mensaje += `   • "${cmd}"\n`;
      });
    }
    
    mensaje += '\n💡 Tip: Di el comando exacto o una variación similar.';
    
    // Mostrar en un alert o en el feedback
    alert(mensaje);
    showFeedback('📋 Comandos mostrados en ventana', 'success');
  }

  // Procesar comandos de voz
  function processVoiceCommand(text) {
    const command = text.toLowerCase().trim();
    console.log('🔍 Procesando comando:', command);

    // Comandos para mostrar ayuda/comandos
    if (command.match(/^(?:mostrar comandos|comandos disponibles|ayuda|qué puedo decir|lista de comandos|help)/i)) {
      mostrarComandosDisponibles();
      return;
    }

    // Comandos para desactivar micrófono
    if (command.match(/^(?:desactivar micrófono|apagar micrófono|detener micrófono|cerrar micrófono|silenciar micrófono|stop|parar|desactivar|apagar|detener)/i)) {
      if (isListening) {
        isListening = false;
        isRestarting = false;
        networkErrorCount = 0;
        try {
          recognition.stop();
        } catch (e) {
          console.log('Error al detener reconocimiento:', e);
        }
        updateVoiceUI('idle');
        hideStatusBanner();
        showFeedback('🔇 Micrófono desactivado', 'success');
      } else {
        showFeedback('ℹ️ El micrófono ya está desactivado', 'success');
      }
      return;
    }

    // Navegación entre pasos
    if (command.match(/siguiente|paso siguiente|adelante|avanzar|next/i)) {
      goToNextStep();
      showFeedback('✅ Paso siguiente', 'success');
      return;
    }

    if (command.match(/anterior|paso anterior|atrás|volver|back|prev/i)) {
      goToPreviousStep();
      showFeedback('✅ Paso anterior', 'success');
      return;
    }

    if (command.match(/ir a paso (uno|1|primero)/i)) {
      goToStep(1);
      showFeedback('✅ Paso 1: Cliente y Vehículo', 'success');
      return;
    }

    if (command.match(/ir a paso (dos|2|segundo)/i)) {
      goToStep(2);
      showFeedback('✅ Paso 2: Diagnóstico y Acciones', 'success');
      return;
    }

    if (command.match(/ir a paso (tres|3|tercero)/i)) {
      goToStep(3);
      showFeedback('✅ Paso 3: Repuestos y Resumen', 'success');
      return;
    }

    // Comandos de guardado
    if (command.match(/guardar|guardar diagnóstico|finalizar|terminar|save/i)) {
      const submitBtn = document.getElementById('wizard-submit');
      if (submitBtn && submitBtn.style.display !== 'none') {
        submitBtn.click();
        showFeedback('✅ Guardando diagnóstico...', 'success');
      } else {
        showFeedback('⚠️ Completa todos los pasos antes de guardar', 'error');
      }
      return;
    }

    if (command.match(/omitir repuestos|saltar repuestos|skip/i)) {
      const skipBtn = document.getElementById('wizard-skip');
      if (skipBtn && skipBtn.style.display !== 'none') {
        skipBtn.click();
        showFeedback('✅ Omitiendo repuestos...', 'success');
      }
      return;
    }

    // Comandos de cancelación
    if (command.match(/cancelar|cancel|salir/i)) {
      if (confirm('¿Estás seguro de cancelar?')) {
        window.history.back();
      }
      return;
    }

    // Dictado de RUT (Paso 1) - MÁS FLEXIBLE (acepta "rut" y "ruth")
    if (command.match(/\b(?:rut|ruth|r\.?u\.?t\.?)\s+/i) || command.match(/^(?:rut|ruth|r\.?u\.?t\.?)\s+/i)) {
      // Intentar extraer el RUT después de "rut", "ruth" o "r.u.t"
      const rutMatch = command.match(/(?:rut|ruth|r\.?u\.?t\.?)\s+([\d\s\-kK]+)/i);
      if (rutMatch) {
        let rutValue = rutMatch[1].replace(/\s+/g, '').replace(/-/g, '');
        // Convertir "k" a mayúscula si está al final
        rutValue = rutValue.replace(/k$/, 'K');
        fillField('id_cliente-rut', rutValue);
        showFeedback(`✅ RUT ingresado: ${rutValue}`, 'success');
        return;
      } else {
        // Si solo dice "rut" o "ruth" sin número, mostrar ayuda
        showFeedback('⚠️ Di "RUT" seguido del número. Ejemplo: "RUT ocho dos seis tres dos uno tres uno"', 'error');
        return;
      }
    }

    // Comandos para abrir/seleccionar cliente existente
    if (command.match(/^(?:seleccionar cliente|elegir cliente|cliente existente|abrir clientes|mostrar clientes|listar clientes)/i)) {
      const clienteSelect = document.getElementById('cliente_existente');
      if (clienteSelect) {
        clienteSelect.focus();
        
        // Mostrar lista de clientes disponibles
        const opciones = Array.from(clienteSelect.options)
          .filter(opt => opt.value && opt.value !== '')
          .map(opt => opt.text.trim());
        
        if (opciones.length > 0) {
          let listaTexto = '📋 CLIENTES DISPONIBLES:\n\n';
          opciones.forEach((opcion, index) => {
            listaTexto += `${index + 1}. ${opcion}\n`;
          });
          listaTexto += '\n💡 Di "Cliente [nombre o RUT]" para seleccionar uno.';
          
          // Mostrar en alert para que el usuario pueda ver la lista
          alert(listaTexto);
          showFeedback(`📋 ${opciones.length} cliente(s) disponibles. Revisa la ventana para ver la lista.`, 'success');
        } else {
          showFeedback('⚠️ No hay clientes disponibles en la lista', 'error');
        }
        
        return;
      } else {
        showFeedback('⚠️ Selector de clientes no encontrado', 'error');
        return;
      }
    }

    // Seleccionar cliente específico por nombre o RUT
    if (command.match(/^(?:cliente|seleccionar cliente|elegir cliente)\s+(.+)/i)) {
      const clienteSelect = document.getElementById('cliente_existente');
      if (!clienteSelect) {
        showFeedback('⚠️ Selector de clientes no encontrado', 'error');
        return;
      }

      const searchTerm = command.match(/^(?:cliente|seleccionar cliente|elegir cliente)\s+(.+)/i)[1].trim().toLowerCase();
      let encontrado = false;

      // Buscar en las opciones del selector
      Array.from(clienteSelect.options).forEach(option => {
        if (option.value && option.value !== '') {
          const optionText = option.text.toLowerCase();
          // Buscar por nombre, RUT o teléfono
          if (optionText.includes(searchTerm) || 
              option.value.toLowerCase().includes(searchTerm.replace(/\s+/g, '').replace(/-/g, ''))) {
            clienteSelect.value = option.value;
            clienteSelect.dispatchEvent(new Event('change', { bubbles: true }));
            encontrado = true;
            showFeedback(`✅ Cliente seleccionado: ${option.text}`, 'success');
            return;
          }
        }
      });

      if (!encontrado) {
        showFeedback(`⚠️ No se encontró cliente con "${searchTerm}". Di "Abrir clientes" para ver la lista.`, 'error');
      }
      return;
    }

    // Comandos para abrir/seleccionar vehículo existente (MISMA LÓGICA QUE CLIENTES)
    if (command.match(/^(?:seleccionar vehículo|elegir vehículo|vehículo existente|abrir vehículos|mostrar vehículos|listar vehículos|seleccionar vehículos)/i)) {
      const vehiculoSelect = document.getElementById('vehiculo_select');
      if (vehiculoSelect) {
        // Verificar que haya un cliente seleccionado primero
        const clienteSelect = document.getElementById('cliente_existente');
        if (!clienteSelect || !clienteSelect.value) {
          showFeedback('⚠️ Primero selecciona un cliente', 'error');
          return;
        }

        vehiculoSelect.focus();
        
        // Mostrar lista de vehículos disponibles (MISMA LÓGICA QUE CLIENTES)
        const opciones = Array.from(vehiculoSelect.options)
          .filter(opt => opt.value && opt.value !== '')
          .map(opt => opt.text.trim());
        
        if (opciones.length > 0) {
          let listaTexto = '🚘 VEHÍCULOS DISPONIBLES:\n\n';
          opciones.forEach((opcion, index) => {
            listaTexto += `${index + 1}. ${opcion}\n`;
          });
          listaTexto += '\n💡 Di "Vehículo [placa o descripción]" para seleccionar uno.';
          
          // Mostrar en alert para que el usuario pueda ver la lista
          alert(listaTexto);
          showFeedback(`🚘 ${opciones.length} vehículo(s) disponible(s). Revisa la ventana para ver la lista.`, 'success');
        } else {
          showFeedback('⚠️ No hay vehículos disponibles para este cliente', 'error');
        }
        
        return;
      } else {
        showFeedback('⚠️ Selector de vehículos no encontrado', 'error');
        return;
      }
    }

    // Seleccionar vehículo específico por placa o descripción (MISMA LÓGICA QUE CLIENTES)
    if (command.match(/^(?:vehículo|seleccionar vehículo|elegir vehículo)\s+(.+)/i)) {
      const vehiculoSelect = document.getElementById('vehiculo_select');
      if (!vehiculoSelect) {
        showFeedback('⚠️ Selector de vehículos no encontrado', 'error');
        return;
      }

      // Verificar que haya un cliente seleccionado
      const clienteSelect = document.getElementById('cliente_existente');
      if (!clienteSelect || !clienteSelect.value) {
        showFeedback('⚠️ Primero selecciona un cliente', 'error');
        return;
      }

      const searchTerm = command.match(/^(?:vehículo|seleccionar vehículo|elegir vehículo)\s+(.+)/i)[1].trim().toLowerCase();
      let encontrado = false;

      // Buscar en las opciones del selector (MISMA LÓGICA QUE CLIENTES)
      Array.from(vehiculoSelect.options).forEach(option => {
        if (option.value && option.value !== '') {
          const optionText = option.text.toLowerCase();
          // Buscar por placa, marca, modelo (búsqueda flexible)
          if (optionText.includes(searchTerm) || searchTerm.includes(optionText.split('•')[0].trim().toLowerCase())) {
            vehiculoSelect.value = option.value;
            vehiculoSelect.dispatchEvent(new Event('change', { bubbles: true }));
            encontrado = true;
            showFeedback(`✅ Vehículo seleccionado: ${option.text}`, 'success');
            return;
          }
        }
      });

      if (!encontrado) {
        showFeedback(`⚠️ No se encontró vehículo con "${searchTerm}". Di "Abrir vehículos" para ver la lista.`, 'error');
      }
      return;
    }

    // Comandos para buscar vehículo en API
    if (command.match(/^(?:buscar|buscar placa|buscar vehículo|buscar patente|buscar en api|buscar api)/i)) {
      const buscarBtn = document.getElementById('btn-buscar-vehiculo');
      if (buscarBtn) {
        buscarBtn.click();
        showFeedback('✅ Buscando vehículo en API...', 'success');
        return;
      } else {
        showFeedback('⚠️ Botón de búsqueda no encontrado', 'error');
        return;
      }
    }

    // Dictado de placa (Paso 1) - MÁS FLEXIBLE
    if (command.match(/\b(?:placa|patente)\s+/i) || command.match(/^(?:placa|patente)\s+/i)) {
      const placaMatch = command.match(/(?:placa|patente)\s+([a-z0-9\s]+)/i);
      if (placaMatch) {
        const placaValue = placaMatch[1].replace(/\s+/g, '').toUpperCase();
        fillField('vehiculo-placa', placaValue);
        // Intentar buscar automáticamente después de un breve delay
        setTimeout(() => {
          const buscarBtn = document.getElementById('btn-buscar-vehiculo');
          if (buscarBtn) {
            buscarBtn.click();
            showFeedback(`✅ Placa ingresada y buscando: ${placaValue}`, 'success');
          } else {
            showFeedback(`✅ Placa ingresada: ${placaValue}`, 'success');
          }
        }, 500);
        return;
      }
    }

    // Dictado de nombre de cliente (Paso 1) - MÁS FLEXIBLE
    if (command.match(/^(?:nombre|cliente|nombre cliente)\s+/i) || command.match(/\b(?:nombre|cliente)\s+/i)) {
      // Intentar extraer el nombre después de "nombre" o "cliente"
      let nombreMatch = command.match(/(?:^nombre\s+|^cliente\s+|nombre cliente\s+)(.+?)(?:\s+(?:teléfono|telefono|fono|rut|placa|patente)|$)/i);
      if (!nombreMatch) {
        // Si no hay palabra clave después, tomar todo lo que sigue
        nombreMatch = command.match(/(?:^nombre\s+|^cliente\s+|nombre cliente\s+)(.+)/i);
      }
      if (nombreMatch) {
        const nombreValue = nombreMatch[1].trim();
        if (nombreValue && nombreValue.length > 1) {
          fillField('id_cliente-nombre', nombreValue);
          showFeedback(`✅ Nombre ingresado: ${nombreValue}`, 'success');
          return;
        }
      }
    }

    // Dictado de teléfono (Paso 1) - MÁS FLEXIBLE (ya funciona bien, solo mejoramos el patrón)
    if (command.match(/\b(?:teléfono|telefono|fono|2teléfono|2telefono)\s+/i) || command.match(/^(?:teléfono|telefono|fono|2teléfono|2telefono)\s+/i)) {
      const telefonoMatch = command.match(/(?:teléfono|telefono|fono|2teléfono|2telefono)\s+([\d\s\+\-\(\)]+)/i);
      if (telefonoMatch) {
        let telefonoValue = telefonoMatch[1].replace(/\s+/g, '').replace(/[\(\)\-]/g, '');
        fillField('id_cliente-telefono', telefonoValue);
        showFeedback(`✅ Teléfono ingresado: ${telefonoValue}`, 'success');
        return;
      }
    }

    // Dictado de email (Paso 1) - NUEVO
    if (command.match(/\b(?:email|correo|e-mail|mail)\s+/i) || command.match(/^(?:email|correo|e-mail|mail)\s+/i)) {
      // Intentar extraer el email después de "email" o "correo"
      let emailMatch = command.match(/(?:email|correo|e-mail|mail)\s+([a-z0-9\.\-\_]+(?:\s+[a-z0-9\.\-\_]+)*\s*(?:arroba|@|at)\s*[a-z0-9\.\-\_]+(?:\s+[a-z0-9\.\-\_]+)*(?:\s+(?:punto|dot|\.)\s*[a-z]+)?)/i);
      if (!emailMatch) {
        // Patrón más simple: todo lo que sigue después de "email" o "correo"
        emailMatch = command.match(/(?:email|correo|e-mail|mail)\s+(.+)/i);
      }
      if (emailMatch) {
        let emailValue = emailMatch[1].trim()
          .replace(/\s+/g, '') // Eliminar espacios
          .replace(/\s*(?:arroba|at)\s*/gi, '@') // Convertir "arroba" o "at" a @
          .replace(/\s*(?:punto|dot)\s*/gi, '.'); // Convertir "punto" o "dot" a .
        fillField('id_cliente-email', emailValue);
        showFeedback(`✅ Email ingresado: ${emailValue}`, 'success');
        return;
      }
    }

    // Dictado de dirección (Paso 1) - NUEVO
    if (command.match(/\b(?:dirección|direccion|dirección|address|domicilio)\s+/i) || command.match(/^(?:dirección|direccion|dirección|address|domicilio)\s+/i)) {
      // Intentar extraer la dirección después de "dirección" o "direccion"
      let direccionMatch = command.match(/(?:dirección|direccion|dirección|address|domicilio)\s+(.+?)(?:\s+(?:email|correo|teléfono|telefono|rut|nombre|placa|patente)|$)/i);
      if (!direccionMatch) {
        // Si no hay palabra clave después, tomar todo lo que sigue
        direccionMatch = command.match(/(?:dirección|direccion|dirección|address|domicilio)\s+(.+)/i);
      }
      if (direccionMatch) {
        const direccionValue = direccionMatch[1].trim();
        if (direccionValue && direccionValue.length > 2) {
          fillField('id_cliente-direccion', direccionValue);
          showFeedback(`✅ Dirección ingresada: ${direccionValue}`, 'success');
          return;
        }
      }
    }

    // Dictado de descripción del problema (Paso 2) - NUEVO
    if (command.match(/^(?:descripción|descripcion|problema|descripción del problema)\s+/i) || command.match(/\b(?:descripción|descripcion|problema)\s+/i)) {
      // Intentar extraer la descripción después de "descripción" o "problema"
      let descripcionMatch = command.match(/(?:descripción|descripcion|problema|descripción del problema)\s+(.+?)(?:\s+(?:seleccionar|activar|marcar|componente|accion)|$)/i);
      if (!descripcionMatch) {
        // Si no hay palabra clave después, tomar todo lo que sigue
        descripcionMatch = command.match(/(?:descripción|descripcion|problema|descripción del problema)\s+(.+)/i);
      }
      if (descripcionMatch) {
        const descripcionValue = descripcionMatch[1].trim();
        if (descripcionValue && descripcionValue.length > 2) {
          // Buscar el campo de descripción (puede tener varios nombres posibles)
          const descripcionField = document.getElementById('id_diagnostico-descripcion') || 
                                   document.getElementById('id_diagnostico-descripcion_problema') ||
                                   document.querySelector('[name="descripcion"]') ||
                                   document.querySelector('[name="descripcion_problema"]') ||
                                   document.querySelector('textarea[name*="descripcion"]');
          if (descripcionField) {
            descripcionField.value = descripcionValue;
            descripcionField.dispatchEvent(new Event('input', { bubbles: true }));
            descripcionField.dispatchEvent(new Event('change', { bubbles: true }));
            showFeedback(`✅ Descripción ingresada: ${descripcionValue.substring(0, 50)}...`, 'success');
          } else {
            showFeedback('⚠️ Campo de descripción no encontrado', 'error');
          }
          return;
        }
      }
    }

    // Selección de componentes (Paso 2) - MEJORADO
    if (command.match(/^(?:seleccionar|activar|marcar)\s+(?:componente\s+)?(.+)/i)) {
      const componenteMatch = command.match(/(?:seleccionar|activar|marcar)\s+(?:componente\s+)?(.+?)(?:\s+(?:accion|acción|para|y|con)|$)/i);
      if (componenteMatch) {
        const componenteNombre = componenteMatch[1].trim().toLowerCase();
        selectComponente(componenteNombre);
        return;
      }
    }

    if (command.match(/^(?:deseleccionar|desactivar|desmarcar)\s+(?:componente\s+)?(.+)/i)) {
      const componenteMatch = command.match(/(?:deseleccionar|desactivar|desmarcar)\s+(?:componente\s+)?(.+)/i);
      if (componenteMatch) {
        const componenteNombre = componenteMatch[1].trim().toLowerCase();
        deselectComponente(componenteNombre);
        return;
      }
    }

    // Selección de acciones de un componente (Paso 2) - NUEVO
    // Formato: "Acción [nombre acción] para [componente]" o "Seleccionar [acción] en [componente]"
    if (command.match(/^(?:acción|accion|seleccionar acción|seleccionar accion|activar acción|activar accion)\s+(.+?)\s+(?:para|en|de|del)\s+(.+)/i)) {
      const accionMatch = command.match(/(?:acción|accion|seleccionar acción|seleccionar accion|activar acción|activar accion)\s+(.+?)\s+(?:para|en|de|del)\s+(.+)/i);
      if (accionMatch) {
        const accionNombre = accionMatch[1].trim().toLowerCase();
        const componenteNombre = accionMatch[2].trim().toLowerCase();
        selectAccionParaComponente(accionNombre, componenteNombre);
        return;
      }
    }

    // Formato alternativo: "Para [componente] acción [nombre acción]"
    if (command.match(/^(?:para|en|del|de)\s+(.+?)\s+(?:acción|accion|seleccionar acción|seleccionar accion)\s+(.+)/i)) {
      const accionMatch = command.match(/(?:para|en|del|de)\s+(.+?)\s+(?:acción|accion|seleccionar acción|seleccionar accion)\s+(.+)/i);
      if (accionMatch) {
        const componenteNombre = accionMatch[1].trim().toLowerCase();
        const accionNombre = accionMatch[2].trim().toLowerCase();
        selectAccionParaComponente(accionNombre, componenteNombre);
        return;
      }
    }

    // Si no se reconoce el comando
    showFeedback(`⚠️ Comando no reconocido: "${text}"`, 'error');
  }

  // Funciones auxiliares para navegación
  function goToNextStep() {
    const btnNext = document.getElementById('wizard-next');
    if (btnNext && btnNext.style.display !== 'none' && !btnNext.disabled) {
      btnNext.click();
      return true;
    }
    return false;
  }

  function goToPreviousStep() {
    const btnPrev = document.getElementById('wizard-prev');
    if (btnPrev && btnPrev.style.display !== 'none' && !btnPrev.disabled) {
      btnPrev.click();
      return true;
    }
    return false;
  }

  function goToStep(step) {
    const currentPane = document.querySelector('.wizard-pane.active');
    const currentStepNum = currentPane ? parseInt(currentPane.dataset.stepPane) : 1;
    
    if (step === currentStepNum) {
      return; // Ya estamos en ese paso
    }
    
    if (step > currentStepNum) {
      // Avanzar paso a paso
      let stepsToGo = step - currentStepNum;
      let delay = 0;
      for (let i = 0; i < stepsToGo; i++) {
        setTimeout(() => {
          if (!goToNextStep() && i === stepsToGo - 1) {
            showFeedback(`⚠️ No se pudo avanzar al paso ${step}`, 'error');
          }
        }, delay);
        delay += 200; // Pequeño delay entre pasos
      }
    } else if (step < currentStepNum) {
      // Retroceder paso a paso
      let stepsToGo = currentStepNum - step;
      let delay = 0;
      for (let i = 0; i < stepsToGo; i++) {
        setTimeout(() => {
          if (!goToPreviousStep() && i === stepsToGo - 1) {
            showFeedback(`⚠️ No se pudo retroceder al paso ${step}`, 'error');
          }
        }, delay);
        delay += 200;
      }
    }
  }

  // Funciones auxiliares para llenar campos
  function fillField(fieldId, value) {
    const field = document.getElementById(fieldId) || document.querySelector(`[name="${fieldId}"]`);
    if (field) {
      field.value = value;
      field.dispatchEvent(new Event('input', { bubbles: true }));
      field.dispatchEvent(new Event('change', { bubbles: true }));
    } else {
      console.warn(`Campo no encontrado: ${fieldId}`);
    }
  }

  // Funciones para seleccionar/deseleccionar componentes
  function selectComponente(nombre) {
    const componentes = document.querySelectorAll('[data-componente-nombre]');
    let encontrado = false;
    
    componentes.forEach(comp => {
      const compNombre = (comp.dataset.componenteNombre || '').toLowerCase();
      if (compNombre.includes(nombre) || nombre.includes(compNombre)) {
        const checkbox = comp.querySelector('.componente-checkbox');
        if (checkbox) {
          if (!checkbox.checked) {
            checkbox.click();
            encontrado = true;
            showFeedback(`✅ Componente "${comp.dataset.componenteNombre}" seleccionado. Las acciones se cargarán automáticamente.`, 'success');
          } else {
            encontrado = true;
            showFeedback(`ℹ️ Componente "${comp.dataset.componenteNombre}" ya estaba seleccionado`, 'success');
          }
        }
      }
    });
    
    if (!encontrado) {
      showFeedback(`⚠️ No se encontró el componente "${nombre}"`, 'error');
    }
  }

  // Función para seleccionar una acción específica de un componente
  function selectAccionParaComponente(accionNombre, componenteNombre) {
    // Primero, buscar y activar el componente si no está activo
    const componentes = document.querySelectorAll('[data-componente-nombre]');
    let componenteEncontrado = null;
    let componenteId = null;
    
    componentes.forEach(comp => {
      const compNombre = (comp.dataset.componenteNombre || '').toLowerCase();
      if (compNombre.includes(componenteNombre) || componenteNombre.includes(compNombre)) {
        componenteEncontrado = comp;
        componenteId = comp.dataset.componenteId;
        const checkbox = comp.querySelector('.componente-checkbox');
        // Activar el componente si no está activo
        if (checkbox && !checkbox.checked) {
          checkbox.click();
          // Esperar a que se carguen las acciones
          setTimeout(() => {
            buscarYSeleccionarAccion(accionNombre, componenteId, comp);
          }, 1000);
          return;
        }
      }
    });

    if (!componenteEncontrado) {
      showFeedback(`⚠️ No se encontró el componente "${componenteNombre}"`, 'error');
      return;
    }

    // Si el componente ya está activo, buscar la acción inmediatamente
    buscarYSeleccionarAccion(accionNombre, componenteId, componenteEncontrado);
  }

  function buscarYSeleccionarAccion(accionNombre, componenteId, componenteElement) {
    // Buscar el panel de acciones del componente
    const panel = componenteElement.querySelector('.acciones-panel');
    if (!panel) {
      showFeedback(`⚠️ El componente no tiene panel de acciones. Espera a que se carguen.`, 'error');
      return;
    }

    // Buscar todas las acciones disponibles en el panel
    const acciones = panel.querySelectorAll('.accion-item');
    let accionEncontrada = false;

    acciones.forEach(accionItem => {
      const label = accionItem.querySelector('label');
      if (label) {
        const textoAccion = label.textContent.trim().toLowerCase();
        if (textoAccion.includes(accionNombre) || accionNombre.includes(textoAccion)) {
          const checkbox = accionItem.querySelector('.accion-checkbox');
          if (checkbox) {
            if (!checkbox.checked) {
              checkbox.click();
              accionEncontrada = true;
              showFeedback(`✅ Acción "${label.textContent.trim()}" seleccionada para el componente`, 'success');
            } else {
              accionEncontrada = true;
              showFeedback(`ℹ️ Acción "${label.textContent.trim()}" ya estaba seleccionada`, 'success');
            }
          }
        }
      }
    });

    if (!accionEncontrada) {
      // Si no se encontró, puede que las acciones aún no se hayan cargado
      showFeedback(`⚠️ No se encontró la acción "${accionNombre}". Asegúrate de que el componente esté activo y las acciones se hayan cargado.`, 'error');
    }
  }

  function deselectComponente(nombre) {
    const componentes = document.querySelectorAll('[data-componente-nombre]');
    let encontrado = false;
    
    componentes.forEach(comp => {
      const compNombre = (comp.dataset.componenteNombre || '').toLowerCase();
      if (compNombre.includes(nombre) || nombre.includes(compNombre)) {
        const checkbox = comp.querySelector('.componente-checkbox');
        if (checkbox && checkbox.checked) {
          checkbox.click();
          encontrado = true;
          showFeedback(`✅ Componente "${comp.dataset.componenteNombre}" deseleccionado`, 'success');
        }
      }
    });
    
    if (!encontrado) {
      showFeedback(`⚠️ No se encontró el componente "${nombre}"`, 'error');
    }
  }

  // Event listener para el botón de micrófono
  if (voiceBtn && recognition) {
    voiceBtn.addEventListener('click', function() {
      if (isListening) {
        // Detener reconocimiento
        isListening = false;
        isRestarting = false;
        networkErrorCount = 0; // Resetear contador
        try {
          recognition.stop();
        } catch (e) {
          console.log('Error al detener reconocimiento:', e);
        }
        updateVoiceUI('idle');
        hideStatusBanner();
        showFeedback('🔇 Micrófono desactivado', 'success');
      } else {
        // Iniciar reconocimiento
        isListening = true;
        networkErrorCount = 0; // Resetear contador al iniciar manualmente
        try {
          recognition.start();
        } catch (error) {
          console.error('Error al iniciar reconocimiento:', error);
          if (error.message && error.message.includes('already started')) {
            // Ya está iniciado, solo actualizar UI
            isListening = true;
            updateVoiceUI('listening');
            showStatusBanner('🎤 Escuchando... Di tu comando');
          } else {
            showFeedback('Error al iniciar el micrófono. Intenta de nuevo.', 'error');
            isListening = false;
          }
        }
      }
    });
  }

  // Sincronizar con el estado del wizard (escuchar cambios de paso)
  const observer = new MutationObserver(function(mutations) {
    const activePane = document.querySelector('.wizard-pane.active');
    if (activePane) {
      currentStep = parseInt(activePane.dataset.stepPane) || 1;
    }
  });

  const wizardContainer = document.getElementById('ingreso-voz-root');
  if (wizardContainer) {
    observer.observe(wizardContainer, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ['class']
    });
  }

  console.log('✅ Control por voz inicializado correctamente');

});

