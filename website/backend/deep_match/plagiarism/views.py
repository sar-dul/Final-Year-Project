from django.shortcuts import render, redirect
from django.core.files.storage import FileSystemStorage
from .helper import process_file, extract_pdf_text, get_sentences, get_embeddings, highlight_plagiarized_text, detect_plagiarism, process_code, detect_code_plagiarism, highlight_plagiarized_code
import os
import base64
from django.conf import settings
from .models import PlagiarismReport, PlagiarismSession
from django.utils import timezone
import time
import zipfile
from django.core.files.storage import FileSystemStorage
from django.core.files.base import ContentFile
from django.contrib import messages

def go_to_multiple_check(request):
    return render(request, 'plagiarism/multiple_check.html')

def go_to_dashboard(request):
    return redirect('welcome')

def go_to_report(request):
    return render(request, 'plagiarism/report_template.html')


def upload_files(request):
    if request.method == 'POST' and request.FILES.getlist('file'):
        files = request.FILES.getlist('file')
        file_urls = []
        fs = FileSystemStorage()

        for uploaded_file in files:
            file_ext = os.path.splitext(uploaded_file.name)[1].lower()

            if file_ext == '.zip':
                # Process ZIP file and extract contents
                with zipfile.ZipFile(uploaded_file, 'r') as zip_ref:
                    for entry in zip_ref.namelist():
                        # Skip directories and hidden files
                        if entry.endswith('/') or entry.startswith('__MACOSX/'):
                            continue
                        # Get base name and extension
                        base_name = os.path.basename(entry)
                        entry_ext = os.path.splitext(base_name)[1].lower()

                        print()
                        print(f"Processing entry: {entry} with extension: {entry_ext}")
                        print()

                        # Determine save directory
                        if entry_ext == '.py':
                            save_dir = 'existing_files/code/'
                        elif entry_ext == '.pdf':
                            save_dir = 'existing_files/pdf/'
                        elif entry.endswith('.DS_Store'):
                            continue
                        else:
                            save_dir = 'existing_files/others/'
                        
                        # Create full save path and ensure filename security
                        save_path = os.path.join(save_dir, base_name)
                        # Extract file data and save
                        file_data = zip_ref.read(entry)
                        content_file = ContentFile(file_data, name=base_name)
                        saved_name = fs.save(save_path, content_file)
                        file_urls.append(fs.url(saved_name))
            else:
                # Handle regular files
                if file_ext == '.py':
                    save_path = f'existing_files/code/{uploaded_file.name}'
                elif file_ext == '.pdf':
                    save_path = f'existing_files/pdf/{uploaded_file.name}'
                else:
                    save_path = f'existing_files/others/{uploaded_file.name}'
                
                saved_name = fs.save(save_path, uploaded_file)
                file_urls.append(fs.url(saved_name))
        

        messages.success(request, 'Files uploaded successfully!')
        return redirect('/welcome')

    return render(request, 'dashboard.html')

def multiple_report_view(request, session_id):

    print("\\\nIn multiple report view\\\n")
    session = PlagiarismSession.objects.get(id=session_id)
    reports = PlagiarismReport.objects.filter(session=session)

    return render(request, 'plagiarism/report.html', {'reports': reports})

def check_single_file(request):
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

        # Check if the file is a PDF
        if uploaded_file.name.lower().endswith('.pdf'):

            # Extract text and generate embeddings
            text = extract_pdf_text(file_content)
            sentences = get_sentences(text)
            embeddings_self = get_embeddings(sentences)
            
            # Define the path to the directory with existing files
            existing_files_dir = os.path.join(settings.MEDIA_ROOT, "existing_files/pdf")

            # Check if the directory exists
            if not os.path.exists(existing_files_dir):
                return render(request, 'plagiarism/error.html', {"message": "Comparison directory not found."})

            # Get a list of all PDF files in the directory
            pdf_files = [f for f in os.listdir(existing_files_dir) if f.lower().endswith('.pdf')]

            # Check if there are any PDF files to process
            if not pdf_files:
                return render(request, 'plagiarism/error.html', {"message": "No PDF files found in the comparison directory."})

            # Initialize a list to store embeddings
            other_embeddings_list = []

            # Process each PDF file
            for pdf_filename in pdf_files:
                file_path = os.path.join(existing_files_dir, pdf_filename)
                
                # Process the file and extract text
                file = process_file(file_path)
                text = next(iter(file.values()))
                
                # Generate embeddings from sentences in the text
                embeddings = get_embeddings(get_sentences(text))
                
                # Append the embeddings to the list
                other_embeddings_list.append(embeddings)
            
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

                # Create session
                session = PlagiarismSession.objects.create(user=request.user)

                # Inside the view, after `highlighted_pdf_path` is defined
                PlagiarismReport.objects.create(
                    session=session,
                    user=request.user,
                    file_name=unique_filename,
                    original_file_name=uploaded_file.name,
                    uploaded_at=timezone.now(),
                    plagiarism_percent=plagiarism_percent,
                    highlighted_file_path=highlighted_pdf_path,
                    base64_pdf=base64_pdf,
                )
                
                return render(request, 'plagiarism/result.html', {
                    'file_url': fs.url(uploaded_file_path),
                    'highlighted_pdf_name': highlighted_pdf_name,
                    'base64_pdf': base64_pdf,
                    'plagiarism_percent': plagiarism_percent,
                    'checked_date': timezone.now()
                })
        else:
            # Process the file as code
            self_file_name, self_file_content = next(iter(process_file(full_uploaded_path).items()))
            codes_self = process_code(self_file_content)
            embeddings_code_self = get_embeddings(codes_self)

            # Define the path to the directory with existing files
            existing_files_dir = os.path.join(settings.MEDIA_ROOT, "existing_files/code")

            # Check if the directory exists
            if not os.path.exists(existing_files_dir):
                return render(request, 'plagiarism/error.html', {"message": "Comparison directory not found."})

            # Get a list of all PDF files in the directory
            code_files = [f for f in os.listdir(existing_files_dir) if f.lower().endswith('.py')]

            # Check if there are any PDF files to process
            if not code_files:
                return render(request, 'plagiarism/error.html', {"message": "No PDF files found in the comparison directory."})

            # Initialize a list to store embeddings
            other_embeddings_list = []

            for code_filename in code_files:
                file_path = os.path.join(existing_files_dir, code_filename)
                
                # Process the file and extract text
                file_name, file_content = next(iter(process_file(file_path).items()))
                
                codes = process_code(file_content)

                embeddings_code = get_embeddings(codes)

                # Append the embeddings to the list
                other_embeddings_list.append(embeddings_code)
            
            # Detect plagiarism
            flagged_codes, plagiarized_codes, plagiarism_percent = detect_code_plagiarism(embeddings_code_self, other_embeddings_list, similarity_threshold=0.9)
            print(f"Length of Plagiarized Sentences: {len(plagiarized_codes)}")
            print(f"Plagiarism Percent: {plagiarism_percent}")

            # Highlight plagiarized code
            result_folder = os.path.join(settings.MEDIA_ROOT, "result")
            os.makedirs(result_folder, exist_ok=True)

            highlighted_code_name = f"highlighted_{unique_filename}"
            highlighted_code_name  = highlighted_code_name .replace('.py', '.pdf')
            highlighted_code_path = os.path.join(result_folder, highlighted_code_name)
            highlighted_code = highlight_plagiarized_code(flagged_codes, highlighted_code_path)

            if highlighted_code:
                # highlighted_code.save()
                
                # Convert to Base64 for preview
                with open(highlighted_code_path, "rb") as f:
                    base64_code = base64.b64encode(f.read()).decode('utf-8')

                # Create session
                session = PlagiarismSession.objects.create(user=request.user)

                # Inside the view, after `highlighted_pdf_path` is defined
                PlagiarismReport.objects.create(
                    session=session,
                    user=request.user,
                    file_name=unique_filename,
                    original_file_name=uploaded_file.name,
                    uploaded_at=timezone.now(),
                    plagiarism_percent=plagiarism_percent,
                    highlighted_file_path=highlighted_code_path,
                    base64_pdf=base64_code,
                )

                return render(request, 'plagiarism/result.html', {
                    'file_url': fs.url(uploaded_file_path),
                    'highlighted_pdf_name': highlighted_code_name,
                    'base64_pdf': base64_code,
                    'plagiarism_percent': plagiarism_percent,
                    'checked_date': timezone.now()
                })
        
    
    return render(request, 'plagiarism/dashboard.html')


def check_multiple_files(request):

    if request.method == 'POST' and request.FILES.getlist('file'):  # Check for multiple files

        report_name = request.POST.get('report_name')

        files = request.FILES.getlist('file')  # Get all uploaded files
        file_urls = []  # List to store the URLs of uploaded files
        
        fs = FileSystemStorage()

        # Create session
        session = PlagiarismSession.objects.create(user=request.user)
        
        # Loop through the files and save each one
        for uploaded_file in files:
            if uploaded_file.name.lower().endswith('.zip'):
                with zipfile.ZipFile(uploaded_file, 'r') as zip_ref:
                    for entry in zip_ref.namelist():
                        # Skip directories and hidden files
                        if entry.endswith('/') or entry.startswith('__MACOSX/'):
                            continue
                        # Get base name and extension
                        base_name = os.path.basename(entry)
                        entry_ext = os.path.splitext(base_name)[1].lower()

                        if entry.endswith('.DS_Store'):
                            continue
                        else:
                            save_dir = 'current_files/'
                        
                        timestamp = int(time.time())
                        new_name = f"{timestamp}_{base_name}"
                        save_path = os.path.join(save_dir, new_name)
                        # Extract file data and save
                        file_data = zip_ref.read(entry)
                        content_file = ContentFile(file_data, name=new_name)
                        saved_name = fs.save(save_path, content_file)
                        file_urls.append(fs.url(saved_name))              
            else:
                file_content = uploaded_file.read()
            
                timestamp = int(time.time())  # e.g., 1712597802
                unique_filename = f"{timestamp}_{uploaded_file.name}"
                
                # Save the uploaded file in "current_files" folder inside media/
                uploaded_file_path = fs.save(f'current_files/{unique_filename}', uploaded_file)
                full_uploaded_path = os.path.join(settings.MEDIA_ROOT, uploaded_file_path)

            print("All files uploaded successfully!")

        # Path to the 'current_files' directory
        current_files_dir = os.path.join(settings.MEDIA_ROOT, 'current_files')

        # Loop through all files in the directory
        for filename in os.listdir(current_files_dir):
            file_path = os.path.join(current_files_dir, filename)

            # Ensure it's a file (not a directory)
            if os.path.isfile(file_path):
                with open(file_path, 'rb') as f:
                    file_content = f.read()
            
            uploaded_file_path = f'current_files/{filename}'  # Relative path from MEDIA_ROOT
            full_uploaded_path = os.path.join(settings.MEDIA_ROOT, uploaded_file_path)

            print()
            print(f"Processing file: {str(filename)}")
            print()
          
            # Check if the file is a PDF
            if uploaded_file_path.lower().endswith('.pdf'):
                # Extract text and generate embeddings
                text = extract_pdf_text(file_content)
                sentences = get_sentences(text)
                embeddings_self = get_embeddings(sentences)
                
                # Define the path to the directory with existing files
                existing_files_dir = os.path.join(settings.MEDIA_ROOT, "existing_files/pdf")

                # Check if the directory exists
                if not os.path.exists(existing_files_dir):
                    return render(request, 'plagiarism/error.html', {"message": "Comparison directory not found."})

                # Get a list of all PDF files in the directory
                pdf_files = [f for f in os.listdir(existing_files_dir) if f.lower().endswith('.pdf')]

                # Check if there are any PDF files to process
                if not pdf_files:
                    return render(request, 'plagiarism/error.html', {"message": "No PDF files found in the comparison directory."})

                # Initialize a list to store embeddings
                other_embeddings_list = []

                # Process each PDF file
                for pdf_filename in pdf_files:
                    file_path = os.path.join(existing_files_dir, pdf_filename)
                    
                    # Process the file and extract text
                    file = process_file(file_path)
                    text = next(iter(file.values()))
                    
                    # Generate embeddings from sentences in the text
                    embeddings = get_embeddings(get_sentences(text))
                    
                    # Append the embeddings to the list
                    other_embeddings_list.append(embeddings)
                
                # Detect plagiarism
                plagiarized_sentences, plagiarism_percent = detect_plagiarism(embeddings_self, other_embeddings_list, similarity_threshold=0.9)
                print(f"Length of Plagiarized Sentences: {len(plagiarized_sentences)}")
                print(f"Plagiarism Percent: {plagiarism_percent}")
                
                # Highlight plagiarized content
                highlighted_pdf = highlight_plagiarized_text(file_content, plagiarized_sentences)
                
                if highlighted_pdf:
                    result_folder = os.path.join(settings.MEDIA_ROOT, "result")
                    os.makedirs(result_folder, exist_ok=True)
                    
                    highlighted_pdf_name = f"highlighted_{str(filename)}"
                    highlighted_pdf_path = os.path.join(result_folder, highlighted_pdf_name)
                    
                    with open(highlighted_pdf_path, "wb") as f:
                        f.write(highlighted_pdf)
                    
                    # Convert to Base64 for preview
                    base64_pdf = base64.b64encode(highlighted_pdf).decode('utf-8')

                    # Inside the view, after `highlighted_pdf_path` is defined
                    PlagiarismReport.objects.create(
                        session=session,
                        user=request.user,
                        file_name=str(filename),
                        original_file_name=str(filename).split('_', 1)[1],
                        report_name=report_name,
                        uploaded_at=timezone.now(),
                        plagiarism_percent=plagiarism_percent,
                        highlighted_file_path=highlighted_pdf_path,
                        base64_pdf=base64_pdf,
                    )   
                
            else:
                # Process the file as code
                self_file_name, self_file_content = next(iter(process_file(full_uploaded_path).items()))
                codes_self = process_code(self_file_content)
                embeddings_code_self = get_embeddings(codes_self)

                # Define the path to the directory with existing files
                existing_files_dir = os.path.join(settings.MEDIA_ROOT, "existing_files/code")

                # Check if the directory exists
                if not os.path.exists(existing_files_dir):
                    return render(request, 'plagiarism/error.html', {"message": "Comparison directory not found."})

                # Get a list of all PDF files in the directory
                code_files = [f for f in os.listdir(existing_files_dir) if f.lower().endswith('.py')]

                # Check if there are any PDF files to process
                if not code_files:
                    return render(request, 'plagiarism/error.html', {"message": "No PDF files found in the comparison directory."})

                # Initialize a list to store embeddings
                other_embeddings_list = []

                for code_filename in code_files:
                    file_path = os.path.join(existing_files_dir, code_filename)
                    
                    # Process the file and extract text
                    file_name, file_content = next(iter(process_file(file_path).items()))
                    
                    codes = process_code(file_content)

                    embeddings_code = get_embeddings(codes)

                    # Append the embeddings to the list
                    other_embeddings_list.append(embeddings_code)
                
                # Detect plagiarism
                flagged_codes, plagiarized_codes, plagiarism_percent = detect_code_plagiarism(embeddings_code_self, other_embeddings_list, similarity_threshold=0.9)
                print(f"Length of Plagiarized Sentences: {len(plagiarized_codes)}")
                print(f"Plagiarism Percent: {plagiarism_percent}")

                # Highlight plagiarized code
                result_folder = os.path.join(settings.MEDIA_ROOT, "result")
                os.makedirs(result_folder, exist_ok=True)

                highlighted_code_name = f"highlighted_{str(filename)}"
                highlighted_code_name  = highlighted_code_name .replace('.py', '.pdf')
                highlighted_code_path = os.path.join(result_folder, highlighted_code_name)
                highlighted_code = highlight_plagiarized_code(flagged_codes, highlighted_code_path)

                if highlighted_code:
                    # highlighted_code.save()
                    
                    # Convert to Base64 for preview
                    with open(highlighted_code_path, "rb") as f:
                        base64_code = base64.b64encode(f.read()).decode('utf-8')

                    # Inside the view, after `highlighted_pdf_path` is defined
                    PlagiarismReport.objects.create(
                        session=session,
                        user=request.user,
                        file_name=str(filename),
                        original_file_name=str(filename).split('_', 1)[1],
                        report_name=report_name,
                        uploaded_at=timezone.now(),
                        plagiarism_percent=plagiarism_percent,
                        highlighted_file_path=highlighted_code_path,
                        base64_pdf=base64_code,
                    )


            reports = PlagiarismReport.objects.filter(session=session)

        # Loop through all items in the directory
        for filename in os.listdir(current_files_dir):
            file_path = os.path.join(current_files_dir, filename)

            # Only delete files (skip directories, if any)
            if os.path.isfile(file_path):
                os.remove(file_path)  # Delete the file
                print(f"Deleted: {file_path}")
                
        return render(request, 'plagiarism/report.html', {'reports': reports})
    
    
    return redirect('welcome')

from django.http import FileResponse

def display_highlighted_pdf(request, file_name):
    result_folder = os.path.join(settings.MEDIA_ROOT, "result")
    highlighted_pdf_path = os.path.join(result_folder, file_name)

    # Ensure file exists before serving
    if os.path.exists(highlighted_pdf_path):
        return FileResponse(open(highlighted_pdf_path, "rb"), content_type="application/pdf")
    else:
        return render(request, "plagiarism/error.html", {"message": "File not found"})
    

from django.shortcuts import render, get_object_or_404

def result_view(request, report_id):
    report = get_object_or_404(PlagiarismReport, id=report_id,)

    context = {
        'checked_date': report.uploaded_at,
        'plagiarism_percent': report.plagiarism_percent,
        'highlighted_pdf_name': f"highlighted_{report.file_name}",
        'base64_pdf': report.base64_pdf,
    }

    return render(request, 'plagiarism/result.html', context)

def files_from_zip():
    # This function is not implemented in the provided code.
    pass