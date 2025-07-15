import os
import io
import base64
from flask import Flask, request, jsonify, render_template, send_file
from PIL import Image, ImageEnhance
from werkzeug.utils import secure_filename
import tempfile
import math
from typing import Sequence, Tuple, Optional
import piexif
from datetime import datetime

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'

# Ensure upload folder exists
# os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'webp'}

# Store original images in memory (in production, consider using Redis or similar)
original_images = {}

def add_exif_metadata(image):
    """Add EXIF metadata to identify processed images"""
    try:
        # Create EXIF data
        exif_dict = {
            "0th": {},
            "Exif": {},
            "GPS": {},
            "1st": {},
            "thumbnail": None,
        }
        
        # Add software information
        exif_dict["0th"][piexif.ImageIFD.Software] = "visual-reasoning-tool-bm"
        
        # Add processing information with the specific keyword
        exif_dict["0th"][piexif.ImageIFD.ImageDescription] = "visual-reasoning-tool-bm-processed-image"
        
        # Add processing date
        processing_date = datetime.now().strftime("%Y:%m:%d %H:%M:%S")
        exif_dict["0th"][piexif.ImageIFD.DateTime] = processing_date
        
        # Add artist information
        exif_dict["0th"][piexif.ImageIFD.Artist] = "visual-reasoning-tool-bm"
        
        # Add copyright information
        exif_dict["0th"][piexif.ImageIFD.Copyright] = "Processed by visual-reasoning-tool-bm"
        
        # Convert to EXIF bytes
        exif_bytes = piexif.dump(exif_dict)
        
        # Add EXIF data to image
        image.info["exif"] = exif_bytes
        
        return image
    except Exception as e:
        print(f"Error adding EXIF metadata: {str(e)}")
        return image

def is_processed_image(image_path):
    """Check if an image has been processed by this tool by examining EXIF metadata"""
    try:
        exif_dict = piexif.load(image_path)
        
        # Check if the image has the specific software tag
        if "0th" in exif_dict and piexif.ImageIFD.Software in exif_dict["0th"]:
            software = exif_dict["0th"][piexif.ImageIFD.Software].decode('utf-8')
            if software == "visual-reasoning-tool-bm":
                return True
        
        # Check if the image has the specific description tag
        if "0th" in exif_dict and piexif.ImageIFD.ImageDescription in exif_dict["0th"]:
            description = exif_dict["0th"][piexif.ImageIFD.ImageDescription].decode('utf-8')
            if description == "visual-reasoning-tool-bm-processed-image":
                return True
        
        return False
    except Exception as e:
        print(f"Error checking EXIF metadata: {str(e)}")
        return False

def calculate_rotation_scale(w, h, angle):
    """
    Calculate the scale factor needed to maintain original image size after rotation.
    This ensures the rotated image fills the original dimensions without white corners.
    """
    # Convert angle to radians
    angle_rad = math.radians(abs(angle))
    
    # Calculate the bounding box of the rotated rectangle
    cos_a = abs(math.cos(angle_rad))
    sin_a = abs(math.sin(angle_rad))
    
    # Calculate the dimensions of the rotated rectangle
    rotated_w = w * cos_a + h * sin_a
    rotated_h = w * sin_a + h * cos_a
    
    # Calculate scale factors to fit the rotated image back to original size
    scale_x = w / rotated_w
    scale_y = h / rotated_h
    
    # Use the smaller scale factor to ensure the image fits completely
    scale = min(scale_x, scale_y)
    
    return scale

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_image_with_settings(original_image_data, settings):
    """Process image with all settings applied to the original image"""
    try:
        # Convert base64 to PIL Image
        image_bytes = base64.b64decode(original_image_data.split(',')[1])
        image = Image.open(io.BytesIO(image_bytes))
        
        # Clamp brightness and contrast
        brightness = float(settings.get('brightness', 1.0))
        brightness = max(0.2, min(1.0, brightness))
        contrast = float(settings.get('contrast', 1.0))
        contrast = max(0.2, min(1.0, contrast))
        # Apply brightness
        if brightness != 1.0:
            enhancer = ImageEnhance.Brightness(image)
            image = enhancer.enhance(brightness)
        # Apply contrast
        if contrast != 1.0:
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(contrast)
        
        # Apply rotation
        if 'rotation' in settings and settings['rotation'] != 0:
            angle = int(settings['rotation'])
            if angle != 0:
                # Store original dimensions
                original_width, original_height = image.size
                
                # Calculate scale factor to maintain original size
                scale = calculate_rotation_scale(original_width, original_height, angle)
                
                # Scale up the image before rotation to compensate for the zoom effect
                scaled_width = int(original_width / scale)
                scaled_height = int(original_height / scale)
                image = image.resize((scaled_width, scaled_height), Image.Resampling.LANCZOS)
                
                # Rotate the scaled image
                image = image.rotate(angle, expand=True, fillcolor=(255,255,255,0) if image.mode == 'RGBA' else (255,255,255))
                
                # Crop to original size, centered
                rotated_width, rotated_height = image.size
                left = (rotated_width - original_width) // 2
                top = (rotated_height - original_height) // 2
                right = left + original_width
                bottom = top + original_height
                
                # Crop the image to original dimensions
                image = image.crop((left, top, right, bottom))
        
        # Apply flip operations
        if 'flip_horizontal' in settings and settings['flip_horizontal']:
            image = image.transpose(Image.FLIP_LEFT_RIGHT)
        
        if 'flip_vertical' in settings and settings['flip_vertical']:
            image = image.transpose(Image.FLIP_TOP_BOTTOM)
        
        # Add EXIF metadata to identify this as a processed image
        image = add_exif_metadata(image)
        
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