from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('core', '0002_alter_fridgeproduct_options_fridgeproduct_created_at_and_more')]
    operations = [
        migrations.AddField(
            model_name='refillsession',
            name='deleted_at',
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
    ]
