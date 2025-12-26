from decimal import Decimal, InvalidOperation
from datetime import date, timedelta
from django.conf import settings
from django.http import Http404
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.templatetags.static import static
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.staticfiles.storage import staticfiles_storage
from django.views.decorators.http import require_GET
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.http import HttpResponse
from django.db.models import Sum
from django.db.models import Q
from urllib.parse import unquote

# NUEVOS IMPORTS PARA PERMISOS
from .decorators import (
    requiere_permiso, requiere_rol, solo_administradores, 
    solo_mecanicos_y_admin, solo_vendedores_y_admin
)
from .forms import RepuestoForm
import pandas as pd
from io import BytesIO
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from difflib import SequenceMatcher
import re
from collections import defaultdict
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from reportlab.lib.styles import ParagraphStyle
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Sum
from django.views.decorators.http import require_http_methods


from .models import Diagnostico, Cliente_Taller, Vehiculo,\
                    Componente, Accion, ComponenteAccion,\
                    DiagnosticoComponenteAccion, Repuesto, VehiculoVersion, RepuestoAplicacion,\
                    DiagnosticoRepuesto, Trabajo, Mecanico, TrabajoFoto,TrabajoRepuesto,\
                    TrabajoAccion, Venta, VentaItem, RepuestoEnStock, StockMovimiento,\
                    VentaPOS, SesionVenta, CarritoItem, AdministracionTaller
from django.contrib.auth.models import User
from django.forms import modelformset_factory
from django.forms import inlineformset_factory
from .utils_auditoria import (
    registrar_diagnostico_creado, registrar_diagnostico_aprobado, registrar_ingreso,
    registrar_cambio_estado, registrar_accion_completada, registrar_accion_pendiente,
    registrar_repuesto_instalado, registrar_repuesto_pendiente, registrar_entrega,
    registrar_abono, registrar_foto_agregada, registrar_mecanico_asignado,
    registrar_mecanico_removido, registrar_observacion
)
from .forms import ComponenteForm, ClienteTallerForm, ClienteTallerRapidoForm, VehiculoForm,\
                   DiagnosticoForm, AccionForm, ComponenteAccionForm,\
                   MecanicoForm, AsignarMecanicosForm, SubirFotoForm,\
                   VentaForm, VentaItemForm, AdministracionTallerForm, RepuestoForm


import datetime
import requests
import json
import openpyxl
import re
import pathlib
import os
from urllib.parse import unquote


def login_view(request):
    # Obtener configuración del taller
    config = AdministracionTaller.get_configuracion_activa()
    
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("panel_principal")  # cámbialo al dashboard que quieras
    else:
        form = AuthenticationForm()
    return render(request, "registration/login.html", {"form": form, "config": config})

def logout_view(request):
    logout(request)
    return redirect("login")


def is_mobile_device(request):
    """
    Detecta si el request viene de un dispositivo móvil.
    Utiliza el User-Agent para identificar móviles, tablets y dispositivos táctiles.
    
    Returns:
        bool: True si es un dispositivo móvil, False si es desktop.
    """
    user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
    mobile_keywords = [
        'mobile', 'android', 'iphone', 'ipad', 'ipod',
        'blackberry', 'windows phone', 'opera mini', 'iemobile',
        'kindle', 'silk', 'fennec', 'maemo', 'tefpad', 'foma',
        'w3c ', 'w3c-', 'netfront', 'opera mobi', 'opera mobi',
        'skyfire', 'bolt', 'iris', 'dolfin', 'palm', 'series',
        'symbian', 'symbos', 'series60', 'series80', 'series90',
        'puffin', 'ucbrowser', 'baiduboxapp', 'miuibrowser'
    ]
    # También detectar por tamaño de pantalla si viene en headers (opcional)
    return any(keyword in user_agent for keyword in mobile_keywords)


@login_required
def componente_list(request):
    # Obtener configuración del taller
    config = AdministracionTaller.get_configuracion_activa()
    
    q = request.GET.get('q', '').strip()
    if q:
        componentes = Componente.objects.filter(nombre__icontains=q).order_by('codigo')
    else:
        componentes = Componente.objects.filter(padre__isnull=True).order_by('codigo')

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        html = render_to_string('car/componentes_tree.html', {'componentes': componentes, 'config': config})
        return JsonResponse({'html': html})

    return render(request, 'car/componentes_list.html', {
        'componentes': componentes,
        'q': q,
        'config': config,
    })


def normalizar_rut(rut):
    """
    Normaliza un RUT para búsquedas: convierte 'k' a minúscula y elimina espacios.
    Esto permite encontrar RUTs independientemente de si tienen 'k' o 'K'.
    """
    if not rut:
        return rut
    rut = str(rut).strip()
    # Si termina en 'k' o 'K', convertir a minúscula
    if rut and rut[-1].lower() == 'k':
        rut = rut[:-1] + 'k'
    return rut

@login_required
@requiere_permiso('diagnosticos')
@transaction.atomic
def ingreso_view(request):
    # Obtener configuración del taller
    config = AdministracionTaller.get_configuracion_activa()
    
    clientes_existentes = Cliente_Taller.objects.filter(activo=True).order_by('nombre')

    selected_cliente = None
    selected_vehiculo = None
    selected_componentes_ids = []

    if request.method == 'POST':
        cliente_form = ClienteTallerForm(request.POST, prefix='cliente')
        vehiculo_form = VehiculoForm(request.POST, prefix='vehiculo')
        diagnostico_form = DiagnosticoForm(request.POST, prefix='diag')

        cliente_id = request.POST.get('cliente_existente')
        vehiculo_id = request.POST.get('vehiculo_existente')
        selected_componentes_ids = request.POST.getlist('componentes_seleccionados')

        # --- Cliente ---
        cliente = None
        if cliente_id:
            # Normalizar el RUT para búsqueda case-insensitive de 'k'
            cliente_id_normalizado = normalizar_rut(cliente_id)
            try:
                cliente = Cliente_Taller.objects.get(rut=cliente_id_normalizado)
                selected_cliente = cliente.rut
            except Cliente_Taller.DoesNotExist:
                # Si no se encuentra, intentar con 'K' mayúscula si el RUT termina en 'k'
                if cliente_id_normalizado and cliente_id_normalizado[-1].lower() == 'k':
                    try:
                        rut_con_k_mayuscula = cliente_id_normalizado[:-1] + 'K'
                        cliente = Cliente_Taller.objects.get(rut=rut_con_k_mayuscula)
                        selected_cliente = cliente.rut
                    except Cliente_Taller.DoesNotExist:
                        cliente_form.add_error(None, "El cliente seleccionado no existe.")
                else:
                    cliente_form.add_error(None, "El cliente seleccionado no existe.")
        else:
            if cliente_form.is_valid():
                cliente = cliente_form.save(commit=False)
                cliente.activo = True  # Asegurar que el cliente esté activo
                cliente.save()
                selected_cliente = cliente.rut

        # --- Vehículo ---
        vehiculo = None
        if vehiculo_id:
            try:
                vehiculo = Vehiculo.objects.get(pk=vehiculo_id, cliente=cliente)
                selected_vehiculo = vehiculo.pk
            except Vehiculo.DoesNotExist:
                vehiculo_form.add_error(None, "El vehículo seleccionado no existe o no pertenece al cliente.")
        else:
            if vehiculo_form.is_valid() and cliente:
                vehiculo = vehiculo_form.save(commit=False)
                vehiculo.cliente = cliente
                vehiculo.save()
                selected_vehiculo = vehiculo.pk

        # --- Diagnóstico ---
        if diagnostico_form.is_valid() and vehiculo:
            diagnostico = diagnostico_form.save(commit=False)
            diagnostico.vehiculo = vehiculo
            diagnostico.save()
            
            # Registrar evento de diagnóstico creado
            registrar_diagnostico_creado(diagnostico, request=request)

            # 🔹 Relación M2M con componentes
            diagnostico.componentes.set(selected_componentes_ids)

            # ====================================================
            # 🔹 Acciones por componente desde hidden JSON
            acciones_json = (request.POST.get("acciones_componentes_json") or "").strip()
            if acciones_json:
                try:
                    items = json.loads(acciones_json)
                    for it in items:
                        try:
                            comp_id = int(it.get("componente_id"))
                            acc_id = int(it.get("accion_id"))
                        except (TypeError, ValueError):
                            continue

                        precio_mano_obra = (it.get("precio_mano_obra") or "").strip()
                        cantidad = int(it.get("cantidad", 1)) if it.get("cantidad") else 1

                        if not diagnostico.componentes.filter(id=comp_id).exists():
                            continue  # ignora acciones de componentes no seleccionados

                        dca = DiagnosticoComponenteAccion(
                            diagnostico=diagnostico,
                            componente_id=comp_id,
                            accion_id=acc_id,
                            cantidad=cantidad
                        )
                        if precio_mano_obra and precio_mano_obra not in ("0", "0.00"):
                            dca.precio_mano_obra = precio_mano_obra
                        dca.save()
                except json.JSONDecodeError:
                    pass
            
            # ====================================================

            # ====================================================
            # 🔹 Repuestos seleccionados desde hidden JSON
            # ====================================================
            repuestos_json = (request.POST.get("repuestos_json") or "").strip()
            print("=" * 80)
            print("📦 DEBUG REPUESTOS_JSON EN BACKEND")
            print("=" * 80)
            print(f"📋 repuestos_json recibido: {repr(repuestos_json)}")
            print(f"📋 Longitud: {len(repuestos_json) if repuestos_json else 0}")
            if repuestos_json:
                try:
                    repuestos_data = json.loads(repuestos_json)
                    print(f"📦 Total repuestos parseados: {len(repuestos_data)}")
                    print(f"📦 Datos completos: {repuestos_data}")
                    
                    for idx, r in enumerate(repuestos_data, 1):
                        try:
                            repuesto_id = int(r.get("id"))
                            repuesto = Repuesto.objects.get(pk=repuesto_id)
                            print(f"✅ [{idx}/{len(repuestos_data)}] Procesando: {repuesto.nombre} (ID: {repuesto_id})")

                            stock_id_raw = r.get("repuesto_stock_id")
                            repuesto_stock = None
                            if stock_id_raw:
                                try:
                                    repuesto_stock = RepuestoEnStock.objects.get(pk=int(stock_id_raw))
                                except (ValueError, RepuestoEnStock.DoesNotExist):
                                    repuesto_stock = None

                            cantidad = int(r.get("cantidad", 1))
                            precio = float(r.get("precio_unitario", repuesto.precio_venta or 0))

                            DiagnosticoRepuesto.objects.create(
                                diagnostico=diagnostico,
                                repuesto=repuesto,
                                repuesto_stock=repuesto_stock,
                                cantidad=cantidad,
                                precio_unitario=precio,
                                subtotal=cantidad * precio
                            )
                            print(f"   ✅ DiagnosticoRepuesto creado: {repuesto.nombre} x{cantidad}")
                        except (ValueError, Repuesto.DoesNotExist, KeyError) as e:
                            print(f"   ❌ Error procesando repuesto: {e}")
                            continue
                    print("=" * 80)
                except json.JSONDecodeError as e:
                    print(f"❌ Error decodificando JSON de repuestos: {e}")
                    print("=" * 80)
                    pass
            else:
                print("⚠️ repuestos_json está vacío o es None")
                print("=" * 80)
            # ====================================================

            # ====================================================
            # 🌐 Repuestos Externos (Referencias)
            # ====================================================
            repuestos_externos_json = (request.POST.get("repuestos_externos_json") or "").strip()
            if repuestos_externos_json:
                try:
                    from .models import RepuestoExterno
                    repuestos_externos_data = json.loads(repuestos_externos_json)
                    for r_ext in repuestos_externos_data:
                        try:
                            repuesto_ext_id = int(r_ext.get("id"))
                            repuesto_externo = RepuestoExterno.objects.get(pk=repuesto_ext_id)
                            
                            cantidad = int(r_ext.get("cantidad", 1))
                            precio = float(r_ext.get("precio", repuesto_externo.precio_referencial))
                            
                            # Crear el DiagnosticoRepuesto con referencia externa
                            DiagnosticoRepuesto.objects.create(
                                diagnostico=diagnostico,
                                repuesto=None,  # Sin repuesto del inventario
                                repuesto_externo=repuesto_externo,  # NUEVO: Referencia al repuesto externo
                                repuesto_stock=None,
                                cantidad=cantidad,
                                precio_unitario=precio,
                                subtotal=cantidad * precio
                            )
                            
                            # Incrementar contador de uso
                            repuesto_externo.incrementar_uso()
                            
                        except (ValueError, RepuestoExterno.DoesNotExist, KeyError) as e:
                            print(f"Error procesando repuesto externo: {e}")
                            continue
                except json.JSONDecodeError as e:
                    print(f"Error decodificando JSON de repuestos externos: {e}")
                    pass
            # ====================================================
            # 🧰 Nota: Los insumos ahora se agregan directamente a repuestos_json
            # desde el frontend, por lo que ya fueron procesados arriba ⬆️
            # ====================================================

            config = AdministracionTaller.get_configuracion_activa()
            if config.ver_mensajes:
                messages.success(request, "Ingreso guardado correctamente.")
            return redirect('panel_principal')

        # else → si hay errores, sigue abajo y vuelve a renderizar

    else:
        cliente_form = ClienteTallerForm(prefix='cliente')
        vehiculo_form = VehiculoForm(prefix='vehiculo')
        diagnostico_form = DiagnosticoForm(prefix='diag')

    vehiculos_existentes = Vehiculo.objects.none()

    # cargar motor.svg como string
    svg_path = os.path.join(settings.BASE_DIR, "static", "images", "vehiculo-desde-abajo.svg")
    svg_content = ""
    try:
        with open(svg_path, "r", encoding="utf-8") as f:
            svg_content = f.read()
    except FileNotFoundError:
        pass

    # Determinar template según dispositivo y ruta solicitada
    is_mobile = is_mobile_device(request)
    resolver_name = getattr(getattr(request, "resolver_match", None), "url_name", None)
    
    # Template de voz tiene prioridad
    if resolver_name == 'ingreso_voz':
        template_name = 'car/ingreso_movil_voz.html'
    elif (
        is_mobile or
        request.GET.get('layout') == 'fusionado' or
        resolver_name == 'ingreso_rapido'
    ):
        template_name = 'car/ingreso_fusionado.html'
    else:
        template_name = 'car/ingreso-pc.html'

    return render(request, template_name, {
        'cliente_form': cliente_form,
        'vehiculo_form': vehiculo_form,
        'config': config,
        'diagnostico_form': diagnostico_form,
        'clientes_existentes': clientes_existentes,
        'vehiculos_existentes': vehiculos_existentes,
        'selected_cliente': selected_cliente,
        'selected_vehiculo': selected_vehiculo,
        'componentes': Componente.objects.filter(padre__isnull=True, activo=True).order_by('nombre'),
        'selected_componentes_ids': selected_componentes_ids,
        'svg': svg_content,
    })





@login_required
def ingreso_exitoso_view(request):
    # Obtener configuración del taller
    config = AdministracionTaller.get_configuracion_activa()
    
    return render(request, 'car/ingreso_exitoso.html', {'config': config})

@login_required
def eliminar_diagnostico(request, pk):
    config = AdministracionTaller.get_configuracion_activa()
    diag = get_object_or_404(Diagnostico, pk=pk)
    diag.delete()
    if config.ver_mensajes:
        messages.success(request, "Diagnóstico eliminado.")
    return redirect('ingreso')

@login_required
def editar_diagnostico(request, pk):
    diag = get_object_or_404(Diagnostico, pk=pk)
    diagnostico_form = DiagnosticoForm(request.POST or None, instance=diag)
    if request.method == 'POST' and diagnostico_form.is_valid():
        diagnostico_form.save()
        return redirect('ingreso')
    # Obtener configuración del taller
    config = AdministracionTaller.get_configuracion_activa()
    
    return render(request, 'car/editar_diagnostico.html', {'form': diagnostico_form, 'config': config})

@login_required
def componente_create(request):
    if request.method == 'POST':
        form = ComponenteForm(request.POST)
        if form.is_valid():
            try:
                config = AdministracionTaller.get_configuracion_activa()
                form.save()
                if config.ver_mensajes:
                    messages.success(request, 'Componente creado correctamente.')
                return redirect('componente_list')
            except (ValidationError, IntegrityError) as e:
                # Muestra el error en el form sin 500
                #form.add_error(None, getattr(e, 'message', str(e)))
                config = AdministracionTaller.get_configuracion_activa()
                if config.ver_mensajes:
                    messages.error(request, 'El componente ya existe. Por favor, use un nombre o código diferente.')
        else:
            # Manejar errores de validación del formulario
            config = AdministracionTaller.get_configuracion_activa()
            if config.ver_mensajes:
                messages.error(request, 'Por favor, corrija los errores en el formulario.')

    else:
        form = ComponenteForm()
    return render(request, 'car/componentes_form.html', {
        'form': form,
        'titulo': 'Nuevo Componente',
        'submit_label': 'Crear',
    })

@login_required
def componente_update(request, pk):
    componente = get_object_or_404(Componente, pk=pk)
    if request.method == 'POST':
        form = ComponenteForm(request.POST, instance=componente)
        if form.is_valid():
            form.save()
            config = AdministracionTaller.get_configuracion_activa()
            if config.ver_mensajes:
                messages.success(request, 'Componente actualizado.')
            return redirect('componente_list')
    else:
        form = ComponenteForm(instance=componente)
    return render(request, 'car/componentes_form.html', {
        'form': form,
        'titulo': 'Editar Componente',
        'submit_label': 'Guardar cambios',
    })

@login_required
def componente_delete(request, pk):
    componente = get_object_or_404(Componente, pk=pk)
    # Obtener configuración del taller
    config = AdministracionTaller.get_configuracion_activa()
    
    # Si ver_avisos = False, eliminar directamente sin mostrar confirmación
    if not config.ver_avisos:
        componente.delete()
        if config.ver_mensajes:
            messages.success(request, 'Componente eliminado.')
        return redirect('componente_list')
    
    if request.method == 'POST':
        componente.delete()
        if config.ver_mensajes:
            messages.success(request, 'Componente eliminado.')
        return redirect('componente_list')
    
    return render(request, 'car/componentes_confirm_delete.html', {
        'componente': componente,
        'config': config
    })


@login_required
def mostrar_plano(request):
    svg_path = pathlib.Path(settings.BASE_DIR) / 'static' / 'images' / 'vehiculo-desde-abajo.svg'
    svg_content = svg_path.read_text(encoding='utf-8')
    # Obtener configuración del taller
    config = AdministracionTaller.get_configuracion_activa()
    
    return render(request, 'car/plano_interactivo.html', {'svg': svg_content, 'config': config})

@login_required
def componentes_lookup(request):
    part = (request.GET.get('part') or '').strip()
    if not part:
        return JsonResponse({'error': 'missing part'}, status=400)

    part_norm = part.lower()

    import re
    if re.match(r'^(g\d+|svg\d+)$', part_norm):
        return JsonResponse({'found': False})

    try:
        comp = Componente.objects.get(codigo__iexact=part_norm)
    except Componente.DoesNotExist:
        comp = Componente.objects.filter(nombre__iexact=part_norm).first()

    if not comp:
        return JsonResponse({'found': False})

    hijos = list(comp.hijos.values('id', 'nombre', 'codigo'))

    # 🔹 buscar imagen en este componente o en su cadena de padres
    imagen_url = None
    current = comp
    while current and not imagen_url:
        try:
            if hasattr(current, 'imagen') and current.imagen:
                imagen_url = current.imagen.url
            else:
                imagen_url = staticfiles_storage.url(f'images/{current.codigo}.svg')
        except Exception:
            imagen_url = settings.STATIC_URL + f'images/{current.codigo}.svg'

        # si tampoco existe, subir al padre
        if not current.padre_id:  
            break
        current = current.padre

    parent = {
        'id': comp.id,
        'nombre': comp.nombre,
        'codigo': comp.codigo,
        'imagen_url': imagen_url
    }

    return JsonResponse({'found': True, 'parent': parent, 'children': hijos})

@login_required
def seleccionar_componente(request, codigo):
    try:
        comp = Componente.objects.get(codigo=codigo)
    except Componente.DoesNotExist:
        raise Http404("Componente nox encontrado")

    hijos = list(comp.hijos.values('id', 'nombre', 'codigo'))
    return JsonResponse({
        'id': comp.id,
        'nombre': comp.nombre,
        'codigo': comp.codigo,
        'hijos': hijos
    })


@login_required
def get_vehiculos_por_cliente(request, cliente_id):
    """
    Devuelve vehículos por cliente_id (RUT).
    Busca intentando ambas variantes (k minúscula y K mayúscula) simultáneamente.
    """
    import logging
    import sys
    logger = logging.getLogger(__name__)
    
    # Forzar salida inmediata a stdout/stderr para Docker - PRIMERO QUE TODO
    print(f"\n{'='*80}", file=sys.stderr, flush=True)
    print(f"🚨 get_vehiculos_por_cliente - FUNCIÓN LLAMADA - RUT: '{cliente_id}'", file=sys.stderr, flush=True)
    print(f"🚨 Request path: {request.path}", file=sys.stderr, flush=True)
    print(f"🚨 Request method: {request.method}", file=sys.stderr, flush=True)
    print(f"🚨 User authenticated: {request.user.is_authenticated}", file=sys.stderr, flush=True)
    print(f"🚨 User: {request.user.username if request.user.is_authenticated else 'ANÓNIMO'}", file=sys.stderr, flush=True)
    print(f"{'='*80}\n", file=sys.stderr, flush=True)
    
    # El decorador @login_required ya maneja la autenticación, pero mantenemos el logging
    if not request.user.is_authenticated:
        print(f"❌ USUARIO NO AUTENTICADO - Retornando 401", file=sys.stderr, flush=True)
        return JsonResponse({'error': 'No autenticado. Por favor inicia sesión.'}, status=401)
    
    if not cliente_id:
        logger.error("❌ get_vehiculos_por_cliente - cliente_id vacío")
        return JsonResponse({'error': 'Parámetro cliente_id vacío'}, status=400)
    
    cliente_id = str(cliente_id).strip()
    
    # Logging a stderr para que aparezca en docker logs
    print(f"🔍 RUT recibido: '{cliente_id}'", file=sys.stderr, flush=True)
    print(f"🔍 Request path: {request.path}", file=sys.stderr, flush=True)
    print(f"🔍 Request method: {request.method}", file=sys.stderr, flush=True)
    print(f"🔍 User: {request.user.username if request.user.is_authenticated else 'Anónimo'}", file=sys.stderr, flush=True)
    
    logger.info(f"🔍 get_vehiculos_por_cliente - INICIO - RUT recibido: '{cliente_id}'")
    logger.info(f"🔍 Request path: {request.path}")
    logger.info(f"🔍 Request method: {request.method}")
    logger.info(f"🔍 User: {request.user.username if request.user.is_authenticated else 'Anónimo'}")
    
    # Si el RUT termina en 'k' o 'K', buscar ambas variantes simultáneamente
    if cliente_id and cliente_id[-1].lower() == 'k':
        # Construir ambas variantes (mantener el formato original del RUT)
        # Si viene "15056879k", buscar tanto "15056879k" como "15056879K"
        rut_minuscula = cliente_id[:-1] + 'k'
        rut_mayuscula = cliente_id[:-1] + 'K'
        
        print(f"🔍 RUT termina en k/K - Buscando variantes:", file=sys.stderr, flush=True)
        print(f"   - Minúscula: '{rut_minuscula}'", file=sys.stderr, flush=True)
        print(f"   - Mayúscula: '{rut_mayuscula}'", file=sys.stderr, flush=True)
        
        logger.info(f"🔍 RUT termina en k/K - Buscando variantes:")
        logger.info(f"   - Minúscula: '{rut_minuscula}'")
        logger.info(f"   - Mayúscula: '{rut_mayuscula}'")
        
        # Verificar qué RUTs existen en la BD antes de buscar
        cliente_min_bd = Cliente_Taller.objects.filter(rut=rut_minuscula).first()
        cliente_may_bd = Cliente_Taller.objects.filter(rut=rut_mayuscula).first()
        
        print(f"🔍 Verificación directa en BD:", file=sys.stderr, flush=True)
        print(f"   - Cliente con '{rut_minuscula}': {'✅ EXISTE' if cliente_min_bd else '❌ NO EXISTE'}", file=sys.stderr, flush=True)
        if cliente_min_bd:
            print(f"      → Nombre: {cliente_min_bd.nombre}, RUT en BD: '{cliente_min_bd.rut}'", file=sys.stderr, flush=True)
        print(f"   - Cliente con '{rut_mayuscula}': {'✅ EXISTE' if cliente_may_bd else '❌ NO EXISTE'}", file=sys.stderr, flush=True)
        if cliente_may_bd:
            print(f"      → Nombre: {cliente_may_bd.nombre}, RUT en BD: '{cliente_may_bd.rut}'", file=sys.stderr, flush=True)
        
        logger.info(f"🔍 Verificación directa en BD:")
        logger.info(f"   - Cliente con '{rut_minuscula}': {'✅ EXISTE' if cliente_min_bd else '❌ NO EXISTE'}")
        if cliente_min_bd:
            logger.info(f"      → Nombre: {cliente_min_bd.nombre}, RUT en BD: '{cliente_min_bd.rut}'")
        logger.info(f"   - Cliente con '{rut_mayuscula}': {'✅ EXISTE' if cliente_may_bd else '❌ NO EXISTE'}")
        if cliente_may_bd:
            logger.info(f"      → Nombre: {cliente_may_bd.nombre}, RUT en BD: '{cliente_may_bd.rut}'")
        
        # Buscar vehículos usando Q object para buscar ambas variantes
        vehiculos = Vehiculo.objects.filter(
            Q(cliente__rut=rut_minuscula) | Q(cliente__rut=rut_mayuscula)
        ).order_by('placa')
        
        logger.info(f"🔍 Búsqueda con Q object - Vehículos encontrados: {vehiculos.count()}")
        if vehiculos.exists():
            for v in vehiculos:
                logger.info(f"   → Vehículo: {v.placa} | Cliente RUT: '{v.cliente.rut}'")
        
        # Verificar si el cliente existe (para dar mejor mensaje de error)
        cliente_existe = Cliente_Taller.objects.filter(
            Q(rut=rut_minuscula) | Q(rut=rut_mayuscula)
        ).exists()
        
        logger.info(f"🔍 Cliente existe (Q filter): {cliente_existe}")
        
        if cliente_existe:
            cliente_encontrado = Cliente_Taller.objects.filter(
                Q(rut=rut_minuscula) | Q(rut=rut_mayuscula)
            ).first()
            logger.info(f"✅ Cliente encontrado con RUT en BD: '{cliente_encontrado.rut if cliente_encontrado else 'N/A'}'")
            logger.info(f"✅ Vehículos encontrados: {vehiculos.count()}")
    else:
        # Si no termina en k/K, buscar directamente
        logger.info(f"🔍 RUT no termina en k/K - Búsqueda directa: '{cliente_id}'")
        
        cliente_directo = Cliente_Taller.objects.filter(rut=cliente_id).first()
        logger.info(f"🔍 Cliente con RUT '{cliente_id}': {'✅ EXISTE' if cliente_directo else '❌ NO EXISTE'}")
        if cliente_directo:
            logger.info(f"   → Nombre: {cliente_directo.nombre}, RUT en BD: '{cliente_directo.rut}'")
        
        vehiculos = Vehiculo.objects.filter(cliente__rut=cliente_id).order_by('placa')
        cliente_existe = Cliente_Taller.objects.filter(rut=cliente_id).exists()
        logger.info(f"🔍 Buscando RUT directo: '{cliente_id}' - Existe: {cliente_existe}, Vehículos: {vehiculos.count()}")
    
    # Si no se encuentran vehículos, verificar si el cliente existe
    if not vehiculos.exists():
        if not cliente_existe:
            # Construir mensaje de error con variantes intentadas
            variantes_intentadas = [cliente_id]
            if cliente_id and cliente_id[-1].lower() == 'k':
                variantes_intentadas.extend([cliente_id[:-1] + 'k', cliente_id[:-1] + 'K'])
            
            # Debug: verificar qué RUTs existen en la BD que sean similares
            rut_base = cliente_id[:-1] if cliente_id and cliente_id[-1].lower() == 'k' else cliente_id
            rut_similares = Cliente_Taller.objects.filter(rut__startswith=rut_base).values_list('rut', flat=True)[:10]
            
            print(f"\n❌ ERROR - Cliente no encontrado", file=sys.stderr, flush=True)
            print(f"   RUT recibido: '{cliente_id}'", file=sys.stderr, flush=True)
            print(f"   Variantes intentadas: {variantes_intentadas}", file=sys.stderr, flush=True)
            print(f"   RUTs similares en BD (primeros 10): {list(rut_similares)}", file=sys.stderr, flush=True)
            
            # Verificar todos los RUTs que terminan en k/K
            todos_ruts_k = Cliente_Taller.objects.filter(
                Q(rut__endswith='k') | Q(rut__endswith='K')
            ).values_list('rut', flat=True)[:20]
            print(f"   Todos los RUTs con k/K en BD (primeros 20): {list(todos_ruts_k)}", file=sys.stderr, flush=True)
            print(f"{'='*80}\n", file=sys.stderr, flush=True)
            
            logger.error(f"❌ ERROR - Cliente no encontrado")
            logger.error(f"   RUT recibido: '{cliente_id}'")
            logger.error(f"   Variantes intentadas: {variantes_intentadas}")
            logger.error(f"   RUTs similares en BD (primeros 10): {list(rut_similares)}")
            logger.error(f"   Todos los RUTs con k/K en BD (primeros 20): {list(todos_ruts_k)}")
            
            return JsonResponse({
                'error': f'Cliente no encontrado con RUT: {cliente_id}',
                'variantes_intentadas': variantes_intentadas,
                'rut_similares_en_bd': list(rut_similares) if rut_similares else []
            }, status=404)
        
        # Si el cliente existe pero no tiene vehículos, retornar lista vacía
        logger.info(f"✅ Cliente existe pero no tiene vehículos - RUT: '{cliente_id}'")
        vehiculos = Vehiculo.objects.none()
    else:
        logger.info(f"✅ ÉXITO - Retornando {vehiculos.count()} vehículos para RUT: '{cliente_id}'")
    
    data = [
        {
            "id": v.id,
            "placa": v.placa,
            "marca": v.marca,
            "modelo": v.modelo,
            "anio": v.anio,
        }
        for v in vehiculos
    ]
    
    print(f"✅ FINAL - Retornando {len(data)} vehículos en JSON para RUT: '{cliente_id}'", file=sys.stderr, flush=True)
    print(f"✅ Datos: {data}", file=sys.stderr, flush=True)
    print(f"{'='*80}\n", file=sys.stderr, flush=True)
    
    logger.info(f"✅ FINAL - Retornando {len(data)} vehículos en JSON para RUT: '{cliente_id}'")
    logger.info(f"✅ Datos: {data}")
    
    return JsonResponse(data, safe=False)

@login_required
@requiere_permiso('diagnosticos')
def lista_diagnosticos(request):
    # Obtener configuración del taller
    config = AdministracionTaller.get_configuracion_activa()
    
    # 🔹 Manejar ocultar diagnóstico
    if request.method == "POST" and "ocultar_diagnostico" in request.POST:
        diagnostico_id = request.POST.get("diagnostico_id")
        try:
            diagnostico = Diagnostico.objects.get(id=diagnostico_id)
            diagnostico.visible = False
            config = AdministracionTaller.get_configuracion_activa()
            diagnostico.save()
            if config.ver_mensajes:
                messages.success(request, f"Diagnóstico #{diagnostico.id} ocultado del listado.")
        except Diagnostico.DoesNotExist:
            config = AdministracionTaller.get_configuracion_activa()
            if config.ver_mensajes:
                messages.error(request, "Diagnóstico no encontrado.")
        return redirect('lista_diagnosticos')
    
    # 🔹 Filtrar solo diagnósticos visibles (visible=True)
    diagnosticos = Diagnostico.objects.filter(visible=True).select_related(
        'vehiculo__cliente'
    ).prefetch_related(
        'componentes',
        'acciones_componentes__accion',
        'acciones_componentes__componente',
        'repuestos'
    ).order_by('-fecha')

    # Los totales ahora se calculan automáticamente usando @property en el modelo
    # No es necesario calcularlos aquí - se acceden directamente en el template

    return render(request, 'car/diagnostico_lista.html', {
        'diagnosticos': diagnosticos,
        'config': config
    })

@login_required
@requiere_permiso('diagnosticos')
def editar_diagnostico(request, pk):
    """Editar diagnóstico con pestañas para acciones, repuestos e insumos"""
    diagnostico = get_object_or_404(Diagnostico, pk=pk)
    
    # 🔹 Helper para redirects con pestaña activa
    def redirect_with_tab(tab_name):
        from django.http import HttpResponseRedirect
        return HttpResponseRedirect(f"/car/diagnosticos/{diagnostico.pk}/editar/?tab={tab_name}")
    
    # Formularios
    from .forms import DiagnosticoForm
    diagnostico_form = DiagnosticoForm(instance=diagnostico)
    
    # Obtener datos para los formularios de agregar
    from .models import Componente, Accion, Repuesto
    from django.db.models import Q
    acciones_disponibles = Accion.objects.all()
    
    # 🔹 COMPONENTES DISPONIBLES (solo componentes padre con sus hijos)
    componentes = Componente.objects.filter(padre__isnull=True, activo=True).prefetch_related('hijos')
    
    # 🔹 FILTRO INTELIGENTE DE REPUESTOS basado en el vehículo del diagnóstico
    repuestos_disponibles = Repuesto.objects.all()
    if diagnostico.vehiculo:
        veh = diagnostico.vehiculo
        veh_marca = veh.marca
        veh_modelo = veh.modelo
        veh_anio = veh.anio
        
        # Filtro inteligente por marca, modelo y año
        repuestos_disponibles = repuestos_disponibles.filter(
            Q(marca_veh__icontains=veh_marca) |
            Q(marca_veh__icontains=veh_modelo) |
            Q(marca_veh__icontains=str(veh_anio)) |
            Q(marca_veh__isnull=True) |  # Incluir repuestos sin marca específica
            Q(marca_veh="")  # Incluir repuestos con marca vacía
        ).distinct()
    
    # 🔹 Detectar pestaña activa desde parámetros URL
    active_tab = request.GET.get('tab', 'acciones')
    
    # 🔹 Obtener componentes ya seleccionados en el diagnóstico
    componentes_diagnostico = list(diagnostico.componentes.values_list('id', flat=True))
    
    # Obtener configuración del taller
    config = AdministracionTaller.get_configuracion_activa()
    
    # 🔹 Manejo de formularios POST
    if request.method == "POST":
        # 🔹 Actualizar descripción del diagnóstico
        if "actualizar_descripcion" in request.POST:
            diagnostico_form = DiagnosticoForm(request.POST, instance=diagnostico)
            if diagnostico_form.is_valid():
                config = AdministracionTaller.get_configuracion_activa()
                diagnostico_form.save()
                if config.ver_mensajes:
                    messages.success(request, "Descripción del diagnóstico actualizada.")
                return redirect_with_tab("acciones")
        
        # 🔹 Agregar acción al diagnóstico
        elif "agregar_accion" in request.POST:
            componente_id = request.POST.get("componente")
            accion_id = request.POST.get("accion")
            precio_mano_obra = request.POST.get("precio_mano_obra", 0)
            
            if componente_id and accion_id:
                try:
                    from .models import DiagnosticoComponenteAccion
                    componente = Componente.objects.get(id=componente_id)
                    accion = Accion.objects.get(id=accion_id)
                    
                    # Verificar si ya existe esta combinación
                    if not DiagnosticoComponenteAccion.objects.filter(
                        diagnostico=diagnostico,
                        componente=componente,
                        accion=accion
                    ).exists():
                        DiagnosticoComponenteAccion.objects.create(
                            diagnostico=diagnostico,
                            componente=componente,
                            accion=accion,
                            precio_mano_obra=float(precio_mano_obra) if precio_mano_obra else 0
                        )
                        config = AdministracionTaller.get_configuracion_activa()
                        if config.ver_mensajes:
                            messages.success(request, f"Acción '{accion.nombre}' agregada a '{componente.nombre}'.")
                    else:
                        config = AdministracionTaller.get_configuracion_activa()
                        if config.ver_mensajes:
                            messages.warning(request, "Esta acción ya está agregada para este componente.")
                except (Componente.DoesNotExist, Accion.DoesNotExist):
                    config = AdministracionTaller.get_configuracion_activa()
                    if config.ver_mensajes:
                        messages.error(request, "Componente o acción no válidos.")
            else:
                config = AdministracionTaller.get_configuracion_activa()
                if config.ver_mensajes:
                    messages.error(request, "Debe seleccionar componente y acción.")
            
            return redirect_with_tab("acciones")
        
        # 🔹 Agregar múltiples acciones (nuevo método)
        elif "agregar_acciones_multiples" in request.POST:
            import json
            import logging
            logger = logging.getLogger(__name__)
            
            logger.info("🔍 INICIANDO AGREGAR ACCIONES MÚLTIPLES")
            logger.info(f"📋 Diagnóstico ID: {diagnostico.id}")
            logger.info(f"📋 POST data: {dict(request.POST)}")
            
            acciones_json = request.POST.get("acciones_json", "")
            componente_id = request.POST.get("componente")
            
            logger.info(f"📋 Acciones JSON: {acciones_json}")
            logger.info(f"📋 Componente ID: {componente_id}")
            
            if acciones_json and componente_id:
                try:
                    acciones_data = json.loads(acciones_json)
                    logger.info(f"📋 Acciones parseadas: {acciones_data}")
                    acciones_creadas = 0
                    
                    for accion_data in acciones_data:
                        try:
                            from .models import DiagnosticoComponenteAccion
                            accion_id = int(accion_data.get("id"))
                            precio_mano_obra = float(accion_data.get("precio", 0))
                            
                            logger.info(f"🛠️ Procesando acción ID: {accion_id}, Precio: {precio_mano_obra}")
                            
                            accion = Accion.objects.get(id=accion_id)
                            componente = Componente.objects.get(id=componente_id)
                            
                            logger.info(f"🛠️ Acción encontrada: {accion.nombre}")
                            logger.info(f"🛠️ Componente encontrado: {componente.nombre}")
                            
                            # Verificar si ya existe esta combinación
                            if not DiagnosticoComponenteAccion.objects.filter(
                                diagnostico=diagnostico,
                                componente=componente,
                                accion=accion
                            ).exists():
                                dca = DiagnosticoComponenteAccion.objects.create(
                                    diagnostico=diagnostico,
                                    componente=componente,
                                    accion=accion,
                                    precio_mano_obra=precio_mano_obra
                                )
                                logger.info(f"✅ Acción creada: {dca.id}")
                                acciones_creadas += 1
                            else:
                                logger.info(f"⚠️ Acción ya existe para este componente")
                                
                        except (ValueError, Accion.DoesNotExist, Componente.DoesNotExist) as e:
                            logger.error(f"❌ Error procesando acción: {e}")
                            continue
                    
                    logger.info(f"📊 Total acciones creadas: {acciones_creadas}")
                    
                    config = AdministracionTaller.get_configuracion_activa()
                    if acciones_creadas > 0:
                        if config.ver_mensajes:
                            config = AdministracionTaller.get_configuracion_activa()
                            if config.ver_mensajes:
                                messages.success(request, f"{acciones_creadas} acción(es) agregada(s) al diagnóstico.")
                    else:
                        config = AdministracionTaller.get_configuracion_activa()
                        if config.ver_mensajes:
                            messages.info(request, "No se agregaron acciones nuevas (posiblemente ya existían).")
                        
                except json.JSONDecodeError as e:
                    logger.error(f"❌ Error parseando JSON: {e}")
                    config = AdministracionTaller.get_configuracion_activa()
                    if config.ver_mensajes:
                        messages.error(request, "Error al procesar las acciones.")
            else:
                logger.error("❌ Faltan datos: acciones_json o componente_id")
                config = AdministracionTaller.get_configuracion_activa()
                if config.ver_mensajes:
                    messages.error(request, "No se recibieron acciones o componente para agregar.")
            
            return redirect_with_tab("acciones")
        
        # 🔹 Toggle acción completada / pendiente
        elif "accion_toggle" in request.POST:
            dca_id = request.POST.get("accion_toggle")
            try:
                from .models import DiagnosticoComponenteAccion
                dca = DiagnosticoComponenteAccion.objects.get(id=dca_id, diagnostico=diagnostico)
                dca.completado = not dca.completado
                dca.fecha = timezone.now() if dca.completado else None
                dca.save()
                config = AdministracionTaller.get_configuracion_activa()
                if config.ver_mensajes:
                    config = AdministracionTaller.get_configuracion_activa()
                    if config.ver_mensajes:
                        config = AdministracionTaller.get_configuracion_activa()
                        if config.ver_mensajes:
                            config = AdministracionTaller.get_configuracion_activa()
                            if config.ver_mensajes:
                                messages.success(request, f"Acción '{dca.accion.nombre}' actualizada.")
            except DiagnosticoComponenteAccion.DoesNotExist:
                messages.error(request, "Acción no encontrada.")
            
            return redirect_with_tab("acciones")
        
        # 🔹 Agregar repuesto al diagnóstico
        elif "agregar_repuesto" in request.POST:
            repuesto_id = request.POST.get("repuesto")
            cantidad = request.POST.get("cantidad", 1)
            precio_unitario = request.POST.get("precio_unitario", 0)
            
            if repuesto_id:
                try:
                    from .models import DiagnosticoRepuesto
                    repuesto = Repuesto.objects.get(id=repuesto_id)
                    
                    # Verificar si ya existe este repuesto
                    if not DiagnosticoRepuesto.objects.filter(
                        diagnostico=diagnostico,
                        repuesto=repuesto
                    ).exists():
                        DiagnosticoRepuesto.objects.create(
                            diagnostico=diagnostico,
                            repuesto=repuesto,
                            cantidad=int(cantidad),
                            precio_unitario=float(precio_unitario) if precio_unitario else 0,
                            subtotal=int(cantidad) * (float(precio_unitario) if precio_unitario else 0)
                        )
                        config = AdministracionTaller.get_configuracion_activa()
                        if config.ver_mensajes:
                            messages.success(request, f"Repuesto '{repuesto.nombre}' agregado.")
                    else:
                        config = AdministracionTaller.get_configuracion_activa()
                        if config.ver_mensajes:
                            messages.warning(request, "Este repuesto ya está agregado.")
                except Repuesto.DoesNotExist:
                    config = AdministracionTaller.get_configuracion_activa()
                    if config.ver_mensajes:
                        messages.error(request, "Repuesto no válido.")
            else:
                config = AdministracionTaller.get_configuracion_activa()
                if config.ver_mensajes:
                    messages.error(request, "Debe seleccionar un repuesto.")
            
            return redirect_with_tab("repuestos")
        
        # 🔹 Agregar múltiples repuestos (nuevo método)
        elif "agregar_repuestos_multiples" in request.POST:
            import json
            repuestos_json = request.POST.get("repuestos_json", "")
            
            if repuestos_json:
                try:
                    repuestos_data = json.loads(repuestos_json)
                    repuestos_creados = 0
                    
                    for repuesto_data in repuestos_data:
                        try:
                            from .models import DiagnosticoRepuesto
                            repuesto_id = int(repuesto_data.get("id"))
                            cantidad = int(repuesto_data.get("cantidad", 1))
                            precio_unitario = float(repuesto_data.get("precio_unitario", 0))
                            
                            repuesto = Repuesto.objects.get(id=repuesto_id)
                            
                            # Verificar si ya existe este repuesto en el diagnóstico
                            if not DiagnosticoRepuesto.objects.filter(
                                diagnostico=diagnostico,
                                repuesto=repuesto
                            ).exists():
                                DiagnosticoRepuesto.objects.create(
                                    diagnostico=diagnostico,
                                    repuesto=repuesto,
                                    cantidad=cantidad,
                                    precio_unitario=precio_unitario,
                                    subtotal=cantidad * precio_unitario
                                )
                                repuestos_creados += 1
                                
                        except (ValueError, Repuesto.DoesNotExist):
                            continue
                    
                    if repuestos_creados > 0:
                        config = AdministracionTaller.get_configuracion_activa()
                        if config.ver_mensajes:
                            messages.success(request, f"{repuestos_creados} repuesto(s) agregado(s) al diagnóstico.")
                    else:
                        config = AdministracionTaller.get_configuracion_activa()
                        if config.ver_mensajes:
                            messages.info(request, "No se agregaron repuestos nuevos (posiblemente ya existían).")
                        
                except json.JSONDecodeError:
                    messages.error(request, "Error al procesar los repuestos.")
            else:
                messages.error(request, "No se recibieron repuestos para agregar.")
            
            return redirect_with_tab("repuestos")
        
        # 🔹 Agregar múltiples insumos (nuevo método)
        elif "agregar_insumos_multiples" in request.POST:
            import json
            insumos_json = request.POST.get("insumos_json", "")
            
            if insumos_json:
                try:
                    insumos_data = json.loads(insumos_json)
                    insumos_creados = 0
                    
                    for insumo_data in insumos_data:
                        try:
                            from .models import DiagnosticoRepuesto
                            repuesto_id = int(insumo_data.get("id"))
                            cantidad = int(insumo_data.get("cantidad", 1))
                            precio_unitario = float(insumo_data.get("precio_unitario", 0))
                            
                            repuesto = Repuesto.objects.get(id=repuesto_id)
                            
                            # Verificar si ya existe este repuesto en el diagnóstico
                            if not DiagnosticoRepuesto.objects.filter(
                                diagnostico=diagnostico,
                                repuesto=repuesto
                            ).exists():
                                DiagnosticoRepuesto.objects.create(
                                    diagnostico=diagnostico,
                                    repuesto=repuesto,
                                    cantidad=cantidad,
                                    precio_unitario=precio_unitario,
                                    subtotal=cantidad * precio_unitario
                                )
                                insumos_creados += 1
                                
                        except (ValueError, Repuesto.DoesNotExist):
                            continue
                    
                    config = AdministracionTaller.get_configuracion_activa()
                    if insumos_creados > 0:
                        if config.ver_mensajes:
                            messages.success(request, f"{insumos_creados} insumo(s) agregado(s) al diagnóstico.")
                    else:
                        if config.ver_mensajes:
                            messages.info(request, "No se agregaron insumos nuevos (posiblemente ya existían).")
                        
                except json.JSONDecodeError:
                    config = AdministracionTaller.get_configuracion_activa()
                    if config.ver_mensajes:
                        messages.error(request, "Error al procesar los insumos.")
            else:
                config = AdministracionTaller.get_configuracion_activa()
                if config.ver_mensajes:
                    messages.error(request, "No se recibieron insumos para agregar.")
            
            return redirect_with_tab("insumos")
        
        # 🔹 Quitar repuesto del diagnóstico
        elif "quitar_repuesto" in request.POST:
            config = AdministracionTaller.get_configuracion_activa()
            rep_id = request.POST.get("quitar_repuesto")
            try:
                from .models import DiagnosticoRepuesto
                rep = DiagnosticoRepuesto.objects.get(id=rep_id, diagnostico=diagnostico)
                rep_nombre = rep.repuesto.nombre
                rep.delete()
                if config.ver_mensajes:
                    messages.success(request, f"Repuesto '{rep_nombre}' quitado del diagnóstico.")
            except DiagnosticoRepuesto.DoesNotExist:
                if config.ver_mensajes:
                    messages.error(request, "Repuesto no encontrado.")
            
            return redirect_with_tab("repuestos")
        
        # 🔹 Quitar acción del diagnóstico
        # 🔹 Editar cantidad de acción
        elif "editar_cantidad_accion" in request.POST:
            dca_id = request.POST.get("dca_id")
            cantidad = request.POST.get("cantidad_accion", 1)
            try:
                from .models import DiagnosticoComponenteAccion
                dca = DiagnosticoComponenteAccion.objects.get(id=dca_id, diagnostico=diagnostico)
                cantidad_int = int(cantidad) if cantidad and int(cantidad) > 0 else 1
                config = AdministracionTaller.get_configuracion_activa()
                dca.cantidad = cantidad_int
                dca.save()
                if config.ver_mensajes:
                    messages.success(request, f"Cantidad de '{dca.accion.nombre}' actualizada a {cantidad_int}.")
            except (DiagnosticoComponenteAccion.DoesNotExist, ValueError):
                if config.ver_mensajes:
                    messages.error(request, "Error al actualizar la cantidad.")
            
            return redirect_with_tab("acciones")
        
        elif "quitar_accion" in request.POST:
            config = AdministracionTaller.get_configuracion_activa()
            accion_id = request.POST.get("quitar_accion")
            try:
                from .models import DiagnosticoComponenteAccion
                accion = DiagnosticoComponenteAccion.objects.get(id=accion_id, diagnostico=diagnostico)
                accion_nombre = f"{accion.componente.nombre} — {accion.accion.nombre}"
                accion.delete()
                if config.ver_mensajes:
                    messages.success(request, f"Acción '{accion_nombre}' quitada del diagnóstico.")
            except DiagnosticoComponenteAccion.DoesNotExist:
                if config.ver_mensajes:
                    messages.error(request, "Acción no encontrada.")
            
            return redirect_with_tab("acciones")
    
    context = {
        "diagnostico": diagnostico,
        "diagnostico_form": diagnostico_form,
        "componentes": componentes,
        "componentes_diagnostico": componentes_diagnostico,
        "acciones_disponibles": acciones_disponibles,
        "repuestos_disponibles": repuestos_disponibles,
        "active_tab": active_tab,
        "config": config,
    }
    return render(request, "car/diagnostico_editar.html", context)

@login_required
def eliminar_diagnostico(request, pk):
    diagnostico = get_object_or_404(Diagnostico, pk=pk)
    # Obtener configuración del taller
    config = AdministracionTaller.get_configuracion_activa()
    
    # Si ver_avisos = False, eliminar directamente sin mostrar confirmación
    if not config.ver_avisos:
        diagnostico.delete()
        if config.ver_mensajes:
            messages.success(request, "Diagnóstico eliminado.")
        return redirect('lista_diagnosticos')
    
    if request.method == 'POST':
        diagnostico.delete()
        if config.ver_mensajes:
            messages.success(request, "Diagnóstico eliminado.")
        return redirect('lista_diagnosticos')
    
    return render(request, 'car/diagnostico_eliminar.html', {'diagnostico': diagnostico, 'config': config})

@login_required
@require_GET
def acciones_por_componente(request, componente_id: int):
    """
    Devuelve las acciones disponibles para un componente dado,
    con el precio base (catálogo) si existe en ComponenteAccion.
    """
    qs = (ComponenteAccion.objects
          .select_related("accion", "componente")
          .filter(componente_id=componente_id)
          .order_by("accion__nombre"))

    data = [
        {
            "id": ca.accion_id,
            "accion_id": ca.accion_id,
            "accion_nombre": ca.accion.nombre,
            "nombre": ca.accion.nombre,
            "precio_base": float(ca.precio_mano_obra) if ca.precio_mano_obra else 0,
        }
        for ca in qs
    ]

    # Si no hay catálogo cargado, devolvemos mensaje específico
    if not data:
        return JsonResponse({
            "ok": False, 
            "mensaje": "Este componente no tiene acciones específicas asociadas. Contacta al administrador para configurar las acciones disponibles para este componente.",
            "acciones": []
        })

    return JsonResponse({"ok": True, "acciones": data})


# ---- EJEMPLO de handler de guardado (adaptar al tuyo actual) ----
# Supone que tu formulario ya crea el Diagnostico y guarda M2M de componentes.
# Solo añadimos la lectura del hidden JSON para poblar DiagnosticoComponenteAccion.

@login_required
def guardar_diagnostico(request):
    if request.method == "POST":
        # ... tu lógica existente para Cliente/Vehiculo/Diagnostico ...
        # Supongamos que al final tienes el objeto diagnostico creado:
        # diagnostico = Diagnostico.objects.create(...)

        acciones_json = request.POST.get("acciones_componentes_json", "").strip()  # hidden input
        if acciones_json:
            try:
                payload = json.loads(acciones_json)
                # Estructura esperada:
                # [
                #   {"componente_id": 1, "accion_id": 3, "precio": "200.00"},
                #   {"componente_id": 2, "accion_id": 1, "precio": ""}  # vacío => autocompleta
                # ]
                with transaction.atomic():
                    for item in payload:
                        comp_id = int(item.get("componente_id"))
                        acc_id = int(item.get("accion_id"))
                        precio = item.get("precio")

                        dca = DiagnosticoComponenteAccion(
                            diagnostico=diagnostico,
                            componente_id=comp_id,
                            accion_id=acc_id,
                        )
                        # Si precio viene vacío o "0", el save() del modelo lo autocompleta desde ComponenteAccion
                        if precio and str(precio).strip() not in ("0", "0.00", ""):
                            dca.precio_mano_obra = precio
                        dca.save()
            except Exception:
                # Puedes loguear el error si quieres
                pass

        # ... redirección o response ...

# ----- ACCION -----

@login_required
def accion_list(request):
    # Obtener configuración del taller
    config = AdministracionTaller.get_configuracion_activa()
    
    q = (request.GET.get("q") or "").strip()
    acciones = Accion.objects.all().order_by("nombre")
    if q:
        acciones = acciones.filter(nombre__icontains=q)
    return render(request, "car/accion_list.html", {"acciones": acciones, "q": q, "config": config})

@login_required
def accion_create(request):
    if request.method == "POST":
        form = AccionForm(request.POST)
        if form.is_valid():
            config = AdministracionTaller.get_configuracion_activa()
            form.save()
            if config.ver_mensajes:
                messages.success(request, "Acción creada correctamente.")
            return redirect("accion_list")
    else:
        form = AccionForm()
    # Obtener configuración del taller
    config = AdministracionTaller.get_configuracion_activa()
    
    return render(request, "car/accion_form.html", {"form": form, "modo": "crear", "config": config})

@login_required
def accion_update(request, pk):
    accion = get_object_or_404(Accion, pk=pk)
    if request.method == "POST":
        form = AccionForm(request.POST, instance=accion)
        if form.is_valid():
            form.save()
            config = AdministracionTaller.get_configuracion_activa()
            if config.ver_mensajes:
                messages.success(request, "Acción actualizada.")
            return redirect("accion_list")
    else:
        form = AccionForm(instance=accion)
    # Obtener configuración del taller
    config = AdministracionTaller.get_configuracion_activa()
    
    return render(request, "car/accion_form.html", {"form": form, "modo": "editar", "accion": accion, "config": config})

@login_required
def accion_delete(request, pk):
    accion = get_object_or_404(Accion, pk=pk)
    # Obtener configuración del taller
    config = AdministracionTaller.get_configuracion_activa()
    
    # Si ver_avisos = False, eliminar directamente sin mostrar confirmación
    if not config.ver_avisos:
        accion.delete()
        if config.ver_mensajes:
            messages.success(request, "Acción eliminada.")
        return redirect("accion_list")
    
    if request.method == "POST":
        accion.delete()
        if config.ver_mensajes:
            messages.success(request, "Acción eliminada.")
        return redirect("accion_list")
    
    return render(request, "car/accion_confirm_delete.html", {"accion": accion, "config": config})


# ----- COMPONENTE + ACCION (precios) -----
@login_required
def comp_accion_list(request):
    q = (request.GET.get("q") or "").strip()
    items = ComponenteAccion.objects.select_related("componente", "accion").order_by("componente__nombre", "accion__nombre")
    if q:
        items = items.filter(
            Q(componente__nombre__icontains=q) | Q(accion__nombre__icontains=q)
        )
    # Obtener configuración del taller
    config = AdministracionTaller.get_configuracion_activa()
    
    return render(request, "car/comp_accion_list.html", {"items": items, "q": q, "config": config})

@login_required
def comp_accion_create(request):
    if request.method == "POST":
        form = ComponenteAccionForm(request.POST)
        config = AdministracionTaller.get_configuracion_activa()
        if form.is_valid():
            form.save()
            if config.ver_mensajes:
                messages.success(request, "Precio de mano de obra registrado.")
            return redirect("comp_accion_list")
    else:
        form = ComponenteAccionForm()
    # Obtener configuración del taller
    config = AdministracionTaller.get_configuracion_activa()
    
    return render(request, "car/comp_accion_form.html", {"form": form, "modo": "crear", "config": config})

@login_required
def comp_accion_update(request, pk):
    obj = get_object_or_404(ComponenteAccion, pk=pk)
    if request.method == "POST":
        form = ComponenteAccionForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            config = AdministracionTaller.get_configuracion_activa()
            if config.ver_mensajes:
                messages.success(request, "Precio de mano de obra actualizado.")
            return redirect("comp_accion_list")
    else:
        form = ComponenteAccionForm(instance=obj)
    # Obtener configuración del taller
    config = AdministracionTaller.get_configuracion_activa()
    
    return render(request, "car/comp_accion_form.html", {"form": form, "modo": "editar", "obj": obj, "config": config})

@login_required
def comp_accion_delete(request, pk):
    obj = get_object_or_404(ComponenteAccion, pk=pk)
    # Obtener configuración del taller
    config = AdministracionTaller.get_configuracion_activa()
    
    # Si ver_avisos = False, eliminar directamente sin mostrar confirmación
    if not config.ver_avisos:
        obj.delete()
        if config.ver_mensajes:
            messages.success(request, "Registro eliminado.")
        return redirect("comp_accion_list")
    
    if request.method == "POST":
        obj.delete()
        if config.ver_mensajes:
            messages.success(request, "Registro eliminado.")
        return redirect("comp_accion_list")
    
    return render(request, "car/comp_accion_confirm_delete.html", {"obj": obj, "config": config})

# funciones adicionales para incluir repuestos


@login_required
def sugerir_repuestos2(request, diagnostico_id=None):
    """
    Vista única:
    - Si viene diagnostico_id: usa los datos guardados en la BD.
    - Si NO viene diagnostico_id: usa los datos enviados por el request (preview).
    """
    print("entrando a buscar repuestos")

    componentes_ids = []
    veh_marca = veh_modelo = None
    veh_anio = None

    if diagnostico_id:  # 🔹 MODO "DIAGNÓSTICO GUARDADO"
        diag = get_object_or_404(Diagnostico, pk=diagnostico_id)
        veh = diag.vehiculo
        veh_marca, veh_modelo, veh_anio = veh.marca, veh.modelo, veh.anio
        componentes_ids = list(diag.componentes.values_list('id', flat=True))

    else:  # 🔹 MODO "PREVIEW" (sin diagnóstico guardado)
        componentes_ids = request.GET.getlist("componentes_ids", [])
        veh_marca = request.GET.get("marca")
        veh_modelo = request.GET.get("modelo")
        veh_anio = request.GET.get("anio")

    # 1) buscar repuestos vinculados directamente a los componentes
    repuestos_comp = Repuesto.objects.filter(
        componenterepuesto__componente_id__in=componentes_ids
    ).distinct()
    print("buscando en punto 1 ",repuestos_comp)

    # 2) compatibilidad con versión del vehículo
    candidates = repuestos_comp
    if veh_marca and veh_modelo and veh_anio:
        # Buscar versión exacta con filtros adicionales si están disponibles
        version_query = VehiculoVersion.objects.filter(
            marca__iexact=veh_marca.strip(),
            modelo__iexact=veh_modelo.strip(),
            anio_desde__lte=veh_anio,
            anio_hasta__gte=veh_anio
        )
        version = version_query.first()
        if version:
            repuestos_by_version = Repuesto.objects.filter(aplicaciones__version=version).distinct()
            candidates = (repuestos_comp | repuestos_by_version).distinct()

    print("resultado del punto 2 ",candidates)        
    # 3) enriquecer con stock y precio
    resultados = []
    for r in candidates.select_related().order_by("nombre")[:60]:
        stock_obj = r.stocks.order_by('-ultima_actualizacion').first()
        resultados.append({
            "id": r.id,
            "sku": r.sku,
            "oem": r.oem,
            "nombre": r.nombre,
            "posicion": r.posicion,
            "precio_venta": float(r.precio_venta or 0),
            "stock": stock_obj.stock if stock_obj else 0,
            "disponible": stock_obj.disponible if stock_obj else 0,
            "repuesto_stock_id": stock_obj.id if stock_obj else None,
        })
    print("resultados del punto 3 ",resultados)
    return JsonResponse({"repuestos": resultados})

@login_required
def sugerir_repuestos(request, diagnostico_id=None):
    """
    Sugerir repuestos en base a:
    1) Componentes seleccionados (ComponenteRepuesto)
    2) Compatibilidad exacta con la versión del vehículo (VehiculoVersion + RepuestoAplicacion)
    3) Filtro inteligente por características del vehículo (marca_veh, tipo_de_motor)
    4) Priorizar filas con stock disponible en RepuestoEnStock
    """
    from django.db.models import Q
    
    componentes_ids = []
    veh_marca = veh_modelo = veh_anio = None
    veh_motor = veh_cilindrada = veh_nro_valvulas = veh_combustible = veh_otro_especial = None

    # MODO "DIAGNÓSTICO GUARDADO"
    if diagnostico_id:
        diag = get_object_or_404(Diagnostico, pk=diagnostico_id)
        veh = diag.vehiculo
        veh_marca, veh_modelo, veh_anio = veh.marca, veh.modelo, veh.anio
        veh_motor = veh.descripcion_motor  # Campo del motor del vehículo
        componentes_ids = list(diag.componentes.values_list('id', flat=True))
        # Obtener datos adicionales del vehículo si están disponibles
        # Nota: Estos campos pueden no estar en el modelo Vehiculo, solo en VehiculoVersion

    # MODO "PREVIEW" (sin guardar)
    else:
        componentes_ids = request.GET.getlist("componentes_ids", [])
        veh_marca = (request.GET.get("marca") or "").strip()
        veh_modelo = (request.GET.get("modelo") or "").strip()
        veh_anio_raw = (request.GET.get("anio") or "").strip()
        veh_motor = (request.GET.get("motor") or "").strip()
        veh_cilindrada = (request.GET.get("cilindrada") or "").strip()
        veh_nro_valvulas = (request.GET.get("nro_valvulas") or "").strip()
        veh_combustible = (request.GET.get("combustible") or "").strip()
        veh_otro_especial = (request.GET.get("otro_especial") or "").strip()
        try:
            veh_anio = int(veh_anio_raw) if veh_anio_raw else None
        except ValueError:
            veh_anio = None

    # 1) Repuestos ligados a los componentes
    repuestos_comp = (
        Repuesto.objects
        .filter(componenterepuesto__componente_id__in=componentes_ids)
        .distinct()
    )

    # 2) Compatibilidad exacta por versión (INTERSECCIÓN)
    candidates = repuestos_comp
    if veh_marca and veh_modelo and veh_anio:
        version = (
            VehiculoVersion.objects
            .filter(
                marca__iexact=veh_marca,
                modelo__iexact=veh_modelo,
                anio_desde__lte=veh_anio,
                anio_hasta__gte=veh_anio
            )
            .first()
        )
        if version:
            candidates = repuestos_comp.filter(aplicaciones__version=version).distinct()

    # 3) FILTRO INTELIGENTE POR CARACTERÍSTICAS DEL VEHÍCULO
    if veh_marca or veh_motor or veh_cilindrada or veh_nro_valvulas or veh_combustible or veh_otro_especial:
        filtro_vehiculo = Q()
        
        # Filtrar por marca del vehículo
        if veh_marca:
            # Buscar repuestos que coincidan con la marca del vehículo
            filtro_vehiculo |= Q(marca_veh__icontains=veh_marca)
            # También buscar por marca general si no hay marca específica
            filtro_vehiculo |= Q(marca_veh__in=['general', 'xxx', ''])
        
        # Filtrar por tipo de motor
        if veh_motor:
            # Buscar repuestos que coincidan con el tipo de motor
            filtro_vehiculo |= Q(tipo_de_motor__icontains=veh_motor)
            # También incluir repuestos generales
            filtro_vehiculo |= Q(tipo_de_motor__in=['zzzzzz', ''])
        
        # Filtrar por cilindrada
        if veh_cilindrada:
            filtro_vehiculo |= Q(cilindrada__icontains=veh_cilindrada)
            filtro_vehiculo |= Q(cilindrada__isnull=True) | Q(cilindrada='')
        
        # Filtrar por número de válvulas
        if veh_nro_valvulas:
            try:
                nro_valvulas_int = int(veh_nro_valvulas)
                filtro_vehiculo |= Q(nro_valvulas=nro_valvulas_int)
                filtro_vehiculo |= Q(nro_valvulas__isnull=True)
            except ValueError:
                pass
        
        # Filtrar por combustible
        if veh_combustible:
            filtro_vehiculo |= Q(combustible__icontains=veh_combustible)
            filtro_vehiculo |= Q(combustible__isnull=True) | Q(combustible='')
        
        # Filtrar por otro especial
        if veh_otro_especial:
            filtro_vehiculo |= Q(otro_especial__icontains=veh_otro_especial)
            filtro_vehiculo |= Q(otro_especial__isnull=True) | Q(otro_especial='')
        
        # Aplicar filtro de vehículo
        candidates = candidates.filter(filtro_vehiculo).distinct()

    # 4) Enriquecer con stock y calcular compatibilidad
    resultados = []
    for r in candidates.select_related().order_by("nombre")[:80]:
        stock_obj = (
            r.stocks.filter(stock__gt=0).order_by('-ultima_actualizacion').first()
            or r.stocks.order_by('-ultima_actualizacion').first()
        )
        
        # Calcular nivel de compatibilidad
        compatibilidad = calcular_compatibilidad_repuesto(r, veh_marca, veh_motor)
        
        resultados.append({
            "id": r.id,
            "sku": r.sku,
            "oem": r.oem,
            "nombre": r.nombre,
            "posicion": r.posicion,
            "marca_veh": r.marca_veh,
            "tipo_motor": r.tipo_de_motor,
            "precio_venta": float(r.precio_venta or 0),
            "stock": stock_obj.stock if stock_obj else 0,
            "disponible": stock_obj.disponible if stock_obj else 0,
            "repuesto_stock_id": stock_obj.id if stock_obj else None,
            "compatibilidad": compatibilidad,
            "compatibilidad_texto": obtener_texto_compatibilidad(compatibilidad),
        })

    # Orden: primero por compatibilidad, luego por stock disponible
    resultados.sort(key=lambda x: (x["compatibilidad"], x["disponible"] > 0, x["stock"]), reverse=True)

    return JsonResponse({"repuestos": resultados})


def calcular_compatibilidad_repuesto(repuesto, veh_marca, veh_motor):
    """
    Calcula el nivel de compatibilidad de un repuesto con el vehículo
    Retorna un score de 0-100
    """
    score = 0
    
    # Compatibilidad por marca del vehículo (40 puntos)
    if veh_marca and repuesto.marca_veh:
        if repuesto.marca_veh.lower() == veh_marca.lower():
            score += 40  # Coincidencia exacta
        elif veh_marca.lower() in repuesto.marca_veh.lower():
            score += 30  # Contiene la marca
        elif repuesto.marca_veh in ['general', 'xxx', '']:
            score += 20  # Repuesto general
    
    # Compatibilidad por tipo de motor (30 puntos)
    if veh_motor and repuesto.tipo_de_motor:
        if repuesto.tipo_de_motor.lower() == veh_motor.lower():
            score += 30  # Coincidencia exacta
        elif veh_motor.lower() in repuesto.tipo_de_motor.lower():
            score += 20  # Contiene el tipo de motor
        elif repuesto.tipo_de_motor in ['zzzzzz', '']:
            score += 15  # Repuesto general
    
    # Bonus por tener stock (20 puntos)
    if repuesto.stock_total > 0:
        score += 20
    
    # Bonus por tener precio (10 puntos)
    if repuesto.precio_venta and repuesto.precio_venta > 0:
        score += 10
    
    return min(score, 100)  # Máximo 100


def obtener_texto_compatibilidad(score):
    """Convierte el score de compatibilidad en texto descriptivo"""
    if score >= 80:
        return "🟢 Excelente compatibilidad"
    elif score >= 60:
        return "🟡 Buena compatibilidad"
    elif score >= 40:
        return "🟠 Compatibilidad media"
    elif score >= 20:
        return "🔴 Baja compatibilidad"
    else:
        return "⚫ Sin compatibilidad verificada"


######################
# 1) repuestos ligados a los componentes seleccionados
#repuestos_comp = (Repuesto.objects
#    .filter(componenterepuesto__componente_id__in=componentes_ids)
#    .distinct())
#
# 2) recortar por versión exacta del vehículo (marca/modelo/año)
#candidates = repuestos_comp
#if veh_marca and veh_modelo and veh_anio:
#    version = (VehiculoVersion.objects
#        .filter(
#            marca__iexact=(veh_marca or "").strip(),
#            modelo__iexact=(veh_modelo or "").strip(),
#            anio_desde__lte=veh_anio,
#            anio_hasta__gte=veh_anio
#        )
#        .first())
#    if version:
#        # Intersección: SOLO compatibles con la versión
#        candidates = repuestos_comp.filter(aplicaciones__version=version).distinct()
#
# 3) enriquecer con stock y precio (prioriza disponibles)
#resultados = []
#for r in candidates.select_related().order_by("nombre")[:80]:
#    stock_obj = (r.stocks
#        .filter(stock__gt=0)         # preferir con stock > 0
#        .order_by('-ultima_actualizacion')
#        .first()
#    ) or r.stocks.order_by('-ultima_actualizacion').first()  # fallback: aunque sea sin stock
#
#    resultados.append({
#        "id": r.id,
#        "sku": r.sku,
#        "oem": r.oem,
#        "nombre": r.nombre,
#        "posicion": r.posicion,
#        "precio_venta": float(r.precio_venta or 0),
#        "stock": stock_obj.stock if stock_obj else 0,
#        "disponible": stock_obj.disponible if stock_obj else 0,
#        "repuesto_stock_id": stock_obj.id if stock_obj else None,
#    })
#return JsonResponse({"repuestos": resultados})
#
#
######################
@login_required
@csrf_exempt
def agregar_repuesto(request, diagnostico_id):
    """
    Agrega un repuesto al diagnóstico y, si hay stock, lo reserva.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    diag = get_object_or_404(Diagnostico, pk=diagnostico_id)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({"error": "JSON inválido"}, status=400)

    repuesto_id = data.get("repuesto_id")
    stock_id = data.get("repuesto_stock_id")
    cantidad = int(data.get("cantidad", 1))

    rep = get_object_or_404(Repuesto, pk=repuesto_id)

    with transaction.atomic():
        repstk = None
        if stock_id:
            repstk = RepuestoEnStock.objects.select_for_update().get(pk=stock_id)
            if repstk.disponible < cantidad:
                return JsonResponse({"error": "Stock insuficiente"}, status=400)
            # Reservar
            repstk.reservado = (repstk.reservado or 0) + cantidad
            repstk.save()
            StockMovimiento.objects.create(
                repuesto_stock=repstk, tipo='reserva', cantidad=cantidad,
                motivo='Reserva desde diagnóstico',
                referencia=f'DIAG-{diag.id}', usuario=request.user if request.user.is_authenticated else None
            )

        dr = DiagnosticoRepuesto.objects.create(
            diagnostico=diag,
            repuesto=rep,
            repuesto_stock=repstk,
            cantidad=cantidad,
            precio_unitario=repstk.precio_venta if repstk and repstk.precio_venta else rep.precio_venta,
            subtotal=(repstk.precio_venta if repstk and repstk.precio_venta else rep.precio_venta or 0) * cantidad,
            reservado=bool(repstk)
        )

    return JsonResponse({"ok": True, "dr_id": dr.id})

@login_required
def listar_repuestos_diagnostico(request, diagnostico_id):
    """
    Devuelve los repuestos ya agregados a un diagnóstico en formato JSON.
    """
    diag = get_object_or_404(Diagnostico, pk=diagnostico_id)
    drs = DiagnosticoRepuesto.objects.filter(diagnostico=diag).select_related("repuesto")

    repuestos = []
    total = 0

    for dr in drs:
        subtotal = (dr.precio_unitario or 0) * dr.cantidad
        total += subtotal
        repuestos.append({
            "id": dr.id,
            "repuesto_id": dr.repuesto.id,
            "nombre": dr.repuesto.nombre,
            "oem": dr.repuesto.oem,
            "cantidad": dr.cantidad,
            "precio_unitario": float(dr.precio_unitario or 0),
            "subtotal": subtotal,
        })

    return JsonResponse({
        "repuestos": repuestos,
        "total": total
    })

@login_required
def exportar_diagnosticos_excel(request):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Diagnósticos"

    # Encabezados
    ws.append([
        "Fecha", "Cliente", "Teléfono", "Vehículo", "Diagnóstico",
        "Acciones", "Total Mano de Obra",
        "Repuestos", "Total Repuestos",
        "Total Presupuesto"
    ])

    for diag in Diagnostico.objects.all():
        acciones = ", ".join([f"{dca.componente.nombre} - {dca.accion.nombre}" for dca in diag.acciones_componentes.all()])
        repuestos = ", ".join([f"{dr.repuesto.nombre} (x{dr.cantidad})" for dr in diag.repuestos.all()])
        total_mo = diag.total_mano_obra or 0
        total_repuestos = sum([dr.subtotal for dr in diag.repuestos.all()])
        total = total_mo + total_repuestos

        ws.append([
            diag.fecha.strftime("%d-%m-%Y"),
            diag.vehiculo.cliente.nombre,
            diag.vehiculo.cliente.telefono,
            str(diag.vehiculo),
            diag.descripcion_problema,
            acciones,
            total_mo,
            repuestos,
            total_repuestos,
            total
        ])

    # Preparar respuesta HTTP
    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = 'attachment; filename="diagnosticos.xlsx"'
    wb.save(response)
    return response


@login_required
def exportar_diagnostico_excel(request, pk):
    diag = get_object_or_404(Diagnostico, pk=pk)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"Diagnóstico {diag.pk}"

    ws.append(["Fecha", diag.fecha.strftime("%d-%m-%Y")])
    ws.append(["Cliente", diag.vehiculo.cliente.nombre])
    ws.append(["Teléfono", diag.vehiculo.cliente.telefono])
    ws.append(["Vehículo", str(diag.vehiculo)])
    ws.append(["Descripción", diag.descripcion_problema])
    ws.append([])

    # Acciones
    ws.append(["Acciones realizadas", "Precio"])
    total_mo = 0
    for dca in diag.acciones_componentes.all():
        ws.append([f"{dca.componente.nombre} — {dca.accion.nombre}", dca.precio_mano_obra or 0])
        total_mo += dca.precio_mano_obra or 0
    ws.append(["Total Mano de Obra", total_mo])
    ws.append([])

    # Repuestos
    ws.append(["Repuestos", "Cantidad", "Precio Unitario", "Subtotal"])
    total_rep = 0
    for dr in diag.repuestos.all():
        subtotal = dr.subtotal or (dr.cantidad * (dr.precio_unitario or 0))
        ws.append([dr.repuesto.nombre, dr.cantidad, dr.precio_unitario, subtotal])
        total_rep += subtotal
    ws.append(["Total Repuestos", "", "", total_rep])
    ws.append([])

    ws.append(["TOTAL PRESUPUESTO", total_mo + total_rep])

    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = f'attachment; filename="diagnostico_{diag.pk}.xlsx"'
    wb.save(response)
    return response

@login_required
def exportar_diagnosticos_pdf(request):
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="diagnosticos.pdf"'

    doc = SimpleDocTemplate(response, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("<b>Reporte de Diagnósticos</b>", styles["Title"]))
    elements.append(Spacer(1, 12))

    data = [["Fecha", "Cliente", "Vehículo","VIN", "Diagnóstico", "Total Presupuesto"]]

    for diag in Diagnostico.objects.all():
        total_mo = diag.total_mano_obra or 0
        total_repuestos = sum([dr.subtotal for dr in diag.repuestos.all()])
        total = total_mo + total_repuestos

        data.append([
            diag.fecha.strftime("%d-%m-%Y"),
            diag.vehiculo.cliente.nombre,
            str(diag.vehiculo),
            diag.vehiculo.vin,
            diag.descripcion_problema,
            f"${total:,}"
        ])

    table = Table(data, colWidths=[80, 100, 120, 150, 80])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.grey),
        ("TEXTCOLOR", (0,0), (-1,0), colors.whitesmoke),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0,0), (-1,0), 8),
        ("GRID", (0,0), (-1,-1), 0.5, colors.black),
    ]))

    elements.append(table)
    doc.build(elements)
    return response



@login_required
def exportar_diagnostico_pdf(request, pk):
    """Generar PDF del diagnóstico con la misma calidad que el PDF de trabajos"""
    import logging
    logger = logging.getLogger(__name__)
    
    from django.http import HttpResponse
    from django.template.loader import get_template
    from django.conf import settings
    import os
    
    logger.info(f"🔍 INICIANDO GENERACIÓN PDF - Diagnóstico ID: {pk}")
    
    diagnostico = get_object_or_404(Diagnostico, pk=pk)
    logger.info(f"✅ Diagnóstico encontrado: {diagnostico.vehiculo} - Estado: {diagnostico.estado}")
    
    # Crear el PDF usando weasyprint
    try:
        from weasyprint import HTML, CSS
        from weasyprint.text.fonts import FontConfiguration
        logger.info("✅ WeasyPrint importado correctamente")
        
        # Template para el PDF
        template = get_template('car/diagnostico_pdf.html')
        logger.info("✅ Template cargado correctamente")
        
        # Preparar contexto con URLs absolutas para las imágenes
        context = {
            'diagnostico': diagnostico,
            'request': request,  # Para generar URLs absolutas
            'now': timezone.now(),
        }
        
        # Log de datos del diagnóstico
        logger.info(f"📋 Componentes: {diagnostico.componentes.count()}")
        logger.info(f"🛠️ Acciones: {diagnostico.acciones_componentes.count()}")
        logger.info(f"⚙️ Repuestos: {diagnostico.repuestos.count()}")
        
        html_content = template.render(context)
        logger.info(f"✅ HTML renderizado - Tamaño: {len(html_content)} caracteres")
        
        # Configuración de fuentes
        font_config = FontConfiguration()
        logger.info("✅ Configuración de fuentes creada")
        
        # Crear el PDF
        logger.info("🔄 Creando documento HTML para WeasyPrint...")
        html_doc = HTML(string=html_content)
        logger.info("✅ Documento HTML creado")
        
        css = CSS(string='''
            @page {
                size: A4;
                margin: 1cm;
            }
            body {
                font-family: Arial, sans-serif;
                font-size: 12px;
            }
            .header {
                text-align: center;
                border-bottom: 2px solid #333;
                padding-bottom: 10px;
                margin-bottom: 20px;
            }
            .section {
                margin-bottom: 15px;
            }
            .section h3 {
                background: #f0f0f0;
                padding: 5px;
                margin: 0 0 10px 0;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 10px;
            }
            th, td {
                border: 1px solid #ddd;
                padding: 5px;
                text-align: left;
            }
            th {
                background: #f0f0f0;
            }
            img {
                max-width: 100%;
                height: auto;
            }
        ''', font_config=font_config)
        logger.info("✅ CSS aplicado")
        
        logger.info("🔄 Generando PDF con WeasyPrint...")
        
        # Crear response PRIMERO (como en exportar_acciones_pdf que funciona)
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="diagnostico_{diagnostico.id}.pdf"'
        
        # Generar el PDF directamente en el response
        pdf_file = html_doc.write_pdf(stylesheets=[css], font_config=font_config)
        logger.info(f"✅ PDF generado exitosamente - Tamaño: {len(pdf_file)} bytes")
        
        # Escribir el PDF al response (como en exportar_acciones_pdf)
        response.write(pdf_file)
        
        logger.info("✅ Respuesta HTTP creada con Content-Disposition: inline (método inline-first)")
        return response
        
    except ImportError as e:
        logger.error(f"❌ ERROR: WeasyPrint no está disponible: {str(e)}")
        # Si weasyprint no está disponible, usar una alternativa simple
        from django.http import HttpResponse
        content = f"Error: WeasyPrint no está instalado o configurado correctamente para generar PDFs. Por favor, instálalo: pip install WeasyPrint. Error: {str(e)}"
        response = HttpResponse(content, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename="diagnostico_{diagnostico.id}_estado.txt"'
        return response
        
    except Exception as e:
        logger.error(f"❌ ERROR GENERAL generando PDF: {str(e)}")
        logger.error(f"❌ Tipo de error: {type(e).__name__}")
        import traceback
        logger.error(f"❌ Traceback completo: {traceback.format_exc()}")
        
        # Respuesta de error
        from django.http import HttpResponse
        response = HttpResponse(content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename="error_diagnostico_{diagnostico.id}.txt"'
        response.write(f"Error generando PDF: {str(e)}")
        return response


# ---- CLIENTES ----
class ClienteListView(ListView):
    """Redirige a la nueva vista de Cliente_Taller"""
    def get(self, request, *args, **kwargs):
        return redirect('cliente_taller_list')

class ClienteCreateView(CreateView):
    """Redirige a la nueva vista de Cliente_Taller"""
    def get(self, request, *args, **kwargs):
        return redirect('cliente_taller_create')

class ClienteUpdateView(UpdateView):
    """Redirige a la nueva vista de Cliente_Taller"""
    def get(self, request, *args, **kwargs):
        return redirect('cliente_taller_list')

class ClienteDeleteView(DeleteView):
    """Redirige a la nueva vista de Cliente_Taller"""
    def get(self, request, *args, **kwargs):
        return redirect('cliente_taller_list')

# ---- VEHICULOS ----
class VehiculoListView(ListView):
    model = Vehiculo
    template_name = "car/vehiculo_list.html"
    context_object_name = "vehiculos"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Obtener configuración del taller
        config = AdministracionTaller.get_configuracion_activa()
        context['config'] = config
        return context

class VehiculoCreateView(CreateView):
    model = Vehiculo
    fields = ["cliente", "placa", "marca", "modelo", "anio", "vin", "descripcion_motor"]
    template_name = "car/vehiculo_form.html"
    success_url = reverse_lazy("vehiculo_list")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Obtener configuración del taller
        config = AdministracionTaller.get_configuracion_activa()
        context['config'] = config
        return context

class VehiculoUpdateView(UpdateView):
    model = Vehiculo
    fields = ["cliente", "placa", "marca", "modelo", "anio", "vin", "descripcion_motor"]
    template_name = "car/vehiculo_form.html"
    success_url = reverse_lazy("vehiculo_list")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Obtener configuración del taller
        config = AdministracionTaller.get_configuracion_activa()
        context['config'] = config
        return context

class VehiculoDeleteView(DeleteView):
    model = Vehiculo
    template_name = "car/vehiculo_confirm_delete.html"
    success_url = reverse_lazy("vehiculo_list")

    def get(self, request, *args, **kwargs):
        """Si ver_avisos = False, eliminar directamente sin mostrar confirmación"""
        config = AdministracionTaller.get_configuracion_activa()
        if not config.ver_avisos:
            self.object = self.get_object()
            self.object.delete()
            if config.ver_mensajes:
                messages.success(request, "Vehículo eliminado exitosamente.")
            return redirect(self.success_url)
        return super().get(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        """Sobrescribir delete para controlar mensajes"""
        config = AdministracionTaller.get_configuracion_activa()
        self.object = self.get_object()
        self.object.delete()
        if config.ver_mensajes:
            messages.success(request, "Vehículo eliminado exitosamente.")
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Obtener configuración del taller
        config = AdministracionTaller.get_configuracion_activa()
        context['config'] = config
        return context

# ---- MecanicoS ----
class MecanicoListView(ListView):
    model = Mecanico
    template_name = "car/mecanico_list.html"
    context_object_name = "mecanicos"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Obtener configuración del taller
        config = AdministracionTaller.get_configuracion_activa()
        context['config'] = config
        return context

class MecanicoCreateView(CreateView):
    model = Mecanico
    fields = ["user", "especialidad","activo"]
    template_name = "car/mecanico_form.html"
    success_url = reverse_lazy("mecanico_list")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Obtener configuración del taller
        config = AdministracionTaller.get_configuracion_activa()
        context['config'] = config
        return context

class MecanicoUpdateView(UpdateView):
    model = Mecanico
    fields = ["user", "especialidad","activo"]
    template_name = "car/mecanico_form.html"
    success_url = reverse_lazy("mecanico_list")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Obtener configuración del taller
        config = AdministracionTaller.get_configuracion_activa()
        context['config'] = config
        return context

class MecanicoDeleteView(DeleteView):
    model = Mecanico
    template_name = "car/mecanico_confirm_delete.html"
    success_url = reverse_lazy("mecanico_list")

    def get(self, request, *args, **kwargs):
        """Si ver_avisos = False, eliminar directamente sin mostrar confirmación"""
        config = AdministracionTaller.get_configuracion_activa()
        if not config.ver_avisos:
            self.object = self.get_object()
            self.object.delete()
            if config.ver_mensajes:
                messages.success(request, "Mecánico eliminado exitosamente.")
            return redirect(self.success_url)
        return super().get(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        """Sobrescribir delete para controlar mensajes"""
        config = AdministracionTaller.get_configuracion_activa()
        self.object = self.get_object()
        self.object.delete()
        if config.ver_mensajes:
            messages.success(request, "Mecánico eliminado exitosamente.")
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Obtener configuración del taller
        config = AdministracionTaller.get_configuracion_activa()
        context['config'] = config
        return context

# ---- TRABAJOS ----
class TrabajoDeleteView(DeleteView):
    model = Trabajo
    template_name = "car/trabajo_confirm_delete.html"
    success_url = reverse_lazy("lista_trabajos")

    def get(self, request, *args, **kwargs):
        """Si ver_avisos = False, eliminar directamente sin mostrar confirmación"""
        config = AdministracionTaller.get_configuracion_activa()
        if not config.ver_avisos:
            self.object = self.get_object()
            self.object.delete()
            if config.ver_mensajes:
                messages.success(request, "Trabajo eliminado exitosamente.")
            return redirect(self.success_url)
        return super().get(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        """Sobrescribir delete para controlar mensajes"""
        config = AdministracionTaller.get_configuracion_activa()
        self.object = self.get_object()
        self.object.delete()
        if config.ver_mensajes:
            messages.success(request, "Trabajo eliminado exitosamente.")
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Obtener configuración del taller
        config = AdministracionTaller.get_configuracion_activa()
        context['config'] = config
        return context

@login_required
@requiere_permiso('diagnosticos')
@transaction.atomic
def guardar_aprobar_y_crear_ot(request):
    """
    Guarda el diagnóstico, lo aprueba y crea la Orden de Trabajo en una sola acción.
    Esta función combina la lógica de ingreso_view y aprobar_diagnostico.
    """
    # Obtener configuración del taller
    config = AdministracionTaller.get_configuracion_activa()
    
    clientes_existentes = Cliente_Taller.objects.filter(activo=True).order_by('nombre')
    
    selected_cliente = None
    selected_vehiculo = None
    selected_componentes_ids = []
    
    if request.method == 'POST':
        cliente_form = ClienteTallerForm(request.POST, prefix='cliente')
        vehiculo_form = VehiculoForm(request.POST, prefix='vehiculo')
        diagnostico_form = DiagnosticoForm(request.POST, prefix='diag')
        
        cliente_id = request.POST.get('cliente_existente')
        vehiculo_id = request.POST.get('vehiculo_existente')
        selected_componentes_ids = request.POST.getlist('componentes_seleccionados')
        
        # --- Cliente ---
        cliente = None
        if cliente_id:
            cliente_id_normalizado = normalizar_rut(cliente_id)
            try:
                cliente = Cliente_Taller.objects.get(rut=cliente_id_normalizado)
                selected_cliente = cliente.rut
            except Cliente_Taller.DoesNotExist:
                if cliente_id_normalizado and cliente_id_normalizado[-1].lower() == 'k':
                    try:
                        rut_con_k_mayuscula = cliente_id_normalizado[:-1] + 'K'
                        cliente = Cliente_Taller.objects.get(rut=rut_con_k_mayuscula)
                        selected_cliente = cliente.rut
                    except Cliente_Taller.DoesNotExist:
                        cliente_form.add_error(None, "El cliente seleccionado no existe.")
                else:
                    cliente_form.add_error(None, "El cliente seleccionado no existe.")
        else:
            if cliente_form.is_valid():
                cliente = cliente_form.save(commit=False)
                cliente.activo = True
                cliente.save()
                selected_cliente = cliente.rut
        
        # --- Vehículo ---
        vehiculo = None
        if vehiculo_id:
            try:
                vehiculo = Vehiculo.objects.get(pk=vehiculo_id, cliente=cliente)
                selected_vehiculo = vehiculo.pk
            except Vehiculo.DoesNotExist:
                vehiculo_form.add_error(None, "El vehículo seleccionado no existe o no pertenece al cliente.")
        else:
            if vehiculo_form.is_valid() and cliente:
                vehiculo = vehiculo_form.save(commit=False)
                vehiculo.cliente = cliente
                vehiculo.save()
                selected_vehiculo = vehiculo.pk
        
        # --- Diagnóstico ---
        if diagnostico_form.is_valid() and vehiculo:
            diagnostico = diagnostico_form.save(commit=False)
            diagnostico.vehiculo = vehiculo
            diagnostico.save()
            
            # Registrar evento de diagnóstico creado
            registrar_diagnostico_creado(diagnostico, request=request)
            
            # 🔹 Relación M2M con componentes
            diagnostico.componentes.set(selected_componentes_ids)
            
            # ====================================================
            # 🔹 Acciones por componente desde hidden JSON
            acciones_json = (request.POST.get("acciones_componentes_json") or "").strip()
            if acciones_json:
                try:
                    items = json.loads(acciones_json)
                    for it in items:
                        try:
                            comp_id = int(it.get("componente_id"))
                            acc_id = int(it.get("accion_id"))
                        except (TypeError, ValueError):
                            continue
                        
                        precio_mano_obra = (it.get("precio_mano_obra") or "").strip()
                        cantidad = int(it.get("cantidad", 1)) if it.get("cantidad") else 1
                        
                        if not diagnostico.componentes.filter(id=comp_id).exists():
                            continue
                        
                        dca = DiagnosticoComponenteAccion(
                            diagnostico=diagnostico,
                            componente_id=comp_id,
                            accion_id=acc_id,
                            cantidad=cantidad
                        )
                        if precio_mano_obra and precio_mano_obra not in ("0", "0.00"):
                            dca.precio_mano_obra = precio_mano_obra
                        dca.save()
                except json.JSONDecodeError:
                    pass
            
            # ====================================================
            # 🔹 Repuestos seleccionados desde hidden JSON
            # ====================================================
            repuestos_json = (request.POST.get("repuestos_json") or "").strip()
            if repuestos_json:
                try:
                    repuestos_data = json.loads(repuestos_json)
                    for r in repuestos_data:
                        try:
                            repuesto_id = int(r.get("id"))
                            repuesto = Repuesto.objects.get(pk=repuesto_id)
                            
                            stock_id_raw = r.get("repuesto_stock_id")
                            repuesto_stock = None
                            if stock_id_raw:
                                try:
                                    repuesto_stock = RepuestoEnStock.objects.get(pk=int(stock_id_raw))
                                except (ValueError, RepuestoEnStock.DoesNotExist):
                                    repuesto_stock = None
                            
                            cantidad = int(r.get("cantidad", 1))
                            precio = float(r.get("precio_unitario", repuesto.precio_venta or 0))
                            
                            DiagnosticoRepuesto.objects.create(
                                diagnostico=diagnostico,
                                repuesto=repuesto,
                                repuesto_stock=repuesto_stock,
                                cantidad=cantidad,
                                precio_unitario=precio,
                                subtotal=cantidad * precio
                            )
                        except (ValueError, Repuesto.DoesNotExist, KeyError):
                            continue
                except json.JSONDecodeError:
                    pass
            
            # ====================================================
            # 🌐 Repuestos Externos (Referencias)
            # ====================================================
            repuestos_externos_json = (request.POST.get("repuestos_externos_json") or "").strip()
            if repuestos_externos_json:
                try:
                    from .models import RepuestoExterno
                    repuestos_externos_data = json.loads(repuestos_externos_json)
                    for r_ext in repuestos_externos_data:
                        try:
                            repuesto_ext_id = int(r_ext.get("id"))
                            repuesto_externo = RepuestoExterno.objects.get(pk=repuesto_ext_id)
                            
                            cantidad = int(r_ext.get("cantidad", 1))
                            precio = float(r_ext.get("precio", repuesto_externo.precio_referencial))
                            
                            DiagnosticoRepuesto.objects.create(
                                diagnostico=diagnostico,
                                repuesto=None,
                                repuesto_externo=repuesto_externo,
                                repuesto_stock=None,
                                cantidad=cantidad,
                                precio_unitario=precio,
                                subtotal=cantidad * precio
                            )
                            
                            repuesto_externo.incrementar_uso()
                        except (ValueError, RepuestoExterno.DoesNotExist, KeyError):
                            continue
                except json.JSONDecodeError:
                    pass
            
            # ====================================================
            # 🚀 APROBAR Y CREAR TRABAJO
            # ====================================================
            if diagnostico.estado != "aprobado":
                trabajo = diagnostico.aprobar_y_clonar()
                
                # Registrar evento de diagnóstico aprobado
                registrar_diagnostico_aprobado(diagnostico, trabajo, request=request)
                
                # Registrar evento de ingreso
                registrar_ingreso(trabajo, request=request)
                
                if config.ver_mensajes:
                    messages.success(request, f"✅ Diagnóstico guardado, aprobado y trabajo #{trabajo.id} creado.")
                
                # Redirigir al editor del trabajo
                return redirect('trabajo_detalle', pk=trabajo.pk)
            else:
                if config.ver_mensajes:
                    messages.info(request, "ℹ️ Este diagnóstico ya estaba aprobado.")
                # Si ya estaba aprobado, buscar el trabajo asociado
                try:
                    trabajo = Trabajo.objects.get(diagnostico=diagnostico)
                    return redirect('trabajo_detalle', pk=trabajo.pk)
                except Trabajo.DoesNotExist:
                    return redirect('panel_principal')
    
    # Si hay errores o es GET, renderizar el formulario nuevamente
    else:
        if request.method == 'GET':
            cliente_form = ClienteTallerForm(prefix='cliente')
            vehiculo_form = VehiculoForm(prefix='vehiculo')
            diagnostico_form = DiagnosticoForm(prefix='diag')
        # Si es POST pero hay errores, los formularios ya tienen los errores
    
    return render(request, 'car/ingreso_fusionado.html', {
        'cliente_form': cliente_form,
        'vehiculo_form': vehiculo_form,
        'diagnostico_form': diagnostico_form,
        'clientes_existentes': clientes_existentes,
        'selected_cliente': selected_cliente,
        'selected_vehiculo': selected_vehiculo,
        'selected_componentes_ids': selected_componentes_ids,
    })


@login_required
def aprobar_diagnostico(request, pk):
    diagnostico = get_object_or_404(Diagnostico, pk=pk)

    if diagnostico.estado != "aprobado":
        trabajo = diagnostico.aprobar_y_clonar()
        
        # Registrar evento de diagnóstico aprobado (con días de diferencia)
        registrar_diagnostico_aprobado(diagnostico, trabajo, request=request)
        
        # Registrar evento de ingreso
        registrar_ingreso(trabajo, request=request)
        config = AdministracionTaller.get_configuracion_activa()
        if config.ver_mensajes:
            messages.success(request, f"✅ Diagnóstico aprobado y trabajo #{trabajo.id} creado.")
    else:
        config = AdministracionTaller.get_configuracion_activa()
        if config.ver_mensajes:
            messages.info(request, "ℹ️ Este diagnóstico ya estaba aprobado.")

    return redirect("lista_diagnosticos")

@login_required
def lista_trabajos2(request):
    trabajos = Trabajo.objects.all().select_related(
        'vehiculo__cliente'
    ).prefetch_related(
        'acciones_componentes__accion',
        'acciones_componentes__componente',
        'repuestos'
    ).order_by('-fecha_inicio')

    # Calcular totales igual que en diagnósticos
    for t in trabajos:
        t.total_mano_obra = sum(tca.precio_mano_obra or 0 for tca in t.acciones_componentes.all())
        t.total_repuestos = sum(tr.subtotal or (tr.cantidad * (tr.precio_unitario or 0)) for tr in t.repuestos.all())
        t.total_presupuesto = t.total_mano_obra + t.total_repuestos

    return render(request, 'car/trabajo_lista.html', {
        'trabajos': trabajos
    })


@login_required
@requiere_permiso('trabajos')
def lista_trabajos(request):
    # Obtener configuración del taller
    config = AdministracionTaller.get_configuracion_activa()
    
    # Filtrar solo trabajos visibles
    trabajos = Trabajo.objects.filter(visible=True).select_related(
        'vehiculo__cliente'
    ).prefetch_related(
        'acciones__accion',
        'acciones__componente',
        'repuestos__repuesto'
    ).order_by('-fecha_inicio')

    # Los totales se calculan automáticamente mediante las @property del modelo
    # No necesitamos asignarlos manualmente

    return render(request, 'car/trabajo_lista.html', {
        'trabajos': trabajos,
        'config': config
    })


@login_required
@requiere_permiso('trabajos')
def historial_trabajos(request):
    """Lista de trabajos no visibles (historial)"""
    # Obtener configuración del taller
    config = AdministracionTaller.get_configuracion_activa()
    
    # Filtrar solo trabajos no visibles
    trabajos = Trabajo.objects.filter(visible=False).select_related(
        'vehiculo__cliente'
    ).prefetch_related(
        'acciones__accion',
        'acciones__componente',
        'repuestos__repuesto',
        'mecanicos__user'
    ).order_by('-fecha_inicio')
    
    # Búsqueda AJAX
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        busqueda = request.GET.get('q', '').strip()
        if busqueda:
            # Buscar por ID, cliente, placa, RUT, mecánico, estado
            trabajos = trabajos.filter(
                Q(id__icontains=busqueda) |
                Q(vehiculo__cliente__nombre__icontains=busqueda) |
                Q(vehiculo__cliente__rut__icontains=busqueda) |
                Q(vehiculo__placa__icontains=busqueda) |
                Q(vehiculo__marca__icontains=busqueda) |
                Q(vehiculo__modelo__icontains=busqueda) |
                Q(mecanicos__user__first_name__icontains=busqueda) |
                Q(mecanicos__user__last_name__icontains=busqueda) |
                Q(mecanicos__user__username__icontains=busqueda) |
                Q(estado__icontains=busqueda) |
                Q(observaciones__icontains=busqueda)
            ).distinct()
        
        # Convertir a JSON
        trabajos_data = []
        for trabajo in trabajos:
            mecanicos_nombres = [f"{mec.user.get_full_name() or mec.user.username}" for mec in trabajo.mecanicos.all()]
            trabajos_data.append({
                'id': trabajo.id,
                'vehiculo': str(trabajo.vehiculo),
                'cliente_nombre': trabajo.vehiculo.cliente.nombre,
                'cliente_rut': trabajo.vehiculo.cliente.rut,
                'placa': trabajo.vehiculo.placa or '',
                'fecha_inicio': trabajo.fecha_inicio.strftime('%d/%m/%Y %H:%M') if trabajo.fecha_inicio else '',
                'estado': trabajo.estado,
                'estado_display': trabajo.get_estado_display(),
                'total_general': float(trabajo.total_general or 0),
                'total_abonos': float(trabajo.total_abonos or 0),
                'saldo_pendiente': float(trabajo.saldo_pendiente or 0),
                'mecanicos': mecanicos_nombres,
                'url_detalle': f'/car/trabajos/{trabajo.id}/',
            })
        
        return JsonResponse({
            'trabajos': trabajos_data,
            'total': len(trabajos_data)
        })

    return render(request, 'car/trabajo_historial.html', {
        'trabajos': trabajos,
        'config': config
    })




@login_required
@requiere_permiso('trabajos')
def trabajo_detalle(request, pk):
    trabajo = get_object_or_404(Trabajo, pk=pk)
    
    # 🔹 Helper para redirects con pestaña activa
    def redirect_with_tab(tab_name):
        from django.http import HttpResponseRedirect
        return HttpResponseRedirect(f"/car/trabajos/{trabajo.pk}/?tab={tab_name}")

    # Formularios
    asignar_form = AsignarMecanicosForm(instance=trabajo)
    foto_form = SubirFotoForm()

    # Obtener datos para los formularios de agregar
    from .models import Componente, Accion, Repuesto
    from django.db.models import Q
    acciones_disponibles = Accion.objects.all()
    
    # 🔹 COMPONENTES DISPONIBLES (igual que en ingreso.html - solo componentes padre)
    # Los componentes no tienen compatibilidad específica por vehículo, son genéricos
    componentes = Componente.objects.filter(padre__isnull=True, activo=True)
    
    # 🔹 FILTRO INTELIGENTE DE REPUESTOS basado en el vehículo del trabajo
    repuestos_disponibles = Repuesto.objects.all()
    if trabajo.vehiculo:
        veh = trabajo.vehiculo
        veh_marca = veh.marca
        veh_motor = veh.descripcion_motor
        
        # Aplicar filtro inteligente por características del vehículo
        if veh_marca or veh_motor:
            filtro_vehiculo = Q()
            
            # Filtrar por marca del vehículo
            if veh_marca:
                filtro_vehiculo |= Q(marca_veh__icontains=veh_marca)
                filtro_vehiculo |= Q(marca_veh__in=['general', 'xxx', ''])
            
            # Filtrar por tipo de motor
            if veh_motor:
                filtro_vehiculo |= Q(tipo_de_motor__icontains=veh_motor)
                filtro_vehiculo |= Q(tipo_de_motor__in=['zzzzzz', ''])
            
            # Aplicar filtro y ordenar por compatibilidad
            repuestos_disponibles = repuestos_disponibles.filter(filtro_vehiculo).distinct()
            
            # Ordenar por stock disponible y precio
            repuestos_disponibles = repuestos_disponibles.order_by('-stock', 'precio_venta', 'nombre')

    if request.method == "POST":
        # 🔹 Guardar observaciones
        if "guardar_observaciones" in request.POST:
            trabajo.observaciones = request.POST.get("observaciones", "")
            trabajo.save()
            config = AdministracionTaller.get_configuracion_activa()
            if config.ver_mensajes:
                messages.success(request, "Observaciones guardadas.")
            # Mantener la pestaña activa después de guardar
            return redirect_with_tab("info")

        # 🔹 Guardar kilometraje
        elif "guardar_kilometraje" in request.POST:
            kilometraje = request.POST.get("lectura_kilometraje_actual", "")
            if kilometraje and kilometraje.strip():
                try:
                    config = AdministracionTaller.get_configuracion_activa()
                    trabajo.lectura_kilometraje_actual = int(kilometraje)
                    trabajo.save()
                    if config.ver_mensajes:
                        messages.success(request, f"Kilometraje guardado: {kilometraje} km")
                except ValueError:
                    messages.error(request, "El kilometraje debe ser un número válido.")
            else:
                trabajo.lectura_kilometraje_actual = None
                trabajo.save()
                config = AdministracionTaller.get_configuracion_activa()
                if config.ver_mensajes:
                    messages.success(request, "Kilometraje eliminado.")
            return redirect("trabajo_detalle", pk=trabajo.pk)

        # 🔹 Asignar mecánicos
        elif "asignar_mecanicos" in request.POST:
            asignar_form = AsignarMecanicosForm(request.POST, instance=trabajo)
            if asignar_form.is_valid():
                # Obtener mecánicos anteriores
                mecanicos_anteriores = set(trabajo.mecanicos.all())
                
                trabajo = asignar_form.save(commit=False)
                if trabajo.estado == "iniciado":
                    estado_anterior = trabajo.estado
                    trabajo.estado = "trabajando"
                    trabajo.fecha_inicio = timezone.now()
                    # Registrar cambio de estado si cambió
                    registrar_cambio_estado(trabajo, estado_anterior, "trabajando", request=request)
                trabajo.save()
                asignar_form.save_m2m()
                
                # Obtener mecánicos nuevos
                mecanicos_nuevos = set(trabajo.mecanicos.all())
                
                # Registrar mecánicos agregados
                mecanicos_agregados = mecanicos_nuevos - mecanicos_anteriores
                for mecanico in mecanicos_agregados:
                    registrar_mecanico_asignado(trabajo, mecanico, request=request)
                
                # Registrar mecánicos removidos
                mecanicos_removidos = mecanicos_anteriores - mecanicos_nuevos
                for mecanico in mecanicos_removidos:
                    registrar_mecanico_removido(trabajo, mecanico, request=request)
                
                config = AdministracionTaller.get_configuracion_activa()
                if config.ver_mensajes:
                    messages.success(request, "Mecánicos asignados y trabajo iniciado.")
                return redirect("trabajo_detalle", pk=trabajo.pk)

        # 🔹 Agregar acción (método tradicional)
        elif "agregar_accion" in request.POST:
            componente_id = request.POST.get("componente")
            accion_id = request.POST.get("accion")
            precio_mano_obra = request.POST.get("precio_mano_obra", 0)
            cantidad = request.POST.get("cantidad", 1)
            
            if componente_id and accion_id:
                try:
                    componente = Componente.objects.get(id=componente_id)
                    accion = Accion.objects.get(id=accion_id)
                    
                    TrabajoAccion.objects.create(
                        trabajo=trabajo,
                        componente=componente,
                        accion=accion,
                        precio_mano_obra=precio_mano_obra or 0,
                        cantidad=int(cantidad) if cantidad else 1
                    )
                    config = AdministracionTaller.get_configuracion_activa()
                    if config.ver_mensajes:
                        messages.success(request, "Acción agregada al trabajo.")
                except (Componente.DoesNotExist, Accion.DoesNotExist):
                    if config.ver_mensajes:
                        messages.error(request, "Error al agregar la acción.")
            return redirect_with_tab("acciones")

        # 🔹 Agregar múltiples acciones (nuevo método)
        elif "agregar_acciones_multiples" in request.POST:
            import json
            is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
            acciones_json = request.POST.get("acciones_json", "")
            
            print(f"DEBUG: acciones_json recibido: {acciones_json}")
            
            if acciones_json:
                try:
                    acciones_data = json.loads(acciones_json)
                    print(f"DEBUG: acciones_data parseado: {acciones_data}")
                    acciones_creadas = 0
                    detalles = []
                    
                    for accion_data in acciones_data:
                        try:
                            componente_id = int(accion_data.get("componente_id"))
                            accion_id = int(accion_data.get("accion_id"))
                            precio_recibido = accion_data.get("precio", 0)
                            cantidad = int(accion_data.get("cantidad", 1))
                            
                            # Convertir a Decimal de forma segura
                            try:
                                precio_mano_obra = Decimal(str(precio_recibido))
                            except:
                                precio_mano_obra = Decimal('0')
                            
                            print(f"DEBUG: Procesando - componente_id: {componente_id}, accion_id: {accion_id}, precio_recibido: {precio_recibido}, precio_decimal: {precio_mano_obra}, cantidad: {cantidad}")
                            
                            componente = Componente.objects.get(id=componente_id)
                            accion = Accion.objects.get(id=accion_id)
                            
                            # 🔹 Si el precio es 0, intentar obtenerlo de ComponenteAccion
                            if precio_mano_obra == 0:
                                try:
                                    comp_accion = ComponenteAccion.objects.filter(
                                        componente=componente,
                                        accion=accion
                                    ).first()
                                    if comp_accion and comp_accion.precio_mano_obra:
                                        precio_mano_obra = comp_accion.precio_mano_obra
                                        print(f"DEBUG: ✅ Precio obtenido de ComponenteAccion: {precio_mano_obra}")
                                except ComponenteAccion.DoesNotExist:
                                    print(f"DEBUG: ⚠️ No se encontró ComponenteAccion para obtener precio")
                            
                            TrabajoAccion.objects.create(
                                trabajo=trabajo,
                                componente=componente,
                                accion=accion,
                                precio_mano_obra=precio_mano_obra,
                                cantidad=cantidad
                            )
                            acciones_creadas += 1
                            detalles.append(f"{componente.nombre} → {accion.nombre} (x{cantidad})")
                            print(f"DEBUG: ✅ Acción creada exitosamente con precio: {precio_mano_obra}")
                                
                        except (ValueError, Componente.DoesNotExist, Accion.DoesNotExist) as e:
                            print(f"DEBUG: Error en acción individual: {str(e)}")
                            continue
                    
                    if acciones_creadas > 0:
                        if not is_ajax:
                            config = AdministracionTaller.get_configuracion_activa()
                            if config.ver_mensajes:
                                messages.success(request, f"{acciones_creadas} acción(es) agregada(s) al trabajo.")
                    else:
                        if not is_ajax:
                            config = AdministracionTaller.get_configuracion_activa()
                            if config.ver_mensajes:
                                config = AdministracionTaller.get_configuracion_activa()
                                if config.ver_mensajes:
                                    messages.warning(request, "No se agregaron acciones. Verifica la selección.")
                        
                except json.JSONDecodeError as e:
                    print(f"DEBUG: Error JSON: {str(e)}")
                    if is_ajax:
                        return JsonResponse({
                            "ok": False,
                            "error": f"Error al procesar las acciones: {str(e)}"
                        }, status=400)
                    config = AdministracionTaller.get_configuracion_activa()
                    if config.ver_mensajes:
                        messages.error(request, f"Error al procesar las acciones: {str(e)}")
                except Exception as e:
                    print(f"DEBUG: Error general: {str(e)}")
                    if is_ajax:
                        return JsonResponse({
                            "ok": False,
                            "error": f"Error al agregar las acciones: {str(e)}"
                        }, status=500)
                    config = AdministracionTaller.get_configuracion_activa()
                    if config.ver_mensajes:
                        messages.error(request, f"Error al agregar las acciones: {str(e)}")
                else:
                    if is_ajax:
                        detalle = ""
                        if detalles:
                            detalle = " · " + " / ".join(detalles)
                        return JsonResponse({
                            "ok": True,
                            "acciones_creadas": acciones_creadas,
                            "detalle": detalle
                        })
            else:
                print("DEBUG: No se recibió acciones_json")
                if is_ajax:
                    return JsonResponse({
                        "ok": False,
                        "error": "No se recibieron acciones para agregar."
                    }, status=400)
                config = AdministracionTaller.get_configuracion_activa()
                if config.ver_mensajes:
                    messages.error(request, "No se recibieron acciones para agregar.")
            
            if not is_ajax:
                return redirect_with_tab("acciones")
            # Si es AJAX ya se devolvió una respuesta arriba
            return JsonResponse({"ok": False, "error": "Respuesta inválida"}, status=400)

        # 🔹 Toggle acción completada / pendiente
        elif "toggle_accion" in request.POST:
            accion_id = request.POST.get("accion_id")
            try:
                accion = TrabajoAccion.objects.get(id=accion_id, trabajo=trabajo)
                config = AdministracionTaller.get_configuracion_activa()
                accion.completado = not accion.completado
                accion.save()
                if config.ver_mensajes:
                    messages.success(request, f"Acción marcada como {'completada' if accion.completado else 'pendiente'}.")
            except TrabajoAccion.DoesNotExist:
                config = AdministracionTaller.get_configuracion_activa()
                if config.ver_mensajes:
                    messages.error(request, "Acción no encontrada.")
            return redirect_with_tab("acciones")

        # 🔹 Editar cantidad de acción
        elif "editar_cantidad_accion" in request.POST:
            accion_id = request.POST.get("accion_id")
            cantidad = request.POST.get("cantidad_accion", 1)
            try:
                accion = TrabajoAccion.objects.get(id=accion_id, trabajo=trabajo)
                cantidad_int = int(cantidad) if cantidad and int(cantidad) > 0 else 1
                accion.cantidad = cantidad_int
                accion.save()
                config = AdministracionTaller.get_configuracion_activa()
                if config.ver_mensajes:
                    messages.success(request, f"Cantidad actualizada a {cantidad_int}.")
            except (TrabajoAccion.DoesNotExist, ValueError):
                if config.ver_mensajes:
                    messages.error(request, "Error al actualizar la cantidad.")
            return redirect_with_tab("acciones")

        # 🔹 Editar precio de acción
        elif "editar_precio_accion" in request.POST:
            accion_id = request.POST.get("accion_id")
            precio_str = request.POST.get("precio_accion", "0")
            try:
                accion = TrabajoAccion.objects.get(id=accion_id, trabajo=trabajo)
                precio_decimal = Decimal(precio_str) if precio_str else Decimal('0')
                if precio_decimal < 0:
                    precio_decimal = Decimal('0')
                config = AdministracionTaller.get_configuracion_activa()
                accion.precio_mano_obra = precio_decimal
                accion.save()
                if config.ver_mensajes:
                    messages.success(request, f"Precio actualizado a ${precio_decimal:,.0f}.")
            except (TrabajoAccion.DoesNotExist, InvalidOperation, ValueError) as e:
                if config.ver_mensajes:
                    messages.error(request, f"Error al actualizar el precio: {str(e)}")
            return redirect_with_tab("acciones")

        # 🔹 Eliminar acción
        elif "eliminar_accion" in request.POST:
            config = AdministracionTaller.get_configuracion_activa()
            accion_id = request.POST.get("accion_id")
            try:
                accion = TrabajoAccion.objects.get(id=accion_id, trabajo=trabajo)
                accion.delete()
                if config.ver_mensajes:
                    messages.success(request, "Acción eliminada.")
            except TrabajoAccion.DoesNotExist:
                if config.ver_mensajes:
                    messages.error(request, "Acción no encontrada.")
            return redirect_with_tab("acciones")

        # 🔹 Agregar repuesto
        elif "agregar_repuesto" in request.POST:
            repuesto_id = request.POST.get("repuesto")
            cantidad = request.POST.get("cantidad", 1)
            precio_unitario = request.POST.get("precio_unitario", 0)
            
            if repuesto_id:
                try:
                    repuesto = Repuesto.objects.get(id=repuesto_id)
                    
                    precio_final = precio_unitario or repuesto.precio_venta or 0
                    subtotal = float(precio_final) * int(cantidad)
                    
                    TrabajoRepuesto.objects.create(
                        trabajo=trabajo,
                        repuesto=repuesto,
                        cantidad=cantidad,
                        precio_unitario=precio_final,
                        subtotal=subtotal
                    )
                    config = AdministracionTaller.get_configuracion_activa()
                    if config.ver_mensajes:
                        messages.success(request, "Repuesto agregado al trabajo.")
                except Repuesto.DoesNotExist:
                    if config.ver_mensajes:
                        messages.error(request, "Repuesto no encontrado.")
            return redirect_with_tab("repuestos")

        # 🔹 Agregar repuesto externo
        elif "agregar_repuesto_externo" in request.POST:
            from .models import RepuestoExterno
            
            repuesto_externo_id = request.POST.get("repuesto_externo_id")
            cantidad = request.POST.get("cantidad", 1)
            
            if repuesto_externo_id:
                try:
                    repuesto_externo = RepuestoExterno.objects.get(id=repuesto_externo_id)
                    
                    precio_unitario = repuesto_externo.precio_referencial
                    subtotal = float(precio_unitario) * int(cantidad)
                    
                    TrabajoRepuesto.objects.create(
                        trabajo=trabajo,
                        repuesto=None,
                        repuesto_externo=repuesto_externo,
                        cantidad=cantidad,
                        precio_unitario=precio_unitario,
                        subtotal=subtotal
                    )
                    
                    # Incrementar contador de uso
                    repuesto_externo.incrementar_uso()
                    config = AdministracionTaller.get_configuracion_activa()
                    if config.ver_mensajes:
                        messages.success(request, f"🌐 Repuesto externo agregado: {repuesto_externo.nombre}")
                except RepuestoExterno.DoesNotExist:
                    if config.ver_mensajes:
                        messages.error(request, "Repuesto externo no encontrado.")
            return redirect_with_tab("repuestos")

        # 🔹 Toggle repuesto completado / pendiente (CON ACTUALIZACIÓN DE STOCK)
        elif "toggle_repuesto" in request.POST:
            repuesto_id = request.POST.get("repuesto_id")
            print(f"\n{'='*80}")
            print(f"🔄 TOGGLE REPUESTO - ID: {repuesto_id}")
            print(f"{'='*80}")
            
            try:
                repuesto_trabajo = TrabajoRepuesto.objects.get(id=repuesto_id, trabajo=trabajo)
                print(f"📦 Repuesto encontrado: {repuesto_trabajo}")
                print(f"📦 Repuesto interno: {repuesto_trabajo.repuesto}")
                print(f"📦 Repuesto externo: {repuesto_trabajo.repuesto_externo}")
                print(f"📦 Estado anterior: {repuesto_trabajo.completado}")
                print(f"📦 Cantidad: {repuesto_trabajo.cantidad}")
                
                # Guardar estado anterior para saber si aumentar o disminuir stock
                estado_anterior = repuesto_trabajo.completado
                
                # Cambiar el estado
                repuesto_trabajo.completado = not repuesto_trabajo.completado
                repuesto_trabajo.save()
                print(f"✅ Nuevo estado guardado: {repuesto_trabajo.completado}")
                
                # ACTUALIZAR STOCK SOLO SI ES REPUESTO DEL INVENTARIO PROPIO
                if repuesto_trabajo.repuesto:  # Solo si es del inventario, no externo
                    from .models import RepuestoEnStock
                    
                    print(f"🔍 Buscando stock para repuesto ID: {repuesto_trabajo.repuesto.id}")
                    print(f"🔍 Nombre del repuesto: {repuesto_trabajo.repuesto.nombre}")
                    
                    try:
                        # 🔥 BÚSQUEDA CONSISTENTE: Solo por repuesto y depósito principal
                        stock_item = RepuestoEnStock.objects.filter(
                            repuesto=repuesto_trabajo.repuesto,
                            deposito='bodega-principal'
                        ).first()
                        
                        print(f"🔍 Buscando stock en bodega-principal...")
                        if stock_item:
                            print(f"   ✅ Stock encontrado - ID: {stock_item.id}, Stock: {stock_item.stock}, Reservado: {stock_item.reservado}")
                        
                        if stock_item:
                            stock_anterior = stock_item.stock
                            repuesto_stock_anterior = repuesto_trabajo.repuesto.stock
                            print(f"✅ Stock encontrado - Depósito: {stock_item.deposito}")
                            print(f"📊 Stock en RepuestoEnStock ANTES: {stock_anterior}")
                            print(f"📊 Stock en Repuesto ANTES: {repuesto_stock_anterior}")
                            
                            cantidad = repuesto_trabajo.cantidad or 0
                            print(f"📦 Cantidad a procesar: {cantidad}")
                            
                            if repuesto_trabajo.completado and not estado_anterior:
                                # Se marcó como completado: DESCONTAR del stock
                                stock_item.stock = (stock_item.stock or 0) - cantidad
                                stock_item.save()
                                
                                # 🔥 SINCRONIZAR con Repuesto.stock
                                repuesto_obj = repuesto_trabajo.repuesto
                                repuesto_obj.stock = (repuesto_obj.stock or 0) - cantidad
                                repuesto_obj.save()
                                
                                print(f"➖ DESCUENTO APLICADO en RepuestoEnStock: {stock_anterior} - {cantidad} = {stock_item.stock}")
                                print(f"➖ DESCUENTO APLICADO en Repuesto: {repuesto_stock_anterior} - {cantidad} = {repuesto_obj.stock}")
                                print(f"✅ Stock actualizado en AMBAS tablas (RepuestoEnStock Y Repuesto)")
                                config = AdministracionTaller.get_configuracion_activa()
                                if config.ver_mensajes:
                                    messages.success(
                                        request, 
                                        f"✅ Repuesto completado. Stock descontado: {stock_item.repuesto.nombre} (Stock anterior: {repuesto_stock_anterior}, Stock actual: {repuesto_obj.stock})"
                                    )
                            elif not repuesto_trabajo.completado and estado_anterior:
                                # Se desmarcó: DEVOLVER al stock
                                stock_item.stock = (stock_item.stock or 0) + cantidad
                                stock_item.save()
                                
                                # 🔥 SINCRONIZAR con Repuesto.stock
                                repuesto_obj = repuesto_trabajo.repuesto
                                repuesto_obj.stock = (repuesto_obj.stock or 0) + cantidad
                                repuesto_obj.save()
                                
                                print(f"➕ DEVOLUCIÓN APLICADA en RepuestoEnStock: {stock_anterior} + {cantidad} = {stock_item.stock}")
                                print(f"➕ DEVOLUCIÓN APLICADA en Repuesto: {repuesto_stock_anterior} + {cantidad} = {repuesto_obj.stock}")
                                print(f"✅ Stock restaurado en AMBAS tablas (RepuestoEnStock Y Repuesto)")
                                config = AdministracionTaller.get_configuracion_activa()
                                if config.ver_mensajes:
                                    messages.success(
                                        request, 
                                        f"↩️ Repuesto desmarcado. Stock restaurado: {stock_item.repuesto.nombre} (Stock anterior: {repuesto_stock_anterior}, Stock actual: {repuesto_obj.stock})"
                                    )
                            else:
                                print(f"⚠️ No se requiere cambio de stock (estado no cambió de pendiente→completado o viceversa)")
                                config = AdministracionTaller.get_configuracion_activa()
                                if config.ver_mensajes:
                                    messages.info(
                                        request, 
                                        f"Estado del repuesto actualizado."
                                    )
                        else:
                            # No hay stock registrado, solo cambiar estado sin actualizar inventario
                            print(f"⚠️ NO SE ENCONTRÓ STOCK para repuesto ID: {repuesto_trabajo.repuesto.id}")
                            config = AdministracionTaller.get_configuracion_activa()
                            if config.ver_mensajes:
                                messages.warning(
                                    request, 
                                    f"⚠️ Estado cambiado a {'completado' if repuesto_trabajo.completado else 'pendiente'}. No se encontró stock del repuesto '{repuesto_trabajo.repuesto.nombre}' en RepuestoEnStock."
                                )
                    except Exception as e:
                        print(f"❌ ERROR actualizando stock: {str(e)}")
                        import traceback
                        print(traceback.format_exc())
                        config = AdministracionTaller.get_configuracion_activa()
                        if config.ver_mensajes:
                            messages.error(request, f"❌ Error actualizando stock: {str(e)}")
                else:
                    # Es un repuesto externo, solo cambiar estado
                    print(f"🌐 Repuesto externo detectado: {repuesto_trabajo.repuesto_externo}")
                    config = AdministracionTaller.get_configuracion_activa()
                    if config.ver_mensajes:
                        messages.success(
                            request,
                            f"🌐 Repuesto externo marcado como {'completado' if repuesto_trabajo.completado else 'pendiente'}: {repuesto_trabajo.repuesto_externo.nombre if repuesto_trabajo.repuesto_externo else 'Sin nombre'}"
                        )
                
                print(f"{'='*80}\n")
                    
            except TrabajoRepuesto.DoesNotExist:
                print(f"❌ TrabajoRepuesto NO ENCONTRADO: ID {repuesto_id}")
                config = AdministracionTaller.get_configuracion_activa()
                if config.ver_mensajes:
                    messages.error(request, "Repuesto no encontrado.")
            except Exception as e:
                print(f"❌ ERROR GENERAL en toggle_repuesto: {str(e)}")
                import traceback
                print(traceback.format_exc())
                config = AdministracionTaller.get_configuracion_activa()
                if config.ver_mensajes:
                    messages.error(request, f"❌ Error: {str(e)}")
            return redirect_with_tab("repuestos")

        # 🔹 Eliminar repuesto (CON DEVOLUCIÓN DE STOCK SI ESTABA COMPLETADO)
        elif "eliminar_repuesto" in request.POST:
            config = AdministracionTaller.get_configuracion_activa()
            repuesto_id = request.POST.get("repuesto_id")
            print(f"\n{'='*80}")
            print(f"🗑️ ELIMINAR REPUESTO - ID: {repuesto_id}")
            print(f"{'='*80}")
            
            try:
                repuesto_trabajo = TrabajoRepuesto.objects.get(id=repuesto_id, trabajo=trabajo)
                print(f"📦 Repuesto a eliminar: {repuesto_trabajo}")
                print(f"📦 Estado completado: {repuesto_trabajo.completado}")
                
                # Si el repuesto estaba completado, devolver al stock antes de eliminar
                if repuesto_trabajo.completado and repuesto_trabajo.repuesto:
                    from .models import RepuestoEnStock
                    
                    print(f"↩️ Repuesto completado detectado, devolviendo stock...")
                    
                    try:
                        # 🔥 BÚSQUEDA CONSISTENTE: Solo por repuesto y depósito principal
                        stock_item = RepuestoEnStock.objects.filter(
                            repuesto=repuesto_trabajo.repuesto,
                            deposito='bodega-principal'
                        ).first()
                        
                        if stock_item:
                            cantidad = repuesto_trabajo.cantidad or 0
                            stock_anterior_enstock = stock_item.stock
                            stock_anterior_repuesto = repuesto_trabajo.repuesto.stock
                            
                            # Devolver a RepuestoEnStock
                            stock_item.stock = (stock_item.stock or 0) + cantidad
                            stock_item.save()
                            
                            # 🔥 SINCRONIZAR con Repuesto.stock
                            repuesto_obj = repuesto_trabajo.repuesto
                            repuesto_obj.stock = (repuesto_obj.stock or 0) + cantidad
                            repuesto_obj.save()
                            
                            print(f"➕ Stock devuelto en RepuestoEnStock: {stock_anterior_enstock} + {cantidad} = {stock_item.stock}")
                            print(f"➕ Stock devuelto en Repuesto: {stock_anterior_repuesto} + {cantidad} = {repuesto_obj.stock}")
                            print(f"✅ Stock restaurado en AMBAS tablas")
                            
                            if config.ver_mensajes:
                                messages.success(
                                    request, 
                                    f"🗑️ Repuesto eliminado. Stock devuelto: {stock_item.repuesto.nombre} (Stock: {repuesto_obj.stock})"
                                )
                        else:
                            print(f"⚠️ No se encontró stock para devolver")
                            if config.ver_mensajes:
                                messages.success(request, "🗑️ Repuesto eliminado (sin stock para devolver).")
                    except Exception as e:
                        print(f"❌ Error devolviendo stock: {str(e)}")
                        import traceback
                        print(traceback.format_exc())
                        if config.ver_mensajes:
                            messages.error(request, f"Error devolviendo stock: {str(e)}")
                        # Aún así eliminar el repuesto
                else:
                    print(f"ℹ️ Repuesto NO estaba completado o es externo, no hay stock que devolver")
                    if config.ver_mensajes:
                        messages.success(request, "🗑️ Repuesto eliminado.")
                
                repuesto_trabajo.delete()
                print(f"✅ Repuesto eliminado de la base de datos")
                print(f"{'='*80}\n")
                
            except TrabajoRepuesto.DoesNotExist:
                print(f"❌ TrabajoRepuesto NO ENCONTRADO: ID {repuesto_id}")
                config = AdministracionTaller.get_configuracion_activa()
                if config.ver_mensajes:
                    messages.error(request, "Repuesto no encontrado.")
            return redirect_with_tab("repuestos")

        # 🔹 Agregar múltiples repuestos (nuevo método)
        elif "agregar_repuestos_multiples" in request.POST:
            import json
            repuestos_json = request.POST.get("repuestos_json", "")
            
            print(f"DEBUG: repuestos_json recibido: {repuestos_json}")
            
            if repuestos_json:
                try:
                    repuestos_data = json.loads(repuestos_json)
                    print(f"DEBUG: repuestos_data parseado: {repuestos_data}")
                    repuestos_creados = 0
                    
                    for repuesto_data in repuestos_data:
                        try:
                            repuesto_id = int(repuesto_data.get("id"))
                            cantidad = int(repuesto_data.get("cantidad", 1))
                            precio_unitario = float(repuesto_data.get("precio_unitario", 0))
                            
                            print(f"DEBUG: Procesando - repuesto_id: {repuesto_id}, cantidad: {cantidad}, precio: {precio_unitario}")
                            
                            repuesto = Repuesto.objects.get(id=repuesto_id)
                            
                            # Verificar si ya existe este repuesto en el trabajo
                            if not TrabajoRepuesto.objects.filter(
                                trabajo=trabajo,
                                repuesto=repuesto
                            ).exists():
                                TrabajoRepuesto.objects.create(
                                    trabajo=trabajo,
                                    repuesto=repuesto,
                                    cantidad=cantidad,
                                    precio_unitario=precio_unitario,
                                    subtotal=cantidad * precio_unitario
                                )
                                repuestos_creados += 1
                                print(f"DEBUG: Repuesto creado exitosamente")
                            else:
                                print(f"DEBUG: Repuesto ya existe, saltando")
                                
                        except (ValueError, Repuesto.DoesNotExist) as e:
                            print(f"DEBUG: Error en repuesto individual: {str(e)}")
                            continue
                    
                    config = AdministracionTaller.get_configuracion_activa()
                    if repuestos_creados > 0:
                        if config.ver_mensajes:
                            messages.success(request, f"{repuestos_creados} repuesto(s) agregado(s) al trabajo.")
                    else:
                        if config.ver_mensajes:
                            messages.info(request, "No se agregaron repuestos nuevos (posiblemente ya existían).")
                        
                except json.JSONDecodeError as e:
                    print(f"DEBUG: Error JSON: {str(e)}")
                    if config.ver_mensajes:
                        messages.error(request, f"Error al procesar los repuestos: {str(e)}")
                except Exception as e:
                    print(f"DEBUG: Error general: {str(e)}")
                    if config.ver_mensajes:
                        messages.error(request, f"Error al agregar los repuestos: {str(e)}")
            else:
                print("DEBUG: No se recibió repuestos_json")
                config = AdministracionTaller.get_configuracion_activa()
                if config.ver_mensajes:
                    messages.error(request, "No se recibieron repuestos para agregar.")
            
            return redirect_with_tab("repuestos")

        # 🔹 Agregar múltiples insumos (nuevo método)
        elif "agregar_insumos_multiples" in request.POST:
            import json
            insumos_json = request.POST.get("insumos_json", "")
            
            print(f"DEBUG: insumos_json recibido: {insumos_json}")
            
            if insumos_json:
                try:
                    insumos_data = json.loads(insumos_json)
                    print(f"DEBUG: insumos_data parseado: {insumos_data}")
                    insumos_creados = 0
                    
                    for insumo_data in insumos_data:
                        try:
                            repuesto_id = int(insumo_data.get("id"))
                            cantidad = int(insumo_data.get("cantidad", 1))
                            precio_unitario = float(insumo_data.get("precio_unitario", 0))
                            
                            print(f"DEBUG: Procesando insumo - repuesto_id: {repuesto_id}, cantidad: {cantidad}, precio: {precio_unitario}")
                            
                            repuesto = Repuesto.objects.get(id=repuesto_id)
                            
                            # Verificar si ya existe este repuesto en el trabajo
                            if not TrabajoRepuesto.objects.filter(
                                trabajo=trabajo,
                                repuesto=repuesto
                            ).exists():
                                TrabajoRepuesto.objects.create(
                                    trabajo=trabajo,
                                    repuesto=repuesto,
                                    cantidad=cantidad,
                                    precio_unitario=precio_unitario,
                                    subtotal=cantidad * precio_unitario
                                )
                                insumos_creados += 1
                                print(f"DEBUG: Insumo creado exitosamente")
                            else:
                                print(f"DEBUG: Insumo ya existe, saltando")
                                
                        except (ValueError, Repuesto.DoesNotExist) as e:
                            print(f"DEBUG: Error en insumo individual: {str(e)}")
                            continue
                    
                    if insumos_creados > 0:
                        config = AdministracionTaller.get_configuracion_activa()
                        if config.ver_mensajes:
                            messages.success(request, f"{insumos_creados} insumo(s) agregado(s) al trabajo.")
                    else:
                        config = AdministracionTaller.get_configuracion_activa()
                        if config.ver_mensajes:
                            messages.info(request, "No se agregaron insumos nuevos (posiblemente ya existían).")
                        
                except json.JSONDecodeError as e:
                    print(f"DEBUG: Error JSON: {str(e)}")
                    config = AdministracionTaller.get_configuracion_activa()
                    if config.ver_mensajes:
                        messages.error(request, f"Error al procesar los insumos: {str(e)}")
                except Exception as e:
                    print(f"DEBUG: Error general: {str(e)}")
                    config = AdministracionTaller.get_configuracion_activa()
                    if config.ver_mensajes:
                        messages.error(request, f"Error al agregar los insumos: {str(e)}")
            else:
                print("DEBUG: No se recibió insumos_json")
                config = AdministracionTaller.get_configuracion_activa()
                if config.ver_mensajes:
                    messages.error(request, "No se recibieron insumos para agregar.")
            
            return redirect_with_tab("insumos")

        # 🔹 Subir foto
        elif "subir_foto" in request.POST:
            foto_form = SubirFotoForm(request.POST, request.FILES)
            if foto_form.is_valid():
                foto = foto_form.save(commit=False)
                foto.trabajo = trabajo
                foto.descripcion = request.POST.get("descripcion", "")
                foto.save()
                
                # Registrar evento de auditoría
                registrar_foto_agregada(trabajo, request=request, descripcion=foto.descripcion)
                
                config = AdministracionTaller.get_configuracion_activa()
                if config.ver_mensajes:
                    messages.success(request, "Foto subida con éxito.")
                return redirect_with_tab("fotos")

        # 🔹 Eliminar foto
        elif "eliminar_foto" in request.POST:
            config = AdministracionTaller.get_configuracion_activa()
            foto_id = request.POST.get("eliminar_foto")
            try:
                foto = TrabajoFoto.objects.get(id=foto_id, trabajo=trabajo)
                foto.delete()
                if config.ver_mensajes:
                    messages.success(request, "Foto eliminada.")
            except TrabajoFoto.DoesNotExist:
                if config.ver_mensajes:
                    messages.error(request, "Foto no encontrada.")
            return redirect_with_tab("fotos")

        # 🔹 Cambiar estado del trabajo
        elif "cambiar_estado" in request.POST:
            nuevo_estado = request.POST.get("cambiar_estado")
            if nuevo_estado in dict(Trabajo.ESTADOS).keys():
                estado_anterior = trabajo.estado
                trabajo.estado = nuevo_estado
                if nuevo_estado == "trabajando" and not trabajo.fecha_inicio:
                    trabajo.fecha_inicio = timezone.now()
                if nuevo_estado in ["completado", "entregado"]:
                    trabajo.fecha_fin = timezone.now()
                else:
                    trabajo.fecha_fin = None
                trabajo.save()
                
                # Registrar evento de auditoría
                registrar_cambio_estado(trabajo, estado_anterior, nuevo_estado, request=request)
                
                # Si es entrega, registrar también como entrega
                if nuevo_estado == "entregado":
                    registrar_entrega(trabajo, request=request)
                    # Generar bonos automáticamente para los mecánicos
                    try:
                        from .views_bonos import generar_bonos_trabajo_entregado
                        bonos_generados = generar_bonos_trabajo_entregado(trabajo)
                        config = AdministracionTaller.get_configuracion_activa()
                        if bonos_generados:
                            total_bonos = sum(b.monto for b in bonos_generados)
                            if config.ver_mensajes:
                                messages.success(
                                    request, 
                                    f"Trabajo actualizado a {trabajo.get_estado_display()}. "
                                    f"Bonos generados: ${total_bonos} para {len(bonos_generados)} mecánico(s)."
                                )
                        else:
                            config = AdministracionTaller.get_configuracion_activa()
                            if config.ver_mensajes:
                                messages.success(request, f"Trabajo actualizado a {trabajo.get_estado_display()}.")
                    except Exception as e:
                        # Si hay error generando bonos, no fallar el cambio de estado
                        config = AdministracionTaller.get_configuracion_activa()
                        if config.ver_mensajes:
                            messages.warning(request, f"Trabajo actualizado, pero hubo un error al generar bonos: {str(e)}")
                else:
                    config = AdministracionTaller.get_configuracion_activa()
                    if config.ver_mensajes:
                        messages.success(request, f"Trabajo actualizado a {trabajo.get_estado_display()}.")
            return redirect_with_tab("estado")

        # 🔹 Toggle acción completada / pendiente (método anterior)
        elif "accion_toggle" in request.POST:
            accion_id = request.POST.get("accion_toggle")
            accion = get_object_or_404(TrabajoAccion, id=accion_id, trabajo=trabajo)
            estaba_completado = accion.completado
            accion.completado = not accion.completado
            accion.fecha = timezone.now() if accion.completado else None
            accion.save()
            
            # Registrar evento de auditoría
            if accion.completado:
                registrar_accion_completada(trabajo, accion, request=request)
            else:
                registrar_accion_pendiente(trabajo, accion, request=request)
            
            config = AdministracionTaller.get_configuracion_activa()
            if config.ver_mensajes:
                messages.success(request, f"Acción '{accion.accion.nombre}' actualizada.")
            return redirect("trabajo_detalle", pk=trabajo.pk)

        # 🔹 Toggle repuesto instalado / pendiente
        elif "repuesto_toggle" in request.POST:
            rep_id = request.POST.get("repuesto_toggle")
            rep = get_object_or_404(TrabajoRepuesto, id=rep_id, trabajo=trabajo)
            estaba_completado = rep.completado
            rep.completado = not rep.completado
            rep.fecha = timezone.now() if rep.completado else None
            rep.save()
            
            # Registrar evento de auditoría
            if rep.completado:
                registrar_repuesto_instalado(trabajo, rep, request=request)
            else:
                registrar_repuesto_pendiente(trabajo, rep, request=request)
            
            config = AdministracionTaller.get_configuracion_activa()
            repuesto_nombre = rep.repuesto.nombre if rep.repuesto else (rep.repuesto_externo.nombre if rep.repuesto_externo else "Repuesto")
            if config.ver_mensajes:
                messages.success(request, f"Repuesto '{repuesto_nombre}' actualizado.")
            return redirect("trabajo_detalle", pk=trabajo.pk)

        # ========================
        # 💵 GESTIÓN DE ABONOS
        # ========================
        elif "agregar_abono" in request.POST:
            from .models import TrabajoAbono
            
            monto = request.POST.get("monto_abono")
            metodo_pago = request.POST.get("metodo_pago", "efectivo")
            descripcion = request.POST.get("descripcion_abono", "").strip()
            
            try:
                monto_decimal = Decimal(monto)
                if monto_decimal <= 0:
                    config = AdministracionTaller.get_configuracion_activa()
                    if config.ver_mensajes:
                        messages.error(request, "❌ El monto del abono debe ser mayor a cero.")
                else:
                    abono = TrabajoAbono.objects.create(
                        trabajo=trabajo,
                        monto=monto_decimal,
                        metodo_pago=metodo_pago,
                        descripcion=descripcion,
                        usuario=request.user
                    )
                    
                    # Registrar evento de auditoría
                    registrar_abono(trabajo, abono, request=request)
                    
                    config = AdministracionTaller.get_configuracion_activa()
                    if config.ver_mensajes:
                        messages.success(request, f"✅ Abono de ${monto_decimal:,.0f} registrado exitosamente.")
            except (ValueError, TypeError):
                messages.error(request, "❌ El monto ingresado no es válido.")
            except Exception as e:
                messages.error(request, f"❌ Error al registrar el abono: {str(e)}")
            
            return redirect_with_tab("abonos")
        
        elif "eliminar_abono" in request.POST:
            from .models import TrabajoAbono
            config = AdministracionTaller.get_configuracion_activa()
            
            abono_id = request.POST.get("abono_id")
            try:
                abono = TrabajoAbono.objects.get(id=abono_id, trabajo=trabajo)
                monto = abono.monto
                abono.delete()
                if config.ver_mensajes:
                    messages.success(request, f"✅ Abono de ${monto:,.0f} eliminado exitosamente.")
            except TrabajoAbono.DoesNotExist:
                if config.ver_mensajes:
                    messages.error(request, "❌ Abono no encontrado.")
            except Exception as e:
                if config.ver_mensajes:
                    messages.error(request, f"❌ Error al eliminar el abono: {str(e)}")
            
            return redirect_with_tab("abonos")

        # ========================
        # 💰 GESTIÓN DE ADICIONALES
        # ========================
        elif "agregar_adicional" in request.POST:
            from .models import TrabajoAdicional
            
            concepto = request.POST.get("concepto_adicional", "").strip()
            monto = request.POST.get("monto_adicional")
            descuento = request.POST.get("es_descuento") == "on"  # Checkbox retorna "on" si está marcado
            
            try:
                if not concepto:
                    messages.error(request, "❌ El concepto no puede estar vacío.")
                else:
                    monto_decimal = Decimal(monto)
                    if monto_decimal <= 0:
                        config = AdministracionTaller.get_configuracion_activa()
                        if config.ver_mensajes:
                            messages.error(request, "❌ El monto del concepto adicional debe ser mayor a cero.")
                    else:
                        adicional = TrabajoAdicional.objects.create(
                            trabajo=trabajo,
                            concepto=concepto,
                            monto=monto_decimal,
                            descuento=descuento,
                            usuario=request.user
                        )
                        
                        config = AdministracionTaller.get_configuracion_activa()
                        tipo = "descuento" if descuento else "concepto adicional"
                        if config.ver_mensajes:
                            messages.success(request, f"✅ {tipo.capitalize()} de ${monto_decimal:,.0f} registrado exitosamente.")
            except (ValueError, TypeError):
                config = AdministracionTaller.get_configuracion_activa()
                if config.ver_mensajes:
                    messages.error(request, "❌ El monto ingresado no es válido.")
            except Exception as e:
                config = AdministracionTaller.get_configuracion_activa()
                if config.ver_mensajes:
                    messages.error(request, f"❌ Error al registrar el concepto adicional: {str(e)}")
            
            return redirect_with_tab("adicionales")
        
        elif "eliminar_adicional" in request.POST:
            from .models import TrabajoAdicional
            config = AdministracionTaller.get_configuracion_activa()
            
            adicional_id = request.POST.get("adicional_id")
            try:
                adicional = TrabajoAdicional.objects.get(id=adicional_id, trabajo=trabajo)
                monto = adicional.monto
                adicional.delete()
                if config.ver_mensajes:
                    messages.success(request, f"✅ Concepto adicional de ${monto:,.0f} eliminado exitosamente.")
            except TrabajoAdicional.DoesNotExist:
                if config.ver_mensajes:
                    messages.error(request, "❌ Concepto adicional no encontrado.")
            except Exception as e:
                if config.ver_mensajes:
                    messages.error(request, f"❌ Error al eliminar el concepto adicional: {str(e)}")
            
            return redirect_with_tab("adicionales")

    # 🔹 Detectar pestaña activa desde parámetros URL
    active_tab = request.GET.get('tab', 'info')
    
    # 🔹 Obtener componentes ya seleccionados en el trabajo
    componentes_trabajo = list(trabajo.acciones.values_list('componente_id', flat=True).distinct())
    
    # Obtener configuración del taller
    config = AdministracionTaller.get_configuracion_activa()
    
    context = {
        "trabajo": trabajo,
        "asignar_form": asignar_form,
        "foto_form": foto_form,
        "componentes": componentes,
        "componentes_trabajo": componentes_trabajo,  # IDs de componentes ya en el trabajo
        "acciones_disponibles": acciones_disponibles,
        "repuestos_disponibles": repuestos_disponibles,
        "active_tab": active_tab,
        "config": config,
        "ver_mensajes": config.ver_mensajes if config else True,
        "ver_avisos": config.ver_avisos if config else True,
    }
    # Detectar móvil y usar template apropiado
    if is_mobile_device(request):
        template_name = "car/trabajo_detalle_movil.html"
    else:
        template_name = "car/trabajo_detalle_nuevo.html"
    
    return render(request, template_name, context)


@login_required
def trabajo_pdf(request, pk):
    """Generar PDF de la orden de trabajo"""
    import logging
    logger = logging.getLogger(__name__)
    
    from django.http import HttpResponse
    from django.template.loader import get_template
    from django.conf import settings
    import os
    
    logger.info(f"🔍 INICIANDO GENERACIÓN PDF - Trabajo ID: {pk}")
    
    trabajo = get_object_or_404(Trabajo, pk=pk)
    logger.info(f"✅ Trabajo encontrado: {trabajo.vehiculo} - Estado: {trabajo.estado}")
    
    # Crear el PDF usando weasyprint o reportlab
    try:
        from weasyprint import HTML, CSS
        from weasyprint.text.fonts import FontConfiguration
        logger.info("✅ WeasyPrint importado correctamente")
        
        # Template para el PDF
        template = get_template('car/trabajo_pdf.html')
        logger.info("✅ Template cargado correctamente")
        
        # Preparar contexto con URLs absolutas para las imágenes
        config = AdministracionTaller.get_configuracion_activa()
        
        # Generar rutas de archivos locales para los logos (WeasyPrint necesita acceso directo)
        logo_path = None
        if config.logo_principal_png and os.path.exists(config.logo_principal_png.path):
            logo_path = f"file://{config.logo_principal_png.path}"
            logger.info(f"🖼️ Logo PNG disponible: {logo_path}")
        elif config.logo_principal_svg and os.path.exists(config.logo_principal_svg.path):
            logo_path = f"file://{config.logo_principal_svg.path}"
            logger.info(f"🖼️ Logo SVG disponible: {logo_path}")
        else:
            # Usar logo por defecto desde static files
            default_logo_path = os.path.join(settings.STATIC_ROOT or settings.STATICFILES_DIRS[0], 'images', 'Logo1.svg')
            if os.path.exists(default_logo_path):
                logo_path = f"file://{default_logo_path}"
                logger.info(f"🖼️ Usando logo por defecto: {logo_path}")
            else:
                logger.warning("⚠️ No se encontró ningún logo disponible")
        
        context = {
            'trabajo': trabajo,
            'request': request,  # Para generar URLs absolutas
            'config': config,  # Configuración del taller para el logo
            'logo_path': logo_path,  # Ruta local del logo para WeasyPrint
        }
        
        # Log de fotos del trabajo
        fotos_count = trabajo.fotos.count()
        logger.info(f"📷 Fotos encontradas en el trabajo: {fotos_count}")
        
        if fotos_count > 0:
            for i, foto in enumerate(trabajo.fotos.all()):
                logger.info(f"📷 Foto {i+1}: {foto.imagen.name} - URL: {foto.imagen.url}")
                # Verificar si el archivo existe físicamente
                if os.path.exists(foto.imagen.path):
                    logger.info(f"✅ Archivo físico existe: {foto.imagen.path}")
                else:
                    logger.error(f"❌ Archivo físico NO existe: {foto.imagen.path}")
        
        html_content = template.render(context)
        logger.info(f"✅ HTML renderizado - Tamaño: {len(html_content)} caracteres")
        
        # Configuración de fuentes
        font_config = FontConfiguration()
        logger.info("✅ Configuración de fuentes creada")
        
        # Crear el PDF
        logger.info("🔄 Creando documento HTML para WeasyPrint...")
        html_doc = HTML(string=html_content)
        logger.info("✅ Documento HTML creado")
        
        css = CSS(string='''
            @page {
                size: A4;
                margin: 1cm;
            }
            body {
                font-family: Arial, sans-serif;
                font-size: 12px;
            }
            .header {
                text-align: center;
                border-bottom: 2px solid #333;
                padding-bottom: 10px;
                margin-bottom: 20px;
            }
            .section {
                margin-bottom: 15px;
            }
            .section h3 {
                background: #f0f0f0;
                padding: 5px;
                margin: 0 0 10px 0;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 10px;
            }
            th, td {
                border: 1px solid #ddd;
                padding: 5px;
                text-align: left;
            }
            th {
                background: #f0f0f0;
            }
            img {
                max-width: 100%;
                height: auto;
            }
        ''', font_config=font_config)
        logger.info("✅ CSS aplicado")
        
        logger.info("🔄 Generando PDF con WeasyPrint...")
        pdf_file = html_doc.write_pdf(stylesheets=[css], font_config=font_config)
        logger.info(f"✅ PDF generado exitosamente - Tamaño: {len(pdf_file)} bytes")
        
        response = HttpResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="orden_trabajo_{trabajo.id}.pdf"'
        response['Content-Length'] = str(len(pdf_file))
        response['X-Content-Type-Options'] = 'nosniff'
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        logger.info("✅ Respuesta HTTP creada")
        return response
        
    except ImportError as e:
        logger.error(f"❌ ERROR: WeasyPrint no está disponible: {str(e)}")
        # Si weasyprint no está disponible, usar una alternativa simple
        from django.http import HttpResponse
        response = HttpResponse(content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename="orden_trabajo_{trabajo.id}.txt"'
            
        content = f"""
ORDEN DE TRABAJO #{trabajo.id}
===============================

Cliente: {trabajo.vehiculo.cliente.nombre}
Teléfono: {trabajo.vehiculo.cliente.telefono}
Vehículo: {trabajo.vehiculo.marca} {trabajo.vehiculo.modelo} {trabajo.vehiculo.anio}
Placa: {trabajo.vehiculo.placa}

Estado: {trabajo.get_estado_display()}
Progreso: {trabajo.porcentaje_avance}%

Fecha Inicio: {trabajo.fecha_inicio|date:"d/m/Y H:i" if trabajo.fecha_inicio else "No iniciado"}
Fecha Fin: {trabajo.fecha_fin|date:"d/m/Y H:i" if trabajo.fecha_fin else "En progreso"}

Observaciones:
{trabajo.observaciones or "Sin observaciones"}

Mecánicos Asignados:
"""
        for mec in trabajo.mecanicos.all():
            content += f"- {mec.user.get_full_name() or mec.user.first_name} ({mec.especialidad or 'Sin especialidad'})\n"
        
        content += "\nAcciones:\n"
        for accion in trabajo.acciones.all():
            estado = "✅ Completado" if accion.completado else "⏳ Pendiente"
            content += f"- {accion.componente.nombre}: {accion.accion.nombre} - {estado}\n"
        
        content += "\nRepuestos:\n"
        for repuesto in trabajo.repuestos.all():
            estado = "✅ Completado" if repuesto.completado else "⏳ Pendiente"
            content += f"- {repuesto.repuesto.nombre} (x{repuesto.cantidad}) - {estado}\n"
        
        content += f"\nTotal: ${trabajo.total_general or 0}\n"
        content += f"\nGenerado el: {timezone.now().strftime('%d/%m/%Y %H:%M')}"
        
        response.write(content)
        return response
        
    except Exception as e:
        logger.error(f"❌ ERROR GENERAL generando PDF: {str(e)}")
        logger.error(f"❌ Tipo de error: {type(e).__name__}")
        import traceback
        logger.error(f"❌ Traceback completo: {traceback.format_exc()}")
        
        # Respuesta de error
        from django.http import HttpResponse
        response = HttpResponse(content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename="error_trabajo_{trabajo.id}.txt"'
        response.write(f"Error generando PDF: {str(e)}")
        return response



@login_required
def pizarra_view(request):
    # Obtener configuración del taller
    config = AdministracionTaller.get_configuracion_activa()
    
    trabajos = Trabajo.objects.select_related("vehiculo", "vehiculo__cliente")
    
    # Filtrar trabajos entregados que tienen más de 3 días (no mostrar en pizarra)
    trabajos_visibles = filtrar_trabajos_entregados_por_dias(trabajos, dias_desde_entrega=3)

    context = {
        "iniciados": trabajos_visibles.filter(estado="iniciado"),
        "trabajando": trabajos_visibles.filter(estado="trabajando"),
        "completados": trabajos_visibles.filter(estado="completado"),
        "entregados": trabajos_visibles.filter(estado="entregado"),  # Solo los recientes (últimos 3 días)
        "config": config,
    }
    return render(request, "car/pizarra_page.html", context)

@login_required
def panel_principal(request):
    """Vista principal que incluye todo el contenido del dashboard"""
    # Obtener configuración del taller
    config = AdministracionTaller.get_configuracion_activa()
    
    # 🔹 Manejar ocultar trabajo
    if request.method == "POST" and "ocultar_trabajo" in request.POST:
        trabajo_id = request.POST.get("trabajo_id")
        try:
            trabajo = Trabajo.objects.get(id=trabajo_id)
            trabajo.visible = False
            trabajo.save()
            config = AdministracionTaller.get_configuracion_activa()
            if config.ver_mensajes:
                messages.success(request, f"Trabajo #{trabajo.id} ocultado del listado.")
        except Trabajo.DoesNotExist:
            messages.error(request, "Trabajo no encontrado.")
        return redirect('panel_principal')
    
    # Estadísticas para el dashboard
    # Usar la fecha local de Santiago, no UTC
    ahora_santiago = timezone.localtime(timezone.now())
    hoy = ahora_santiago.date()
    
    # Estadísticas de diagnósticos
    diagnosticos_total = Diagnostico.objects.count()
    
    # Usar timezone-aware para la consulta con fecha local
    inicio_dia = ahora_santiago.replace(hour=0, minute=0, second=0, microsecond=0)
    fin_dia = inicio_dia + timedelta(days=1)
    diagnosticos_hoy = Diagnostico.objects.filter(fecha__gte=inicio_dia, fecha__lt=fin_dia).count()
    
    diagnosticos_pendientes = Diagnostico.objects.filter(estado='pendiente').count()
    
    
    # Estadísticas de trabajos (solo visibles)
    trabajos = Trabajo.objects.filter(visible=True).select_related("vehiculo", "vehiculo__cliente")
    trabajos_activos = trabajos.filter(estado__in=['iniciado', 'trabajando']).count()
    trabajos_completados_hoy = trabajos.filter(
        fecha_fin__gte=inicio_dia, 
        fecha_fin__lt=fin_dia,
        estado='completado'
    ).count()
    
    # Estadísticas del POS
    ventas_hoy = VentaPOS.objects.filter(fecha__gte=inicio_dia, fecha__lt=fin_dia).count()
    total_ventas_hoy = VentaPOS.objects.filter(
        fecha__gte=inicio_dia, fecha__lt=fin_dia
    ).aggregate(total=Sum('total'))['total'] or 0
    
    # Estadísticas de repuestos
    repuestos_total = Repuesto.objects.count()
    # Usar el nuevo sistema de stock unificado
    repuestos_sin_stock = 0  # Se calculará en el template usando las propiedades del modelo
    
    
    # Datos del POS para el template unificado
    sesion_pos = SesionVenta.objects.filter(
        usuario=request.user, 
        activa=True
    ).first()
    
    if not sesion_pos:
        sesion_pos = SesionVenta.objects.create(
            usuario=request.user,
            activa=True
        )
    
    carrito_items = sesion_pos.carrito_items.all().order_by('-agregado_en')
    subtotal_pos = sum(item.subtotal for item in carrito_items)
    
    context = {
        # Trabajos para la pizarra
        "iniciados": trabajos.filter(estado="iniciado"),
        "trabajando": trabajos.filter(estado="trabajando"),
        "completados": trabajos.filter(estado="completado"),
        "entregados": trabajos.filter(estado="entregado"),
        
        # Estadísticas del dashboard
        'hoy': hoy,
        'diagnosticos_hoy': diagnosticos_hoy,
        'diagnosticos_total': diagnosticos_total,
        'diagnosticos_pendientes': diagnosticos_pendientes,
        'trabajos_activos': trabajos_activos,
        'trabajos_completados_hoy': trabajos_completados_hoy,
        'ventas_hoy': ventas_hoy,
        'total_ventas_hoy': total_ventas_hoy,
        'repuestos_total': repuestos_total,
        'repuestos_sin_stock': repuestos_sin_stock,
        
        # Datos del POS
        'sesion': sesion_pos,
        'carrito_items': carrito_items,
        'subtotal': subtotal_pos,
        
        # Configuración del taller
        'config': config,
    }
    
    return render(request, "car/panel_definitivo.html", context)


def venta_crear(request):
    today = datetime.date.today()
    fecha_str = request.GET.get("fecha")
    try:
        filtro_fecha = datetime.date.fromisoformat(fecha_str) if fecha_str else today
    except ValueError:
        filtro_fecha = today

    if request.method == "POST":
        form = VentaForm(request.POST)
        cart_json = request.POST.get("cart_json", "[]")
        try:
            cart = json.loads(cart_json)
        except Exception:
            cart = []
        # Validación mínima del cart
        if not cart:
            config = AdministracionTaller.get_configuracion_activa()
            if config.ver_mensajes:
                messages.error(request, "No hay productos en la venta.")
        elif not form.is_valid():
            config = AdministracionTaller.get_configuracion_activa()
            if config.ver_mensajes:
                messages.error(request, "Corrige los datos del formulario.")
        else:
            # Guardar la venta + items
            with transaction.atomic():
                venta = form.save(commit=False)
                venta.usuario = request.user
                venta.total = Decimal("0")
                venta.save()

                total = Decimal("0")
                for idx, it in enumerate(cart):
                    try:
                        repuesto_stock_id = int(it.get("repuesto_stock_id"))
                        cantidad = int(it.get("cantidad", 1))
                        precio_unitario = round(Decimal(str(it.get("precio_unitario", "0"))))
                    except (ValueError, TypeError, InvalidOperation) as e:
                        raise ValueError(f"Datos inválidos en item #{idx+1}: {e}")

                    rs = get_object_or_404(RepuestoEnStock, pk=repuesto_stock_id)

                    # validar stock disponible
                    if rs.disponible < cantidad:
                        raise ValueError(f"Stock insuficiente para {rs.repuesto.nombre} (Disponible: {rs.disponible})")

                    subtotal = precio_unitario * cantidad

                    VentaItem.objects.create(
                        venta=venta,
                        repuesto_stock=rs,
                        cantidad=cantidad,
                        precio_unitario=precio_unitario,
                        subtotal=subtotal
                    )

                    # actualizar stock y movimiento
                    rs.stock = rs.stock - cantidad
                    rs.save(update_fields=["stock", "ultima_actualizacion"])
                    StockMovimiento.objects.create(
                        repuesto_stock=rs,
                        tipo="salida",
                        cantidad=cantidad,
                        motivo=f"Venta #{venta.id}",
                        referencia=str(venta.id),
                        usuario=request.user
                    )

                    total += subtotal

                venta.total = total
                venta.pagado = True
                venta.save(update_fields=["total", "pagado"])

            config = AdministracionTaller.get_configuracion_activa()
            if config.ver_mensajes:
                messages.success(request, f"Venta #{venta.id} creada (Total: {total})")
            return redirect("venta_detalle", pk=venta.pk)

    else:
        form = VentaForm()

    # ---- cálculo de arqueo ----
    ventas_hoy = Venta.objects.filter(fecha__date=filtro_fecha, pagado=True)

    total_efectivo = ventas_hoy.filter(metodo_pago="efectivo").aggregate(s=Sum("total"))["s"] or Decimal("0")
    total_tarjeta = ventas_hoy.filter(metodo_pago="tarjeta").aggregate(s=Sum("total"))["s"] or Decimal("0")
    total_transferencia = ventas_hoy.filter(metodo_pago="transferencia").aggregate(s=Sum("total"))["s"] or Decimal("0")
    total_general = total_efectivo + total_tarjeta + total_transferencia

    context = {
        "form": form,
        "today": today.isoformat(),
        "total_efectivo": total_efectivo,
        "total_tarjeta": total_tarjeta,
        "total_transferencia": total_transferencia,
        "total_general": total_general,
        "filtro_fecha": filtro_fecha.isoformat(),
    }
    return render(request, "ventas/venta_crear.html", context)




def venta_detalle(request, pk):
    venta = get_object_or_404(Venta, pk=pk)
    return render(request, "ventas/venta_detalle.html", {"venta": venta})


def ventas_historial(request):
    ventas = Venta.objects.all().order_by("-fecha")
    return render(request, "ventas/ventas_historial.html", {"ventas": ventas})


def repuesto_lookup(request):
    q = request.GET.get("q", "").strip()
    results = []

    if q:
        # Búsqueda básica
        repuestos = RepuestoEnStock.objects.select_related("repuesto").filter(
            Q(repuesto__nombre__icontains=q) |
            Q(repuesto__sku__icontains=q) |
            Q(repuesto__oem__icontains=q) |
            Q(repuesto__codigo_barra__icontains=q) |
            Q(repuesto__marca__icontains=q) |
            Q(repuesto__descripcion__icontains=q) |
            Q(repuesto__marca_veh__icontains=q) |
            Q(repuesto__tipo_de_motor__icontains=q) |
            Q(repuesto__cod_prov__icontains=q) |
            Q(repuesto__origen_repuesto__icontains=q)
        )[:20]  # limitar a 20 resultados para que sea rápido
        
        # Si no hay resultados y el término contiene guiones, buscar por partes del SKU
        if not repuestos.exists() and '-' in q:
            partes = q.split('-')
            if len(partes) > 1:
                # Buscar SKUs que contengan todas las partes
                sku_filter = Q()
                for parte in partes:
                    if parte.strip():  # Ignorar partes vacías
                        sku_filter &= Q(repuesto__sku__icontains=parte.strip())
                
                if sku_filter:
                    repuestos = RepuestoEnStock.objects.select_related("repuesto").filter(sku_filter)[:20]

        for r in repuestos:
            text = f"{r.repuesto.sku or '-'} | {r.repuesto.nombre} | {r.repuesto.marca or ''} | Stock: {r.stock}"
            results.append({
                "id": r.id,   # ID de RepuestoEnStock
                "repuesto_nombre": r.repuesto.nombre,  # Nombre del repuesto
                "text": f"{r.repuesto.sku or '-'} | {r.repuesto.nombre} | {r.repuesto.marca or ''} | Stock: {r.stock}",
                "stock": r.stock,  # Stock disponible
                "deposito": r.deposito,  # Depósito
                "precio_venta": r.precio_venta
            })

    print("results :",{"results": results})
    return JsonResponse({"results": results})


@login_required
def buscar_insumos(request):
    """Buscar insumos para la pestaña de insumos en trabajos y diagnósticos - Búsqueda amplia sin filtros"""
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'insumos': []})
    
    try:
        from django.db.models import Q
        from .models import RepuestoEnStock
        
        # Búsqueda amplia en RepuestoEnStock (tabla por defecto)
        repuestos_stock = RepuestoEnStock.objects.select_related("repuesto").filter(
            Q(repuesto__nombre__icontains=query) |
            Q(repuesto__sku__icontains=query) |
            Q(repuesto__oem__icontains=query) |
            Q(repuesto__codigo_barra__icontains=query) |
            Q(repuesto__marca__icontains=query) |
            Q(repuesto__descripcion__icontains=query) |
            Q(repuesto__marca_veh__icontains=query) |
            Q(repuesto__tipo_de_motor__icontains=query) |
            Q(repuesto__cod_prov__icontains=query) |
            Q(repuesto__origen_repuesto__icontains=query) |
            Q(repuesto__carroceria__icontains=query) |
            Q(repuesto__referencia__icontains=query)
        )
        
        # Si no hay resultados y el término contiene guiones, buscar por partes del SKU
        if not repuestos_stock.exists() and '-' in query:
            partes = query.split('-')
            if len(partes) > 1:
                # Buscar SKUs que contengan todas las partes
                sku_filter = Q()
                for parte in partes:
                    if parte.strip():  # Ignorar partes vacías
                        sku_filter &= Q(repuesto__sku__icontains=parte.strip())
                
                if sku_filter:
                    repuestos_stock = RepuestoEnStock.objects.select_related("repuesto").filter(sku_filter)
        
        # Ordenar por nombre y limitar resultados
        repuestos_stock = repuestos_stock.order_by('repuesto__nombre')[:20]
        
        # Convertir a formato JSON
        insumos = []
        for stock_item in repuestos_stock:
            repuesto = stock_item.repuesto
            
            # Stock disponible (stock - reservado)
            stock_disponible = (stock_item.stock or 0) - (stock_item.reservado or 0)
            
            # Precio de venta desde RepuestoEnStock
            precio_venta = stock_item.precio_venta or 0
            
            # Incluir todos los repuestos (con o sin stock para insumos)
            insumos.append({
                'id': repuesto.id,
                'nombre': repuesto.nombre,
                'sku': repuesto.sku or '',
                'codigo': repuesto.codigo_barra or '',  # Usar codigo_barra como codigo
                'marca': repuesto.marca or '',
                'precio': float(precio_venta),
                'stock': int(stock_disponible),
                'codigo_barra': repuesto.codigo_barra or '',
                'unidad': repuesto.unidad or '',
                'oem': repuesto.oem or '',
                'referencia': repuesto.referencia or '',
                'marca_veh': repuesto.marca_veh or '',
                'tipo_motor': repuesto.tipo_de_motor or '',
                'carroceria': repuesto.carroceria or '',
                'deposito': stock_item.deposito or '',
                'proveedor': stock_item.proveedor or '',
                'descripcion': repuesto.descripcion or '',
                'medida': repuesto.medida or '',
            })
        
        return JsonResponse({'insumos': insumos})
        
    except Exception as e:
        print(f"Error buscando insumos: {e}")
        return JsonResponse({'insumos': [], 'error': str(e)})



class RepuestoListView(ListView):
    model = Repuesto
    template_name = "repuestos/repuesto_list.html"
    context_object_name = "repuestos"
    
    def get_queryset(self):
        # Solo seleccionar campos que existen en la base de datos
        return Repuesto.objects.all().select_related()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Obtener configuración del taller
        config = AdministracionTaller.get_configuracion_activa()
        context['config'] = config
        return context

class RepuestoCreateView(CreateView):
    model = Repuesto
    form_class = RepuestoForm
    template_name = "repuestos/repuesto_form.html"
    success_url = reverse_lazy("repuesto_list")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Obtener configuración del taller
        config = AdministracionTaller.get_configuracion_activa()
        context['config'] = config
        return context
    
    def form_valid(self, form):
        """Sobrescribir para crear clon en RepuestoEnStock al crear repuesto"""
        response = super().form_valid(form)
        
        # Crear clon en RepuestoEnStock
        try:
            from .views import clone_repuesto_to_stock
            clone_repuesto_to_stock(
                repuesto=self.object,
                deposito='bodega-principal',
                proveedor=''
            )
            self.request.session['repuesto_created'] = True
        except Exception as e:
            # Log del error pero no interrumpir el flujo
            print(f"Error creando clon en RepuestoEnStock: {e}")
        
        return response


class RepuestoUpdateView(UpdateView):
    model = Repuesto
    form_class = RepuestoForm
    template_name = "repuestos/repuesto_form.html"
    success_url = reverse_lazy("repuesto_list")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Obtener configuración del taller
        config = AdministracionTaller.get_configuracion_activa()
        context['config'] = config
        return context
    
    def form_valid(self, form):
        """Sobrescribir para sincronizar con RepuestoEnStock al actualizar repuesto"""
        response = super().form_valid(form)
        
        # Sincronizar con RepuestoEnStock
        try:
            from .views import clone_repuesto_to_stock
            clone_repuesto_to_stock(
                repuesto=self.object,
                deposito='bodega-principal',
                proveedor=''
            )
            self.request.session['repuesto_updated'] = True
        except Exception as e:
            # Log del error pero no interrumpir el flujo
            print(f"Error sincronizando con RepuestoEnStock: {e}")
        
        return response

class RepuestoDeleteView(DeleteView):
    model = Repuesto
    template_name = "repuestos/repuesto_confirm_delete.html"
    success_url = reverse_lazy("repuesto_list")

    def get(self, request, *args, **kwargs):
        """Si ver_avisos = False, eliminar directamente sin mostrar confirmación"""
        config = AdministracionTaller.get_configuracion_activa()
        if not config.ver_avisos:
            self.object = self.get_object()
            self.object.delete()
            if config.ver_mensajes:
                messages.success(request, "Repuesto eliminado exitosamente.")
            return redirect(self.success_url)
        return super().get(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        """Sobrescribir delete para controlar mensajes"""
        config = AdministracionTaller.get_configuracion_activa()
        self.object = self.get_object()
        self.object.delete()
        if config.ver_mensajes:
            messages.success(request, "Repuesto eliminado exitosamente.")
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Obtener configuración del taller
        config = AdministracionTaller.get_configuracion_activa()
        context['config'] = config
        return context


# ============================
# Seguimiento público por placa
# ============================

@require_http_methods(["GET"])
def tracking_publico(request):
    """Página pública con formulario simple para buscar por placa y ver avance.
    No requiere login. Si se pasa ?placa=... intenta mostrar el detalle.
    """
    placa = (request.GET.get("placa") or "").strip().upper()
    trabajo = None
    if placa:
        trabajo = (
            Trabajo.objects.select_related("vehiculo", "vehiculo__cliente")
            .prefetch_related("acciones", "repuestos", "fotos")
            .filter(vehiculo__placa__iexact=placa)
            .order_by("-fecha_inicio")
            .first()
        )
    return render(request, "car/tracking_publico.html", {"placa": placa, "trabajo": trabajo})

@require_http_methods(["GET"])
def tracking_publico_preview(request):
    """Devuelve un fragmento HTML del card de trabajo para insertar bajo el formulario."""
    placa = (request.GET.get("placa") or "").strip().upper()
    trabajo = None
    if placa:
        trabajo = (
            Trabajo.objects.select_related("vehiculo", "vehiculo__cliente")
            .prefetch_related("acciones", "repuestos", "fotos")
            .filter(vehiculo__placa__iexact=placa)
            .order_by("-fecha_inicio")
            .first()
        )
    html = render_to_string("car/_tracking_card.html", {"trabajo": trabajo}, request=request)
    return JsonResponse({"html": html, "found": bool(trabajo)})



# === Utilidad temporal: clonar Repuesto → RepuestoEnStock ===
def clone_repuesto_to_stock(repuesto: Repuesto, deposito: str = "bodega-principal", proveedor: str = "") -> RepuestoEnStock:
    """
    Crea o actualiza una fila en RepuestoEnStock para el `repuesto` dado.
    - depósito por defecto: "bodega-principal"
    - proveedor por defecto: "" (vacío)
    Copia: stock, precio_compra, precio_venta desde Repuesto.
    Retorna la instancia de RepuestoEnStock creada/actualizada.
    """
    from django.db import transaction
    
    with transaction.atomic():
        # Primero, eliminar cualquier registro duplicado existente
        registros_existentes = RepuestoEnStock.objects.filter(
            repuesto=repuesto,
            deposito=deposito
        )
        
        if registros_existentes.count() > 1:
            # Mantener solo el más reciente y eliminar los duplicados
            registro_principal = registros_existentes.order_by('-id').first()
            registros_duplicados = registros_existentes.exclude(id=registro_principal.id)
            registros_duplicados.delete()
        
        defaults = {
            "stock": repuesto.stock or 0,  # Usar el stock del repuesto, o 0 si es None
            "reservado": 0,
            "precio_compra": repuesto.precio_costo or 0,
            "precio_venta": repuesto.precio_venta or 0,
        }

        repstk, created = RepuestoEnStock.objects.get_or_create(
            repuesto=repuesto,
            deposito=deposito,
            proveedor=proveedor,
            defaults=defaults,
        )

        if not created:
            # Actualizar precios si han cambiado
            if repuesto.precio_costo is not None:
                repstk.precio_compra = repuesto.precio_costo
            if repuesto.precio_venta is not None:
                repstk.precio_venta = repuesto.precio_venta
            
            # SIEMPRE sincronizar el stock - esto es lo que queremos para simplificar
            if repuesto.stock is not None:
                repstk.stock = repuesto.stock
                
            repstk.save()

        return repstk


def sincronizar_stock_repuestos():
    """
    Función para sincronizar el stock de repuestos existentes que no tienen
    registro en RepuestoEnStock o que tienen stock diferente.
    """
    repuestos_sin_stock = Repuesto.objects.filter(stocks__isnull=True)
    repuestos_con_stock_diferente = []
    
    for repuesto in Repuesto.objects.all():
        if repuesto.stocks.exists():
            from django.db.models import Sum
            stock_total = repuesto.stocks.aggregate(total=Sum('stock'))['total'] or 0
            if repuesto.stock != stock_total:
                repuestos_con_stock_diferente.append(repuesto)
    
    print(f"Repuestos sin registro en RepuestoEnStock: {repuestos_sin_stock.count()}")
    print(f"Repuestos con stock desincronizado: {len(repuestos_con_stock_diferente)}")
    
    # Crear registros faltantes
    for repuesto in repuestos_sin_stock:
        if repuesto.stock and repuesto.stock > 0:
            clone_repuesto_to_stock(repuesto)
            print(f"Creado RepuestoEnStock para: {repuesto.nombre} (stock: {repuesto.stock})")
    
    # Sincronizar stocks diferentes
    for repuesto in repuestos_con_stock_diferente:
        stock_obj = repuesto.stocks.first()
        if stock_obj:
            stock_obj.stock = repuesto.stock
            stock_obj.save()
            print(f"Sincronizado stock para: {repuesto.nombre} (stock: {repuesto.stock})")


# === Vistas: crear/editar Repuesto clonando a RepuestoEnStock ===


@login_required
def administracion_taller(request):
    """Vista para configurar la administración del taller"""
    config = AdministracionTaller.get_configuracion_activa()
    
    if request.method == 'POST':
        form = AdministracionTallerForm(request.POST, request.FILES, instance=config)
        if form.is_valid():
            config = form.save(commit=False)
            config.creado_por = request.user
            config.save()
            if config.ver_mensajes:
                messages.success(request, "Configuración del taller actualizada correctamente.")
            return redirect('administracion_taller')
    else:
        form = AdministracionTallerForm(instance=config)
    
    context = {
        'form': form,
        'config': config,
    }
    return render(request, 'car/administracion_taller.html', context)


# ======================
# VISTAS PARA CLIENTE_TALLER
# ======================

class ClienteTallerListView(ListView):
    """Lista de clientes del taller con RUT como identificador único"""
    model = Cliente_Taller
    template_name = "car/cliente_taller_list.html"
    context_object_name = "clientes"
    paginate_by = 20

    def get_queryset(self):
        queryset = Cliente_Taller.objects.filter(activo=True)
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(nombre__icontains=search) | 
                Q(rut__icontains=search) | 
                Q(telefono__icontains=search)
            )
        return queryset.order_by('nombre')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Obtener configuración del taller
        config = AdministracionTaller.get_configuracion_activa()
        context['config'] = config
        return context


class ClienteTallerCreateView(CreateView):
    """Crear nuevo cliente del taller"""
    model = Cliente_Taller
    form_class = ClienteTallerForm
    template_name = "car/cliente_taller_form.html"
    success_url = reverse_lazy("cliente_taller_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Obtener configuración del taller
        config = AdministracionTaller.get_configuracion_activa()
        context['config'] = config
        return context

    def form_valid(self, form):
        # Asegurar que el cliente esté activo por defecto
        form.instance.activo = True
        config = AdministracionTaller.get_configuracion_activa()
        if config.ver_mensajes:
            messages.success(self.request, f"Cliente {form.instance.nombre} creado correctamente.")
        return super().form_valid(form)


class ClienteTallerUpdateView(UpdateView):
    """Editar cliente del taller existente"""
    model = Cliente_Taller
    form_class = ClienteTallerForm
    template_name = "car/cliente_taller_form.html"
    success_url = reverse_lazy("cliente_taller_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Obtener configuración del taller
        config = AdministracionTaller.get_configuracion_activa()
        context['config'] = config
        return context

    def form_valid(self, form):
        from .models import AdministracionTaller
        config = AdministracionTaller.get_configuracion_activa()
        if config.ver_mensajes:
            messages.success(self.request, f"Cliente {form.instance.nombre} actualizado correctamente.")
        return super().form_valid(form)


class ClienteTallerDeleteView(DeleteView):
    """Eliminar cliente del taller (soft delete)"""
    model = Cliente_Taller
    template_name = "car/cliente_taller_confirm_delete.html"
    success_url = reverse_lazy("cliente_taller_list")

    def get(self, request, *args, **kwargs):
        """Si ver_avisos = False, eliminar directamente sin mostrar confirmación"""
        config = AdministracionTaller.get_configuracion_activa()
        if not config.ver_avisos:
            cliente = self.get_object()
            cliente.activo = False
            cliente.save()
            if config.ver_mensajes:
                messages.success(request, f"Cliente {cliente.nombre} desactivado correctamente.")
            return redirect(self.success_url)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Obtener configuración del taller
        config = AdministracionTaller.get_configuracion_activa()
        context['config'] = config
        return context

    def delete(self, request, *args, **kwargs):
        config = AdministracionTaller.get_configuracion_activa()
        cliente = self.get_object()
        cliente.activo = False
        cliente.save()
        if config.ver_mensajes:
            messages.success(request, f"Cliente {cliente.nombre} desactivado correctamente.")
        return redirect(self.success_url)


@login_required
def cliente_taller_lookup(request):
    """API para búsqueda de clientes del taller (para AJAX)"""
    query = request.GET.get('q', '')
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    clientes = Cliente_Taller.objects.filter(
        activo=True
    ).filter(
        Q(nombre__icontains=query) | 
        Q(rut__icontains=query) | 
        Q(telefono__icontains=query)
    )[:10]
    
    results = []
    for cliente in clientes:
        results.append({
            'id': cliente.rut,
            'text': f"{cliente.nombre} ({cliente.rut})",
            'nombre': cliente.nombre,
            'rut': cliente.rut,
            'telefono': cliente.telefono or '',
        })
    
    return JsonResponse({'results': results})


@login_required
def vehiculos_por_cliente(request, cliente_rut):
    """Devuelve los vehículos asociados a un cliente del taller."""
    raw_rut = unquote(cliente_rut).strip()

    if not raw_rut:
        return JsonResponse({'error': 'Parámetro cliente_rut vacío'}, status=400)

    # Si el RUT termina en 'k' o 'K', buscar ambas variantes simultáneamente
    if raw_rut and raw_rut[-1].lower() == 'k':
        rut_minuscula = raw_rut[:-1] + 'k'
        rut_mayuscula = raw_rut[:-1] + 'K'
        
        # Buscar cliente usando Q object para buscar ambas variantes
        try:
            cliente = Cliente_Taller.objects.get(
                Q(rut=rut_minuscula) | Q(rut=rut_mayuscula)
            )
        except Cliente_Taller.DoesNotExist:
            # También intentar con la versión normalizada si es diferente
            rut_normalizado = normalizar_rut(raw_rut)
            if rut_normalizado not in [rut_minuscula, rut_mayuscula]:
                try:
                    cliente = Cliente_Taller.objects.get(rut=rut_normalizado)
                except Cliente_Taller.DoesNotExist:
                    variantes_intentadas = [raw_rut, rut_minuscula, rut_mayuscula, rut_normalizado]
                    return JsonResponse({
                        'error': f'Cliente no encontrado con RUT: {raw_rut}',
                        'variantes_intentadas': list(set(variantes_intentadas))
                    }, status=404)
            else:
                variantes_intentadas = [raw_rut, rut_minuscula, rut_mayuscula]
                return JsonResponse({
                    'error': f'Cliente no encontrado con RUT: {raw_rut}',
                    'variantes_intentadas': list(set(variantes_intentadas))
                }, status=404)
    else:
        # Si no termina en k/K, buscar directamente
        try:
            cliente = Cliente_Taller.objects.get(rut=raw_rut)
        except Cliente_Taller.DoesNotExist:
            return JsonResponse({'error': f'Cliente no encontrado con RUT: {raw_rut}'}, status=404)

    vehiculos = (
        Vehiculo.objects
        .filter(cliente=cliente)
        .order_by('placa')
    )

    data = [
        {
            'id': vehiculo.pk,
            'placa': (vehiculo.placa or '').strip(),
            'marca': (vehiculo.marca or '').strip(),
            'modelo': (vehiculo.modelo or '').strip(),
            'anio': vehiculo.anio or '',
            'descripcion_motor': (vehiculo.descripcion_motor or '').strip(),
        }
        for vehiculo in vehiculos
    ]

    return JsonResponse(data, safe=False)


@login_required
def selector_test_view(request):
    clientes = Cliente_Taller.objects.filter(activo=True).order_by('nombre')
    return render(request, 'car/selector_test.html', {'clientes': clientes})


# ========================
# FUNCIONES DE EXPORTACIÓN
# ========================

@login_required
def exportar_componentes_excel(request):
    """Exportar lista de componentes a Excel"""
    componentes = Componente.objects.filter(padre__isnull=True).order_by('padre__nombre', 'nombre')
    
    data = []
    for comp in componentes:
        data.append({
            'Código': comp.codigo or '',
            'Nombre': comp.nombre,
            'Estado': 'Activo' if comp.activo else 'Inactivo',
            'Familia': comp.padre.nombre if comp.padre else 'Principal',
            'Hijos': comp.hijos.count(),
        })
    
    df = pd.DataFrame(data)
    
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="componentes.xlsx"'
    
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Componentes', index=False)
    
    return response

@login_required
def exportar_componentes_pdf(request):
    """Exportar lista de componentes a PDF"""
    componentes = Componente.objects.filter(padre__isnull=True).order_by('padre__nombre', 'nombre')
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="componentes.pdf"'
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    
    # Título
    title = Paragraph("Lista de Componentes", styles['Title'])
    
    # Datos de la tabla
    data = [['Código', 'Nombre', 'Estado', 'Familia', 'Hijos']]
    
    for comp in componentes:
        data.append([
            comp.codigo or '',
            comp.nombre,
            'Activo' if comp.activo else 'Inactivo',
            comp.padre.nombre if comp.padre else 'Principal',
            str(comp.hijos.count())
        ])
    
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements = [title, Spacer(1, 12), table]
    doc.build(elements)
    
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    
    return response

@login_required
def exportar_acciones_excel(request):
    """Exportar lista de acciones a Excel"""
    acciones = Accion.objects.all().order_by('nombre')
    
    data = []
    for accion in acciones:
        data.append({
            'Nombre': accion.nombre,
            'ID': accion.id,
            'Usos': accion.componenteaccion_set.count(),
        })
    
    df = pd.DataFrame(data)
    
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="acciones.xlsx"'
    
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Acciones', index=False)
    
    return response

@login_required
def exportar_acciones_pdf(request):
    """Exportar lista de acciones a PDF"""
    acciones = Accion.objects.all().order_by('nombre')
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="acciones.pdf"'
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    
    # Título
    title = Paragraph("Lista de Acciones", styles['Title'])
    
    # Datos de la tabla
    data = [['Nombre', 'ID', 'Usos']]
    
    for accion in acciones:
        data.append([
            accion.nombre,
            str(accion.id),
            str(accion.componenteaccion_set.count())
        ])
    
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements = [title, Spacer(1, 12), table]
    doc.build(elements)
    
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    
    return response

@login_required
def exportar_precios_excel(request):
    """Exportar lista de precios (ComponenteAccion) a Excel"""
    items = ComponenteAccion.objects.select_related("componente", "accion").order_by("componente__padre__nombre", "componente__nombre", "accion__nombre")
    
    data = []
    for item in items:
        data.append({
            'Componente': item.componente.nombre,
            'Acción': item.accion.nombre,
            'Precio Mano de Obra': f"${item.precio_mano_obra:,.0f}" if item.precio_mano_obra else '$0',
            'Familia': item.componente.padre.nombre if item.componente.padre else 'Principal',
            'ID': item.id,
        })
    
    df = pd.DataFrame(data)
    
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="lista_precios.xlsx"'
    
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Lista de Precios', index=False)
    
    return response

@login_required
def exportar_precios_pdf(request):
    """Exportar lista de precios (ComponenteAccion) a PDF"""
    items = ComponenteAccion.objects.select_related("componente", "accion").order_by("componente__padre__nombre", "componente__nombre", "accion__nombre")
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="lista_precios.pdf"'
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    
    # Título
    title = Paragraph("Lista de Precios - Componentes y Acciones", styles['Title'])
    
    # Datos de la tabla
    data = [['Componente', 'Acción', 'Precio Mano de Obra', 'Familia']]
    
    for item in items:
        data.append([
            item.componente.nombre,
            item.accion.nombre,
            f"${item.precio_mano_obra:,.0f}" if item.precio_mano_obra else '$0',
            item.componente.padre.nombre if item.componente.padre else 'Principal'
        ])
    
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))
    
    elements = [title, Spacer(1, 12), table]
    doc.build(elements)
    
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    
    return response




@login_required
def repuesto_compatibilidad(request, pk):
    """Vista para gestionar la compatibilidad de un repuesto con vehículos"""
    repuesto = get_object_or_404(Repuesto, pk=pk)
    
    # Obtener aplicaciones existentes
    aplicaciones_existentes = RepuestoAplicacion.objects.filter(repuesto=repuesto).select_related("version")
    
    # Obtener todas las versiones de vehículos disponibles
    versiones_disponibles = VehiculoVersion.objects.all().order_by("marca", "modelo", "anio_desde")
    
    # Agrupar por marca
    marcas_data = {}
    marcas_count = {}
    for version in versiones_disponibles:
        marca = version.marca
        if marca not in marcas_data:
            marcas_data[marca] = []
            marcas_count[marca] = 0
        marcas_data[marca].append(version)
        marcas_count[marca] += 1
    
    # Ordenar marcas alfabéticamente y crear lista con conteos
    marcas_ordenadas = sorted(marcas_data.keys())
    marcas_con_conteos = [(marca, marcas_count[marca]) for marca in marcas_ordenadas]
    
    if request.method == "POST":
        # Procesar el formulario
        versiones_seleccionadas = request.POST.getlist("versiones")
        
        # Eliminar aplicaciones existentes
        RepuestoAplicacion.objects.filter(repuesto=repuesto).delete()
        
        # Crear nuevas aplicaciones
        for version_id in versiones_seleccionadas:
            try:
                version = VehiculoVersion.objects.get(id=version_id)
                posicion = request.POST.get(f"posicion_{version_id}", "")
                motor = request.POST.get(f"motor_{version_id}", "")
                carroceria = request.POST.get(f"carroceria_{version_id}", "")
                cilindrada = request.POST.get(f"cilindrada_{version_id}", "")
                nro_valvulas = request.POST.get(f"nro_valvulas_{version_id}", "")
                combustible = request.POST.get(f"combustible_{version_id}", "")
                otro_especial = request.POST.get(f"otro_especial_{version_id}", "")
                
                # Convertir nro_valvulas a entero si existe
                nro_valvulas_int = None
                if nro_valvulas:
                    try:
                        nro_valvulas_int = int(nro_valvulas)
                    except ValueError:
                        nro_valvulas_int = None
                
                RepuestoAplicacion.objects.create(
                    repuesto=repuesto,
                    version=version,
                    posicion=posicion,
                    motor=motor,
                    carroceria=carroceria,
                    cilindrada=cilindrada,
                    nro_valvulas=nro_valvulas_int,
                    combustible=combustible,
                    otro_especial=otro_especial
                )
            except VehiculoVersion.DoesNotExist:
                continue
        
        config = AdministracionTaller.get_configuracion_activa()
        if config.ver_mensajes:
            messages.success(request, f"Compatibilidad actualizada para {repuesto.nombre}")
        return redirect("repuesto_compatibilidad", pk=repuesto.pk)
    
    context = {
        "repuesto": repuesto,
        "aplicaciones_existentes": aplicaciones_existentes,
        "versiones_disponibles": versiones_disponibles,
        "marcas_data": marcas_data,
        "marcas_count": marcas_count,
        "marcas_ordenadas": marcas_ordenadas,
        "marcas_con_conteos": marcas_con_conteos,
    }
    
    return render(request, "repuestos/repuesto_compatibilidad.html", context)


# ========================
# GESTIÓN DE USUARIOS Y PERMISOS
# ========================

@login_required
@solo_administradores
def gestion_usuarios(request):
    """Vista para gestionar usuarios y sus permisos"""
    usuarios = User.objects.filter(mecanico__isnull=False).select_related('mecanico')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'crear_usuario':
            username = request.POST.get('username')
            password = request.POST.get('password')
            rol = request.POST.get('rol', 'mecanico')
            # Nuevos campos
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            email = request.POST.get('email', '').strip()
            especialidad = request.POST.get('especialidad', '').strip()
            
            if User.objects.filter(username=username).exists():
                messages.error(request, f"El usuario '{username}' ya existe")
            else:
                user = User.objects.create_user(
                    username=username, 
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    email=email
                )
                mecanico = Mecanico.objects.create(
                    user=user,
                    rol=rol,
                    especialidad=especialidad
                )
                config = AdministracionTaller.get_configuracion_activa()
                if config.ver_mensajes:
                    messages.success(request, f"✅ Usuario '{username}' creado como {mecanico.get_rol_display()}")
        
        elif action == 'editar_usuario':
            user_id = request.POST.get('user_id')
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            email = request.POST.get('email', '').strip()
            especialidad = request.POST.get('especialidad', '').strip()
            is_active = request.POST.get('is_active') == 'on'
            
            try:
                user = User.objects.get(id=user_id)
                user.first_name = first_name
                user.last_name = last_name
                user.email = email
                user.is_active = is_active
                user.save()
                
                # Actualizar especialidad del mecánico
                if hasattr(user, 'mecanico'):
                    user.mecanico.especialidad = especialidad
                    user.mecanico.save()
                
                config = AdministracionTaller.get_configuracion_activa()
                if config.ver_mensajes:
                    messages.success(request, f"✅ Información de '{user.username}' actualizada exitosamente")
            except User.DoesNotExist:
                config = AdministracionTaller.get_configuracion_activa()
                if config.ver_mensajes:
                    messages.error(request, "❌ Usuario no encontrado")
        
        elif action == 'cambiar_password':
            user_id = request.POST.get('user_id')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            
            try:
                if new_password != confirm_password:
                    messages.error(request, "❌ Las contraseñas no coinciden")
                elif len(new_password) < 4:
                    messages.error(request, "❌ La contraseña debe tener al menos 4 caracteres")
                else:
                    user = User.objects.get(id=user_id)
                    user.set_password(new_password)
                    user.save()
                    config = AdministracionTaller.get_configuracion_activa()
                    if config.ver_mensajes:
                        messages.success(request, f"✅ Contraseña de '{user.username}' cambiada exitosamente. Nueva contraseña: {new_password}")
            except User.DoesNotExist:
                config = AdministracionTaller.get_configuracion_activa()
                if config.ver_mensajes:
                    messages.error(request, "❌ Usuario no encontrado")
        
        elif action == 'cambiar_rol':
            user_id = request.POST.get('user_id')
            nuevo_rol = request.POST.get('nuevo_rol')
            
            try:
                user = User.objects.get(id=user_id)
                mecanico = user.mecanico
                mecanico.rol = nuevo_rol
                mecanico.save()
                config = AdministracionTaller.get_configuracion_activa()
                if config.ver_mensajes:
                    messages.success(request, f"✅ Rol de {user.username} cambiado a {mecanico.get_rol_display()}")
            except User.DoesNotExist:
                config = AdministracionTaller.get_configuracion_activa()
                if config.ver_mensajes:
                    messages.error(request, "❌ Usuario no encontrado")
        
        elif action == 'toggle_permiso':
            user_id = request.POST.get('user_id')
            permiso = request.POST.get('permiso')
            activo = request.POST.get('activo') == 'true'
            
            try:
                user = User.objects.get(id=user_id)
                mecanico = user.mecanico
                setattr(mecanico, permiso, activo)
                mecanico.save()
                config = AdministracionTaller.get_configuracion_activa()
                if config.ver_mensajes:
                    messages.success(request, f"✅ Permiso '{permiso}' {'activado' if activo else 'desactivado'} para {user.username}")
            except User.DoesNotExist:
                config = AdministracionTaller.get_configuracion_activa()
                if config.ver_mensajes:
                    messages.error(request, "❌ Usuario no encontrado")
        
        elif action == 'eliminar_usuario':
            config = AdministracionTaller.get_configuracion_activa()
            user_id = request.POST.get('user_id')
            
            try:
                user = User.objects.get(id=user_id)
                if user == request.user:
                    if config.ver_mensajes:
                        messages.error(request, "❌ No puedes eliminar tu propio usuario")
                else:
                    username = user.username
                    user.delete()
                    if config.ver_mensajes:
                        messages.success(request, f"✅ Usuario '{username}' eliminado exitosamente")
            except User.DoesNotExist:
                if config.ver_mensajes:
                    messages.error(request, "❌ Usuario no encontrado")
        
        return redirect('gestion_usuarios')
    
    # Obtener configuración del taller
    config = AdministracionTaller.get_configuracion_activa()
    
    # Estadísticas
    total_usuarios = usuarios.count()
    usuarios_activos = usuarios.filter(is_active=True).count()
    usuarios_inactivos = usuarios.filter(is_active=False).count()
    
    return render(request, 'car/gestion_usuarios.html', {
        'usuarios': usuarios,
        'roles_choices': Mecanico.ROLES_CHOICES,
        'config': config,
        'total_usuarios': total_usuarios,
        'usuarios_activos': usuarios_activos,
        'usuarios_inactivos': usuarios_inactivos,
    })


@login_required
@solo_administradores
def crear_usuario_rapido(request):
    """API para crear usuarios rápidamente"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        rol = request.POST.get('rol', 'mecanico')
        
        if User.objects.filter(username=username).exists():
            return JsonResponse({'error': f'El usuario "{username}" ya existe'}, status=400)
        
        try:
            user = User.objects.create_user(username=username, password=password)
            mecanico = Mecanico.objects.create(user=user, rol=rol)
            
            return JsonResponse({
                'success': True,
                'message': f'Usuario "{username}" creado como {mecanico.get_rol_display()}',
                'usuario': {
                    'id': user.id,
                    'username': user.username,
                    'rol': mecanico.rol,
                    'rol_display': mecanico.get_rol_display()
                }
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)


@login_required
@solo_administradores
def toggle_permiso_usuario(request):
    """API para activar/desactivar permisos de usuarios"""
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        permiso = request.POST.get('permiso')
        activo = request.POST.get('activo') == 'true'
        
        try:
            user = User.objects.get(id=user_id)
            mecanico = user.mecanico
            setattr(mecanico, permiso, activo)
            mecanico.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Permiso "{permiso}" {"activado" if activo else "desactivado"} para {user.username}'
            })
        except User.DoesNotExist:
            return JsonResponse({'error': 'Usuario no encontrado'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)


@login_required
def repuesto_compatibilidad_api(request, repuesto_id):
    """API para obtener vehículos compatibles de un repuesto"""
    try:
        repuesto = Repuesto.objects.get(id=repuesto_id)
        
        # 1. Obtener aplicaciones específicas (compatibilidad directa)
        aplicaciones = RepuestoAplicacion.objects.filter(repuesto=repuesto).select_related('version')
        vehiculos_directos = []
        for aplicacion in aplicaciones:
            vehiculos_directos.append({
                'marca': aplicacion.version.marca,
                'modelo': aplicacion.version.modelo,
                'anio_desde': aplicacion.version.anio_desde,
                'anio_hasta': aplicacion.version.anio_hasta,
                'motor': aplicacion.motor or aplicacion.version.motor or '',
                'carroceria': aplicacion.carroceria or aplicacion.version.carroceria or '',
                'posicion': aplicacion.posicion or '',
                'tipo': 'directo'
            })
        
        # 2. Buscar coincidencias por motor y carrocería del repuesto
        vehiculos_coincidencias = []
        
        # Si el repuesto tiene motor, buscar vehículos con ese motor
        if repuesto.tipo_de_motor and repuesto.tipo_de_motor.strip() and repuesto.tipo_de_motor != 'zzzzzz':
            vehiculos_motor = VehiculoVersion.objects.filter(
                motor__icontains=repuesto.tipo_de_motor
            ).exclude(
                id__in=[a.version.id for a in aplicaciones]
            )
            for vehiculo in vehiculos_motor:
                vehiculos_coincidencias.append({
                    'marca': vehiculo.marca,
                    'modelo': vehiculo.modelo,
                    'anio_desde': vehiculo.anio_desde,
                    'anio_hasta': vehiculo.anio_hasta,
                    'motor': vehiculo.motor or '',
                    'carroceria': vehiculo.carroceria or '',
                    'posicion': '',
                    'tipo': 'coincidencia_motor'
                })
        
        # Si el repuesto tiene carrocería, buscar vehículos con esa carrocería
        if repuesto.carroceria and repuesto.carroceria.strip() and repuesto.carroceria != 'yyyyyy':
            vehiculos_carroceria = VehiculoVersion.objects.filter(
                carroceria__icontains=repuesto.carroceria
            ).exclude(
                id__in=[a.version.id for a in aplicaciones]
            )
            for vehiculo in vehiculos_carroceria:
                vehiculos_coincidencias.append({
                    'marca': vehiculo.marca,
                    'modelo': vehiculo.modelo,
                    'anio_desde': vehiculo.anio_desde,
                    'anio_hasta': vehiculo.anio_hasta,
                    'motor': vehiculo.motor or '',
                    'carroceria': vehiculo.carroceria or '',
                    'posicion': '',
                    'tipo': 'coincidencia_carroceria'
                })
        
        # Combinar todos los vehículos
        vehiculos = vehiculos_directos + vehiculos_coincidencias
        
        return JsonResponse({
            'success': True,
            'repuesto': {
                'id': repuesto.id,
                'nombre': repuesto.nombre,
                'sku': repuesto.sku or '',
                'tipo_motor': repuesto.tipo_de_motor or '',
                'carroceria': repuesto.carroceria or ''
            },
            'vehiculos': vehiculos
        })
        
    except Repuesto.DoesNotExist:
        return JsonResponse({'error': 'Repuesto no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ========================
# REPUESTOS EXTERNOS
# ========================

@login_required
def buscar_repuestos_externos_json(request):
    """
    Busca repuestos externos (referencias) para mostrar junto a los del inventario
    """
    from .models import RepuestoExterno
    from django.db.models import Q
    
    termino = request.GET.get('termino', '').strip()
    
    if not termino or len(termino) < 2:
        return JsonResponse({'repuestos': []})
    
    # Buscar en repuestos externos activos
    repuestos_externos = RepuestoExterno.objects.filter(
        activo=True
    ).filter(
        Q(nombre__icontains=termino) |
        Q(marca__icontains=termino) |
        Q(codigo_proveedor__icontains=termino) |
        Q(descripcion__icontains=termino)
    )[:10]
    
    resultados = []
    for rep in repuestos_externos:
        proveedor_display = rep.get_proveedor_display() if rep.proveedor != 'otro' else rep.proveedor_nombre
        resultados.append({
            'id': rep.id,
            'nombre': rep.nombre,
            'proveedor': proveedor_display,
            'precio': int(rep.precio_referencial),
            'marca': rep.marca or '',
            'codigo': rep.codigo_proveedor or '',
            'url': rep.get_url_busqueda(),
            'es_externo': True
        })
    
    return JsonResponse({'repuestos': resultados})


@login_required
def agregar_repuesto_externo(request):
    """
    Vista para agregar una referencia de repuesto externo
    """
    from .models import RepuestoExterno
    
    if request.method == 'POST':
        try:
            nombre = request.POST.get('nombre', '').strip()
            proveedor = request.POST.get('proveedor', 'otro')
            proveedor_nombre = request.POST.get('proveedor_nombre', '').strip()
            codigo_proveedor = request.POST.get('codigo_proveedor', '').strip()
            precio_referencial = request.POST.get('precio_referencial', '0')
            url_producto = request.POST.get('url_producto', '').strip()
            descripcion = request.POST.get('descripcion', '').strip()
            marca = request.POST.get('marca', '').strip()
            
            if not nombre:
                return JsonResponse({'success': False, 'error': 'El nombre es obligatorio'}, status=400)
            
            # Convertir precio
            try:
                precio = Decimal(precio_referencial)
            except:
                precio = Decimal('0')
            
            # Crear repuesto externo
            repuesto = RepuestoExterno.objects.create(
                nombre=nombre,
                proveedor=proveedor,
                proveedor_nombre=proveedor_nombre if proveedor == 'otro' else None,
                codigo_proveedor=codigo_proveedor,
                precio_referencial=precio,
                url_producto=url_producto if url_producto else None,
                descripcion=descripcion,
                marca=marca,
                creado_por=request.user
            )
            
            return JsonResponse({
                'success': True,
                'repuesto': {
                    'id': repuesto.id,
                    'nombre': repuesto.nombre,
                    'proveedor': repuesto.get_proveedor_display() if repuesto.proveedor != 'otro' else repuesto.proveedor_nombre,
                    'precio': int(repuesto.precio_referencial),
                    'url': repuesto.get_url_busqueda()
                }
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)


@login_required
def agregar_repuesto_externo_rapido(request):
    """
    Vista que recibe datos del bookmarklet y muestra un formulario pre-llenado
    """
    from .models import RepuestoExterno
    
    # Obtener datos de query params (enviados por el bookmarklet)
    datos_bookmarklet = {
        'nombre': request.GET.get('nombre', ''),
        'precio': request.GET.get('precio', '0'),
        'marca': request.GET.get('marca', ''),
        'codigo': request.GET.get('codigo', ''),
        'proveedor': request.GET.get('proveedor', 'otro'),
        'url_producto': request.GET.get('url_producto', ''),
    }
    
    if request.method == 'POST':
        # Guardar la referencia
        try:
            nombre = request.POST.get('nombre', '').strip()
            proveedor = request.POST.get('proveedor', 'otro')
            proveedor_nombre = request.POST.get('proveedor_nombre', '').strip()
            codigo_proveedor = request.POST.get('codigo_proveedor', '').strip()
            precio_referencial = request.POST.get('precio_referencial', '0')
            url_producto = request.POST.get('url_producto', '').strip()
            descripcion = request.POST.get('descripcion', '').strip()
            marca = request.POST.get('marca', '').strip()
            
            if not nombre:
                messages.error(request, 'El nombre es obligatorio')
                return render(request, 'car/agregar_repuesto_externo_rapido.html', {'datos': datos_bookmarklet})
            
            # Convertir precio
            try:
                precio = Decimal(precio_referencial)
            except:
                precio = Decimal('0')
            
            # Crear repuesto externo
            repuesto = RepuestoExterno.objects.create(
                nombre=nombre,
                proveedor=proveedor,
                proveedor_nombre=proveedor_nombre if proveedor == 'otro' else None,
                codigo_proveedor=codigo_proveedor,
                precio_referencial=precio,
                url_producto=url_producto if url_producto else None,
                descripcion=descripcion,
                marca=marca,
                creado_por=request.user
            )
            
            config = AdministracionTaller.get_configuracion_activa()
            if config.ver_mensajes:
                messages.success(request, f'✅ Referencia guardada: {repuesto.nombre}')
            return redirect('panel_principal')
            
        except Exception as e:
            config = AdministracionTaller.get_configuracion_activa()
            if config.ver_mensajes:
                messages.error(request, f'Error al guardar: {str(e)}')
    
    return render(request, 'car/agregar_repuesto_externo_rapido.html', {'datos': datos_bookmarklet})


@login_required
def bookmarklet_info(request):
    """
    Página de información del bookmarklet
    """
    return render(request, 'car/bookmarklet_repuestos.html')

