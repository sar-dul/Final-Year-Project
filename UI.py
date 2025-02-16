import streamlit as st
from helper import process_file, extract_pdf_text, get_sentences, get_embeddings
from sklearn.metrics.pairwise import cosine_similarity

# Configure the page
st.set_page_config(page_title="Plagiarism Detection System", layout="wide")

# Sidebar for additional settings or info
with st.sidebar:
    st.title("Settings")
    st.write("Adjust the plagiarism detection options below.")
    
    # Placeholder for future settings
    detection_level = st.selectbox("Detection Sensitivity Level", ["Low", "Medium", "High"], index=1)
    file_retention = st.checkbox("Keep uploaded files for future comparison")

# Title and description
st.title("Plagiarism Detection System")
st.write("""
    This tool lets you upload text (PDF) or code files (individual or zipped collections) to check for plagiarism against stored files.
    The results include a plagiarism percentage for each file submitted.
""")

# File upload section
st.subheader("File Upload")
uploaded_files = st.file_uploader("Upload your files (PDF or ZIP)", type=["pdf", "zip", "py"], accept_multiple_files=True)

# Analysis button and progress indicator
if uploaded_files:
    if st.button("Analyze for Plagiarism"):
        # Progress indicator
        with st.spinner("Analyzing files, please wait..."):
            # Placeholder for function call (add your detection logic here)
            st.write("Analyzing...")  # Placeholder for progress

        # Placeholder for results
        st.success("Analysis complete!")
        
        # Results Display Section
        st.subheader("Analysis Results")
        
        # Example output display (replace with actual results)
        for i, file in enumerate(uploaded_files, 1):
            st.markdown(f"**{i}. {file.name}**")
            st.write("Plagiarism Detected: **45%**")  # Placeholder for result
            st.progress(45)  # Example progress bar, replace with actual result

        # Option to download report
        st.download_button(
            label="Download Full Report",
            data="Sample report data",  # Replace with actual report data
            file_name="plagiarism_report.txt",
            mime="text/plain"
        )

        # Display the extracted text
        text = extract_pdf_text(uploaded_files[0].read())
        sentences = get_sentences(text)
        st.write("No of sentences in Input: ", len(sentences))
        embeddings_self = get_embeddings(sentences)
        st.write("No of Embeddings for Input: ", len(embeddings_self))

        # Display two existing texts
        file1 = process_file("test_files/Test1.pdf")
        text1 = next(iter(file1.values()))
        sentences1 = get_sentences(text1)
        embeddings_other_1 = get_embeddings(sentences1)

        file2 = process_file("test_files/Test2.pdf")
        text2 = next(iter(file2.values()))
        sentences2 = get_sentences(text2)
        embeddings_other_2 = get_embeddings(sentences2)

        existing_files = [embeddings_other_1,  embeddings_other_2]

        # Dictionary to track flagged sentences for plagiarism
        flagged_sentence = {}

        # List to store similarity metrics for all files compared
        mult_file_similarity = []

        # Iterate through each file in the existing_files list
        for other_file in existing_files:
            mult_sen_similarity = {}  # Dictionary to store similarities for the current file
            for i, each_input in enumerate(embeddings_self):
                each_sen_similarity = []  # List to store similarities for the current sentence
                for j, each_output in enumerate(other_file):
                    # Calculate cosine similarity between two sentences
                    similarity = cosine_similarity([embeddings_self[each_input]], [other_file[each_output]])
                    
                    if similarity >= 0.9:
                        # Flag the sentence as plagiarized if similarity is above the threshold
                        flagged_sentence[each_input] = True  # Use each_input instead of sentences[i]
                    elif each_input not in flagged_sentence:  # Check against each_input
                        # If the sentence hasn't been flagged yet, set it as not plagiarized
                        flagged_sentence[each_input] = False
                    
                    # Append the similarity score for the current sentence pair
                    each_sen_similarity.append(similarity)

                # Store all similarity scores for the current input sentence
                mult_sen_similarity[i] = each_sen_similarity
            
            # Append the similarities for the current file to the list
            mult_file_similarity.append(mult_sen_similarity)
            

        # Output the flagged sentences and their plagiarism status
        st.write(flagged_sentence)
        st.write(len(flagged_sentence))

        

else:
    st.info("Upload at least one PDF or ZIP file to begin analysis.")
