# -*- coding: utf-8 -*-
!pip install streamlit-jupyter
!pip install google-generativeai
!pip install python-dotenv
!pip install Pillow
!pip install -upgrade streamlit tqdm ipywidgets

import streamlit as st
import pandas as pd
import math
from pathlib import Path

# Import necessary libraries
import os
import streamlit as st
from PIL import Image
from dotenv import load_dotenv  # Use dotenv to load environment variables
import google.generativeai as genai

# Load all the environment variables from the .env file
load_dotenv()

# Get the API key from the environment variables
api_key = os.getenv("GOOGLE_API_KEY")

# Check if the API key is set
if not api_key:
    st.error("API key not found. Please set the GOOGLE_API_KEY environment variable in your .env file.")
    raise ValueError("API key not found. Please set the GOOGLE_API_KEY environment variable.")
else:
    # Configure the generative AI client with the provided API key
    genai.configure(api_key=api_key)
    st.success("API key successfully loaded and configured!")

def get_gemini_response(input_text, image, prompt):
    """Generates a response from the Gemini model based on the input and image."""
    try:
        # Use generative AI model for processing input and image
        response = genai.generate_text(prompt=prompt, input=image)
        return response.text  # Get the text response
    except Exception as e:
        st.error(f"An error occurred while generating the response: {str(e)}")
        return None

def input_image_details(uploaded_file):
    """Returns image details from the uploaded file."""
    if uploaded_file is not None:
        # Read the file into bytes
        bytes_data = uploaded_file.getvalue()
        image_parts = [
            {
                "mime_type": uploaded_file.type,  # Get the MIME type of the uploaded file
                "data": bytes_data
            }
        ]
        return image_parts
    else:
        raise FileNotFoundError("File not found")

# Initialize the Streamlit app
st.set_page_config(page_title="MultiLanguage Text Extractor")
st.header("MultiLanguage Text Extractor")

# User inputs
input_text = st.text_input("Input prompt:", key="input")
uploaded_file = st.file_uploader("Choose an image containing text...", type=["jpg", "jpeg", "png"], key="image")

# Display uploaded image
if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Image", use_column_width=True)

# Button to process the image
submit = st.button("Tell me about the extracted text")

# Generative AI prompt
input_prompt = """
You are an expert in understanding text in images. We will upload an image of the text, and you will analyze and describe the text in the image.
The text can be in any language.
"""

# Button click logic
if submit:
    try:
        image_data = input_image_details(uploaded_file)
        response = get_gemini_response(input_text, image_data, input_prompt)

        st.subheader("The Response is:")
        if response:
            st.write(response)
        else:
            st.error("No response generated. Please try again.")
    except FileNotFoundError as e:
        st.error(str(e))
