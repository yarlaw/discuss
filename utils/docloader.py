import os
import fitz
import requests
from bs4 import BeautifulSoup
import streamlit as st

def load_pdf(file_path):
    doc = fitz.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text

def load_documents_from_folder(folder_path):
    documents = []
    for filename in os.listdir(folder_path):
        if filename.endswith(".pdf"):
            text = load_pdf(os.path.join(folder_path, filename))
            documents.append({"filename": filename, "text": text})
    return documents

def load_wiki_content(url):
    try:
        response = requests.get(url, headers={'User-Agent': 'DiscussionBot Wiki Fetcher/1.0'})
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        main_content = soup.select_one('#mw-content-text')
        
        if main_content:
            for unwanted in main_content.select('.mw-editsection, .reference, .reflist, table'):
                unwanted.decompose()
                
            text = main_content.get_text(separator=' ', strip=True)
            return text
        else:
            body = soup.find('body')
            if body:
                return body.get_text(separator=' ', strip=True)
            return soup.get_text(separator=' ', strip=True)
    
    except Exception as e:
        st.error(f"Error fetching wiki content: {str(e)}", icon="🚨")
        return None