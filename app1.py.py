import streamlit as st
st.set_page_config(page_title="Ancient & Modern OCR", layout="wide")  # Must be first Streamlit command

import easyocr
from PIL import Image
import os
from dotenv import load_dotenv
import base64
import io
import csv
import json
import torch
import numpy as np
from langdetect import detect
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
import sqlite3
import unicodedata
from datetime import datetime
import regex
from langchain.output_parsers import StructuredOutputParser
import pandas as pd
import openai
import pytesseract
import subprocess

# Configure Tesseract path and optionally specify tessdata directory
pytesseract.pytesseract.tesseract_cmd = r"C:\\Users\\amanz\\Python313\\project\\Mythical animals in archiology files\\OCR app\\tesseract.exe"
os.environ['TESSDATA_PREFIX'] = r"C:\\Users\\amanz\\Python313\\project\\Mythical animals in archiology files\\OCR app\\tessdata"  # Optional: if using custom tessdata directory

# Confirm Tesseract is working
try:
    version = subprocess.check_output([pytesseract.pytesseract.tesseract_cmd, "--version"], text=True)
    st.sidebar.success("✅ Tesseract is working:\n" + version.splitlines()[0])
except Exception as e:
    st.sidebar.error(f"❌ Tesseract Error: {str(e)}")

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Load Ge'ez dictionary from a JSON file
try:
    with open("geez_dict.json", "r", encoding="utf-8") as f:
        geez_dict = json.load(f)
except FileNotFoundError:
    geez_dict = {}

st.sidebar.title("🔧 Settings")

# Auto-detect script option
auto_detect_script = st.sidebar.checkbox("🧠 Auto-detect Script Type", value=True)

# Default or manual script selection (if auto-detect is off)
manual_script_type = st.sidebar.radio("🧬 Script Type", ['Modern (OCR)', 'Ancient (GPT-4 Vision)'])

# Confidence threshold
min_confidence = st.sidebar.slider("🧐 Min OCR Confidence", 0, 100, 50)

# Translation options
translate = st.sidebar.checkbox("🌐 Translate OCR text?")
available_langs = ['eng', 'fra', 'spa', 'deu', 'ita', 'por', 'ara', 'chi_sim', 'hin', 'amh']
lang_display = {
    'eng': 'English', 'fra': 'French', 'spa': 'Spanish', 'deu': 'German',
    'ita': 'Italian', 'por': 'Portuguese', 'ara': 'Arabic', 'chi_sim': 'Chinese (Simplified)',
    'hin': 'Hindi', 'amh': 'Amharic'
}
target_lang = st.sidebar.selectbox("📅 Translate To (Auto overrides if language is detected)", list(lang_display.values()), index=1)

# Optional GPT-4 prompt
user_prompt = st.sidebar.text_area("✍️ GPT-4 Prompt (for Ancient Scripts)", height=140, value="This image contains Geʿez or another ancient script. Please interpret or describe the content.")

# Show installed Tesseract languages
if st.sidebar.button("📚 List Installed OCR Languages"):
    try:
        lang_output = subprocess.check_output([pytesseract.pytesseract.tesseract_cmd, "--list-langs"], stderr=subprocess.STDOUT, text=True)
        st.sidebar.success("Installed Tesseract Languages:")
        st.sidebar.text(lang_output)
    except subprocess.CalledProcessError as e:
        st.sidebar.error(f"Error listing Tesseract languages: {e.output}")

try:
    lang_output = subprocess.check_output([pytesseract.pytesseract.tesseract_cmd, "--list-langs"], stderr=subprocess.STDOUT, text=True)
    installed_langs = lang_output.splitlines()[1:]  # skip first line
except Exception:
    installed_langs = []

# Ge'ez dictionary editing
if st.sidebar.checkbox("✏️ Edit Geʽez Dictionary"):
    new_char = st.sidebar.text_input("Character")
    new_translit = st.sidebar.text_input("Transliteration")
    new_meaning = st.sidebar.text_input("Meaning")
    if st.sidebar.button("Add to Dictionary"):
        geez_dict[new_char] = {"transliteration": new_translit, "meaning": new_meaning}
        with open("geez_dict.json", "w", encoding="utf-8") as f:
            json.dump(geez_dict, f, ensure_ascii=False, indent=2)
        st.sidebar.success(f"Added {new_char} to dictionary.")

if st.sidebar.checkbox("🔍 Search Geʽez Dictionary"):
    search_query = st.sidebar.text_input("🔎 Search character or transliteration")
    if search_query:
        st.sidebar.markdown("### Search Results")
        for char, data in geez_dict.items():
            if search_query in char or search_query in data.get("transliteration", ""):
                st.sidebar.markdown(f"**{char}** → {data.get('transliteration')} — {data.get('meaning')}")

st.title("📜 Multilingual OCR + Ancient Script Reader")
uploaded_files = st.file_uploader("📄 Upload image(s) (JPG/PNG)", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

st.sidebar.title("🛠 Manual Correction")
manual_text_input = st.sidebar.text_area("✍️ Manually correct OCR output")

conn = sqlite3.connect("ocr_results.db")
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS results (
        filename TEXT, 
        raw_text TEXT, 
        translated_text TEXT, 
        transliteration TEXT, 
        meaning TEXT,
        entities TEXT,
        timestamp TEXT
    )
""")
conn.commit()

# OCR processing block
if uploaded_files:
    for uploaded_file in uploaded_files:
        try:
            image = Image.open(uploaded_file).convert("RGB")
            st.image(image, caption=f"Uploaded Image: {uploaded_file.name}", use_column_width=True)
            text = pytesseract.image_to_string(image, lang='eng')
            st.text_area("📄 OCR Result", value=text, height=300)
        except Exception as e:
            st.error(f"🚫 OCR failed for {uploaded_file.name}: {str(e)}")
