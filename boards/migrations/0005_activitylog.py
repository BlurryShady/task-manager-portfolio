from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ("boards", "0004_alter_task_column"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ActivityLog",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("action", models.CharField(max_length=120)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("request_path", models.CharField(blank=True, max_length=255)),
                (
                    "ip_address",
                    models.GenericIPAddressField(blank=True, null=True),
                ),
                ("user_agent", models.CharField(blank=True, max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="activitylog",
            index=models.Index(
                fields=["action", "created_at"],
                name="boards_act_action__c77dcd_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="activitylog",
            index=models.Index(
                fields=["user", "created_at"],
                name="boards_act_user_id_de2bcb_idx",
            ),
        ),
    ]
