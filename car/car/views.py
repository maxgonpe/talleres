from decimal import Decimal,InvalidOperation
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
            try:
                cliente = Cliente_Taller.objects.get(rut=cliente_id)
                selected_cliente = cliente.rut
            except Cliente_Taller.DoesNotExist:
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

                        if not diagnostico.componentes.filter(id=comp_id).exists():
                            continue  # ignora acciones de componentes no seleccionados

                        dca = DiagnosticoComponenteAccion(
                            diagnostico=diagnostico,
                            componente_id=comp_id,
                            accion_id=acc_id,
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
            # 🔹 Repuestos seleccionados desde hidden JSON
            repuestos_json = (request.POST.get("repuestos_json") or "").strip()
            print("1 Antesss")
            print("2 DEBUG repuestos_json:", repr(repuestos_json))
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
                            print("DEBUG repuestos_json:", repr(repuestos_json))
                        except (ValueError, Repuesto.DoesNotExist, KeyError):
                            continue
                except json.JSONDecodeError:
                    print("3 pasando por el pass")
                    print("4 DEBUG repuestos_json:", repr(repuestos_json))
                    pass
            print("5 DEBUG repuestos_json:", repr(repuestos_json))
# ====================================================

            # ====================================================

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

    return render(request, 'car/ingreso.html', {
        'cliente_form': cliente_form,
        'vehiculo_form': vehiculo_form,
        'config': config,
        'diagnostico_form': diagnostico_form,
        'clientes_existentes': clientes_existentes,
        'vehiculos_existentes': vehiculos_existentes,
        'selected_cliente': selected_cliente,
        'selected_vehiculo': selected_vehiculo,
        'componentes': Componente.objects.filter(padre__isnull=True, activo=True),
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
    diag = get_object_or_404(Diagnostico, pk=pk)
    diag.delete()
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
                form.save()
                messages.success(request, 'Componente creado correctamente.')
                return redirect('componente_list')
            except (ValidationError, IntegrityError) as e:
                # Muestra el error en el form sin 500
                #form.add_error(None, getattr(e, 'message', str(e)))
                messages.error(request, 'El componente ya existe. Por favor, use un nombre o código diferente.')
        else:
            # Manejar errores de validación del formulario
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
    if request.method == 'POST':
        componente.delete()
        messages.success(request, 'Componente eliminado.')
        return redirect('componente_list')
    return render(request, 'car/componentes_confirm_delete.html', {
        'componente': componente
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
    vehiculos = Vehiculo.objects.filter(cliente__rut=cliente_id).order_by('placa')
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
    return JsonResponse(data, safe=False)

@login_required
@requiere_permiso('diagnosticos')
def lista_diagnosticos(request):
    # Obtener configuración del taller
    config = AdministracionTaller.get_configuracion_activa()
    
    diagnosticos = Diagnostico.objects.all().select_related(
        'vehiculo__cliente'
    ).prefetch_related(
        'componentes',
        'acciones_componentes__accion',
        'acciones_componentes__componente',
        'repuestos'
    ).order_by('-fecha')

    # Agregar campos calculados manualmente
    for diag in diagnosticos:
        diag.total_mano_obra = sum(dca.precio_mano_obra or 0 for dca in diag.acciones_componentes.all())
        diag.total_repuestos = sum(dr.subtotal or (dr.cantidad * (dr.precio_unitario or 0)) for dr in diag.repuestos.all())
        diag.total_presupuesto = diag.total_mano_obra + diag.total_repuestos

    return render(request, 'car/diagnostico_lista.html', {
        'diagnosticos': diagnosticos,
        'config': config
    })

@login_required
def eliminar_diagnostico(request, pk):
    diagnostico = get_object_or_404(Diagnostico, pk=pk)
    if request.method == 'POST':

        diagnostico.delete()
        
        return redirect('lista_diagnosticos')
    # Obtener configuración del taller
    config = AdministracionTaller.get_configuracion_activa()
    
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
            "accion_id": ca.accion_id,
            "accion_nombre": ca.accion.nombre,
            "precio_base": str(ca.precio_mano_obra),
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
            form.save()
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
    if request.method == "POST":
        accion.delete()
        messages.success(request, "Acción eliminada.")
        return redirect("accion_list")
    # Obtener configuración del taller
    config = AdministracionTaller.get_configuracion_activa()
    
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
        if form.is_valid():
            form.save()
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
    if request.method == "POST":
        obj.delete()
        messages.success(request, "Registro eliminado.")
        return redirect("comp_accion_list")
    # Obtener configuración del taller
    config = AdministracionTaller.get_configuracion_activa()
    
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
        version = VehiculoVersion.objects.filter(
            marca__iexact=veh_marca.strip(),
            modelo__iexact=veh_modelo.strip(),
            anio_desde__lte=veh_anio,
            anio_hasta__gte=veh_anio
        ).first()
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
    veh_motor = None

    # MODO "DIAGNÓSTICO GUARDADO"
    if diagnostico_id:
        diag = get_object_or_404(Diagnostico, pk=diagnostico_id)
        veh = diag.vehiculo
        veh_marca, veh_modelo, veh_anio = veh.marca, veh.modelo, veh.anio
        veh_motor = veh.descripcion_motor  # Campo del motor del vehículo
        componentes_ids = list(diag.componentes.values_list('id', flat=True))

    # MODO "PREVIEW" (sin guardar)
    else:
        componentes_ids = request.GET.getlist("componentes_ids", [])
        veh_marca = (request.GET.get("marca") or "").strip()
        veh_modelo = (request.GET.get("modelo") or "").strip()
        veh_anio_raw = (request.GET.get("anio") or "").strip()
        veh_motor = (request.GET.get("motor") or "").strip()
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
    if veh_marca or veh_motor:
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
    diag = get_object_or_404(Diagnostico, pk=pk)

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="diagnostico_{diag.pk}.pdf"'

    doc = SimpleDocTemplate(response, pagesize=A4)
    styles = getSampleStyleSheet()
    # Define un nuevo estilo para el texto rojo
    red_text_style = ParagraphStyle(
    name='RedText',
    fontName='Helvetica',
    fontSize=10,
    textColor=colors.red,  # Cambia el color a rojo
    
)
    elements = []

    elements.append(Paragraph(f"<b>Diagnóstico #{diag.pk}</b>", styles["Title"]))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"<b>Fecha:</b> {diag.fecha.strftime('%d-%m-%Y')}", styles["Normal"]))
    elements.append(Paragraph(f"<b>Cliente:</b> {diag.vehiculo.cliente.nombre}", styles["Normal"]))
    elements.append(Paragraph(f"<b>Vehículo:</b> {diag.vehiculo}", styles["Normal"]))
    elements.append(Paragraph(f"<b>VIN:</b> {diag.vehiculo.vin}", red_text_style))
    elements.append(Paragraph(f"<b>Descripción:</b> {diag.descripcion_problema}", styles["Normal"]))
    elements.append(Spacer(1, 12))

    # Tabla de Acciones
    acciones_data = [["Mano de Obra", "Precio"]]
    total_mo = 0
    for dca in diag.acciones_componentes.all():
        acciones_data.append([f"{dca.componente.nombre} — {dca.accion.nombre}", f"${dca.precio_mano_obra or 0:,}"])
        total_mo += dca.precio_mano_obra or 0
    acciones_data.append(["Total Mano de Obra", f"${total_mo:,}"])

    acciones_table = Table(acciones_data, colWidths=[290, 100])  # Ajustar colWidths
    acciones_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('SIZE', (0, 0), (-1, 0), 14),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(acciones_table)
    elements.append(Spacer(1, 12))

    # Tabla de Repuestos
    repuestos_data = [["Repuesto", "Cantidad", "Unitario", "Precio"]]
    total_rep = 0
    for dr in diag.repuestos.all():
        subtotal = dr.subtotal or (dr.cantidad * (dr.precio_unitario or 0))
        repuestos_data.append([dr.repuesto.nombre, dr.cantidad, f"${dr.precio_unitario:,}", f"${subtotal:,}"])
        total_rep += subtotal
    repuestos_data.append(["Total Repuestos", "", "", f"${total_rep:,}"])

    repuestos_table = Table(repuestos_data, colWidths=[150, 70, 70, 100])  # Ajustar colWidths
    repuestos_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('SIZE', (0, 0), (-1, 0), 14),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(repuestos_table)
    elements.append(Spacer(1, 12))

    # Total Presupuesto
    total_presupuesto = total_mo + total_rep
    elements.append(Paragraph(f"<b>TOTAL PRESUPUESTO: ${total_presupuesto:,}</b>", styles["Heading2"]))

    doc.build(elements)
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
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Obtener configuración del taller
        config = AdministracionTaller.get_configuracion_activa()
        context['config'] = config
        return context

@login_required
def aprobar_diagnostico(request, pk):
    diagnostico = get_object_or_404(Diagnostico, pk=pk)

    if diagnostico.estado != "aprobado":
        trabajo = diagnostico.aprobar_y_clonar()
        messages.success(request, f"✅ Diagnóstico aprobado y trabajo #{trabajo.id} creado.")
    else:
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
    
    trabajos = Trabajo.objects.all().select_related(
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
            messages.success(request, "Observaciones guardadas.")
            return redirect("trabajo_detalle", pk=trabajo.pk)

        # 🔹 Asignar mecánicos
        elif "asignar_mecanicos" in request.POST:
            asignar_form = AsignarMecanicosForm(request.POST, instance=trabajo)
            if asignar_form.is_valid():
                trabajo = asignar_form.save(commit=False)
                if trabajo.estado == "iniciado":
                    trabajo.estado = "trabajando"
                    trabajo.fecha_inicio = timezone.now()
                trabajo.save()
                asignar_form.save_m2m()
                messages.success(request, "Mecánicos asignados y trabajo iniciado.")
                return redirect("trabajo_detalle", pk=trabajo.pk)

        # 🔹 Agregar acción (método tradicional)
        elif "agregar_accion" in request.POST:
            componente_id = request.POST.get("componente")
            accion_id = request.POST.get("accion")
            precio_mano_obra = request.POST.get("precio_mano_obra", 0)
            
            if componente_id and accion_id:
                try:
                    componente = Componente.objects.get(id=componente_id)
                    accion = Accion.objects.get(id=accion_id)
                    
                    TrabajoAccion.objects.create(
                        trabajo=trabajo,
                        componente=componente,
                        accion=accion,
                        precio_mano_obra=precio_mano_obra or 0
                    )
                    messages.success(request, "Acción agregada al trabajo.")
                except (Componente.DoesNotExist, Accion.DoesNotExist):
                    messages.error(request, "Error al agregar la acción.")
            return redirect_with_tab("acciones")

        # 🔹 Agregar múltiples acciones (nuevo método)
        elif "agregar_acciones_multiples" in request.POST:
            import json
            acciones_json = request.POST.get("acciones_json", "")
            
            print(f"DEBUG: acciones_json recibido: {acciones_json}")
            
            if acciones_json:
                try:
                    acciones_data = json.loads(acciones_json)
                    print(f"DEBUG: acciones_data parseado: {acciones_data}")
                    acciones_creadas = 0
                    
                    for accion_data in acciones_data:
                        try:
                            componente_id = int(accion_data.get("componente_id"))
                            accion_id = int(accion_data.get("accion_id"))
                            precio_mano_obra = accion_data.get("precio", "0")
                            
                            print(f"DEBUG: Procesando - componente_id: {componente_id}, accion_id: {accion_id}, precio: {precio_mano_obra}")
                            
                            componente = Componente.objects.get(id=componente_id)
                            accion = Accion.objects.get(id=accion_id)
                            
                            # Verificar si ya existe esta combinación
                            if not TrabajoAccion.objects.filter(
                                trabajo=trabajo,
                                componente=componente,
                                accion=accion
                            ).exists():
                                TrabajoAccion.objects.create(
                                    trabajo=trabajo,
                                    componente=componente,
                                    accion=accion,
                                    precio_mano_obra=precio_mano_obra or 0
                                )
                                acciones_creadas += 1
                                print(f"DEBUG: Acción creada exitosamente")
                            else:
                                print(f"DEBUG: Acción ya existe, saltando")
                                
                        except (ValueError, Componente.DoesNotExist, Accion.DoesNotExist) as e:
                            print(f"DEBUG: Error en acción individual: {str(e)}")
                            continue
                    
                    if acciones_creadas > 0:
                        messages.success(request, f"{acciones_creadas} acción(es) agregada(s) al trabajo.")
                    else:
                        messages.info(request, "No se agregaron acciones nuevas (posiblemente ya existían).")
                        
                except json.JSONDecodeError as e:
                    print(f"DEBUG: Error JSON: {str(e)}")
                    messages.error(request, f"Error al procesar las acciones: {str(e)}")
                except Exception as e:
                    print(f"DEBUG: Error general: {str(e)}")
                    messages.error(request, f"Error al agregar las acciones: {str(e)}")
            else:
                print("DEBUG: No se recibió acciones_json")
                messages.error(request, "No se recibieron acciones para agregar.")
            
            return redirect_with_tab("acciones")

        # 🔹 Toggle acción completada / pendiente
        elif "toggle_accion" in request.POST:
            accion_id = request.POST.get("accion_id")
            try:
                accion = TrabajoAccion.objects.get(id=accion_id, trabajo=trabajo)
                accion.completado = not accion.completado
                accion.save()
                messages.success(request, f"Acción marcada como {'completada' if accion.completado else 'pendiente'}.")
            except TrabajoAccion.DoesNotExist:
                messages.error(request, "Acción no encontrada.")
            return redirect_with_tab("acciones")

        # 🔹 Eliminar acción
        elif "eliminar_accion" in request.POST:
            accion_id = request.POST.get("accion_id")
            try:
                accion = TrabajoAccion.objects.get(id=accion_id, trabajo=trabajo)
                accion.delete()
                messages.success(request, "Acción eliminada.")
            except TrabajoAccion.DoesNotExist:
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
                    messages.success(request, "Repuesto agregado al trabajo.")
                except Repuesto.DoesNotExist:
                    messages.error(request, "Repuesto no encontrado.")
            return redirect_with_tab("repuestos")

        # 🔹 Toggle repuesto completado / pendiente
        elif "toggle_repuesto" in request.POST:
            repuesto_id = request.POST.get("repuesto_id")
            try:
                repuesto = TrabajoRepuesto.objects.get(id=repuesto_id, trabajo=trabajo)
                repuesto.completado = not repuesto.completado
                repuesto.save()
                messages.success(request, f"Repuesto marcado como {'completado' if repuesto.completado else 'pendiente'}.")
            except TrabajoRepuesto.DoesNotExist:
                messages.error(request, "Repuesto no encontrado.")
            return redirect_with_tab("repuestos")

        # 🔹 Eliminar repuesto
        elif "eliminar_repuesto" in request.POST:
            repuesto_id = request.POST.get("repuesto_id")
            try:
                repuesto = TrabajoRepuesto.objects.get(id=repuesto_id, trabajo=trabajo)
                repuesto.delete()
                messages.success(request, "Repuesto eliminado.")
            except TrabajoRepuesto.DoesNotExist:
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
                    
                    if repuestos_creados > 0:
                        messages.success(request, f"{repuestos_creados} repuesto(s) agregado(s) al trabajo.")
                    else:
                        messages.info(request, "No se agregaron repuestos nuevos (posiblemente ya existían).")
                        
                except json.JSONDecodeError as e:
                    print(f"DEBUG: Error JSON: {str(e)}")
                    messages.error(request, f"Error al procesar los repuestos: {str(e)}")
                except Exception as e:
                    print(f"DEBUG: Error general: {str(e)}")
                    messages.error(request, f"Error al agregar los repuestos: {str(e)}")
            else:
                print("DEBUG: No se recibió repuestos_json")
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
                        messages.success(request, f"{insumos_creados} insumo(s) agregado(s) al trabajo.")
                    else:
                        messages.info(request, "No se agregaron insumos nuevos (posiblemente ya existían).")
                        
                except json.JSONDecodeError as e:
                    print(f"DEBUG: Error JSON: {str(e)}")
                    messages.error(request, f"Error al procesar los insumos: {str(e)}")
                except Exception as e:
                    print(f"DEBUG: Error general: {str(e)}")
                    messages.error(request, f"Error al agregar los insumos: {str(e)}")
            else:
                print("DEBUG: No se recibió insumos_json")
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
                messages.success(request, "Foto subida con éxito.")
                return redirect_with_tab("fotos")

        # 🔹 Eliminar foto
        elif "eliminar_foto" in request.POST:
            foto_id = request.POST.get("eliminar_foto")
            try:
                foto = TrabajoFoto.objects.get(id=foto_id, trabajo=trabajo)
                foto.delete()
                messages.success(request, "Foto eliminada.")
            except TrabajoFoto.DoesNotExist:
                messages.error(request, "Foto no encontrada.")
            return redirect_with_tab("fotos")

        # 🔹 Cambiar estado del trabajo
        elif "cambiar_estado" in request.POST:
            nuevo_estado = request.POST.get("cambiar_estado")
            if nuevo_estado in dict(Trabajo.ESTADOS).keys():
                trabajo.estado = nuevo_estado
                if nuevo_estado == "trabajando" and not trabajo.fecha_inicio:
                    trabajo.fecha_inicio = timezone.now()
                if nuevo_estado in ["completado", "entregado"]:
                    trabajo.fecha_fin = timezone.now()
                else:
                    trabajo.fecha_fin = None
                trabajo.save()
                messages.success(request, f"Trabajo actualizado a {trabajo.get_estado_display()}.")
            return redirect_with_tab("estado")

        # 🔹 Toggle acción completada / pendiente (método anterior)
        elif "accion_toggle" in request.POST:
            accion_id = request.POST.get("accion_toggle")
            accion = get_object_or_404(TrabajoAccion, id=accion_id, trabajo=trabajo)
            accion.completado = not accion.completado
            accion.fecha = timezone.now() if accion.completado else None
            accion.save()
            messages.success(request, f"Acción '{accion.accion.nombre}' actualizada.")
            return redirect("trabajo_detalle", pk=trabajo.pk)

        # 🔹 Toggle repuesto instalado / pendiente
        elif "repuesto_toggle" in request.POST:
            rep_id = request.POST.get("repuesto_toggle")
            rep = get_object_or_404(TrabajoRepuesto, id=rep_id, trabajo=trabajo)
            rep.completado = not rep.completado
            rep.fecha = timezone.now() if rep.completado else None
            rep.save()
            messages.success(request, f"Repuesto '{rep.repuesto.nombre}' actualizado.")
            return redirect("trabajo_detalle", pk=trabajo.pk)

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
    }
    return render(request, "car/trabajo_detalle_nuevo.html", context)


@login_required
def trabajo_pdf(request, pk):
    """Generar PDF del estado del trabajo"""
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
        context = {
            'trabajo': trabajo,
            'request': request,  # Para generar URLs absolutas
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
        response['Content-Disposition'] = f'inline; filename="trabajo_{trabajo.id}_estado.pdf"'
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
        response['Content-Disposition'] = f'attachment; filename="trabajo_{trabajo.id}_estado.txt"'
        
        content = f"""
ESTADO DEL TRABAJO #{trabajo.id}
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

    context = {
        "iniciados": trabajos.filter(estado="iniciado"),
        "trabajando": trabajos.filter(estado="trabajando"),
        "completados": trabajos.filter(estado="completado"),
        "entregados": trabajos.filter(estado="entregado"),
        "config": config,
    }
    return render(request, "car/pizarra_page.html", context)

@login_required
def panel_principal(request):
    """Vista principal que incluye todo el contenido del dashboard"""
    # Obtener configuración del taller
    config = AdministracionTaller.get_configuracion_activa()
    
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
    
    
    # Estadísticas de trabajos
    trabajos = Trabajo.objects.select_related("vehiculo", "vehiculo__cliente")
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
            messages.error(request, "No hay productos en la venta.")
        elif not form.is_valid():
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
    """Buscar insumos para la pestaña de insumos en trabajos - Búsqueda amplia sin filtros"""
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
        messages.success(self.request, f"Cliente {form.instance.nombre} actualizado correctamente.")
        return super().form_valid(form)


class ClienteTallerDeleteView(DeleteView):
    """Eliminar cliente del taller (soft delete)"""
    model = Cliente_Taller
    template_name = "car/cliente_taller_confirm_delete.html"
    success_url = reverse_lazy("cliente_taller_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Obtener configuración del taller
        config = AdministracionTaller.get_configuracion_activa()
        context['config'] = config
        return context

    def delete(self, request, *args, **kwargs):
        cliente = self.get_object()
        cliente.activo = False
        cliente.save()
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
                RepuestoAplicacion.objects.create(
                    repuesto=repuesto,
                    version=version,
                    posicion=posicion,
                    motor=motor,
                    carroceria=carroceria
                )
            except VehiculoVersion.DoesNotExist:
                continue
        
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
            
            if User.objects.filter(username=username).exists():
                messages.error(request, f"El usuario '{username}' ya existe")
            else:
                user = User.objects.create_user(username=username, password=password)
                mecanico = Mecanico.objects.create(
                    user=user,
                    rol=rol
                )
                messages.success(request, f"Usuario '{username}' creado como {mecanico.get_rol_display()}")
        
        elif action == 'cambiar_rol':
            user_id = request.POST.get('user_id')
            nuevo_rol = request.POST.get('nuevo_rol')
            
            try:
                user = User.objects.get(id=user_id)
                mecanico = user.mecanico
                mecanico.rol = nuevo_rol
                mecanico.save()
                messages.success(request, f"Rol de {user.username} cambiado a {mecanico.get_rol_display()}")
            except User.DoesNotExist:
                messages.error(request, "Usuario no encontrado")
        
        elif action == 'toggle_permiso':
            user_id = request.POST.get('user_id')
            permiso = request.POST.get('permiso')
            activo = request.POST.get('activo') == 'true'
            
            try:
                user = User.objects.get(id=user_id)
                mecanico = user.mecanico
                setattr(mecanico, permiso, activo)
                mecanico.save()
                messages.success(request, f"Permiso '{permiso}' {'activado' if activo else 'desactivado'} para {user.username}")
            except User.DoesNotExist:
                messages.error(request, "Usuario no encontrado")
        
        elif action == 'eliminar_usuario':
            user_id = request.POST.get('user_id')
            
            try:
                user = User.objects.get(id=user_id)
                if user == request.user:
                    messages.error(request, "No puedes eliminar tu propio usuario")
                else:
                    username = user.username
                    user.delete()
                    messages.success(request, f"Usuario '{username}' eliminado")
            except User.DoesNotExist:
                messages.error(request, "Usuario no encontrado")
        
        return redirect('gestion_usuarios')
    
    # Obtener configuración del taller
    config = AdministracionTaller.get_configuracion_activa()
    
    return render(request, 'car/gestion_usuarios.html', {
        'usuarios': usuarios,
        'roles_choices': Mecanico.ROLES_CHOICES,
        'config': config,
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

