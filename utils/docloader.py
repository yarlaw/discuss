import os
import fitz
import requests
from bs4 import BeautifulSoup
import streamlit as st
from urllib.parse import urlparse, unquote

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

def extract_persona_name_from_wiki_url(url):
    try:
        if not url or "wikipedia.org" not in url:
            return None
            
        parsed_url = urlparse(url)
        path_parts = parsed_url.path.strip('/').split('/')
        
        if not path_parts or "wiki" not in path_parts:
            return None
            
        wiki_index = path_parts.index("wiki")
        if wiki_index < len(path_parts) - 1:
            title = path_parts[wiki_index + 1]
            
            title = unquote(title)
            
            title = title.replace('_', ' ')
            
            return title
        
        return None
        
    except Exception:
        return None