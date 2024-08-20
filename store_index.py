# use this featur to push my vector to db
from src.helper import load_pdf, text_split, download_huggingface_embeddings
from langchain_pinecone import PineconeVectorStore
from dotenv import load_dotenv
import os



load_dotenv()

PINECONE_API_KEY = os.environ.get('PINECONE_API_KEY')

#print(f'Pinecone API Key: {PINECONE_API_KEY}')

extracted_data = load_pdf('data')
text_chunks = text_split(extracted_data)
embeddings = download_huggingface_embeddings()

# Embed each chunk and upsert the embeddings into your Pinecone index.
docsearch = PineconeVectorStore.from_documents(
     documents=text_chunks,
     index_name="mchatbot",
     embedding=embeddings, 
     namespace="default" 
 )