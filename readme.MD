# 📸 Camera Trap Metadata Editor

A professional web-based application for viewing, editing, and managing metadata of camera trap images. Designed for wildlife researchers, conservationists, and field biologists who need to efficiently organize and annotate large collections of camera trap photos with AI-powered species identification.


## 🌟 What This Software Does

The Camera Trap Metadata Editor streamlines the camera trap image analysis workflow by providing:

- **🤖 AI-Powered Species Identification**: Advanced computer vision using OpenAI's GPT-4 Vision API to automatically identify wildlife species from image selections
- **📊 Intelligent Footer Data Extraction**: Automatically extracts temperature, camera ID, and timestamp data from camera trap image footers
- **🗂️ Comprehensive Metadata Management**: Edit, add, and organize custom metadata fields specific to wildlife research
- **💾 Dual Storage System**: Saves metadata to both human-readable sidecar files and embedded EXIF data
- **🌍 Geographic Customization**: Fully customizable AI prompts tailored to specific geographic regions and local wildlife
- **📱 Modern Web Interface**: Responsive design that works seamlessly across desktop, tablet, and mobile devices

### Perfect For:
- Wildlife researchers and field biologists
- Conservation organizations
- Camera trap survey projects
- Biodiversity monitoring programs
- Ecological research institutions
- Wildlife photography projects

## ✨ Key Features

### 🔍 Advanced AI Species Identification
- **Click-and-drag selection**: Select specific areas of images for targeted species identification
- **Geographic awareness**: AI prompts customized for your specific location and local wildlife
- **Confidence scoring**: Receive confidence levels for species identifications
- **Scientific naming**: Get both common and scientific names for identified species
- **Behavioral analysis**: AI describes animal behavior and posture

### 📋 Comprehensive Metadata Management
- **Pre-configured fields**: Species, Count, Behavior, Weather, Location, Camera_ID, Researcher, Notes
- **Custom field creation**: Add unlimited project-specific metadata fields
- **EXIF integration**: View and edit existing camera EXIF data
- **Batch processing**: Efficient navigation through large image collections
- **Data validation**: Ensures metadata integrity and consistency

### 🖼️ Professional Image Viewer
- **High-quality display**: Optimized image rendering with zoom and pan capabilities
- **Keyboard navigation**: Arrow keys, Home, End for rapid image browsing
- **Image information**: File size, dimensions, and technical details
- **Responsive design**: Works perfectly on any screen size

### 💾 Robust Data Storage
- **Sidecar files**: Human-readable `[filename]_metadata.txt` files alongside images
- **EXIF embedding**: Metadata written directly to JPEG/TIFF image files
- **Backup protection**: Automatic backup creation before modifying images
- **Cross-platform compatibility**: Works on Windows, macOS, and Linux

## 🚀 Installation

### Prerequisites
- **Python 3.8+** (recommended: Python 3.9 or higher)
- **OpenAI API Key** (for AI species identification)
- **Modern web browser** (Chrome, Firefox, Safari, Edge)

### Step 1: Clone the Repository
```bash
git clone https://github.com/anderdad/camtrap-metadata.git
cd camtrap-metadata.
```

### Step 2: Create Virtual Environment (Recommended)
```bash
# Create virtual environment
python -m venv camera_trap_env

# Activate virtual environment
# On macOS/Linux:
source camera_trap_env/bin/activate
# On Windows:
camera_trap_env\Scripts\activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

## 🔧 Environment Configuration

### Setting Up Environment Variables

1. **Copy the example environment file:**
```bash
cp .env.example .env
```

2. **Edit the `.env` file with your configuration:**
```bash
# Required: OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Optional: Camera Trap Location Configuration
CAMERA_TRAP_LOCATION=Namibia, Africa
CAMERA_TRAP_REGION=Southern Africa
```

### Environment Variables Explained

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `OPENAI_API_KEY` | **Yes** | Your OpenAI API key for species identification | `sk-proj-abc123...` |
| `CAMERA_TRAP_LOCATION` | No | Specific location of your camera traps | `Yellowstone National Park, USA` |
| `CAMERA_TRAP_REGION` | No | Broader geographic region | `North America` |

### Getting Your OpenAI API Key

1. Visit [OpenAI Platform](https://platform.openai.com/api-keys)
2. Sign up or log in to your account
3. Navigate to "API Keys" section
4. Click "Create new secret key"
5. Copy the key and paste it into your `.env` file

**Important**: Keep your API key secure and never commit it to version control.

## 🌍 Customizing AI Prompts for Your Geography

The AI species identification system is fully customizable for different geographic regions. This ensures accurate species identification based on local wildlife.

### Quick Setup for Common Regions

Edit `ai_prompt_config.py` and customize the `AI_PROMPT_TEMPLATE` for your location:

#### Example: North American Configuration
```python
AI_PROMPT_TEMPLATE = """Analyze this camera trap image crop from {location_upper} and identify any animals present.

IMPORTANT CONTEXT: This image is from a camera trap in {location}, so focus specifically on wildlife species native to or commonly found in {region} ecosystems including:

LARGE MAMMALS: White-tailed deer, mule deer, elk, moose, black bear, brown bear, mountain lion, bobcat, coyote, gray wolf, pronghorn

SMALLER MAMMALS: Raccoon, opossum, skunk, porcupine, beaver, river otter, red fox, gray fox, various squirrel species, chipmunks

BIRDS: Wild turkey, various ground-dwelling species that might trigger camera traps

Please provide:
1. Species name (common and scientific name)
2. Confidence level (High/Medium/Low) - be more confident if it matches known {region} species
3. Count of individuals visible
4. Brief description including behavior/posture
5. Habitat context if visible (forest, grassland, wetland, etc.)

Format your response as JSON with keys: species, scientific_name, confidence, count, description, habitat"""
```

#### Example: European Configuration
```python
AI_PROMPT_TEMPLATE = """Analyze this camera trap image crop from {location_upper} and identify any animals present.

IMPORTANT CONTEXT: This image is from a camera trap in {location}, so focus specifically on wildlife species native to or commonly found in {region} ecosystems including:

LARGE MAMMALS: Red deer, roe deer, wild boar, brown bear, Eurasian lynx, gray wolf, European pine marten

SMALLER MAMMALS: European badger, red fox, European hare, various mustelid species, hedgehog, squirrel species

BIRDS: Various ground-dwelling species including game birds

Please provide species identification with confidence level and count for {region} wildlife."""
```

### Advanced Customization

1. **Species Lists**: Replace with animals specific to your study area
2. **Habitat Types**: Adjust habitat descriptions (desert, rainforest, tundra, etc.)
3. **Confidence Criteria**: Modify how the AI assesses identification confidence
4. **Behavioral Categories**: Add region-specific behaviors to look for
5. **Seasonal Considerations**: Include seasonal migration or hibernation patterns

### Using Environment Variables in Prompts

The prompt system uses these variables from your `.env` file:
- `{location}`: Your specific camera trap location
- `{location_upper}`: Location in uppercase for emphasis
- `{region}`: Broader geographic region

Example `.env` configuration:
```bash
CAMERA_TRAP_LOCATION=Kruger National Park, South Africa
CAMERA_TRAP_REGION=Southern African Savanna
```

Results in prompt text:
```
"This image is from a camera trap in Kruger National Park, South Africa, so focus specifically on wildlife species native to or commonly found in Southern African Savanna ecosystems..."
```

## 🎯 How to Use

### 1. Start the Application
```bash
python app.py
```

### 2. Access the Web Interface
Open your browser and navigate to: `http://localhost:5000`

### 3. Load Your Images
1. Click **"Browse Folders"** to open the folder navigator
2. Navigate to your camera trap images directory
3. Select the folder containing your images
4. Click **"Load Images"** to begin

### 4. Navigate Through Images
- **Mouse**: Use First, Previous, Next, Last buttons
- **Keyboard**: Arrow keys (←/→), Home, End
- **Image counter**: Shows current position (e.g., "Image 15 of 247")

### 5. AI Species Identification
1. Click the **"Identify Species"** button (purple button)
2. **Click and drag** on the image to select the animal area
3. Wait for AI analysis (usually 3-5 seconds)
4. Review the populated metadata fields:
   - Species (common name)
   - Scientific_Name
   - AI_Confidence
   - Count
   - Behavior description

### 6. Footer Data Extraction
For camera traps with embedded text footers:
1. The system automatically extracts footer data when loading images
2. Look for populated fields: `Temperature_C`, `Temperature_F`, `Camera_ID`, `DateTime`
3. Data is extracted from the bottom portion of images using AI vision

### 7. Manual Metadata Editing
- **Edit existing fields**: Click in any metadata field to modify
- **Add custom fields**: Click "Add Custom Field" button
- **Delete fields**: Use the red × button next to custom fields
- **Save changes**: Click "Save Changes" to persist metadata

### 8. Data Export
Metadata is automatically saved in two formats:
- **Sidecar files**: `[imagename]_metadata.txt` (human-readable)
- **EXIF data**: Embedded in JPEG/TIFF files (machine-readable)

## 📁 Project Structure

```
camera-trap-metadata-editor/
├── app.py                    # Main Flask application
├── ai_prompt_config.py       # AI prompt customization
├── create_favicon.py         # Favicon generation script
├── requirements.txt          # Python dependencies
├── .env.example             # Environment variables template
├── .env                     # Your environment configuration (create this)
├── static/                  # Static web assets
│   ├── css/style.css        # Application styling
│   ├── js/app.js           # Frontend JavaScript
│   ├── favicon.ico         # Website favicon
│   └── [various favicon files]
├── templates/
│   └── index.html          # Main web interface
└── README.md               # This file
```

## ⌨️ Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `←` | Previous image |
| `→` | Next image |
| `Home` | First image |
| `End` | Last image |
| `Escape` | Cancel species identification mode |
| `Enter` | Load folder (when in folder input) |

## 🔧 Technical Details

### Architecture
- **Backend**: Flask (Python web framework)
- **Frontend**: Vanilla JavaScript with responsive CSS
- **AI Integration**: OpenAI GPT-4 Vision API
- **Image Processing**: Pillow (PIL), OpenCV, NumPy
- **Metadata Handling**: piexif for EXIF data manipulation

### Supported Image Formats
- **JPEG/JPG**: Full EXIF support + sidecar files
- **TIFF/TIF**: Full EXIF support + sidecar files  
- **PNG**: Sidecar files only (PNG doesn't support EXIF)

### Data Storage
- **Sidecar Files**: Plain text format for maximum compatibility
- **EXIF Metadata**: Industry-standard embedded metadata
- **Backup System**: Automatic `.backup` file creation before modifications
- **Cross-Platform**: Works on Windows, macOS, Linux

### Performance Considerations
- **Local Processing**: All image processing happens locally
- **API Efficiency**: Only sends cropped image sections to OpenAI
- **Memory Management**: Optimized for large image collections
- **Responsive Design**: Efficient loading and navigation

## 🐛 Troubleshooting

### Common Issues

**AI Species Identification Not Working**
- Verify OpenAI API key is correctly set in `.env`
- Check internet connection
- Ensure you have API credits available
- Try selecting a clearer area of the animal

**Footer Extraction Failing**
- Ensure image has a dark footer with white text
- Check that text is clearly visible and high contrast
- Try images with standard camera trap footer formats

**Images Not Loading**
- Verify folder path is correct and accessible
- Check that folder contains supported image formats
- Ensure proper file permissions

**Metadata Not Saving**
- Check write permissions in the image directory
- Verify disk space availability
- For EXIF writing, ensure images are JPEG or TIFF format

### Getting Help

1. **Check the console output** when running `python app.py`
2. **Verify environment variables** are correctly set
3. **Test with sample images** to isolate issues
4. **Check file permissions** in your image directories

## 🤝 Contributing

We welcome contributions! Please feel free to:
- Report bugs and issues
- Suggest new features
- Submit pull requests
- Improve documentation
- Share your AI prompt configurations for different regions


## 🙏 Acknowledgments

- **OpenAI** for providing the GPT-4 Vision API
- **Camera trap research community** for feedback and testing
- **Open source contributors** who made this project possible

---

**Built for wildlife research and conservation** 🦁🐘🦅

*Making camera trap data management efficient, accurate, and accessible for researchers worldwide.*

## 📄 License

Copyright (c) 2025 Anderdad 

Licensed under the MIT License. See LICENSE file for details.

[Contact Us](mailto:paul.ande@outlook.com)

![Camera Trap Metadata Editor](static/favicon-192x192.png)
