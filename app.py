#!/usr/bin/env python3
"""
Copyright (c) 2025 Anderdad <paul.ande@outlook.com>
Licensed under the MIT License.
Camera Trap Metadata Editor - Web Version
A web-based application for viewing and editing image metadata from camera traps.
"""

from flask import Flask, render_template, request, jsonify, send_file
import os
import glob
import json
import base64
import io
import shutil
import re
from PIL import Image
from PIL.ExifTags import TAGS
import piexif
from datetime import datetime
from dotenv import load_dotenv
import openai
from ai_prompt_config import AI_PROMPT_TEMPLATE
# Image processing dependencies
try:
    import cv2
    import numpy as np
    print("Image processing libraries available")
except ImportError as e:
    print(f"Image processing libraries missing: {e}")
    print("Install with: pip install opencv-python")

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Initialize OpenAI client
openai.api_key = os.getenv('OPENAI_API_KEY')
client = openai.OpenAI() if os.getenv('OPENAI_API_KEY') else None

class ImageManager:
    def __init__(self):
        self.current_folder = None
        self.image_files = []
        
    def load_folder(self, folder_path):
        if not os.path.exists(folder_path):
            raise ValueError("Folder does not exist")
        
        # Clear previous folder data completely
        self.current_folder = None
        self.image_files = []
        
        # Set new folder
        self.current_folder = folder_path
        
        # Supported image formats
        extensions = ['*.jpg', '*.jpeg', '*.png', '*.tiff', '*.tif', '*.JPG', '*.JPEG']
        
        # Load new image files
        new_image_files = []
        for ext in extensions:
            new_image_files.extend(glob.glob(os.path.join(folder_path, ext)))
        
        # Sort and assign
        new_image_files.sort()
        self.image_files = new_image_files
        
        print(f"Loaded {len(self.image_files)} images from {folder_path}")
        return len(self.image_files)
    
    def get_image_info(self, index):
        if not self.image_files or index >= len(self.image_files):
            return None
            
        image_path = self.image_files[index]
        
        try:
            # Basic file info
            file_stats = os.stat(image_path)
            image = Image.open(image_path)
            
            info = {
                'path': image_path,
                'filename': os.path.basename(image_path),
                'size_mb': round(file_stats.st_size / (1024*1024), 2),
                'dimensions': f"{image.size[0]} x {image.size[1]}",
                'index': index,
                'total': len(self.image_files)
            }
            
            # Load metadata from both EXIF and sidecar file
            metadata = {}
            
            # First load from sidecar file (this is our primary source)
            custom_metadata = self.load_custom_metadata(image_path)
            metadata.update(custom_metadata)
            
            # Then load from EXIF and extract our custom fields
            exif_metadata = self.load_exif_metadata(image_path)
            
            # Only add EXIF fields that aren't already in sidecar
            for key, value in exif_metadata.items():
                if key not in metadata:
                    metadata[key] = value
            
            # Extract footer metadata (temperature and camera ID) using OpenAI Vision API
            # Only if not already present in sidecar or EXIF
            if 'Temperature_C' not in metadata or 'Temperature_F' not in metadata or 'Camera_ID' not in metadata:
                footer_metadata = self.extract_footer_metadata(image_path)
                for key, value in footer_metadata.items():
                    if key not in metadata:  # Don't overwrite existing metadata
                        metadata[key] = value
            
            info['metadata'] = metadata
            return info
            
        except Exception as e:
            return {'error': str(e)}
    
    def load_custom_metadata(self, image_path):
        base_name = os.path.splitext(image_path)[0]
        sidecar_path = f"{base_name}_metadata.txt"
        
        metadata = {}
        if os.path.exists(sidecar_path):
            try:
                with open(sidecar_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and ':' in line:
                            key, value = line.split(':', 1)
                            metadata[key.strip()] = value.strip()
            except Exception:
                pass
                
        return metadata
    
    def load_exif_metadata(self, image_path):
        """Load metadata from EXIF data, prioritizing UserComment over individual fields"""
        metadata = {}
        
        try:
            # Check if file format supports EXIF
            file_ext = os.path.splitext(image_path)[1].lower()
            if file_ext not in ['.jpg', '.jpeg', '.tiff', '.tif']:
                return metadata
            
            # Load EXIF data using piexif for better control
            exif_dict = piexif.load(image_path)
            
            # First, check if we have UserComment with our custom metadata
            has_custom_metadata = False
            if "Exif" in exif_dict and piexif.ExifIFD.UserComment in exif_dict["Exif"]:
                user_comment = exif_dict["Exif"][piexif.ExifIFD.UserComment]
                if isinstance(user_comment, bytes):
                    try:
                        comment_text = user_comment.decode('utf-8')
                        # Check if this is our custom metadata (starts with CTME:)
                        if comment_text.startswith('CTME:'):
                            has_custom_metadata = True
                            # Remove our identifier and parse the rest
                            metadata_text = comment_text[5:]  # Remove "CTME:"
                            if ' | ' in metadata_text:
                                pairs = metadata_text.split(' | ')
                                for pair in pairs:
                                    if ':' in pair:
                                        key, value = pair.split(':', 1)
                                        key = key.strip()
                                        value = value.strip()
                                        if key and value:
                                            metadata[key] = value
                    except Exception as e:
                        print(f"Error parsing UserComment: {e}")
                        pass
            
            # Only read from individual EXIF fields if we have UserComment metadata
            # This prevents reading original camera data as our custom fields
            if has_custom_metadata:
                print(f"Found custom metadata in UserComment for {os.path.basename(image_path)}")
            else:
                # No custom metadata found, only load standard EXIF for display
                print(f"No custom metadata found in {os.path.basename(image_path)}, showing original EXIF")
            
            # Load standard EXIF fields for display (but not our reserved fields)
            image = Image.open(image_path)
            exif_data = image.getexif()
            
            if exif_data:
                for tag_id, value in exif_data.items():
                    tag_name = TAGS.get(tag_id, f"Tag_{tag_id}")
                    
                    # Skip binary data, very long values
                    if isinstance(value, bytes) or (isinstance(value, str) and len(value) > 200):
                        continue
                    
                    # If we have custom metadata, skip the fields we use for custom data
                    # If no custom metadata, show original camera EXIF but with original names
                    if has_custom_metadata:
                        # Skip our custom fields when we have UserComment metadata
                        if tag_name in ['ImageDescription', 'Software', 'Artist', 'Copyright', 'Make', 'Model', 'UserComment']:
                            continue
                    else:
                        # Show original EXIF with clear names to avoid confusion
                        if tag_name == 'Make':
                            tag_name = 'Camera_Make'
                        elif tag_name == 'Model':
                            tag_name = 'Camera_Model'
                        elif tag_name == 'Software':
                            tag_name = 'Camera_Software'
                        elif tag_name == 'ImageDescription':
                            tag_name = 'Original_Description'
                        elif tag_name == 'Artist':
                            tag_name = 'Original_Artist'
                        elif tag_name == 'Copyright':
                            tag_name = 'Original_Copyright'
                        elif tag_name == 'UserComment':
                            continue  # Skip empty UserComment
                    
                    # Only add if not already in metadata from UserComment
                    if tag_name not in metadata:
                        metadata[tag_name] = str(value)
                    
        except Exception as e:
            print(f"Error loading EXIF metadata: {e}")
            
        return metadata
    


    def extract_footer_with_openai(self, footer_image_array):
        """Use OpenAI Vision API to extract footer data from camera trap images"""
        if not client:
            print("    OpenAI client not available - check API key")
            return {}
        
        try:
            # Convert numpy array to PIL Image
            if len(footer_image_array.shape) == 3:
                # Color image
                pil_image = Image.fromarray(cv2.cvtColor(footer_image_array, cv2.COLOR_BGR2RGB))
            else:
                # Grayscale image
                pil_image = Image.fromarray(footer_image_array)
            
            # Convert to base64 for OpenAI API
            buffer = io.BytesIO()
            pil_image.save(buffer, format='PNG')
            image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            print("    Sending footer image to OpenAI Vision API...")
            
            # Create the prompt for footer extraction
            prompt = """
            This is a footer from a camera trap image. Please extract the following information and return it as JSON:

            1. DateTime: The date and time (format: YYYY-MM-DD HH:MM:SS)
            2. Temperature_C: Temperature in Celsius (just the number, like "21")
            3. Temperature_F: Temperature in Fahrenheit (just the number, like "70") 
            4. Camera_ID: The camera identifier (like "CT10", "CIT11", etc.)

            Look for patterns like:
            - Date: 2024/04/16 or similar
            - Time: 14:14:59 or similar  
            - Temperature: 21°C 70°F or 21C 70F or similar
            - Camera ID: Usually letters and numbers like CT10, CIT11, etc.

            Return ONLY a JSON object with these exact keys:
            {
                "DateTime": "YYYY-MM-DD HH:MM:SS",
                "Temperature_C": "number",
                "Temperature_F": "number", 
                "Camera_ID": "identifier"
            }

            If you cannot find a value, use null for that field.
            """
            
            response = client.chat.completions.create(
                model="gpt-4o",  # Use GPT-4 with vision
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_base64}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=300,
                temperature=0.1  # Low temperature for consistent extraction
            )
            
            # Parse the response
            response_text = response.choices[0].message.content.strip()
            print(f"    OpenAI response: {response_text}")
            
            # Try to parse JSON from response
            try:
                # Clean up response - sometimes AI adds markdown formatting
                if "```json" in response_text:
                    response_text = response_text.split("```json")[1].split("```")[0].strip()
                elif "```" in response_text:
                    response_text = response_text.split("```")[1].strip()
                
                footer_data = json.loads(response_text)
                
                # Validate and clean the data
                result = {}
                if footer_data.get('DateTime'):
                    result['DateTime'] = footer_data['DateTime']
                if footer_data.get('Temperature_C'):
                    result['Temperature_C'] = f"{footer_data['Temperature_C']}°C"
                if footer_data.get('Temperature_F'):
                    result['Temperature_F'] = f"{footer_data['Temperature_F']}°F"
                if footer_data.get('Camera_ID'):
                    result['Camera_ID'] = footer_data['Camera_ID']
                
                print(f"    ✓ OpenAI extracted: {result}")
                return result
                
            except json.JSONDecodeError as e:
                print(f"    Failed to parse OpenAI JSON response: {e}")
                print(f"    Raw response: {response_text}")
                return {}
                
        except Exception as e:
            print(f"    OpenAI Vision API error: {e}")
            return {}

    def detect_footer_boundary(self, img_array):
        """Detect the exact footer boundary by scanning from bottom up"""
        height, width = img_array.shape[:2]
        
        # Convert to grayscale for analysis
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array
        
        print(f"  Detecting footer boundary...")
        
        # Scan from bottom up, line by line
        footer_start = height  # Start assuming no footer
        
        # Look at the bottom 20% of the image maximum
        scan_start = max(int(height * 0.8), height - 200)
        
        for y in range(height - 1, scan_start, -1):
            # Get the current row
            row = gray[y, :]
            
            # Calculate row statistics
            row_mean = np.mean(row)
            row_std = np.std(row)
            row_min = np.min(row)
            row_max = np.max(row)
            
            # Check if this row looks like a footer (dark, uniform)
            is_dark = row_mean < 80  # Dark row
            is_uniform = row_std < 30  # Low variation (uniform color)
            has_contrast = (row_max - row_min) > 100  # Has white text on dark background
            
            if is_dark and (is_uniform or has_contrast):
                footer_start = y
                print(f"    Footer detected at row {y} (mean={row_mean:.1f}, std={row_std:.1f})")
            else:
                # Found the top of the footer
                if footer_start < height:
                    break
        
        footer_height = height - footer_start
        
        if footer_height > 5:  # Minimum footer height
            print(f"  ✓ Footer boundary detected: {footer_height} pixels high (rows {footer_start}-{height})")
            return footer_start, footer_height
        else:
            print(f"  ⚠ No clear footer boundary found, using fallback")
            return height - int(height * 0.08), int(height * 0.08)  # Fallback to 8%

    def extract_footer_metadata(self, image_path):
        """Extract temperature and camera ID from image footer using OpenAI Vision API"""
        print(f"🚀 EXTRACT_FOOTER_METADATA CALLED for: {image_path}")
        footer_metadata = {}
        
        # Check if we have OpenAI API available
        if not client:
            print("OpenAI API not available - check API key")
            return footer_metadata
        
        try:
            # Load image
            image = Image.open(image_path)
            img_array = np.array(image)
            
            # Get image dimensions
            height, width = img_array.shape[:2]
            print(f"Processing image {os.path.basename(image_path)} - dimensions: {width}x{height}")
            
            # Detect the exact footer boundary
            footer_start, footer_height = self.detect_footer_boundary(img_array)
            
            # Create footer regions based on detected boundary
            footer_regions = [
                (footer_height, "exact"),  # Exact detected footer
                (footer_height + 5, "exact+5px"),  # Slightly larger
                (int(footer_height * 1.2), "exact+20%"),  # 20% larger
                (max(footer_height, int(height * 0.08)), "fallback")  # Fallback
            ]
            
            for footer_height, region_name in footer_regions:
                print(f"  Trying footer region: {region_name} ({footer_height} pixels)")
                
                # Extract footer region based on detected boundary or fallback
                # Focus on RIGHT HALF only to avoid circular time indicator on left
                right_half_start = width // 2
                
                if region_name.startswith("exact"):
                    # Use detected boundary - RIGHT HALF ONLY
                    footer_region = img_array[footer_start:height, right_half_start:width]
                else:
                    # Use traditional bottom-up approach - RIGHT HALF ONLY
                    footer_region = img_array[height - footer_height:height, right_half_start:width]
                
                print(f"    Extracted right half of footer: {footer_region.shape[1]}x{footer_region.shape[0]} pixels")
                
                # Use OpenAI Vision API for footer extraction
                print(f"    🤖 Trying OpenAI Vision API for footer extraction...")
                openai_result = self.extract_footer_with_openai(footer_region)
                if openai_result:
                    print(f"    ✓ OpenAI successfully extracted footer data!")
                    print(f"    📋 OpenAI Metadata: {openai_result}")
                    footer_metadata.update(openai_result)
                    break  # Success! No need to try other regions
                else:
                    print(f"    ⚠️ OpenAI failed to extract data from this region, trying next...")
            
            if not footer_metadata:
                print("    ❌ Failed to extract footer data from all regions")
        
        except Exception as e:
            print(f"Error in footer extraction: {e}")
        
        print(f"🔄 Returning footer metadata: {footer_metadata}")
        print(f"🔄 Metadata keys: {list(footer_metadata.keys())}")
        return footer_metadata

    def save_custom_metadata(self, index, metadata):
        if not self.image_files or index >= len(self.image_files):
            return False
            
        image_path = self.image_files[index]
        base_name = os.path.splitext(image_path)[0]
        sidecar_path = f"{base_name}_metadata.txt"
        
        try:
            # Save to sidecar text file
            with open(sidecar_path, 'w', encoding='utf-8') as f:
                f.write(f"# Metadata for {os.path.basename(image_path)}\n")
                f.write(f"# Generated by Camera Trap Metadata Editor\n")
                f.write(f"# Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                for key, value in metadata.items():
                    if value.strip():  # Only save non-empty values
                        f.write(f"{key}: {value}\n")
            
            # Write EXIF metadata to the actual image file
            self.write_exif_metadata(image_path, metadata)
            
            return True
        except Exception as e:
            print(f"Error saving metadata: {e}")
            return False
    
    def write_exif_metadata(self, image_path, metadata):
        """Write custom metadata to EXIF data in the image file"""
        try:
            # Check if file format supports EXIF (JPEG/TIFF)
            file_ext = os.path.splitext(image_path)[1].lower()
            if file_ext not in ['.jpg', '.jpeg', '.tiff', '.tif']:
                print(f"Skipping EXIF write for {file_ext} format (not supported)")
                return
            
            # Load existing EXIF data
            try:
                exif_dict = piexif.load(image_path)
            except Exception:
                # Create new EXIF dict if none exists
                exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}
            
            # Ensure required sections exist
            if "0th" not in exif_dict:
                exif_dict["0th"] = {}
            if "Exif" not in exif_dict:
                exif_dict["Exif"] = {}
            
            # Build comment string with all metadata
            comment_parts = []
            for key, value in metadata.items():
                if value and value.strip():
                    comment_parts.append(f"{key}: {value.strip()}")
            
            if comment_parts:
                # Store all metadata in UserComment with our identifier
                comment_text = "CTME:" + " | ".join(comment_parts)  # CTME = Camera Trap Metadata Editor
                # Ensure comment is not too long (EXIF has limits)
                if len(comment_text) > 500:
                    comment_text = comment_text[:497] + "..."
                exif_dict["Exif"][piexif.ExifIFD.UserComment] = comment_text.encode('utf-8')
            
            # Map specific fields to EXIF tags - using consistent naming
            field_mapping = {
                'Species': piexif.ImageIFD.ImageDescription,
                'Scientific_Name': piexif.ImageIFD.Software,
                'Count': piexif.ImageIFD.Artist,
                'Behavior': piexif.ImageIFD.Copyright,
                'Location': piexif.ImageIFD.Make,
                'Weather': piexif.ImageIFD.Model
            }
            
            # Also check for variations in field names
            field_variations = {
                'Scientific Name': 'Scientific_Name',
                'scientific_name': 'Scientific_Name',
                'AI_Confidence': 'AI_Confidence',
                'Camera_ID': 'Camera_ID',
                'Researcher': 'Researcher',
                'Notes': 'Notes'
            }
            
            # Normalize field names
            normalized_metadata = {}
            for key, value in metadata.items():
                normalized_key = field_variations.get(key, key)
                normalized_metadata[normalized_key] = value
            
            # Write the mapped fields
            for field_name, exif_tag in field_mapping.items():
                if field_name in normalized_metadata and normalized_metadata[field_name].strip():
                    value = normalized_metadata[field_name].strip()
                    # Limit field length
                    if len(value) > 100:
                        value = value[:97] + "..."
                    exif_dict["0th"][exif_tag] = value.encode('utf-8')
            
            # Add timestamp
            current_time = datetime.now().strftime("%Y:%m:%d %H:%M:%S")
            exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal] = current_time.encode('utf-8')
            
            # Convert back to bytes and save
            exif_bytes = piexif.dump(exif_dict)
            
            # Create backup of original file (only once)
            backup_path = f"{image_path}.backup"
            if not os.path.exists(backup_path):
                shutil.copy2(image_path, backup_path)
            
            # Save image with new EXIF data
            image = Image.open(image_path)
            
            # Preserve original format and quality
            save_kwargs = {'exif': exif_bytes}
            if file_ext in ['.jpg', '.jpeg']:
                save_kwargs['quality'] = 95
                save_kwargs['optimize'] = True
            
            image.save(image_path, **save_kwargs)
            
            print(f"Successfully wrote EXIF metadata to {os.path.basename(image_path)}")
            print(f"  - Wrote {len([k for k in normalized_metadata.keys() if k in field_mapping])} mapped fields")
            print(f"  - UserComment contains {len(comment_parts)} metadata pairs")
            
        except Exception as e:
            print(f"Error writing EXIF metadata to {image_path}: {e}")
            # Don't fail the entire save operation if EXIF writing fails

# Global image manager instance
image_manager = ImageManager()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/load_folder', methods=['POST'])
def load_folder():
    folder_path = request.json.get('folder_path')
    
    try:
        print(f"Loading folder: {folder_path}")
        count = image_manager.load_folder(folder_path)
        print(f"Successfully loaded {count} images from {folder_path}")
        return jsonify({'success': True, 'count': count, 'folder': folder_path})
    except Exception as e:
        print(f"Error loading folder {folder_path}: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/image/<int:index>')
def get_image(index):
    info = image_manager.get_image_info(index)
    if info:
        return jsonify(info)
    else:
        return jsonify({'error': 'Image not found'}), 404

@app.route('/api/image_file/<int:index>')
def serve_image(index):
    if index < len(image_manager.image_files):
        image_path = image_manager.image_files[index]
        print(f"Serving image {index}: {os.path.basename(image_path)} from {os.path.dirname(image_path)}")
        return send_file(image_path)
    print(f"Image not found at index {index}, total images: {len(image_manager.image_files)}")
    return "Image not found", 404

@app.route('/api/save_metadata', methods=['POST'])
def save_metadata():
    data = request.json
    index = data.get('index')
    metadata = data.get('metadata', {})
    
    success = image_manager.save_custom_metadata(index, metadata)
    
    if success:
        image_path = image_manager.image_files[index] if index < len(image_manager.image_files) else None
        filename = os.path.basename(image_path) if image_path else "unknown"
        return jsonify({
            'success': True, 
            'message': f'Metadata saved to both sidecar file and EXIF data for {filename}'
        })
    else:
        return jsonify({
            'success': False, 
            'error': 'Failed to save metadata'
        })

@app.route('/api/browse_folders')
def browse_folders():
    path = request.args.get('path', os.path.expanduser('~'))
    
    try:
        # Ensure path exists and is accessible
        if not os.path.exists(path) or not os.path.isdir(path):
            path = os.path.expanduser('~')
        
        items = []
        
        # Add parent directory option (except for root)
        parent_path = os.path.dirname(path)
        if parent_path != path:  # Not at root
            items.append({
                'name': '..',
                'path': parent_path,
                'type': 'parent',
                'is_dir': True
            })
        
        # List directory contents
        try:
            for item in sorted(os.listdir(path)):
                if item.startswith('.'):  # Skip hidden files/folders
                    continue
                    
                item_path = os.path.join(path, item)
                is_dir = os.path.isdir(item_path)
                
                if is_dir:
                    # Count images in directory
                    image_count = 0
                    try:
                        extensions = ['*.jpg', '*.jpeg', '*.png', '*.tiff', '*.tif', '*.JPG', '*.JPEG']
                        for ext in extensions:
                            image_count += len(glob.glob(os.path.join(item_path, ext)))
                    except (PermissionError, OSError):
                        pass
                    
                    items.append({
                        'name': item,
                        'path': item_path,
                        'type': 'directory',
                        'is_dir': True,
                        'image_count': image_count
                    })
                elif item.lower().endswith(('.jpg', '.jpeg', '.png', '.tiff', '.tif')):
                    items.append({
                        'name': item,
                        'path': item_path,
                        'type': 'file',
                        'is_dir': False
                    })
        except PermissionError:
            pass  # Skip directories we can't read
        
        return jsonify({
            'success': True,
            'current_path': path,
            'items': items
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/identify_species', methods=['POST'])
def identify_species():
    if not client:
        return jsonify({'success': False, 'error': 'OpenAI API key not configured'})
    
    try:
        data = request.json
        image_index = data.get('image_index')
        selection = data.get('selection')  # {x, y, width, height} in pixels
        
        if image_index >= len(image_manager.image_files):
            return jsonify({'success': False, 'error': 'Invalid image index'})
        
        # Load the original image
        image_path = image_manager.image_files[image_index]
        image = Image.open(image_path)
        
        # Crop the selected region
        left = int(selection['x'])
        top = int(selection['y'])
        right = int(selection['x'] + selection['width'])
        bottom = int(selection['y'] + selection['height'])
        
        # Ensure coordinates are within image bounds
        left = max(0, min(left, image.width))
        top = max(0, min(top, image.height))
        right = max(left, min(right, image.width))
        bottom = max(top, min(bottom, image.height))
        
        cropped_image = image.crop((left, top, right, bottom))
        
        # Convert to base64 for API
        buffer = io.BytesIO()
        cropped_image.save(buffer, format='JPEG', quality=95)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        # Get location context from environment
        location = os.getenv('CAMERA_TRAP_LOCATION', 'Namibia, Africa')
        region = os.getenv('CAMERA_TRAP_REGION', 'Southern Africa')
        
        # Load and format the AI prompt from configuration
        prompt_text = AI_PROMPT_TEMPLATE.format(
            location=location,
            location_upper=location.upper(),
            region=region
        )
        
        # Call OpenAI Vision API with configurable prompt
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt_text
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=600
        )
        
        # Parse the response
        ai_response = response.choices[0].message.content
        
        # Try to extract JSON from the response
        try:
            # Look for JSON in the response
            import re
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                # Fallback: create structured response from text
                result = {
                    "species": "Unknown",
                    "scientific_name": "",
                    "confidence": "Low",
                    "count": 0,
                    "description": ai_response
                }
        except json.JSONDecodeError:
            # Fallback for non-JSON responses
            result = {
                "species": "Analysis Complete",
                "scientific_name": "",
                "confidence": "Medium",
                "count": 1,
                "description": ai_response
            }
        
        return jsonify({
            'success': True,
            'identification': result
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/suggest_footer_correction', methods=['POST'])
def suggest_footer_correction():
    """Suggest footer text correction based on OCR results"""
    try:
        data = request.json
        ocr_results = data.get('ocr_results', [])
        
        # Find the best OCR result (longest with recognizable patterns)
        best_result = ""
        for result in ocr_results:
            if len(result) > len(best_result) and any(char.isdigit() for char in result):
                best_result = result
        
        if not best_result:
            return jsonify({
                'success': True,
                'suggested_text': '🔋 80% 2024/04/17 08:31:56 28°C 82°F CT14',
                'message': 'No OCR text found, using template'
            })
        
        # Extract recognizable patterns and suggest corrections
        suggested_text = best_result
        
        # Common OCR corrections
        corrections = {
            'Y7E': '82°F',  # Common OCR error for temperature
            'CTI4': 'CT14', # I/1 confusion
            'CI19': 'CT19', # I/T confusion
            '280': '28°C',  # Missing degree symbol
            '316': '31°C',  # Missing degree symbol
            '& a': '🔋',    # Battery symbol
            '?': ' ',       # Question marks to spaces
        }
        
        for error, correction in corrections.items():
            suggested_text = suggested_text.replace(error, correction)
        
        # Clean up extra spaces and characters
        suggested_text = re.sub(r'[^\w\s°CF:/🔋%-]', ' ', suggested_text)
        suggested_text = re.sub(r'\s+', ' ', suggested_text).strip()
        
        return jsonify({
            'success': True,
            'suggested_text': suggested_text,
            'original_ocr': best_result,
            'message': 'Suggested correction based on OCR'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/parse_manual_footer', methods=['POST'])
def parse_manual_footer():
    """Parse manually entered footer text"""
    try:
        data = request.json
        footer_text = data.get('footer_text', '').strip()
        
        if not footer_text:
            return jsonify({'success': False, 'error': 'No footer text provided'})
        
        print(f"Manual footer parsing: '{footer_text}'")
        
        # Use the same parsing logic as automatic extraction
        footer_metadata = {}
        
        # Parse temperature data - improved for camera trap footer format
        temp_patterns = [
            # Standard patterns with proper spacing (including negative temps)
            r'\b(-?\d{1,2})°C\s+(-?\d{1,3})°F\b',       # -3°C 27°F or 23°C 73°F (with spaces)
            r'\b(-?\d{1,2})°C\s*(-?\d{1,3})°F\b',       # -3°C27°F or 23°C73°F (no space)
            r'\b(-?\d{1,2})C\s*(-?\d{1,3})F\b',         # -3C27F or 23C73F (no degree symbol)
            
            # Patterns that handle datetime bleeding into temperature
            r'(?:\d{2,4})\s*(-?[0-5]?\d)°C\s*(-?\d{1,3})°F\b',  # datetime-3°C27°F or datetime23°C73°F
            r'(?:\d{2,4})\s*(-?[0-5]?\d)C\s*(-?\d{1,3})F\b',    # datetime-3C27F or datetime23C73F
            
            # More flexible patterns for edge cases
            r'(-?\d{1,2})°C.*?(-?\d{1,3})°F',           # -3°C...27°F or 23°C...73°F (anything between)
            r'(-?[0-5]?\d)°C\s*(-?\d{1,3})°F',          # Temperature range validation with negatives
        ]
        
        temperature_found = False
        for i, temp_pattern in enumerate(temp_patterns):
            temp_match = re.search(temp_pattern, footer_text)
            if temp_match:
                celsius = int(temp_match.group(1))
                fahrenheit = int(temp_match.group(2))
                
                # Validate temperature ranges (including negatives)
                if -20 <= celsius <= 50 and -4 <= fahrenheit <= 122:
                    # Double-check conversion is approximately correct
                    expected_f = (celsius * 9/5) + 32
                    if abs(fahrenheit - expected_f) <= 3:  # Allow 3°F tolerance
                        temperature_value = f"{celsius}°C {fahrenheit}°F"
                        footer_metadata['Temperature'] = temperature_value
                        print(f"  ✓ Temperature found (pattern {i+1}): {temperature_value}")
                        temperature_found = True
                        break
                    else:
                        print(f"  ⚠ Temperature conversion mismatch: {celsius}°C ≠ {fahrenheit}°F (expected ~{expected_f:.0f}°F)")
                else:
                    print(f"  ⚠ Temperature out of range: {celsius}°C {fahrenheit}°F")
        
        # Parse camera ID - should be the text AFTER the Fahrenheit value
        camera_id_found = False
        if temperature_found:
            # Find the Fahrenheit temperature in the text and get everything after it
            temp_value = footer_metadata['Temperature']
            fahrenheit_val = temp_value.split(' ')[1].split('°F')[0]
            
            # Look for the Fahrenheit value in the original text and get what follows
            fahrenheit_patterns = [
                rf'{fahrenheit_val}°F\s*([A-Z0-9]+)',      # 73°F ABC123
                rf'{fahrenheit_val}F\s*([A-Z0-9]+)',       # 73F ABC123
                rf'{fahrenheit_val}°F\s*([A-Z]+\d+)',      # 73°F ABC123
                rf'{fahrenheit_val}°F\s*(\w+)',            # 73°F anything
            ]
            
            for pattern in fahrenheit_patterns:
                camera_match = re.search(pattern, footer_text, re.IGNORECASE)
                if camera_match:
                    camera_id = camera_match.group(1).upper()
                    # Validate camera ID (should be alphanumeric, 2+ chars)
                    if len(camera_id) >= 2 and camera_id.isalnum():
                        footer_metadata['Camera_ID'] = camera_id
                        print(f"  ✓ Camera ID found after {fahrenheit_val}°F: {camera_id}")
                        camera_id_found = True
                        break
        
        # Fallback camera ID detection if temperature-based method fails
        if not camera_id_found:
            # Look for camera ID patterns at the end of the text
            camera_id_patterns = [
                r'([A-Z]{2,6}\d{1,4}[A-Z]*)$',           # ABC123, CT14A at end
                r'([A-Z]+\d+[A-Z]*)$',                   # ABC123A at end
                r'(\w+\d+\w*)$',                         # General alphanumeric at end
            ]
            
            for pattern in camera_id_patterns:
                camera_match = re.search(pattern, footer_text.strip())
                if camera_match:
                    camera_id = camera_match.group(1).upper()
                    if len(camera_id) >= 2:
                        footer_metadata['Camera_ID'] = camera_id
                        print(f"  ✓ Camera ID found (fallback): {camera_id}")
                        break
        
        return jsonify({
            'success': True,
            'footer_metadata': footer_metadata,
            'original_text': footer_text,
            'message': f'Parsed {len(footer_metadata)} fields from manual input'
        })
        
    except Exception as e:
        print(f"Manual footer parsing error: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/extract_footer/<int:index>')
def extract_footer_metadata_endpoint(index):
    """Manual endpoint to test footer metadata extraction"""
    if not client:
        return jsonify({
            'success': False, 
            'error': 'OpenAI API not available - check API key'
        })
    
    if index >= len(image_manager.image_files):
        return jsonify({'success': False, 'error': 'Invalid image index'})
    
    try:
        image_path = image_manager.image_files[index]
        footer_metadata = image_manager.extract_footer_metadata(image_path)
        
        return jsonify({
            'success': True,
            'footer_metadata': footer_metadata,
            'image': os.path.basename(image_path)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/debug_footer/<int:index>')
def debug_footer_extraction(index):
    """Debug endpoint to save processed footer images for inspection"""
    if not client:
        return jsonify({'success': False, 'error': 'OpenAI API not available - check API key'})
    
    if index >= len(image_manager.image_files):
        return jsonify({'success': False, 'error': 'Invalid image index'})
    
    try:
        image_path = image_manager.image_files[index]
        image = Image.open(image_path)
        img_array = np.array(image)
        height, width = img_array.shape[:2]
        
        files_saved = []
        ocr_results = []
        regions_processed = 0
        
        print(f"DEBUG: Processing {os.path.basename(image_path)} - {width}x{height}")
        
        # Detect footer boundary first
        footer_start, detected_footer_height = image_manager.detect_footer_boundary(img_array)
        
        # Process different footer regions including detected boundary
        footer_regions = [
            (detected_footer_height, "detected"),
            (detected_footer_height + 5, "detected+5px"),
            (int(detected_footer_height * 1.2), "detected+20%"),
            (int(height * 0.08), "fallback_8%")
        ]
        
        for i, (footer_height, region_name) in enumerate(footer_regions):
            print(f"  Processing region {region_name} ({footer_height} pixels)")
            
            # Extract footer region based on detection method
            if region_name.startswith("detected"):
                footer_region = img_array[footer_start:height, 0:width]
            else:
                footer_region = img_array[height - footer_height:height, 0:width]
            
            if len(footer_region.shape) == 3:
                footer_gray = cv2.cvtColor(footer_region, cv2.COLOR_RGB2GRAY)
            else:
                footer_gray = footer_region
            
            avg_brightness = np.mean(footer_gray)
            min_brightness = np.min(footer_gray)
            max_brightness = np.max(footer_gray)
            contrast = max_brightness - min_brightness
            
            print(f"    Brightness: avg={avg_brightness:.1f}, min={min_brightness}, max={max_brightness}, contrast={contrast}")
            
            # Save original footer region
            debug_filename = f"debug_footer_{os.path.splitext(os.path.basename(image_path))[0]}_{region_name.replace('%', 'pct')}_original.png"
            cv2.imwrite(debug_filename, footer_gray)
            files_saved.append(debug_filename)
            
            # Process and save enhanced version
            if avg_brightness < 120:
                footer_processed = cv2.bitwise_not(footer_gray)
                print(f"    Applied color inversion (dark footer)")
            else:
                footer_processed = footer_gray.copy()
                print(f"    No color inversion (light footer)")
            
            # Apply enhancement
            footer_processed = cv2.convertScaleAbs(footer_processed, alpha=2.5, beta=10)
            footer_processed = cv2.GaussianBlur(footer_processed, (1, 1), 0)
            
            # Apply morphological operations
            kernel = np.ones((2, 2), np.uint8)
            footer_processed = cv2.morphologyEx(footer_processed, cv2.MORPH_CLOSE, kernel)
            
            # Scale up for better OCR
            scale_factor = 4
            new_width = int(footer_processed.shape[1] * scale_factor)
            new_height = int(footer_processed.shape[0] * scale_factor)
            footer_resized = cv2.resize(footer_processed, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
            
            processed_filename = f"debug_footer_{os.path.splitext(os.path.basename(image_path))[0]}_{region_name.replace('%', 'pct')}_processed.png"
            cv2.imwrite(processed_filename, footer_resized)
            files_saved.append(processed_filename)
            
            # Try OCR on this region with multiple configurations
            try:
                # Try different OCR configurations for better results
                ocr_configs = [
                    r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz°CF%:/-',
                    r'--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz°CF%:/-',
                    r'--oem 3 --psm 8 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz°CF%:/-',
                    r'--oem 3 --psm 6',  # No character restriction
                ]
                
                best_ocr_text = ""
                for config in ocr_configs:
                    try:
                        ocr_text = pytesseract.image_to_string(footer_resized, config=config).strip()
                        if len(ocr_text) > len(best_ocr_text):
                            best_ocr_text = ocr_text
                    except:
                        continue
                
                ocr_results.append(f"Region {region_name}: '{best_ocr_text}'")
                print(f"    OCR result: '{best_ocr_text}'")
                
                # Test parsing on this OCR result
                if best_ocr_text:
                    # Test temperature parsing
                    temp_patterns = [
                        r'\b(-?\d{1,2})°C\s+(-?\d{1,3})°F\b',
                        r'(?:\d{2,4})\s*(-?[0-5]?\d)°C\s*(-?\d{1,3})°F\b',
                        r'(-?[0-5]?\d)°C\s*(-?\d{1,3})°F',
                    ]
                    
                    for pattern in temp_patterns:
                        temp_match = re.search(pattern, best_ocr_text)
                        if temp_match:
                            celsius = int(temp_match.group(1))
                            fahrenheit = int(temp_match.group(2))
                            if -20 <= celsius <= 50 and -4 <= fahrenheit <= 122:
                                expected_f = (celsius * 9/5) + 32
                                if abs(fahrenheit - expected_f) <= 3:
                                    print(f"    ✓ Parsed temperature: {celsius}°C {fahrenheit}°F")
                                    
                                    # Test camera ID parsing
                                    camera_pattern = rf'{fahrenheit}°F\s*([A-Z0-9]+)'
                                    camera_match = re.search(camera_pattern, best_ocr_text, re.IGNORECASE)
                                    if camera_match:
                                        camera_id = camera_match.group(1).upper()
                                        print(f"    ✓ Parsed camera ID: {camera_id}")
                                    break
                            
            except Exception as ocr_error:
                ocr_results.append(f"Region {region_name}: OCR failed - {str(ocr_error)}")
                print(f"    OCR failed: {ocr_error}")
            
            regions_processed += 1
        
        return jsonify({
            'success': True,
            'regions_processed': regions_processed,
            'files_saved': files_saved,
            'ocr_results': ocr_results,
            'message': f'Debug complete: {len(files_saved)} files saved, {regions_processed} regions processed'
        })
        
    except Exception as e:
        print(f"Debug extraction error: {e}")
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True, port=5001)