# Updated UI.py
# Add this before importing any PyTorch related modules
import torch

# Monkey-patch to fix Streamlit's path inspection
if hasattr(torch.classes, '__path__'):
    del torch.classes.__path__
    
import streamlit as st
from helper import process_file, extract_pdf_text, get_sentences, get_embeddings, highlight_plagiarized_text
from sklearn.metrics.pairwise import cosine_similarity
import base64
from io import BytesIO

# Configure the page
st.set_page_config(page_title="Plagiarism Detection System", layout="wide")

# Sidebar for additional settings or info
with st.sidebar:
    st.title("Settings")
    st.write("Adjust the plagiarism detection options below.")
    detection_level = st.selectbox("Detection Sensitivity Level", ["Low", "Medium", "High"], index=1)
    file_retention = st.checkbox("Keep uploaded files for future comparison")

# Main UI
st.title("Plagiarism Detection System")
st.write("""
    This tool lets you upload text (PDF) or code files (individual or zipped collections) to check for plagiarism against stored files.
    The results include a plagiarism percentage for each file submitted.
""")

# File upload section
uploaded_files = st.file_uploader("Upload your files (PDF or ZIP)", type=["pdf", "zip", "py"], accept_multiple_files=True)

if uploaded_files:
    uploaded_file = uploaded_files[0]
    file_bytes = uploaded_file.read()

    if st.button("Analyze for Plagiarism"):
        with st.spinner("Analyzing files, please wait..."):
            # Existing analysis logic
            text = extract_pdf_text(file_bytes)
            sentences = get_sentences(text)
            embeddings_self = get_embeddings(sentences)

            # Load comparison files
            file1 = process_file("test_files/Test 1.pdf")
            text1 = next(iter(file1.values()))
            sentences1 = get_sentences(text1)
            embeddings_other_1 = get_embeddings(sentences1)

            file2 = process_file("test_files/Test 2.pdf")
            text2 = next(iter(file2.values()))
            sentences2 = get_sentences(text2)
            embeddings_other_2 = get_embeddings(sentences2)

            # Plagiarism detection logic
            flagged_sentences = {}
            for other_file in [embeddings_other_1, embeddings_other_2]:
                for i, input_sentence in enumerate(embeddings_self):
                    max_similarity = 0
                    for output_sentence in other_file:
                        similarity = cosine_similarity(
                            [embeddings_self[input_sentence]],
                            [other_file[output_sentence]]
                        )[0][0]
                        if similarity > max_similarity:
                            max_similarity = similarity
                    if max_similarity >= 0.9:
                        flagged_sentences[input_sentence] = True
                    elif input_sentence not in flagged_sentences:
                        flagged_sentences[input_sentence] = False

            plagiarized_sentences = [sentence for sentence, flag in flagged_sentences.items() if flag]

            st.write("Plagiarized Sentences:")
            for sentence in plagiarized_sentences:
                st.write(sentence)

            # Highlight PDF
            if plagiarized_sentences:
                highlighted_pdf = highlight_plagiarized_text(file_bytes, plagiarized_sentences)
                
                # Display PDF preview
                st.subheader("Highlighted PDF Preview")
                base64_pdf = base64.b64encode(highlighted_pdf).decode('utf-8')
                pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800" type="application/pdf"></iframe>'
                st.markdown(pdf_display, unsafe_allow_html=True)

                # Download button
                st.download_button(
                    label="Download Highlighted PDF",
                    data=highlighted_pdf,
                    file_name="highlighted.pdf",
                    mime="application/pdf"
                )
            else:
                st.info("No plagiarized content found")

        st.success("Analysis complete!")
        st.subheader("Analysis Results")
        
        # Display basic results
        for i, file in enumerate(uploaded_files, 1):
            st.markdown(f"**{i}. {file.name}**")
            st.write("Plagiarism Detected: **45%**")  # Replace with actual calculation
            st.progress(45)