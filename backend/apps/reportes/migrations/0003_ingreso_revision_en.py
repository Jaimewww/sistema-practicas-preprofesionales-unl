from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("reportes", "0002_requiere_revision_y_tope_semanal"),
    ]

    operations = [
        migrations.AddField(
            model_name="reportesemanal",
            name="ingreso_revision_en",
            field=models.DateTimeField(blank=True, editable=False, null=True),
        ),
    ]
