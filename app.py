import os
import requests
from flask import Flask, render_template, request, jsonify
from PIL import Image
from io import BytesIO
import vertexai
from vertexai.preview.generative_models import GenerativeModel, Part
import base64

app = Flask(__name__)

# Initialize Vertex AI
vertexai.init(project="gemini-image-generator-420017", location="us-central1")

# Load the generative model
model = GenerativeModel("gemini-pro-vision")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate-image', methods=['POST'])
def generate_image():
    try:
        data = request.get_json()
        prompt = data.get('prompt')

        if not prompt:
            return jsonify({'error': 'Prompt is required'}), 400

        # Generate the image using Vertex AI
        response = model.generate_content(
            [f"Generate an image of: {prompt}"],
            generation_config={
                "max_output_tokens": 2048,
                "temperature": 0.4,
                "top_p": 1,
                "top_k": 32,
            },
        )

        # Decode the base64 image
        image_data = base64.b64decode(response.candidates[0].content.parts[0].inline_data.data)

        # Create the directory if it doesn't exist
        if not os.path.exists("static/generated-images"):
            os.makedirs("static/generated-images")

        # Save the image
        image_path = f"static/generated-images/{prompt.replace(' ', '_')}.png"
        with open(image_path, "wb") as f:
            f.write(image_data)

        return jsonify({'image_url': f'/{image_path}'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=int(os.environ.get("PORT", 8080)))
