import os
import io
import base64
from flask import Flask, request, jsonify, render_template, send_file
from PIL import Image, ImageEnhance
from werkzeug.utils import secure_filename
import tempfile
import math
from typing import Sequence, Tuple, Optional

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'

# Ensure upload folder exists
# os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'webp'}

# Store original images in memory (in production, consider using Redis or similar)
original_images = {}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def largest_rotated_rect(w, h, angle):
    # Returns width and height of the largest possible axis-aligned rectangle
    # within the rotated rectangle (no white corners)
    angle = abs(angle)
    if w <= 0 or h <= 0:
        return 0, 0
    quadrant = int(math.floor(angle / (math.pi / 2))) & 3
    sign_alpha = angle if ((quadrant & 1) == 0) else math.pi - angle
    alpha = (sign_alpha % math.pi)
    bb_w = w * math.cos(alpha) + h * math.sin(alpha)
    bb_h = w * math.sin(alpha) + h * math.cos(alpha)
    gamma = math.atan2(h, w) if w < h else math.atan2(w, h)
    delta = math.pi - alpha - gamma
    length = h if w < h else w
    d = length * math.cos(alpha)
    a = d * math.sin(alpha) / math.sin(delta)
    y = a * math.cos(gamma)
    x = y * math.tan(gamma)
    return int(bb_w - 2 * x), int(bb_h - 2 * y)

def process_image_with_settings(original_image_data, settings):
    """Process image with all settings applied to the original image"""
    try:
        # Convert base64 to PIL Image
        image_bytes = base64.b64decode(original_image_data.split(',')[1])
        image = Image.open(io.BytesIO(image_bytes))
        
        # Apply brightness
        if 'brightness' in settings and settings['brightness'] != 1.0:
            enhancer = ImageEnhance.Brightness(image)
            image = enhancer.enhance(float(settings['brightness']))
        
        # Apply contrast
        if 'contrast' in settings and settings['contrast'] != 1.0:
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(float(settings['contrast']))
        
        # Apply rotation
        if 'rotation' in settings and settings['rotation'] != 0:
            angle = int(settings['rotation'])
            if angle != 0:
                image = image.rotate(angle, expand=True, fillcolor=(255,255,255,0) if image.mode == 'RGBA' else (255,255,255))
        
        # Apply flip operations
        if 'flip_horizontal' in settings and settings['flip_horizontal']:
            image = image.transpose(Image.FLIP_LEFT_RIGHT)
        
        if 'flip_vertical' in settings and settings['flip_vertical']:
            image = image.transpose(Image.FLIP_TOP_BOTTOM)
        
        # Convert back to base64
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        buffer.seek(0)
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"
    
    except Exception as e:
        print(f"Error processing image: {str(e)}")
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        # Read file and convert to base64
        file_data = file.read()
        img_str = base64.b64encode(file_data).decode()
        
        # Determine MIME type
        filename = secure_filename(file.filename)
        file_ext = filename.rsplit('.', 1)[1].lower()
        mime_type = f"image/{file_ext}" if file_ext != 'jpg' else 'image/jpeg'
        
        image_data = f"data:{mime_type};base64,{img_str}"
        
        # Store original image with a unique identifier
        import uuid
        image_id = str(uuid.uuid4())
        original_images[image_id] = image_data
        
        return jsonify({
            'success': True,
            'image': image_data,
            'filename': filename,
            'image_id': image_id
        })
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/process', methods=['POST'])
def process():
    data = request.get_json()
    
    if not data or 'image_id' not in data or 'settings' not in data:
        return jsonify({'error': 'Missing required data'}), 400
    
    image_id = data['image_id']
    settings = data['settings']
    
    if image_id not in original_images:
        return jsonify({'error': 'Original image not found'}), 404
    
    original_image_data = original_images[image_id]
    processed_image = process_image_with_settings(original_image_data, settings)
    
    if processed_image:
        return jsonify({
            'success': True,
            'processed_image': processed_image
        })
    else:
        return jsonify({'error': 'Failed to process image'}), 500

@app.route('/download', methods=['POST'])
def download():
    data = request.get_json()
    
    if not data or 'image_id' not in data or 'filename' not in data or 'settings' not in data:
        return jsonify({'error': 'Missing required data'}), 400
    
    try:
        image_id = data['image_id']
        settings = data['settings']
        
        if image_id not in original_images:
            return jsonify({'error': 'Original image not found'}), 404
        
        original_image_data = original_images[image_id]
        processed_image_data = process_image_with_settings(original_image_data, settings)
        
        if not processed_image_data:
            return jsonify({'error': 'Failed to process image for download'}), 500
        
        # Convert base64 to image
        image_bytes = base64.b64decode(processed_image_data.split(',')[1])
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
            tmp_file.write(image_bytes)
            tmp_path = tmp_file.name
        
        # Generate download filename
        original_filename = data['filename']
        name, ext = os.path.splitext(original_filename)
        download_filename = f"{name}_processed.png"
        
        return send_file(
            tmp_path,
            as_attachment=True,
            download_name=download_filename,
            mimetype='image/png'
        )
    
    except Exception as e:
        return jsonify({'error': f'Download failed: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000))) 