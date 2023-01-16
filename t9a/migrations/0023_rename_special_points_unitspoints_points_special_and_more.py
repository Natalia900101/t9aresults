# Generated by Django 4.1.3 on 2023-01-16 13:44

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('t9a', '0022_unitspoints'),
    ]

    operations = [
        migrations.RenameField(
            model_name='unitspoints',
            old_name='special_points',
            new_name='points_special',
        ),
        migrations.AddField(
            model_name='unitspoints',
            name='list_unit',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='t9a.listsunits'),
        ),
        migrations.AlterField(
            model_name='unitspoints',
            name='unit',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='t9a.units'),
        ),
    ]