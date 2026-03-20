import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import os

from dotenv import load_dotenv
load_dotenv()
db = Chroma(persist_directory='./vector_db', embedding_function=GoogleGenerativeAIEmbeddings(model='models/gemini-embedding-001'), collection_name='mutual_fund_faq')
docs = db.get()
print('TOTAL DOCS:', len(docs['ids']))

kotak_docs = db.get(where={'fund_name': 'Kotak Midcap Fund'})
print('KOTAK DOCS:', len(kotak_docs['ids']))
for i in range(len(kotak_docs['ids'])):
    print(f"ID: {kotak_docs['ids'][i]}\nContent:\n{kotak_docs['documents'][i]}\n---")
