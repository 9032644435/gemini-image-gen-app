import os
import google.generativeai as genai
from google.generativeai import types
from flask import Flask, render_template, request, jsonify
from PIL import Image
from io import BytesIO
import uuid
import atexit
import sys # Add sys import for flushing

print("--- app.py: STARTING SCRIPT ---", flush=True) # Added log

app = Flask(__name__)

# --- Configuration ---
GENERATED_IMG_DIR = "static/generated-images"
if not os.path.exists(GENERATED_IMG_DIR):
    os.makedirs(GENERATED_IMG_DIR)

API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    print("WARNING: GEMINI_API_KEY environment variable not found.", flush=True) # Added flush
    # Handle missing key if necessary, maybe raise error or use placeholder
    # For now, let's proceed and see if genai.configure handles it

print("--- app.py: Attempting genai.configure... ---", flush=True) # Added log
try:
    genai.configure(api_key=API_KEY)
    client = genai.Client(api_key=API_KEY) # Assuming you need a client instance too
    print("--- app.py: genai.configure SUCCEEDED ---", flush=True) # Added log
except Exception as e:
    print(f"--- app.py: genai.configure FAILED: {e} ---", flush=True) # Added log
    # Decide how to handle configuration failure - maybe exit or raise?
    # For now, let it proceed to see Gunicorn logs

# --- Routes ---
@app.route('/')
def index():
    print("--- app.py: Handling request for / ---", flush=True) # Added log
    return render_template('index.html')

@app.route('/generate-image', methods=['POST'])
def handle_generate_image():
    try:
        # Get data from the frontend
        data = request.json
        prompt = data.get('prompt')
        # Aspect ratio is handled differently now (often within the prompt or specific model tuning)
        # We will use the standard Imagen model which defaults to square unless specified otherwise
        # aspect_ratio = data.get('aspect_ratio') # We might not use this directly anymore

        if not prompt:
            return jsonify({"error": "Prompt is required."}), 400

        # --- Instantiate the Imagen Model ---
        # Use a model specifically capable of image generation, like Gemini 1.5 Pro or Flash with image output
        # Or ideally, an explicit Imagen model if available via the library this way
        # NOTE: As of late 2025, direct Imagen generation via 'generate_content' might still be evolving.
        # This uses the standard multimodal approach which might produce image descriptions
        # or require specific prompting for direct image output. Adjust model name if needed.
        print(f"--- app.py: Instantiating model gemini-1.5-flash ---", flush=True)
        # model = genai.GenerativeModel('gemini-1.5-flash') # Or 'gemini-1.5-pro' if preferred

        # --- CORRECTED APPROACH using a dedicated Imagen model if the library structure supports it ---
        # The previous error used 'imagegeneration@006' - let's try calling Imagen more directly if the library allows
        # Based on common patterns, it might be:
        print(f"--- app.py: Instantiating Imagen model ---", flush=True)
        model = genai.GenerativeModel('gemini-1.5-pro') # Still using Pro, will instruct it for images


        # --- Call the Google AI API - Updated Method ---
        print(f"Generating image with prompt: {prompt}", flush=True)
        # Instruct the model clearly to GENERATE an image
        generation_prompt = f"Generate an image based on this description: {prompt}"

        # Use generate_content - the response structure needs checking
        response = model.generate_content(generation_prompt)

        # --- Process and Save the Image ---
        # The response structure for image generation needs careful handling.
        # It might be in response.parts[0].image_data or similar.
        # THIS PART IS AN EDUCATED GUESS AND MAY NEED DEBUGGING BASED ON ACTUAL RESPONSE
        print(f"--- app.py: Processing response ---", flush=True)
        if not response.parts or not hasattr(response.parts[0], 'blob') or not response.parts[0].blob.mime_type.startswith('image/'):
             # Check if there's text, maybe an error or description instead of image
             if response.text:
                 print(f"--- app.py: API returned text instead of image: {response.text}", flush=True)
                 # Check for refusal / safety flags
                 try:
                    if response.prompt_feedback.block_reason:
                        raise ValueError(f"Image generation blocked due to safety settings: {response.prompt_feedback.block_reason}")
                 except (AttributeError, ValueError):
                    pass # No block reason found
                 raise ValueError(f"API did not return image data. Response text: {response.text}")
             else:
                raise ValueError("API did not return image data or text explanation.")

        image_blob = response.parts[0].blob
        image_bytes = image_blob.data
        image = Image.open(BytesIO(image_bytes))

        # Create a unique filename
        filename = f"{uuid.uuid4()}.png" # Assuming PNG, adjust if needed based on mime_type
        save_path = os.path.join(GENERATED_IMG_DIR, filename)
        image.save(save_path)

        # Send the *URL* of the saved image back to the frontend
        image_url = f"/{save_path}" # e.g., /static/generated-images/1234.png
        print(f"Image saved to: {image_url}", flush=True)

        return jsonify({"url": image_url, "prompt": prompt})

    except Exception as e:
        print(f"--- app.py: Error during image generation: {e} ---", flush=True)
        # Specific error checking can remain
        if "API key not valid" in str(e):
             return jsonify({"error": "The provided GEMINI_API_KEY is invalid."}), 500
        # Add check for permission denied / quota
        if "permission denied" in str(e).lower() or "quota exceeded" in str(e).lower():
            return jsonify({"error": f"API Error: {e}"}), 429 # Return 429 for quota

        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

# --- Cleanup ---
def cleanup_generated_images():
    print("--- app.py: Cleaning up generated images... ---", flush=True) # Added log
    for filename in os.listdir(GENERATED_IMG_DIR):
        if filename.endswith(".png"): # Or other image extensions
            os.remove(os.path.join(GENERATED_IMG_DIR, filename))

atexit.register(cleanup_generated_images)

print("--- app.py: SCRIPT LOADED, ready to run Flask app ---", flush=True) # Added log
