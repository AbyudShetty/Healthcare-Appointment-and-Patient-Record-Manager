from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('electronic_records', '0002_patientdocument'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='patientrecord',
            index=models.Index(fields=['created_at'], name='record_created_idx'),
        ),
        migrations.AddIndex(
            model_name='clinicalnote',
            index=models.Index(fields=['created_at'], name='note_created_idx'),
        ),
    ]