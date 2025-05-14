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


# Set up SSL context first
import ssl
import certifi
ssl._create_default_https_context = lambda: ssl.create_default_context(cafile=certifi.where())

# Then import nltk and download resources
import nltk
# nltk.download('punkt')
# nltk.download('punkt_tab')  # Add this line
# nltk.download('wordnet')    # Sometimes needed for text processing

# Rest of your imports
from sentence_transformers import SentenceTransformer
import re
from nltk.tokenize import sent_tokenize


# Load pre-trained SBERT model
model = SentenceTransformer('all-MiniLM-L6-v2')

def get_sentences(text):
    # Remove extra newlines but keep paragraph breaks
    text = re.sub(r"\n+", " ", text)  # Replace multiple newlines with space
    
    # Remove extra spaces around punctuation
    text = re.sub(r'\s+([.,!?])', r'\1', text)

    # Fix broken words (e.g., "c hange" -> "change") using a basic pattern
    text = re.sub(r'\b(\w)\s+(\w)\b', r'\1\2', text)

    # Remove multiple spaces
    text = re.sub(r'\s+', ' ', text).strip()

    # Tokenize into proper sentences
    sentences = sent_tokenize(text)

    # # Remove punctuation from each sentence
    # sentences = [re.sub(r'[^\w\s]', '', sentence) for sentence in sentences]

    return list(dict.fromkeys(sentences))

    # text = text.split('.')  # Split by full stop
    # return list(dict.fromkeys([sen.strip() for sen in text[:-1]]))



def get_embeddings(sentences):
    embeddings = {}

    # Generate sentence embeddings
    sentence_embeddings = model.encode(sentences)

    # Display the embeddings
    for i, embedding in enumerate(sentence_embeddings):
        embeddings[sentences[i]] = embedding
    
    return embeddings


#--------------------------------------- Embeddings -------------------------------------------#


#--------------------------------------- Compare Similarity -------------------------------------------#

from sklearn.metrics.pairwise import cosine_similarity

def detect_plagiarism(embeddings_self, other_embeddings_list, similarity_threshold=0.9):
    
    flagged_sentences = {}

    # Loop over all files in other embeddings list
    for other_file in other_embeddings_list:
        for i, input_sentence in enumerate(embeddings_self):
            max_similarity = 0

            # Compare each sentence from the self document with sentences from other documents
            for output_sentence in other_file:
                similarity = cosine_similarity(
                    [embeddings_self[input_sentence]],
                    [other_file[output_sentence]]
                )[0][0]

                if similarity > max_similarity:
                    max_similarity = similarity

            # Flag sentence as plagiarized if similarity is above threshold
            if max_similarity >= similarity_threshold:
                flagged_sentences[input_sentence] = True
            elif input_sentence not in flagged_sentences:
                flagged_sentences[input_sentence] = False

    # Filter out plagiarized sentences
    plagiarized_sentences = [sentence for sentence, flag in flagged_sentences.items() if flag]

    # Calculate plagiarism percentage
    total_sentences = len(embeddings_self)
    plagiarized_count = len(plagiarized_sentences)
    plagiarism_percentage = (plagiarized_count / total_sentences) * 100 if total_sentences > 0 else 0


    return plagiarized_sentences, plagiarism_percentage



#--------------------------------------- Compare Similarity -------------------------------------------#



#------------------------------------ PDF Highlighting ----------------------------------------#

import fitz

def highlight_plagiarized_text(file_bytes, plagiarized_sentences):
    """Highlight plagiarized text in PDF bytes and return modified PDF bytes."""
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    
    for page in doc:
        words = page.get_text("words")
        if not words:
            continue
        
        word_list = [(word[4].strip(), fitz.Rect(word[:4])) for word in words]
        
        for sentence in plagiarized_sentences:
            if not sentence:
                continue
            sentence_words = sentence.split()
            if not sentence_words:
                continue

            for i in range(len(word_list) - len(sentence_words) + 1):
                match = True
                for j in range(len(sentence_words)):
                    if word_list[i + j][0] != sentence_words[j]:
                        match = False
                        break
                if not match:
                    continue

                matched_sequence = word_list[i:i + len(sentence_words)]
                line_groups = []
                current_line = [matched_sequence[0][1]]
                current_y0 = matched_sequence[0][1].y0

                for k in range(1, len(matched_sequence)):
                    word_rect = matched_sequence[k][1]
                    if abs(word_rect.y0 - current_y0) < 1:
                        current_line.append(word_rect)
                    else:
                        line_groups.append(current_line)
                        current_line = [word_rect]
                        current_y0 = word_rect.y0
                line_groups.append(current_line)

                for line in line_groups:
                    combined_rect = line[0]
                    for rect in line[1:]:
                        combined_rect |= rect
                    page.add_highlight_annot(combined_rect)

    output_buffer = BytesIO()
    doc.save(output_buffer)
    doc.close()
    return output_buffer.getvalue()



#------------------------------------ PDF Highlighting ----------------------------------------#



