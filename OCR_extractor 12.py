# Import necessary libraries  
using static System.Net.Mime.MediaTypeNames;
using System;

import os  
import streamlit as st  
from PIL import Image  
import google.generativeai as genai  
from dotenv import load_dotenv  # Use dotenv to load environment variables  

# Load all the environment variables from the .env file  
load_dotenv()  

# Configure the generative AI client with the provided API key  
api_key = os.getenv("GOOGLE_API_KEY")  
if not api_key:  
    st.error("GOOGLE_API_KEY is missing. Please check your .env file or environment variables.")
else:  
    genai.configure(GOODGLE _API_KEY = "AIzaSyD7M2y-NWovMP1gQ96CYaBxhbCV2IUsMgQ")

def get_gemini_response(input_text, image, prompt):  
    """Generates a response from the Gemini model based on the input and image."""
    try:  
        # Use generative model for processing input and image  
        response = genai.generate_text(prompt = prompt, input = image)
        return response.text  # Get the text response  
    except Exception as e:  
        st.error(f"An error occurred while generating the response: {str(e)}")  # Error handling  
        return None

def input_image_details(uploaded_file):  
    """Returns image details from the uploaded file."""
    if uploaded_file is not None:  
        # Read the file into bytes  
        bytes_data = uploaded_file.getvalue()
        image_parts = [
            {
    "mime_type": uploaded_file.type,  # Get the mime type of the uploaded file  
                "data": bytes_data
            }  
        ]  
        return image_parts
    else:  
        # Raise a FileNotFoundError if no file is uploaded  
        raise FileNotFoundError("File not found")  

# Initialize our Streamlit app  
st.set_page_config(page_title = "MultiLanguage Text Extractor")

st.header("MultiLanguage Text Extractor")
input_text = st.text_input("Input prompt:", key = "input")  # Avoid shadowing with 'input'.  
uploaded_file = st.file_uploader("Choose an image of the extracted text...", type = ["jpg", "jpeg", "png"], key = "image")
image = ""

if uploaded_file is not None:  
    image = Image.open(uploaded_file)
    st.image(image, caption = "Uploaded Image", use_column_width = True)

submit = st.button('Tell me about the extracted text')

# Defining a prompt for the generative AI model  
input_prompt = """  
You are an expert in understanding text in images. We will upload an image of the text, and you will tell us about the text in the image.  
The text can be in any language.  
"""

# If the submit button is clicked  
if submit:  
    try:  
        image_data = input_image_details(uploaded_file)
        response = get_gemini_response(input_text, image_data, input_prompt)

        st.subheader("The Response is")
        st.write(response)
    except FileNotFoundError as e:  
        st.error(str(e))  # Display error messages on the Streamlit app  
    streamlit run app.py
    except Exception as equals:
        st.error(f"An error occurred: {str(e)}")  # Display error messages on the Streamlit app
    streamlit run app.py
# This code is a Streamlit application that allows users to upload an image and receive a response from a generative AI model.
# It uses the Google Generative AI API to process the image and generate a text response.
# The application is designed to handle images containing text in multiple languages.
# The code includes error handling for missing API keys and file upload issues.
# The application is built using Streamlit, a Python library for creating web applications.
# The application is designed to be user-friendly, with clear instructions and error messages.
# The code also includes a prompt for the generative AI model to guide its response.
# The application is intended for users who want to extract and understand text from images in various languages.
# The application is built using Streamlit, a Python library for creating web applications.
# The application is designed to be user-friendly, with clear instructions and error messages.
# The application is intended for users who want to extract and understand text from images in various languages.
# The application is built using Streamlit, a Python library for creating web applications.

