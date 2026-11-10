"""Personalización visual persistente por instalación; superusuarios exclusivamente."""
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from .models import AdministracionTaller
from .visual_catalog import (SPECIALTIES, ICONS, ALLOWED_ICONS,
                             MENU_SECTIONS, menu_key, editable_menu_items, default_icon)


@user_passes_test(lambda u: u.is_authenticated and u.is_active and u.is_superuser)
@require_http_methods(['GET', 'POST'])
def identidad_visual(request):
    config = AdministracionTaller.get_configuracion_activa()
    if request.method == 'POST':
        tipo = request.POST.get('tipo_taller', '')
        if tipo not in dict(SPECIALTIES):
            messages.error(request, 'Especialidad inválida. No se guardaron los cambios.')
            return redirect('identidad_visual')
        campos = {menu_key(group, label) for group, labels in MENU_SECTIONS for label in labels}
        overrides = {}
        for key in campos:
            selected = request.POST.get('icon_' + key, '')
            if selected and selected not in ALLOWED_ICONS:
                messages.error(request, 'Un icono no pertenece al catálogo. No se guardaron los cambios.')
                return redirect('identidad_visual')
            group, label_slug = key.split('.', 1)
            label = next((lab for grp, labs in MENU_SECTIONS if grp == group
                          for lab in labs if menu_key(grp, lab) == key), None)
            if selected and label and selected != default_icon(group, label, tipo):
                overrides[key] = selected
        config.tipo_taller = tipo
        config.mostrar_jerarquia = request.POST.get('mostrar_jerarquia') == 'on'
        config.iconos_menu = overrides
        config.save(update_fields=['tipo_taller', 'mostrar_jerarquia', 'iconos_menu', 'fecha_actualizacion'])
        messages.success(request, 'Identidad visual guardada correctamente.')
        return redirect('identidad_visual')
    return render(request, 'car/identidad_visual.html', {
        'identidad': config, 'especialidades': SPECIALTIES,
        'catalogo_iconos': ICONS, 'items_menu': editable_menu_items(config),
    })
