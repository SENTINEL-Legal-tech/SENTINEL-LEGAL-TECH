import streamlit as st
import hashlib
from pypdf import PdfReader
import io
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import SupabaseVectorStore

class SentinelIO:
    """Handles the Drag-and-Drop interface and Document Recognition."""
    
    def __init__(self, supabase_client, embed_model):
        self.supabase = supabase_client
        self.embed_model = embed_model

    def render_dropzone(self):
        """Creates a high-visibility drop area for dockets."""
        st.markdown("""
            <style>
                /* Makes the upload area look like a professional drop zone */
                [data-testid="stFileUploader"] {
                    background-color: #1e1f20;
                    border: 2px dashed #444;
                    border-radius: 10px;
                    padding: 20px;
                }
            </style>
        """, unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader(
            "DRAG DOCKETS HERE FOR INSTANT ANALYSIS", 
            type=['pdf'],
            help="SENTINEL forensic indexing will begin immediately upon drop.",
            label_visibility="collapsed"
        )
        return uploaded_file

    def process_document(self, uploaded_file):
        """The 'Brain' that ensures the file is actually recognized and indexed."""
        try:
            # 1. Reset and Read
            uploaded_file.seek(0)
            pdf_bytes = uploaded_file.read()
            reader = PdfReader(io.BytesIO(pdf_bytes))
            
            text = ""
            for page in reader.pages:
                content = page.extract_text()
                if content:
                    text += content + "\n"

            if len(text.strip()) < 50:
                st.error("🚨 DOCUMENT RECOGNITION FAILURE: File appears empty or scanned without OCR.")
                return None

            # 2. Chunking for the Cloud Index
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000, 
                chunk_overlap=150
            )
            chunks = splitter.split_text(text)

            # 3. Direct Push to Supabase
            vector_db = SupabaseVectorStore.from_texts(
                texts=chunks,
                embedding=self.embed_model,
                client=self.supabase,
                table_name="sentinel_docs",
                query_name="match_documents"
            )
            
            return vector_db

        except Exception as e:
            st.error(f"🚨 SYSTEM IO ERROR: {str(e)}")
            return None

    def generate_file_id(self, file):
        """Creates a unique fingerprint so we don't re-index the same file twice."""
        return hashlib.md5(file.name.encode()).hexdigest()