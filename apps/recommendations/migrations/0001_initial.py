from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import django.core.validators

class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('inventory', '0001_initial'),
        ('warehouse', '0002_zonegroup_aisle_rack_aisle_zone_zone_group'),
    ]

    operations = [
        migrations.CreateModel(
            name='RecommendationRule',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('movement_type', models.CharField(max_length=20, choices=[
                    ('FAST', 'Fast Moving'),
                    ('SLOW', 'Slow Moving'),
                    ('FRAGILE', 'Fragile'),
                    ('HAZARDOUS', 'Hazardous'),
                ])),
                ('storage_type', models.CharField(max_length=20, choices=[
                    ('GENERAL', 'General Storage'),
                    ('SECURE', 'Secure Storage'),
                    ('COLD', 'Cold Storage'),
                    ('BULK', 'Bulk Storage'),
                ])),
                ('zone_group_type', models.CharField(max_length=30, choices=[
                    ('GENERAL_STORAGE', 'General Storage'),
                    ('SECURE_STORAGE', 'Secure Storage'),
                    ('COLD_STORAGE', 'Cold Storage'),
                    ('BULK_STORAGE', 'Bulk Storage'),
                    ('FRAGILE_STORAGE', 'Fragile Storage'),
                    ('HAZARDOUS_STORAGE', 'Hazardous Storage'),
                    ('FAST_MOVING_STORAGE', 'Fast Moving Storage'),
                    ('SLOW_MOVING_STORAGE', 'Slow Moving Storage'),
                ])),
                ('priority', models.PositiveIntegerField(default=1)),
                ('description', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['-priority'],
                'unique_together': {('movement_type', 'storage_type', 'zone_group_type')},
            },
        ),
        migrations.CreateModel(
            name='ProductClassification',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('movement_type', models.CharField(max_length=20, choices=[
                    ('FAST', 'Fast Moving'),
                    ('SLOW', 'Slow Moving'),
                    ('FRAGILE', 'Fragile'),
                    ('HAZARDOUS', 'Hazardous'),
                ])),
                ('storage_type', models.CharField(max_length=20, choices=[
                    ('GENERAL', 'General Storage'),
                    ('SECURE', 'Secure Storage'),
                    ('COLD', 'Cold Storage'),
                    ('BULK', 'Bulk Storage'),
                ])),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('product', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='classification', to='inventory.Product')),
            ],
        ),
        migrations.CreateModel(
            name='StorageRecommendation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('recommendation_reason', models.TextField()),
                ('recommendation_score', models.FloatField(validators=[
                    django.core.validators.MinValueValidator(0.0),
                    django.core.validators.MaxValueValidator(1.0)
                ])),
                ('recommendation_source', models.CharField(max_length=20, choices=[
                    ('RULE_ENGINE', 'Rule Engine'),
                    ('ML_MODEL', 'ML Model'),
                ])),
                ('recommendation_version', models.CharField(default='v1', max_length=20)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='storage_recommendations', to='inventory.Product')),
                ('zone', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='storage_recommendations', to='warehouse.Zone')),
                ('zone_group', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='storage_recommendations', to='warehouse.ZoneGroup')),
            ],
            options={
                'ordering': ['-created_at'],
                'indexes': [models.Index(fields=['product', 'zone_group', 'zone'], name='storage_rec_query_idx')],
            },
        ),
    ]
