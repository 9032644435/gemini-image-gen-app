import os
from flask import Flask, render_template, request, jsonify
from PIL import Image
from io import BytesIO
import google.generativeai as genai
import base64

app = Flask(__name__)

# Configure the generative AI client
genai.configure(api_key=os.environ["API_KEY"])

# Load the generative model
model = genai.GenerativeModel("gemini-2.5-flash-image")

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

        # Generate the image using the Gemini model
        response = model.generate_content(f"Generate an image of: {prompt}")

        # Assuming the response contains the image data in a supported format
        # This part might need adjustment based on the actual response structure
        image_data = response.candidates[0].content.parts[0].inline_data.data

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
