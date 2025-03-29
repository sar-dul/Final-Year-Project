from django.shortcuts import render, redirect
from django.core.files.storage import FileSystemStorage

def upload_file(request):
    print("Inside upload_file view")
    if request.method == 'POST' and request.FILES['file']:
        uploaded_file = request.FILES['file']

        print("The uploaded file name is: ", uploaded_file.name)
        
        fs = FileSystemStorage()
        filename = fs.save('current_files/' +  uploaded_file.name, uploaded_file)  # Save the file
        file_url = fs.url(filename)  # Get the URL to access the file

        return render(request, 'plagiarism/dashboard.html', {
            'file_url': file_url
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