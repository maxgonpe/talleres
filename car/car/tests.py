from decimal import Decimal

from django.contrib.auth.models import User
from django.db import IntegrityError
from django.test import TestCase

from .models import (
    Accion,
    Cliente_Taller,
    Componente,
    Diagnostico,
    DiagnosticoComponenteAccion,
    DiagnosticoRepuesto,
    Compra,
    CompraItem,
    CarritoItem,
    Mecanico,
    SesionVenta,
    StockMovimiento,
    TrabajoAbono,
    VentaPOS,
    VentaPOSItem,
    Repuesto,
    Trabajo,
    TrabajoAccion,
    Vehiculo,
    actualizar_stock_venta_pos,
)
from .services.inventory import mover_stock
from .forms import CompraItemForm
from .services.work_stock import ajustar_stock_repuesto_trabajo
from .services.stock import reservar_stock, liberar_reserva


class TallerIntegrityTests(TestCase):
    def test_inventory_movement_is_idempotent_and_master_based(self):
        repuesto = Repuesto.objects.create(nombre="Filtro", stock=2)

        mover_stock(repuesto.pk, 1, "salida", "Venta", "IDEMP-1")
        mover_stock(repuesto.pk, 1, "salida", "Venta", "IDEMP-1")

        repuesto.refresh_from_db()
        self.assertEqual(repuesto.stock, 1)
        self.assertEqual(StockMovimiento.objects.filter(referencia="IDEMP-1").count(), 1)

    def setUp(self):
        self.cliente = Cliente_Taller.objects.create(
            rut="12.345.678-k",
            nombre="Cliente de Prueba",
        )
        self.vehiculo = Vehiculo.objects.create(
            cliente=self.cliente,
            marca="Toyota",
            modelo="Yaris",
            anio=2020,
            placa="ABCD12",
        )
        self.componente = Componente.objects.create(nombre="Frenos")
        self.accion = Accion.objects.create(nombre="Cambio de pastillas")

    def test_rut_is_normalized_before_persisting(self):
        self.assertEqual(self.cliente.rut, "12345678K")

    def test_vehicle_plate_is_unique(self):
        with self.assertRaises(IntegrityError):
            Vehiculo.objects.create(
                cliente=self.cliente,
                marca="Mazda",
                modelo="2",
                anio=2021,
                placa="ABCD12",
            )

    def test_diagnosis_totals_use_quantity_and_unit_price(self):
        diagnostico = Diagnostico.objects.create(
            vehiculo=self.vehiculo,
            descripcion_problema="Desgaste normal",
        )
        DiagnosticoComponenteAccion.objects.create(
            diagnostico=diagnostico,
            componente=self.componente,
            accion=self.accion,
            precio_mano_obra=Decimal("25000"),
            cantidad=2,
        )
        repuesto = Repuesto.objects.create(
            nombre="Pastilla de freno",
            precio_venta=Decimal("18000"),
        )
        DiagnosticoRepuesto.objects.create(
            diagnostico=diagnostico,
            repuesto=repuesto,
            cantidad=2,
            precio_unitario=Decimal("18000"),
            subtotal=Decimal("36000"),
        )

        self.assertEqual(diagnostico.total_mano_obra, Decimal("50000"))
        self.assertEqual(diagnostico.total_repuestos, Decimal("36000"))
        self.assertEqual(diagnostico.total_presupuesto, Decimal("86000"))

    def test_approved_diagnosis_clones_once_into_work_order(self):
        diagnostico = Diagnostico.objects.create(
            vehiculo=self.vehiculo,
            descripcion_problema="Revisión",
        )
        diagnostico.componentes.add(self.componente)
        DiagnosticoComponenteAccion.objects.create(
            diagnostico=diagnostico,
            componente=self.componente,
            accion=self.accion,
            precio_mano_obra=Decimal("30000"),
            cantidad=1,
        )
        repuesto = Repuesto.objects.create(nombre="Pastilla reservada", stock=2, stock_reservado=1)
        DiagnosticoRepuesto.objects.create(
            diagnostico=diagnostico,
            repuesto=repuesto,
            cantidad=1,
            precio_unitario=Decimal("1000"),
            subtotal=Decimal("1000"),
            reservado=True,
        )

        trabajo = diagnostico.aprobar_y_clonar()

        self.assertEqual(diagnostico.estado, "aprobado")
        self.assertEqual(Trabajo.objects.count(), 1)
        self.assertEqual(TrabajoAccion.objects.filter(trabajo=trabajo).count(), 1)
        self.assertEqual(list(trabajo.componentes.all()), [self.componente])
        repuesto.refresh_from_db()
        self.assertEqual(repuesto.stock_reservado, 0)

    def test_generated_sku_is_unique_and_stock_is_available(self):
        repuesto = Repuesto.objects.create(
            nombre="Filtro de aceite",
            precio_costo=Decimal("1000"),
        )

        self.assertTrue(repuesto.sku)
        self.assertEqual(len(repuesto.sku.split("-")), 4)
        self.assertEqual(repuesto.stock_disponible, 0)
        self.assertFalse(repuesto.tiene_stock_suficiente(1))

    def test_receiving_purchase_updates_master_and_detailed_stock(self):
        repuesto = Repuesto.objects.create(nombre="Filtro aire")
        compra = Compra.objects.create(proveedor="Proveedor de prueba")
        item = CompraItem.objects.create(
            compra=compra,
            repuesto=repuesto,
            cantidad=3,
            precio_unitario=Decimal("5000"),
        )

        item.recibir_item()
        item.recibir_item()

        repuesto.refresh_from_db()
        self.assertTrue(item.recibido)
        self.assertEqual(repuesto.stock, 3)
        self.assertEqual(StockMovimiento.objects.filter(tipo="entrada").count(), 1)

    def test_paid_pos_sale_decreases_stock_and_records_movement(self):
        user = User.objects.create_user(username="caja", password="test-pass-123")
        repuesto = Repuesto.objects.create(
            nombre="Bujía",
            stock=5,
            precio_venta=Decimal("4000"),
        )
        sesion = SesionVenta.objects.create(usuario=user)
        venta = VentaPOS.objects.create(
            sesion=sesion,
            usuario=user,
            subtotal=Decimal("8000"),
            total=Decimal("8000"),
            pagado=True,
        )
        VentaPOSItem.objects.create(
            venta=venta,
            repuesto=repuesto,
            cantidad=2,
            precio_unitario=Decimal("4000"),
            subtotal=Decimal("8000"),
        )

        actualizar_stock_venta_pos(venta)
        actualizar_stock_venta_pos(venta)

        repuesto.refresh_from_db()
        self.assertEqual(repuesto.stock, 3)
        self.assertEqual(StockMovimiento.objects.filter(tipo="salida").count(), 1)

    def test_unpaid_pos_sale_does_not_change_stock(self):
        user = User.objects.create_user(username="vendedor", password="test-pass-123")
        repuesto = Repuesto.objects.create(nombre="Aceite", stock=4)
        sesion = SesionVenta.objects.create(usuario=user)
        venta = VentaPOS.objects.create(
            sesion=sesion,
            usuario=user,
            total=Decimal("1000"),
            pagado=False,
        )
        VentaPOSItem.objects.create(
            venta=venta,
            repuesto=repuesto,
            cantidad=1,
            precio_unitario=Decimal("1000"),
            subtotal=Decimal("1000"),
        )

        actualizar_stock_venta_pos(venta)

        repuesto.refresh_from_db()
        self.assertEqual(repuesto.stock, 4)
        self.assertFalse(StockMovimiento.objects.filter(repuesto=repuesto).exists())

    def test_cancelled_sale_is_kept_and_cannot_reverse_stock_twice(self):
        user = User.objects.create_user(username="caja-anula", password="test-pass-123")
        Mecanico.objects.create(user=user, rol="vendedor")
        repuesto = Repuesto.objects.create(nombre="Correa", stock=2)
        sesion = SesionVenta.objects.create(usuario=user)
        venta = VentaPOS.objects.create(
            sesion=sesion,
            usuario=user,
            subtotal=Decimal("1000"),
            total=Decimal("1000"),
            pagado=True,
        )
        VentaPOSItem.objects.create(
            venta=venta,
            repuesto=repuesto,
            cantidad=1,
            precio_unitario=Decimal("1000"),
            subtotal=Decimal("1000"),
        )
        actualizar_stock_venta_pos(venta)
        self.client.force_login(user)

        self.client.post(f"/car/pos/venta/{venta.pk}/anular/")
        self.client.post(f"/car/pos/venta/{venta.pk}/anular/")

        repuesto.refresh_from_db()
        venta.refresh_from_db()
        self.assertEqual(repuesto.stock, 2)
        self.assertFalse(venta.pagado)
        self.assertEqual(
            StockMovimiento.objects.filter(referencia=f"ANULACION-VENTA-POS-{venta.pk}").count(),
            1,
        )

    def test_work_order_balance_is_realized_amount_minus_payments(self):
        diagnostico = Diagnostico.objects.create(
            vehiculo=self.vehiculo,
            descripcion_problema="Pago parcial",
        )
        trabajo = Trabajo.objects.create(
            diagnostico=diagnostico,
            vehiculo=self.vehiculo,
        )
        TrabajoAccion.objects.create(
            trabajo=trabajo,
            componente=self.componente,
            accion=self.accion,
            precio_mano_obra=Decimal("50000"),
            completado=True,
        )
        TrabajoAbono.objects.create(
            trabajo=trabajo,
            monto=Decimal("20000"),
        )

        self.assertEqual(trabajo.total_realizado, Decimal("50000"))
        self.assertEqual(trabajo.total_abonos, Decimal("20000"))
        self.assertEqual(trabajo.saldo_pendiente, Decimal("30000"))

    def test_work_part_stock_service_install_and_return(self):
        repuesto = Repuesto.objects.create(nombre="Pastilla", stock=4)
        diagnostico = Diagnostico.objects.create(
            vehiculo=self.vehiculo,
            descripcion_problema="Instalación",
        )
        trabajo = Trabajo.objects.create(diagnostico=diagnostico, vehiculo=self.vehiculo)
        from .models import TrabajoRepuesto
        item = TrabajoRepuesto.objects.create(
            trabajo=trabajo,
            repuesto=repuesto,
            cantidad=2,
            precio_unitario=Decimal("1000"),
            subtotal=Decimal("2000"),
        )

        self.assertTrue(ajustar_stock_repuesto_trabajo(item, delta=-1))
        repuesto.refresh_from_db()
        self.assertEqual(repuesto.stock, 2)
        self.assertEqual(StockMovimiento.objects.filter(tipo='salida').count(), 1)
        self.assertTrue(ajustar_stock_repuesto_trabajo(item, delta=1))
        repuesto.refresh_from_db()
        self.assertEqual(repuesto.stock, 4)
        self.assertEqual(StockMovimiento.objects.filter(tipo='liberacion').count(), 1)

    def test_work_part_stock_service_rejects_insufficient_stock(self):
        repuesto = Repuesto.objects.create(nombre="Filtro", stock=1)
        diagnostico = Diagnostico.objects.create(
            vehiculo=self.vehiculo,
            descripcion_problema="Sin stock",
        )
        trabajo = Trabajo.objects.create(diagnostico=diagnostico, vehiculo=self.vehiculo)
        from .models import TrabajoRepuesto
        item = TrabajoRepuesto.objects.create(
            trabajo=trabajo,
            repuesto=repuesto,
            cantidad=2,
            precio_unitario=Decimal("1000"),
            subtotal=Decimal("2000"),
        )

        self.assertFalse(ajustar_stock_repuesto_trabajo(item, delta=-1))
        repuesto.refresh_from_db()
        self.assertEqual(repuesto.stock, 1)

    def test_stock_reservation_can_be_released_once(self):
        repuesto = Repuesto.objects.create(nombre="Sensor", stock=3)
        reservar_stock(repuesto, 2, "Reserva de prueba", "DIAG-TEST")
        repuesto = liberar_reserva(repuesto, 2, "Liberación de prueba", "DIAG-TEST")

        self.assertEqual(repuesto.stock_reservado, 0)
        self.assertEqual(StockMovimiento.objects.filter(repuesto=repuesto).count(), 2)

    def test_work_order_states_follow_the_operational_sequence(self):
        diagnostico = Diagnostico.objects.create(
            vehiculo=self.vehiculo,
            descripcion_problema="Estados",
        )
        trabajo = Trabajo.objects.create(diagnostico=diagnostico, vehiculo=self.vehiculo)

        self.assertTrue(trabajo.cambiar_estado("trabajando"))
        self.assertTrue(trabajo.cambiar_estado("completado"))
        self.assertTrue(trabajo.cambiar_estado("entregado"))
        self.assertIsNotNone(trabajo.fecha_fin)

    def test_work_order_rejects_state_jump(self):
        diagnostico = Diagnostico.objects.create(
            vehiculo=self.vehiculo,
            descripcion_problema="Estado inválido",
        )
        trabajo = Trabajo.objects.create(diagnostico=diagnostico, vehiculo=self.vehiculo)

        with self.assertRaises(ValueError):
            trabajo.cambiar_estado("entregado")

    def test_mechanic_can_only_access_assigned_work(self):
        owner = User.objects.create_user(username="mec-asignado", password="test-pass-123")
        other = User.objects.create_user(username="mec-no-asignado", password="test-pass-123")
        assigned = Mecanico.objects.create(user=owner, rol="mecanico")
        Mecanico.objects.create(user=other, rol="mecanico")
        diagnostico = Diagnostico.objects.create(
            vehiculo=self.vehiculo,
            descripcion_problema="Acceso por objeto",
        )
        trabajo = Trabajo.objects.create(diagnostico=diagnostico, vehiculo=self.vehiculo)
        trabajo.mecanicos.add(assigned)

        self.client.force_login(owner)
        allowed = self.client.get(f"/car/trabajos/{trabajo.pk}/")
        self.assertEqual(allowed.status_code, 200)

        self.client.force_login(other)
        denied = self.client.get(f"/car/trabajos/{trabajo.pk}/")
        self.assertEqual(denied.status_code, 404)

    def test_purchase_item_form_rejects_invalid_values(self):
        repuesto = Repuesto.objects.create(nombre="Filtro")
        form = CompraItemForm(data={
            "repuesto": repuesto.pk,
            "cantidad": 0,
            "precio_unitario": -1,
        })

        self.assertFalse(form.is_valid())
        self.assertIn("cantidad", form.errors)
        self.assertIn("precio_unitario", form.errors)


class AuthenticationSmokeTests(TestCase):
    def test_login_page_is_reachable(self):
        response = self.client.get("/car/login/")
        self.assertEqual(response.status_code, 200)

    def test_anonymous_user_is_redirected_from_pos(self):
        response = self.client.get("/car/pos/")
        self.assertRedirects(response, "/car/login/?next=/car/pos/")

    def test_mechanic_cannot_enter_pos(self):
        user = User.objects.create_user(username="mecanico", password="test-pass-123")
        Mecanico.objects.create(user=user, rol="mecanico")
        self.client.force_login(user)

        response = self.client.get("/car/pos/")

        self.assertRedirects(response, "/")

    def test_vendor_can_enter_pos(self):
        user = User.objects.create_user(username="vendedor", password="test-pass-123")
        Mecanico.objects.create(user=user, rol="vendedor")
        self.client.force_login(user)

        response = self.client.get("/car/pos/")

        self.assertEqual(response.status_code, 200)

    def test_mechanic_cannot_enter_purchases(self):
        user = User.objects.create_user(username="mecanico-compras", password="test-pass-123")
        Mecanico.objects.create(user=user, rol="mecanico")
        self.client.force_login(user)

        response = self.client.get("/car/compras/")

        self.assertRedirects(response, "/")
