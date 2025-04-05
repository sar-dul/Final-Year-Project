from django.shortcuts import render, redirect
from django.core.files.storage import FileSystemStorage
from .helper import process_file, extract_pdf_text, get_sentences, get_embeddings, highlight_plagiarized_text, detect_plagiarism
import os
import base64
from django.conf import settings
from .models import PlagiarismReport
from django.utils import timezone
import time


def upload_file(request):
    print("Inside upload_file view")
    
    if request.method == 'POST' and request.FILES.get('file'):
        uploaded_file = request.FILES['file']
        fs = FileSystemStorage()

        file_content = uploaded_file.read()

        if not file_content:
            print("Error: Uploaded file is empty!")
            return redirect('dashboard')
        
        timestamp = int(time.time())  # e.g., 1712597802
        unique_filename = f"{timestamp}_{uploaded_file.name}"

        # Save the uploaded file in "current_files" folder inside media/
        uploaded_file_path = fs.save(f'current_files/{unique_filename}', uploaded_file)
        full_uploaded_path = os.path.join(settings.MEDIA_ROOT, uploaded_file_path)
        
        # Extract text and generate embeddings
        text = extract_pdf_text(file_content)
        sentences = get_sentences(text)
        embeddings_self = get_embeddings(sentences)
        
        # Load comparison files from "existing_files" inside media/
        file1_path = os.path.join(settings.MEDIA_ROOT, "existing_files/Test 1.pdf")
        file2_path = os.path.join(settings.MEDIA_ROOT, "existing_files/Test 2.pdf")
        
        if not os.path.exists(file1_path) or not os.path.exists(file2_path):
            return render(request, 'plagiarism/error.html', {"message": "Comparison files not found."})
        
        file1 = process_file(file1_path)
        text1 = next(iter(file1.values()))
        embeddings_other_1 = get_embeddings(get_sentences(text1))
        
        file2 = process_file(file2_path)
        text2 = next(iter(file2.values()))
        embeddings_other_2 = get_embeddings(get_sentences(text2))
        
        other_embeddings_list = [embeddings_other_1, embeddings_other_2]
        
        # Detect plagiarism
        plagiarized_sentences, plagiarism_percent = detect_plagiarism(embeddings_self, other_embeddings_list, similarity_threshold=0.9)
        print(f"Length of Plagiarized Sentences: {len(plagiarized_sentences)}")
        print(f"Plagiarism Percent: {plagiarism_percent}")
        
        # Highlight plagiarized content
        highlighted_pdf = highlight_plagiarized_text(file_content, plagiarized_sentences)
        
        if highlighted_pdf:
            result_folder = os.path.join(settings.MEDIA_ROOT, "result")
            os.makedirs(result_folder, exist_ok=True)
            
            highlighted_pdf_name = f"highlighted_{unique_filename}"
            highlighted_pdf_path = os.path.join(result_folder, highlighted_pdf_name)
            
            with open(highlighted_pdf_path, "wb") as f:
                f.write(highlighted_pdf)
            
            # Convert to Base64 for preview
            base64_pdf = base64.b64encode(highlighted_pdf).decode('utf-8')

            # Inside the view, after `highlighted_pdf_path` is defined
            PlagiarismReport.objects.create(
                user=request.user,
                file_name=unique_filename,
                uploaded_at=timezone.now(),
                plagiarism_percent=plagiarism_percent,
                highlighted_file_path=highlighted_pdf_path
            )
            
            return render(request, 'plagiarism/result.html', {
                'file_url': fs.url(uploaded_file_path),
                'highlighted_pdf_name': highlighted_pdf_name,
                'base64_pdf': base64_pdf
            })
    
    return render(request, 'plagiarism/dashboard.html')

def upload_multiple_files(request):
    if request.method == 'POST' and request.FILES.getlist('file'):  # Check for multiple files
        files = request.FILES.getlist('file')  # Get all uploaded files
        file_urls = []  # List to store the URLs of uploaded files
        
        fs = FileSystemStorage()
        
        # Loop through the files and save each one
        for uploaded_file in files:
            filename = fs.save('current_files/' + uploaded_file.name, uploaded_file)
            file_url = fs.url(filename)
            file_urls.append(file_url)

        
        # Pass the list of URLs to the template
        return render(request, 'plagiarism/dashboard.html', {
            'file_urls': file_urls  # Send multiple file URLs to the template
        })

    return render(request, 'plagiarism/dashboard.html')

from django.http import FileResponse

def display_highlighted_pdf(request, file_name):
    result_folder = os.path.join(settings.MEDIA_ROOT, "result")
    highlighted_pdf_path = os.path.join(result_folder, file_name)

    # Ensure file exists before serving
    if os.path.exists(highlighted_pdf_path):
        return FileResponse(open(highlighted_pdf_path, "rb"), content_type="application/pdf")
    else:
        return render(request, "plagiarism/error.html", {"message": "File not found"})
