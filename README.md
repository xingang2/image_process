# Image Processor - PIL Tools

A modern web application for image manipulation using Python PIL (Pillow) library. Built with Flask and designed for deployment on Vercel.

## Features

- **Brightness Adjustment**: Adjust image brightness with real-time preview
- **Contrast Adjustment**: Enhance or reduce image contrast
- **Rotation**: Rotate images without expanding (maintains original dimensions)
- **Flip Operations**: Horizontal and vertical image flipping
- **Multiple Formats**: Supports PNG, JPG, JPEG, GIF, BMP, TIFF, WEBP

## Local Development

### Prerequisites

- Python 3.9 or higher
- pip (Python package installer)

### Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd image_process
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python app.py
```

4. Open your browser and navigate to `http://localhost:5000`

## Deployment to Vercel

### Method 1: Using Vercel CLI

1. Install Vercel CLI:
```bash
npm install -g vercel
```

2. Login to Vercel:
```bash
vercel login
```

3. Deploy the application:
```bash
vercel
```

4. Follow the prompts to complete deployment

### Method 2: Using GitHub Integration

1. Push your code to a GitHub repository
2. Go to [Vercel Dashboard](https://vercel.com/dashboard)
3. Click "New Project"
4. Import your GitHub repository
5. Vercel will automatically detect the Python configuration and deploy

### Method 3: Direct Upload

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click "New Project"
3. Choose "Upload" option
4. Upload your project files
5. Deploy

## Project Structure

```
image_process/
├── app.py              # Main Flask application
├── requirements.txt    # Python dependencies
├── vercel.json        # Vercel configuration
├── runtime.txt        # Python runtime specification
├── templates/
│   └── index.html     # Main web interface
├── uploads/           # Upload directory (created automatically)
└── README.md          # This file
```

## API Endpoints

- `GET /`: Main application interface
- `POST /upload`: Upload image file
- `POST /process`: Process image with specified operation
- `POST /download`: Download processed image

## Image Processing Operations

### Brightness
- Range: 0.1 to 3.0
- Default: 1.0 (original brightness)
- Values < 1.0: Darker image
- Values > 1.0: Brighter image

### Contrast
- Range: 0.1 to 3.0
- Default: 1.0 (original contrast)
- Values < 1.0: Lower contrast
- Values > 1.0: Higher contrast

### Rotation
- Range: -180° to 180°
- Default: 0° (no rotation)
- Rotation is performed without expanding the canvas

### Flip
- Horizontal: Mirror image left-to-right
- Vertical: Mirror image top-to-bottom

## Technical Details

- **Backend**: Flask (Python)
- **Image Processing**: PIL (Pillow)
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Deployment**: Vercel
- **File Size Limit**: 16MB
- **Supported Formats**: PNG, JPG, JPEG, GIF, BMP, TIFF, WEBP

## Browser Compatibility

- Chrome 60+
- Firefox 55+
- Safari 12+
- Edge 79+

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source and available under the [MIT License](LICENSE).

## Support

If you encounter any issues or have questions, please open an issue on the GitHub repository. 