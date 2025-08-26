# Generated migration file
# Create this as tasks/migrations/0005_task_user.py

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tasks', '0004_remove_task_category_remove_historicaltask_category_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='user',
            field=models.ForeignKey(
                default=1,  # You might need to adjust this based on your existing data
                on_delete=django.db.models.deletion.CASCADE,
                related_name='user_tasks',
                to=settings.AUTH_USER_MODEL
            ),
            preserve_default=False,
        ),
    ]