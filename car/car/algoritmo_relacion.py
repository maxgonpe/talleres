from difflib import SequenceMatcher
import re
from collections import defaultdict
from django.shortcuts import render
from .models import Repuesto, Componente, ComponenteRepuesto

def algoritmo_relacion_inteligente(umbral=0.6, solo_analizar=False, ejecutar=False):
    """
    Algoritmo inteligente para relacionar repuestos con componentes
    """
    # Obtener todos los repuestos y componentes
    repuestos = Repuesto.objects.all()
    componentes = Componente.objects.filter(activo=True)
    
    # Obtener relaciones existentes
    relaciones_existentes = set()
    for rel in ComponenteRepuesto.objects.all():
        relaciones_existentes.add((rel.componente.id, rel.repuesto.id))
    
    resultados = {
        'relaciones_encontradas': [],
        'relaciones_no_encontradas': [],
        'estadisticas': {
            'total_repuestos': repuestos.count(),
            'total_componentes': componentes.count(),
            'relaciones_existentes': len(relaciones_existentes),
            'nuevas_relaciones': 0,
            'porcentaje_exito': 0
        }
    }
    
    # Palabras clave para diferentes categorías
    palabras_clave = {
        'motor': ['motor', 'cilindro', 'piston', 'valvula', 'bujia', 'filtro aceite', 'aceite', 'refrigerante', 'termostato', 'radiador', 'bomba agua', 'correa', 'tensor'],
        'frenos': ['freno', 'pastilla', 'disco', 'tambor', 'liquido frenos', 'bomba frenos', 'cilindro freno', 'manguera freno', 'sensor abs'],
        'suspension': ['amortiguador', 'resorte', 'brazo', 'rotula', 'terminal', 'buje', 'silentblock', 'barra estabilizadora', 'soporte motor'],
        'direccion': ['direccion', 'cremallera', 'terminal', 'rotula', 'bomba direccion', 'liquido direccion', 'columna direccion'],
        'transmision': ['embrague', 'disco embrague', 'plato presion', 'collar', 'caja cambios', 'diferencial', 'cardan', 'junta homocinetica'],
        'electrico': ['alternador', 'motor arranque', 'bateria', 'fusible', 'relay', 'sensor', 'actuador', 'bobina', 'distribuidor'],
        'combustible': ['bomba combustible', 'filtro combustible', 'inyector', 'regulador presion', 'tanque', 'manguera combustible'],
        'escape': ['catalizador', 'silenciador', 'mofle', 'sonda lambda', 'sensor oxigeno', 'tubo escape'],
        'climatizacion': ['compresor', 'condensador', 'evaporador', 'filtro aire', 'ventilador', 'termostato aire'],
        'carroceria': ['parachoques', 'farol', 'luz', 'espejo', 'manija', 'cerradura', 'vidrio', 'parabrisas'],
        'neumaticos': ['llanta', 'neumatico', 'rueda', 'valvula neumatico', 'sensor presion'],
        'lubricacion': ['aceite', 'filtro', 'grasa', 'lubricante', 'aditivo'],
        'refrigeracion': ['radiador', 'termostato', 'bomba agua', 'manguera', 'refrigerante', 'ventilador'],
    }
    
    # Función para calcular similitud
    def calcular_similitud(texto1, texto2):
        if not texto1 or not texto2:
            return 0
        return SequenceMatcher(None, texto1.lower(), texto2.lower()).ratio()
    
    # Función para extraer palabras clave
    def extraer_palabras_clave(texto):
        if not texto:
            return []
        texto_limpio = re.sub(r'[^\w\s]', ' ', texto.lower())
        palabras = texto_limpio.split()
        return [palabra for palabra in palabras if len(palabra) > 2]
    
    # Función para puntuar relación
    def puntuar_relacion(repuesto, componente):
        puntuacion = 0
        razones = []
        
        # 1. Similitud directa de nombres (peso: 40%)
        similitud_nombre = calcular_similitud(repuesto.nombre, componente.nombre)
        if similitud_nombre > 0.3:
            puntuacion += similitud_nombre * 0.4
            razones.append(f"Similitud nombre: {similitud_nombre:.2f}")
        
        # 2. Coincidencia en descripción (peso: 20%)
        if repuesto.descripcion:
            similitud_desc = calcular_similitud(repuesto.descripcion, componente.nombre)
            if similitud_desc > 0.3:
                puntuacion += similitud_desc * 0.2
                razones.append(f"Similitud descripción: {similitud_desc:.2f}")
        
        # 3. Coincidencia en posición (peso: 15%)
        if repuesto.posicion:
            similitud_pos = calcular_similitud(repuesto.posicion, componente.nombre)
            if similitud_pos > 0.3:
                puntuacion += similitud_pos * 0.15
                razones.append(f"Similitud posición: {similitud_pos:.2f}")
        
        # 4. Palabras clave (peso: 25%)
        palabras_repuesto = extraer_palabras_clave(repuesto.nombre + ' ' + (repuesto.descripcion or ''))
        palabras_componente = extraer_palabras_clave(componente.nombre)
        
        coincidencias = 0
        for palabra in palabras_repuesto:
            if palabra in palabras_componente:
                coincidencias += 1
        
        if palabras_componente:
            ratio_coincidencias = coincidencias / len(palabras_componente)
            puntuacion += ratio_coincidencias * 0.25
            razones.append(f"Coincidencias palabras: {coincidencias}/{len(palabras_componente)}")
        
        # 5. Bonus por categorías específicas
        for categoria, palabras in palabras_clave.items():
            for palabra in palabras:
                if palabra in repuesto.nombre.lower() and palabra in componente.nombre.lower():
                    puntuacion += 0.1
                    razones.append(f"Bonus categoría {categoria}: {palabra}")
                    break
        
        return puntuacion, razones
    
    # Analizar cada repuesto
    repuestos_sin_relacion = []
    
    for repuesto in repuestos:
        mejor_puntuacion = 0
        mejor_componente = None
        mejores_razones = []
        
        # Buscar el mejor componente para este repuesto
        for componente in componentes:
            # Verificar si ya existe la relación
            if (componente.id, repuesto.id) in relaciones_existentes:
                continue
            
            puntuacion, razones = puntuar_relacion(repuesto, componente)
            
            if puntuacion > mejor_puntuacion:
                mejor_puntuacion = puntuacion
                mejor_componente = componente
                mejores_razones = razones
        
        # Si encontramos una relación con puntuación suficiente
        if mejor_puntuacion >= umbral and mejor_componente:
            resultado = {
                'repuesto': repuesto,
                'componente': mejor_componente,
                'puntuacion': mejor_puntuacion,
                'razones': mejores_razones,
                'ya_existe': False
            }
            
            if ejecutar:
                # Crear la relación
                ComponenteRepuesto.objects.create(
                    componente=mejor_componente,
                    repuesto=repuesto,
                    nota=f"Relación automática (puntuación: {mejor_puntuacion:.2f})"
                )
                resultados['estadisticas']['nuevas_relaciones'] += 1
            
            resultados['relaciones_encontradas'].append(resultado)
        else:
            repuestos_sin_relacion.append({
                'repuesto': repuesto,
                'mejor_puntuacion': mejor_puntuacion,
                'mejor_componente': mejor_componente
            })
    
    resultados['relaciones_no_encontradas'] = repuestos_sin_relacion
    
    # Calcular estadísticas
    total_repuestos = resultados['estadisticas']['total_repuestos']
    relaciones_encontradas = len(resultados['relaciones_encontradas'])
    
    if total_repuestos > 0:
        resultados['estadisticas']['porcentaje_exito'] = (relaciones_encontradas / total_repuestos) * 100
    
    return resultados













