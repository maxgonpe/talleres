import logging
import os

import requests
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

logger = logging.getLogger(__name__)


@login_required
def vehiculo_lookup(request):
    placa = request.GET.get("placa", "").upper().strip()
    if not placa:
        return JsonResponse({"error": "Falta parámetro placa"}, status=400)

    api_key = os.environ.get("VEHICLE_LOOKUP_API_KEY", "")
    if not api_key:
        logger.error("VEHICLE_LOOKUP_API_KEY no está configurada")
        return JsonResponse({"error": "Servicio de vehículos no configurado"}, status=503)

    try:
        response = requests.get(
            f"https://chile.getapi.cl/v1/vehicles/plate/{placa}",
            headers={"X-Api-Key": api_key},
            timeout=10,
        )
        data = response.json()
        if not data.get("success"):
            return JsonResponse({"error": "No se encontró vehículo"}, status=404)

        api_data = data.get("data", {})
        motor = api_data.get("engine")
        version = api_data.get("version")
        descripcion_motor = None
        if motor and version:
            descripcion_motor = f"Motor {motor} • {version}"
        elif motor:
            descripcion_motor = f"Motor {motor}"
        elif version:
            descripcion_motor = version

        return JsonResponse({
            "marca": api_data.get("model", {}).get("brand", {}).get("name"),
            "modelo": api_data.get("model", {}).get("name"),
            "anio": api_data.get("year"),
            "vin": api_data.get("vinNumber"),
            "placa": api_data.get("licensePlate"),
            "descripcion_motor": descripcion_motor,
        })
    except (requests.RequestException, ValueError, TypeError):
        logger.exception("Error consultando servicio de vehículos")
        return JsonResponse({"error": "Error consultando API"}, status=500)
