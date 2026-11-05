from django.db import migrations, models
import django.db.models.deletion


def migrate_inventory(apps, schema_editor):
    StockMovimiento = apps.get_model('car', 'StockMovimiento')
    for movement in StockMovimiento.objects.select_related('repuesto_stock'):
        movement.repuesto_id = movement.repuesto_stock.repuesto_id
        movement.save(update_fields=['repuesto'])

    DiagnosticoRepuesto = apps.get_model('car', 'DiagnosticoRepuesto')
    for item in DiagnosticoRepuesto.objects.filter(repuesto__isnull=True).select_related('repuesto_stock'):
        if item.repuesto_stock_id:
            item.repuesto_id = item.repuesto_stock.repuesto_id
            item.save(update_fields=['repuesto'])


class Migration(migrations.Migration):
    dependencies = [('car', '0052_remove_ventaitem_repuesto_stock_and_more')]

    operations = [
        migrations.AddField(
            model_name='stockmovimiento', name='repuesto',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='car.repuesto'),
        ),
        migrations.RunPython(migrate_inventory, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='stockmovimiento', name='repuesto',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='movimientos', to='car.repuesto'),
        ),
        migrations.RemoveField(model_name='stockmovimiento', name='repuesto_stock'),
        migrations.RemoveField(model_name='diagnosticorepuesto', name='repuesto_stock'),
    ]
