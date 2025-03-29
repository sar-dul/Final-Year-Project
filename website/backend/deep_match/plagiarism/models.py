from django.db import models

class UploadedFile(models.Model):
    file = models.FileField(upload_to='current_files/')  # This will save files to the 'uploads/' folder in MEDIA_ROOT
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file.name
