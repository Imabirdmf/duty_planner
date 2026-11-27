from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("planner", "0009_alter_dutyassignment_jira_issue_key_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="staff",
            name="is_active",
            field=models.BooleanField(db_index=True, default=True),
        ),
    ]
