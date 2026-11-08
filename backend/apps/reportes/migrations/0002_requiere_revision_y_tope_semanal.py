from django.db import migrations, models

import apps.reportes.models

UMBRAL_REVISION_HORAS = 40


def marcar_reportes_existentes(apps_, schema_editor):
    """Los reportes previos de más de 40 h se señalan para el tutor (S5)."""
    ReporteSemanal = apps_.get_model("reportes", "ReporteSemanal")
    ReporteSemanal.objects.filter(horas_reportadas__gt=UMBRAL_REVISION_HORAS).update(
        requiere_revision=True
    )


class Migration(migrations.Migration):

    dependencies = [
        ('reportes', '0001_reportesemanal'),
    ]

    operations = [
        migrations.AddField(
            model_name='reportesemanal',
            name='requiere_revision',
            field=models.BooleanField(default=False, editable=False),
        ),
        migrations.AlterField(
            model_name='reportesemanal',
            name='horas_reportadas',
            field=models.PositiveIntegerField(validators=[apps.reportes.models.validar_horas_positivas, apps.reportes.models.validar_tope_semanal]),
        ),
        migrations.RunPython(marcar_reportes_existentes, migrations.RunPython.noop),
    ]
