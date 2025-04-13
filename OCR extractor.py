import streamlit as st
import openai
import easyocr
import os
from dotenv import load_dotenv
from PIL import Image
import base64
import json
import torch
import numpy as np
from langdetect import detect
import sqlite3
from datetime import datetime
import regex  # Import regex for script detection

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Load Ge'ez dictionary from a JSON file
try:
    with open("geez_dict.json", "r", encoding="utf-8") as f:
        geez_dict = json.load(f)
except FileNotFoundError:
    geez_dict = {}

st.set_page_config(page_title="Ancient & Modern OCR", layout="wide")
st.sidebar.title("🔧 Settings")

# Auto-detect script option
auto_detect_script = st.sidebar.checkbox("🧠 Auto-detect Script Type", value=True)

# Default or manual script selection (if auto-detect is off)
manual_script_type = st.sidebar.radio("🧬 Script Type", ['Modern (OCR)', 'Ancient (GPT-4 Vision)'])

# Confidence threshold
min_confidence = st.sidebar.slider("🧐 Min OCR Confidence", 0, 100, 50)

# Translation options
translate = st.sidebar.checkbox("🌐 Translate OCR text?")
easyocr_langs = ['english', 'french', 'spanish', 'german', 'italian', 'portuguese', 'arabic', 'chinese_simplified', 'hindi', 'amharic']
available_langs = ['en', 'fr', 'es', 'de', 'it', 'pt', 'ar', 'zh', 'hi', 'am']
target_lang = st.sidebar.selectbox("📥 Translate To (Auto overrides if language is detected)", available_langs, index=1)

# Optional GPT-4 prompt
user_prompt = st.sidebar.text_area("✍️ GPT-4 Prompt (for Ancient Scripts)", height=140, value="This image contains Geʿez or another ancient script. Please interpret or describe the content.")

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

# Ge'ez dictionary search
if st.sidebar.checkbox("🔍 Search Geʽez Dictionary"):
    search_query = st.sidebar.text_input("🔎 Search character or transliteration")
    if search_query:
        st.sidebar.markdown("### Search Results")
        for char, data in geez_dict.items():
            if search_query.lower() in char.lower() or search_query.lower() in data.get("transliteration", "").lower():
                st.sidebar.markdown(f"**{char}** → {data.get('transliteration')} — {data.get('meaning')}")

# Upload image
st.title("📜 Multilingual OCR + Ancient Script Reader")
uploaded_files = st.file_uploader("📤 Upload image(s) (JPG/PNG)", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

# Manual correction
st.sidebar.title("🛠 Manual Correction")
manual_text_input = st.sidebar.text_area("✏️ Manually correct OCR output")

# Database setup
with sqlite3.connect("ocr_results.db") as conn:
    cursor = conn.cursor()
    cursor.execute(""" 
        CREATE TABLE IF NOT EXISTS results (
            filename TEXT, 
            raw_text TEXT, 
            translated_text TEXT, 
            transliteration TEXT, 
            meaning TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()

# Helper: Check if Ge'ez script is likely present
def contains_geez(text):
    for char in text:
        try:
            # Enhanced Ge'ez detection using Unicode range
            if '\u1200' <= char <= '\u137F':  # Ethiopic Unicode range
                return True
        except ValueError:
            continue
    return False

# Detect script type (added regex import)
def detect_script(text):
    if regex.search(r'\p{Script=Ethiopic}', text):  # Check if regex is available
        return "Ethiopic"
    return "Unknown"

# Initialize EasyOCR reader manually and store it in Streamlit session state
if "easyocr_reader" not in st.session_state:
    st.session_state.easyocr_reader = easyocr.Reader(easyocr_langs, gpu=torch.cuda.is_available())

reader = st.session_state.easyocr_reader

# GPT-4 Vision Interaction using updated OpenAI SDK
def call_gpt4_vision(prompt, image):
    base64_image = base64.b64encode(image).decode('utf-8')
    try:
        response = openai.chat.completions.create(
            model="gpt-4-vision-preview",  # Make sure you have access to this model
            messages=[ 
                {"role": "user", "content": prompt},
                {"role": "user", "content": f"data:image/jpeg;base64,{base64_image}"}
            ],
            max_tokens=1000
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        st.error(f"❌ GPT-4 Vision Error: {str(e)}")
        return ""

# Process multiple uploaded images
if uploaded_files:
    for uploaded_file in uploaded_files:
        image = Image.open(uploaded_file)
        # Perform OCR and GPT-4 processing
        ocr_result = reader.readtext(np.array(image))
        ocr_text = " ".join([result[1] for result in ocr_result if result[2] >= min_confidence / 100])
        
        st.write(f"### OCR Output for {uploaded_file.name}:")
        st.write(ocr_text)

        # Detect if it's a modern or ancient script
        script = detect_script(ocr_text) if auto_detect_script else manual_script_type
        st.write(f"Detected Script: {script}")

        # If it's an ancient script, use GPT-4 Vision for interpretation
        if script == "Ethiopic" or "Ancient" in script:
            gpt_response = call_gpt4_vision(user_prompt, uploaded_file.read())
            st.write("### GPT-4 Interpretation:")
            st.write(gpt_response)

        # Optionally, translate the OCR text
        if translate:
            translated_text = openai.Completion.create(
                engine="text-davinci-003", 
                prompt=f"Translate the following text to {target_lang}: {ocr_text}", 
                max_tokens=1000
            ).choices[0].text.strip()
            st.write(f"### Translated Text:")
            st.write(translated_text)

        # Save results to the database
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with sqlite3.connect("ocr_results.db") as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO results (filename, raw_text, translated_text, transliteration, meaning, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (uploaded_file.name, ocr_text, translated_text, "", "", timestamp))
            conn.commit()
