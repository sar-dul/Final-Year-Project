import zipfile
from pathlib import Path
from io import BytesIO  # Import BytesIO
from PyPDF2 import PdfReader  # No PdfReadError in the latest PyPDF2


#--------------------------------------- Text Extraction -------------------------------------------#

def process_file(file_path):
    # Get the extension of the submitted file
    file_extension = Path(file_path).suffix

    if file_extension == '.zip':
        # Open the zip file and process its contents
        file_contents = {}
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            for file_name in zip_ref.namelist():
                # Skip macOS metadata files
                if file_name.startswith('__MACOSX/') or file_name.endswith('/'):
                    print(f"Skipping unwanted file: {file_name}")
                    continue

                if file_name.endswith('.pdf') or file_name.endswith('.py'):
                    try:
                        with zip_ref.open(file_name) as file:
                            # Read as binary content for compatibility
                            content = store_file(file.read(), file_name)
                            file_contents[file_name] = content
                    except Exception as e:
                        print(f"Error processing {file_name}: {e}")
        return file_contents

    elif file_extension in ['.pdf', '.py']:
        # If it's a .pdf or .py file, store its content directly
        with open(file_path, 'rb') as file:
            content = store_file(file.read(), file_path)
        return {file_path: content}
    else:
        print("Unsupported file type.")
        return None


def store_file(file_content, file_name):
    # Check file extension to determine the handling method
    if file_name.endswith('.pdf'):
        return extract_pdf_text(file_content)
    elif file_name.endswith('.py'):
        return read_python_file(file_content)


def extract_pdf_text(file_content):
    # Read the content from the PDF file-like object
    try:
        reader = PdfReader(BytesIO(file_content))  # Use BytesIO for file-like object
        text = ''
        for page in reader.pages:
            text += page.extract_text() or ""  # Safely handle None
        print("Extracted text from PDF.")
        return text
    except Exception as e:  # Handle general exceptions
        print(f"Error reading PDF: {e}")
        return f"Error: Unable to read PDF."


def read_python_file(file_content):
    # Read the Python (.py) file content
    encodings = ['utf-8', 'ISO-8859-1', 'latin-1']
    for encoding in encodings:
        try:
            content = file_content.decode(encoding)
            print(f"Successfully read Python file with {encoding} encoding.")
            return content
        except UnicodeDecodeError:
            print(f"Failed to read Python file with {encoding} encoding. Trying next...")
    raise UnicodeDecodeError("Unable to read Python file with any encoding.")

#--------------------------------------- Text Extraction -------------------------------------------#

#--------------------------------------- Embeddings -------------------------------------------#

from sentence_transformers import SentenceTransformer

# Load pre-trained SBERT model
model = SentenceTransformer('all-MiniLM-L6-v2')

def get_sentences(text):
    # Split text into sentences
    text = text.split('.')  # Split by full stop
    return [sen.strip() for sen in text[:-1]]

def get_embeddings(sentences):
    embeddings = {}

    # Generate sentence embeddings
    sentence_embeddings = model.encode(sentences)

    # Display the embeddings
    for i, embedding in enumerate(sentence_embeddings):
        embeddings[sentences[i]] = embedding
    
    return embeddings



#--------------------------------------- Embeddings -------------------------------------------#



