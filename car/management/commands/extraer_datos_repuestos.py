import re
from django.core.management.base import BaseCommand
from django.db import transaction
from car.models import Repuesto


class Command(BaseCommand):
    help = 'Extrae datos estructurados del campo descripcion de los repuestos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Ejecutar sin guardar cambios (solo mostrar qué se haría)',
        )
        parser.add_argument(
            '--id',
            type=int,
            help='Procesar solo un repuesto específico por ID',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=100,
            help='Límite de repuestos a procesar (default: 100)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        repuesto_id = options.get('id')
        limit = options['limit']

        # Obtener repuestos a procesar
        if repuesto_id:
            repuestos = Repuesto.objects.filter(id=repuesto_id)
        else:
            repuestos = Repuesto.objects.filter(descripcion__isnull=False).exclude(descripcion='')[:limit]

        total_repuestos = repuestos.count()
        self.stdout.write(f"Procesando {total_repuestos} repuestos...")

        if dry_run:
            self.stdout.write(self.style.WARNING("MODO DRY-RUN: No se guardarán cambios"))

        procesados = 0
        actualizados = 0

        for repuesto in repuestos:
            procesados += 1
            self.stdout.write(f"\n--- Procesando ID {repuesto.id}: {repuesto.nombre} ---")
            
            # Extraer datos de la descripción
            datos_extraidos = self.extraer_datos_descripcion(repuesto.descripcion)
            
            if datos_extraidos:
                self.stdout.write(f"Descripción: {repuesto.descripcion[:100]}...")
                
                # Mostrar datos extraídos
                for campo, valor in datos_extraidos.items():
                    if valor:
                        self.stdout.write(f"  {campo}: {valor}")
                
                # Actualizar el repuesto si no es dry-run
                if not dry_run:
                    actualizado = self.actualizar_repuesto(repuesto, datos_extraidos)
                    if actualizado:
                        actualizados += 1
                        self.stdout.write(self.style.SUCCESS("  ✓ Actualizado"))
                    else:
                        self.stdout.write(self.style.WARNING("  - Sin cambios"))
                else:
                    actualizados += 1
            else:
                self.stdout.write("  - No se encontraron datos extraíbles")

        self.stdout.write(f"\n{'='*50}")
        self.stdout.write(f"Resumen:")
        self.stdout.write(f"  Repuestos procesados: {procesados}")
        self.stdout.write(f"  Repuestos actualizados: {actualizados}")
        
        if dry_run:
            self.stdout.write(self.style.WARNING("Ejecuta sin --dry-run para aplicar los cambios"))

    def extraer_datos_descripcion(self, descripcion):
        """
        Extrae datos estructurados de la descripción del repuesto
        """
        if not descripcion:
            return {}

        datos = {}
        descripcion_lower = descripcion.lower()

        # 1. Extraer OEM
        oem_patterns = [
            r'oem:\s*([A-Z0-9\-\.]+)',
            r'oem\s+([A-Z0-9\-\.]+)',
        ]
        for pattern in oem_patterns:
            match = re.search(pattern, descripcion, re.IGNORECASE)
            if match:
                datos['oem'] = match.group(1).strip()
                break

        # 2. Extraer Marca del repuesto
        marca_patterns = [
            r'marca\s+([A-Za-z0-9\s]+?)(?:\s+Origen|OEM|Código|$)',
            r'marca\s+([A-Za-z0-9\s]+?)(?:\s*$)',
        ]
        for pattern in marca_patterns:
            match = re.search(pattern, descripcion, re.IGNORECASE)
            if match:
                marca = match.group(1).strip()
                # Limpiar marca de caracteres no deseados
                marca = re.sub(r'\s+', ' ', marca)
                if len(marca) > 2:  # Evitar marcas muy cortas
                    datos['marca'] = marca
                break

        # 3. Extraer Origen
        origen_patterns = [
            r'origen:\s*([A-Za-z\s]+?)(?:\s+OEM|Código|$)',
            r'origen\s+([A-Za-z\s]+?)(?:\s+OEM|Código|$)',
        ]
        for pattern in origen_patterns:
            match = re.search(pattern, descripcion, re.IGNORECASE)
            if match:
                origen = match.group(1).strip()
                if len(origen) > 2:
                    datos['origen_repuesto'] = origen
                break

        # 4. Extraer Código Proveedor
        codigo_patterns = [
            r'código\s+proveedor:\s*([A-Z0-9\-\.\s]+?)(?:\s+[A-Za-z]|$)',
            r'código\s+noriega:\s*([A-Z0-9\-\.\s]+?)(?:\s+[A-Za-z]|$)',
            r'código\s+mundo\s+repuestos:\s*([A-Z0-9\-\.\s]+?)(?:\s+[A-Za-z]|$)',
            r'código\s+([A-Z0-9\-\.\s]+?)(?:\s+[A-Za-z]|$)',
        ]
        for pattern in codigo_patterns:
            match = re.search(pattern, descripcion, re.IGNORECASE)
            if match:
                codigo = match.group(1).strip()
                if len(codigo) > 1:
                    datos['cod_prov'] = codigo
                break

        # 5. Extraer Marca Vehículo
        marca_veh_patterns = [
            r'(nissan|toyota|honda|hyundai|kia|chevrolet|ford|mazda|suzuki|mitsubishi|peugeot|citroen|vw|volkswagen|renault|fiat|jeep|mercedes|bmw|audi|volvo|seat|skoda|opel|daewoo|hafei|chery|foton|mg|geely|lifan|byd|datsun)(?:\s+y\s+(nissan|toyota|honda|hyundai|kia|chevrolet|ford|mazda|suzuki|mitsubishi|peugeot|citroen|vw|volkswagen|renault|fiat|jeep|mercedes|bmw|audi|volvo|seat|skoda|opel|daewoo|hafei|chery|foton|mg|geely|lifan|byd|datsun))?',
        ]
        for pattern in marca_veh_patterns:
            match = re.search(pattern, descripcion, re.IGNORECASE)
            if match:
                marca_veh = match.group(0).strip()
                # Capitalizar primera letra de cada palabra
                marca_veh = ' '.join(word.capitalize() for word in marca_veh.split())
                datos['marca_veh'] = marca_veh
                break

        # 6. Extraer Tipo de Motor (motores separados por guiones)
        motor_patterns = [
            r'([A-Z0-9]+(?:\s*-\s*[A-Z0-9]+)*)',
        ]
        
        # Buscar patrones específicos de motores
        motor_specific_patterns = [
            r'(E\d+[A-Z]?\s*-\s*E\d+[A-Z]?(?:\s*-\s*E\d+[A-Z]?)*)',  # E13 - E15 -E16
            r'(G\d+[A-Z]{2}\s*-\s*G\d+[A-Z]{2}(?:\s*-\s*G\d+[A-Z]{2})*)',  # G4EH - G4EB - G4EA - G4EK
            r'(A\d+[A-Z]\s*-\s*S\d+[A-Z](?:\s*-\s*[A-Z]\d+[A-Z])*)',  # A5D - S5D - A3E - S6D
            r'(F\d+[A-Z]\s*-\s*[A-Z]\d+[A-Z](?:\s*-\s*[A-Z]\d+[A-Z])*)',  # F8D, A16DMS, etc.
            r'(GA\d+[A-Z]{2}\s*-\s*GA\d+[A-Z]{2}(?:\s*-\s*GA\d+[A-Z]{2})*)',  # GA16DE - GA16DNE
            r'(KA\d+[A-Z]\s*-\s*KA\d+[A-Z](?:\s*-\s*KA\d+[A-Z])*)',  # KA24E
            r'(SR\d+[A-Z]{2}\s*-\s*SR\d+[A-Z]{2}(?:\s*-\s*SR\d+[A-Z]{2})*)',  # SR20DE
            r'(HR\d+[A-Z]{2}\s*-\s*HR\d+[A-Z]{2}(?:\s*-\s*HR\d+[A-Z]{2})*)',  # HR16DE
            r'(VQ\d+[A-Z]{2}\s*-\s*VQ\d+[A-Z]{2}(?:\s*-\s*VQ\d+[A-Z]{2})*)',  # VQ35DE
            r'(D\d+[A-Z]{2}\s*-\s*D\d+[A-Z]{2}(?:\s*-\s*D\d+[A-Z]{2})*)',  # D4BH - D4BF
            r'(4G\d+\s*-\s*4G\d+(?:\s*-\s*4G\d+)*)',  # 4G18 - 473QE
            r'(4D\d+\s*-\s*4D\d+(?:\s*-\s*4D\d+)*)',  # 4D56 - 4D56T
            r'(C\d+[A-Z]{2}\s*-\s*C\d+[A-Z]{2}(?:\s*-\s*C\d+[A-Z]{2})*)',  # C20NE - C20NZ
            r'(X\d+[A-Z]{2}\s*-\s*X\d+[A-Z]{2}(?:\s*-\s*X\d+[A-Z]{2})*)',  # X20XE
            r'(Z\d+[A-Z]{2}\s*-\s*Z\d+[A-Z]{2}(?:\s*-\s*Z\d+[A-Z]{2})*)',  # Z22SE
            r'(B\d+[A-Z]\s*-\s*B\d+[A-Z](?:\s*-\s*B\d+[A-Z])*)',  # B10S
            r'(J\d+[A-Z]\s*-\s*J\d+[A-Z](?:\s*-\s*J\d+[A-Z])*)',  # J18, J20A
            r'(K\d+[A-Z]\s*-\s*K\d+[A-Z](?:\s*-\s*K\d+[A-Z])*)',  # K12B - K14B
            r'(M\d+[A-Z]\s*-\s*M\d+[A-Z](?:\s*-\s*M\d+[A-Z])*)',  # M16A - M13A
            r'(P\d+[A-Z]\s*-\s*P\d+[A-Z](?:\s*-\s*P\d+[A-Z])*)',  # P4AT - T22DD
            r'(W\d+[A-Z]\s*-\s*W\d+[A-Z](?:\s*-\s*W\d+[A-Z])*)',  # WLAA - WLE7
            r'(T\d+[A-Z]\s*-\s*T\d+[A-Z](?:\s*-\s*T\d+[A-Z])*)',  # T22DD
            r'(L\d+[A-Z]\s*-\s*L\d+[A-Z](?:\s*-\s*L\d+[A-Z])*)',  # L4KA
            r'(R\d+\s*-\s*R\d+(?:\s*-\s*R\d+)*)',  # R5 - R10 - R12
            r'(TU\d+[A-Z]\s*-\s*TU\d+[A-Z](?:\s*-\s*TU\d+[A-Z])*)',  # TU5JP4
            r'(DW\d+[A-Z]\s*-\s*DW\d+[A-Z](?:\s*-\s*DW\d+[A-Z])*)',  # DW10TD
            r'(DV\d+[A-Z]\s*-\s*DV\d+[A-Z](?:\s*-\s*DV\d+[A-Z])*)',  # DV4TD - DV4TED
            r'(EW\d+[A-Z]\s*-\s*EW\d+[A-Z](?:\s*-\s*EW\d+[A-Z])*)',  # EW10A - EW7J4
            r'(AEH\s*-\s*ADP\s*-\s*BSE\s*-\s*ALT\s*-\s*ABU)',  # AEH - ADP - BSE - ALT - ABU
            r'(ABF\s*-\s*AKR)',  # ABF - AKR
            r'(1KDFTV\s*-\s*2KDFTV\s*-\s*1KZTE)',  # 1KDFTV - 2KDFTV - 1KZTE
            r'(2E\s*-\s*3EE)',  # 2E - 3EE
            r'(3ZZFE\s*-\s*1ZZFE)',  # 3ZZFE - 1ZZFE
            r'(5AFE\s*-\s*4AFE)',  # 5AFE - 4AFE
            r'(2NRFE)',  # 2NRFE
            r'(QG\d+\s*-\s*QG\d+(?:\s*-\s*QG\d+)*)',  # QG15 - QG16 - QG18DE
            r'(DA\d+[A-Z]\s*-\s*DA\d+[A-Z](?:\s*-\s*DA\d+[A-Z])*)',  # DA468QL1
            r'(4N\d+\s*-\s*4N\d+(?:\s*-\s*4N\d+)*)',  # 4N15
            r'(YS\d+\s*-\s*YS\d+(?:\s*-\s*YS\d+)*)',  # YS23
            r'(M9T\s*-\s*M9T)',  # M9T
            r'(0M\d+\.\d+)',  # 0M699.301
            r'(SQR\d+\s*-\s*SQR\d+(?:\s*-\s*SQR\d+)*)',  # SQR481
            r'(MIDI\d+[A-Z]\s*-\s*MIDI\d+[A-Z](?:\s*-\s*MIDI\d+[A-Z])*)',  # MIDI16V
            r'(15S\d+[A-Z]\s*-\s*15S\d+[A-Z](?:\s*-\s*15S\d+[A-Z])*)',  # 15S4U
            r'(AVB\d+\s*-\s*AVB\d+(?:\s*-\s*AVB\d+)*)',  # AVB414
            r'(AZI\d+\s*-\s*AZI\d+(?:\s*-\s*AZI\d+)*)',  # AZI412
            r'(U\d+-\d+[A-Z]\s*-\s*U\d+-\d+[A-Z](?:\s*-\s*U\d+-\d+[A-Z])*)',  # U202-15YE2A
            r'(WL\d+-\d+-\d+[A-Z]\s*-\s*WL\d+-\d+-\d+[A-Z](?:\s*-\s*WL\d+-\d+-\d+[A-Z])*)',  # WL81-15-100C
            r'(MR\d+[A-Z]\s*-\s*MR\d+[A-Z](?:\s*-\s*MR\d+[A-Z])*)',  # MR479Q
            r'(479Q)',  # 479Q
            r'(G\d+[A-Z]\s*-\s*G\d+[A-Z](?:\s*-\s*G\d+[A-Z])*)',  # G63B
            r'(MD-\d+\s*-\s*MD-\d+(?:\s*-\s*MD-\d+)*)',  # MD-134754, MD-179030
            r'(473QE)',  # 473QE
            r'(171\d+\s*-\s*171\d+(?:\s*-\s*171\d+)*)',  # 171193 - 171162 - 171582
            r'(172\d+\s*-\s*172\d+(?:\s*-\s*172\d+)*)',  # 172162 - 172062
            r'(962\d+\s*-\s*962\d+(?:\s*-\s*962\d+)*)',  # 96291306, 96288956
            r'(964\d+\s*-\s*964\d+(?:\s*-\s*964\d+)*)',  # 96450249, 96497773
            r'(245\d+\s*-\s*245\d+(?:\s*-\s*245\d+)*)',  # 24512582
            r'(S\d+-\d+[A-Z]\s*-\s*S\d+-\d+[A-Z](?:\s*-\s*S\d+-\d+[A-Z])*)',  # S4-29285E
            r'(4ZA\d+\s*-\s*4ZA\d+(?:\s*-\s*4ZA\d+)*)',  # 4ZA1
            r'(G\d+[A-Z]\s*-\s*G\d+[A-Z](?:\s*-\s*G\d+[A-Z])*)',  # G161Z - G18Z - G200Z
            r'(4ZD\d+\s*-\s*4ZD\d+(?:\s*-\s*4ZD\d+)*)',  # 4ZD1
            r'(F\d+[A-Z]\s*-\s*F\d+[A-Z](?:\s*-\s*F\d+[A-Z])*)',  # F14D3 - A16DMS - A16DMN
            r'(A\d+[A-Z]\s*-\s*A\d+[A-Z](?:\s*-\s*A\d+[A-Z])*)',  # A16DMS - A16DMN
            r'(11400-\d+\s*-\s*11400-\d+(?:\s*-\s*11400-\d+)*)',  # 11400-78850, 11400-57810
            r'(10101-\d+[A-Z]\s*-\s*10101-\d+[A-Z](?:\s*-\s*10101-\d+[A-Z])*)',  # 10101-74Y25, 10101-40F25
            r'(10101-[A-Z]{2}\d+\s*-\s*10101-[A-Z]{2}\d+(?:\s*-\s*10101-[A-Z]{2}\d+)*)',  # 10101-EE025
            r'(11401-\d+\s*-\s*11401-\d+(?:\s*-\s*11401-\d+)*)',  # 11401-79863
            r'(11400-\d+\s*-\s*11400-\d+(?:\s*-\s*11400-\d+)*)',  # 11400-65860
            r'(10101-[A-Z]{2}\d+\s*-\s*10101-[A-Z]{2}\d+(?:\s*-\s*10101-[A-Z]{2}\d+)*)',  # 10101-CD325
            r'(20910-\d+[A-Z]\s*-\s*20910-\d+[A-Z](?:\s*-\s*20910-\d+[A-Z])*)',  # 20910-42A200, 20910-22N10
            r'(030\d+-\d+\s*-\s*030\d+-\d+(?:\s*-\s*030\d+-\d+)*)',  # 0301408-8
            r'(0197-[A-Z]\d+\s*-\s*0197-[A-Z]\d+(?:\s*-\s*0197-[A-Z]\d+)*)',  # 0197-AB, 0197-16, 0197-X4
            r'(050\d+\s*-\s*050\d+(?:\s*-\s*050\d+)*)',  # 050019812A
            r'(22433-\d+[A-Z]\s*-\s*22433-\d+[A-Z](?:\s*-\s*22433-\d+[A-Z])*)',  # 22433-51J10, 22433-53F00
            r'(27301-\d+\s*-\s*27301-\d+(?:\s*-\s*27301-\d+)*)',  # 27301-26620, 27301-04000
            r'(964\d+\s*-\s*964\d+(?:\s*-\s*964\d+)*)',  # 96453420
            r'(27300-\d+[A-Z]\s*-\s*27300-\d+[A-Z](?:\s*-\s*27300-\d+[A-Z])*)',  # 27300-2G000
            r'(904\d+\s*-\s*904\d+(?:\s*-\s*904\d+)*)',  # 90449739
            r'(8-\d+-\d+-\d+\s*-\s*8-\d+-\d+-\d+(?:\s*-\s*8-\d+-\d+-\d+)*)',  # 8-94371-838-0
            r'(22448-[A-Z]\d+\s*-\s*22448-[A-Z]\d+(?:\s*-\s*22448-[A-Z]\d+)*)',  # 22448-ED800
            r'(932\d+\s*-\s*932\d+(?:\s*-\s*932\d+)*)',  # 93248876
            r'(126\d+\s*-\s*126\d+(?:\s*-\s*126\d+)*)',  # 12611424
            r'(161\d+\s*-\s*161\d+(?:\s*-\s*161\d+)*)',  # 1610089400, 16100-29099, 16110-19135, 16100-19125, 16100-09260
            r'(210\d+\s*-\s*210\d+(?:\s*-\s*210\d+)*)',  # 21010-4M525, 21010-00Q2H, 21010-53Y00
            r'(4710[A-Z]-\d+\s*-\s*4710[A-Z]-\d+(?:\s*-\s*4710[A-Z]-\d+)*)',  # 4710QR-1307960
            r'(1300[A-Z]\d+\s*-\s*1300[A-Z]\d+(?:\s*-\s*1300[A-Z]\d+)*)',  # 1300A040
            r'(484[A-Z]-\d+\s*-\s*484[A-Z]-\d+(?:\s*-\s*484[A-Z]-\d+)*)',  # 484FC-1307010
            r'(130\d+-\d+[A-Z]\s*-\s*130\d+-\d+[A-Z](?:\s*-\s*130\d+-\d+[A-Z])*)',  # 1307010-26L
            r'(MG\d+\s*-\s*MG\d+(?:\s*-\s*MG\d+)*)',  # MG104798
            r'(17400-\d+[A-Z]\s*-\s*17400-\d+[A-Z](?:\s*-\s*17400-\d+[A-Z])*)',  # 17400-51K00, 17400-69G00, 17400-50810, 17400-M79F00
            r'(21500-\d+[A-Z]\s*-\s*21500-\d+[A-Z](?:\s*-\s*21500-\d+[A-Z])*)',  # 21500-4A800, 21500-4Z000
            r'(25100-\d+\s*-\s*25100-\d+(?:\s*-\s*25100-\d+)*)',  # 25100-25002, 25100-27000, 25100-22650, 25100-42540
            r'(133\d+\s*-\s*133\d+(?:\s*-\s*133\d+)*)',  # 1334010
            r'(1201-[A-Z]\d+\s*-\s*1201-[A-Z]\d+(?:\s*-\s*1201-[A-Z]\d+)*)',  # 1201-A2, 1201.F4
            r'(902\d+\s*-\s*902\d+(?:\s*-\s*902\d+)*)',  # 9025153
            r'(06B\d+\s*-\s*06B\d+(?:\s*-\s*06B\d+)*)',  # 06B121011B
        ]
        
        for pattern in motor_specific_patterns:
            match = re.search(pattern, descripcion, re.IGNORECASE)
            if match:
                motor = match.group(1).strip()
                # Limpiar espacios extra y normalizar guiones
                motor = re.sub(r'\s*-\s*', ' - ', motor)
                motor = re.sub(r'\s+', ' ', motor)
                datos['tipo_de_motor'] = motor
                break

        # 7. Extraer Referencia (si no se encontró OEM, usar el primer código encontrado)
        if 'oem' not in datos:
            referencia_patterns = [
                r'([A-Z0-9]{6,}(?:-[A-Z0-9]+)*)',
                r'([0-9]{6,}(?:-[0-9]+)*)',
            ]
            for pattern in referencia_patterns:
                match = re.search(pattern, descripcion)
                if match:
                    ref = match.group(1).strip()
                    if len(ref) >= 6:  # Solo códigos de al menos 6 caracteres
                        datos['referencia'] = ref
                        break

        return datos

    def actualizar_repuesto(self, repuesto, datos_extraidos):
        """
        Actualiza el repuesto con los datos extraídos
        """
        actualizado = False
        
        # Mapeo de campos
        campos_mapeo = {
            'oem': 'oem',
            'marca': 'marca',
            'origen_repuesto': 'origen_repuesto',
            'cod_prov': 'cod_prov',
            'marca_veh': 'marca_veh',
            'tipo_de_motor': 'tipo_de_motor',
            'referencia': 'referencia',
        }
        
        for campo_extraido, campo_modelo in campos_mapeo.items():
            if campo_extraido in datos_extraidos and datos_extraidos[campo_extraido]:
                valor_actual = getattr(repuesto, campo_modelo)
                valor_nuevo = datos_extraidos[campo_extraido]
                
                # Solo actualizar si el campo está vacío o es diferente
                if not valor_actual or valor_actual != valor_nuevo:
                    setattr(repuesto, campo_modelo, valor_nuevo)
                    actualizado = True
        
        if actualizado:
            repuesto.save()
        
        return actualizado
