import os
import vertexai
from vertexai.preview.generative_models import GenerativeModel, Part
from flask import Flask, render_template, request, jsonify
from PIL import Image
from io import BytesIO
import uuid
import atexit
import sys # Add sys import for flushing
import base64

print("--- app.py: STARTING SCRIPT ---", flush=True) # Added log

app = Flask(__name__)

# --- Configuration ---
GENERATED_IMG_DIR = "static/generated-images"
if not os.path.exists(GENERATED_IMG_DIR):
    os.makedirs(GENERATED_IMG_DIR)

print("--- app.py: Attempting vertexai.init... ---", flush=True) # Added log
try:
    vertexai.init(project=os.environ.get("GCP_PROJECT"), location=os.environ.get("GCP_LOCATION"))
    print("--- app.py: vertexai.init SUCCEEDED ---", flush=True) # Added log
except Exception as e:
    print(f"--- app.py: vertexai.init FAILED: {e} ---", flush=True) # Added log
    # Decide how to handle configuration failure - maybe exit or raise?
    # For now, let it proceed to see Gunicorn logs

# --- Routes ---
@app.route('/')
def index():
    print("--- app.py: Handling request for / ---", flush=True) # Added log
    return render_template('index.html')

@app.route('/generate-image', methods=['POST'])
def generate_image():
    try:
        data = request.get_json()
        prompt = data.get('prompt')

        if not prompt:
            return jsonify({'error': 'Prompt is required'}), 400

        # Generate the image using the Imagen model
        model = GenerativeModel("imagegeneration@006")
        response = model.generate_content(
            [f"Generate an image of: {prompt}"],
            generation_config={
                "max_output_tokens": 2048,
                "temperature": 0.4,
                "top_p": 1,
                "top_k": 32,
            },
        )

        image_data = base64.b64decode(response.candidates[0].content.parts[0].inline_data.data)

        # Save the image
        image_path = f"static/generated-images/{uuid.uuid4()}.png"
        with open(image_path, "wb") as f:
            f.write(image_data)

        return jsonify({'image_url': f'/{image_path}'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- Cleanup ---
def cleanup_generated_images():
    print("--- app.py: Cleaning up generated images... ---", flush=True) # Added log
    for filename in os.listdir(GENERATED_IMG_DIR):
        if filename.endswith(".png"): # Or other image extensions
            os.remove(os.path.join(GENERATED_IMG_DIR, filename))

atexit.register(cleanup_generated_images)

print("--- app.py: SCRIPT LOADED, ready to run Flask app ---", flush=True) # Added log
