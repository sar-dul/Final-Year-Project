from django.db import models
from users.models import User


class UploadedFile(models.Model):
    file = models.FileField(upload_to='current_files/')  # This will save files to the 'uploads/' folder in MEDIA_ROOT
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file.name
    

class PlagiarismReport(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    file_name = models.CharField(max_length=255, unique=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    plagiarism_percent = models.FloatField()
    highlighted_file_path = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.file_name} by {self.user.username} on {self.uploaded_at.strftime('%Y-%m-%d')}"
