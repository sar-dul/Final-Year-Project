from django.db import models
from users.models import User


class UploadedFile(models.Model):
    file = models.FileField(upload_to='current_files/')  # This will save files to the 'uploads/' folder in MEDIA_ROOT
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file.name
    
    
class PlagiarismSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    submitted_at = models.DateTimeField(auto_now_add=True)
    id = models.AutoField(primary_key=True)

    def __str__(self):
        return f"Session by {self.user.username} on {self.submitted_at.strftime('%Y-%m-%d %H:%M:%S')}"
    

class PlagiarismReport(models.Model):
    session = models.ForeignKey(PlagiarismSession, on_delete=models.CASCADE, related_name='reports', null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    file_name = models.CharField(max_length=255, unique=True)
    original_file_name = models.CharField(max_length=255, blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    report_name = models.CharField(max_length=255, blank=True, null=True)
    plagiarism_percent = models.FloatField()
    highlighted_file_path = models.CharField(max_length=255, null=True, blank=True)
    base64_pdf = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.file_name} by {self.user.username} on {self.uploaded_at.strftime('%Y-%m-%d')}"
    

