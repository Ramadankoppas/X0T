import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_postgres.vectorstores import PGVector
# from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings
import logging
logger = logging.getLogger("uvicorn.error")

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

CONNECTION_STRING = os.getenv(
    "DATABASE_URL_SYNC",
    "postgresql+psycopg://x0t_user:x0t_password@postgres:5432/x0t_db"
)

def get_vector_store():
    return PGVector(
        embeddings=embeddings,
        collection_name="pdf_documents",
        connection=CONNECTION_STRING,
        use_jsonb=True,
        async_mode=False,
    )

async def process_and_index_pdf(file_path: str):
    logger.info('start')
    loader = PyPDFLoader(file_path)
    docs = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", "؟", "!", ".", " ", ""]
    )
    chunks = text_splitter.split_documents(docs)
    vector_store = get_vector_store()
    vector_store.add_documents(chunks)
    
    return len(chunks)