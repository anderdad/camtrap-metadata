// Copyright (c) 2025 Anderdad <paul.ande@outlook.com>
// Licensed under the MIT License.
// Camera Trap Metadata Editor - Web Version
// A web-based application for viewing and editing image metadata from camera traps.

class CameraTrapApp {
    constructor() {
        this.currentIndex = 0;
        this.totalImages = 0;
        this.currentMetadata = {};
        
        this.initializeElements();
        this.bindEvents();
    }
    
    initializeElements() {
        // Main elements
        this.browseFoldersBtn = document.getElementById('browseFolders');
        this.selectedPath = document.getElementById('selectedPath');
        this.loadFolderBtn = document.getElementById('loadFolder');
        this.mainContent = document.getElementById('mainContent');
        this.welcomeMessage = document.getElementById('welcomeMessage');
        
        // Image elements
        this.currentImage = document.getElementById('currentImage');
        this.imageWrapper = document.getElementById('imageWrapper');
        this.selectionCanvas = document.getElementById('selectionCanvas');
        this.selectionBox = document.getElementById('selectionBox');
        this.imageInfo = document.getElementById('imageInfo');
        this.imageCounter = document.getElementById('imageCounter');
        this.selectionInfo = document.getElementById('selectionInfo');
        this.cancelSelection = document.getElementById('cancelSelection');
        
        // Navigation elements
        this.firstBtn = document.getElementById('firstBtn');
        this.prevBtn = document.getElementById('prevBtn');
        this.nextBtn = document.getElementById('nextBtn');
        this.lastBtn = document.getElementById('lastBtn');
        this.identifyBtn = document.getElementById('identifyBtn');
        
        // Metadata elements
        this.metadataContainer = document.getElementById('metadataContainer');
        this.addFieldBtn = document.getElementById('addFieldBtn');
        this.saveBtn = document.getElementById('saveBtn');
        this.debugOutput = document.getElementById('debugOutput');
        
        // Folder browser elements
        this.folderBrowserModal = document.getElementById('folderBrowserModal');
        this.currentPath = document.getElementById('currentPath');
        this.folderTree = document.getElementById('folderTree');
        this.selectFolderBtn = document.getElementById('selectFolderBtn');
        this.cancelBrowserBtn = document.getElementById('cancelBrowserBtn');
        
        // Modal elements
        this.addFieldModal = document.getElementById('addFieldModal');
        this.fieldName = document.getElementById('fieldName');
        this.fieldValue = document.getElementById('fieldValue');
        this.addFieldConfirm = document.getElementById('addFieldConfirm');
        this.addFieldCancel = document.getElementById('addFieldCancel');
        
        // Debug output buffer
        this.debugBuffer = '';
        
        // Selection state
        this.isSelecting = false;
        this.selectionStart = null;
        this.currentSelection = null;
        
        // Folder browser state
        this.currentBrowserPath = null;
        this.selectedFolderPath = null;
    }
    
    bindEvents() {
        // Folder browser
        this.browseFoldersBtn.addEventListener('click', () => this.showFolderBrowser());
        this.loadFolderBtn.addEventListener('click', () => this.loadFolder());
        this.selectFolderBtn.addEventListener('click', () => this.selectCurrentFolder());
        this.cancelBrowserBtn.addEventListener('click', () => this.hideFolderBrowser());
        
        // Navigation
        this.firstBtn.addEventListener('click', () => this.navigateToImage(0));
        this.prevBtn.addEventListener('click', () => this.navigateToImage(this.currentIndex - 1));
        this.nextBtn.addEventListener('click', () => this.navigateToImage(this.currentIndex + 1));
        this.lastBtn.addEventListener('click', () => this.navigateToImage(this.totalImages - 1));
        this.identifyBtn.addEventListener('click', () => this.toggleIdentifyMode());
        
        // Keyboard navigation
        document.addEventListener('keydown', (e) => {
            if (this.totalImages === 0 || this.isSelecting) return;
            
            switch(e.key) {
                case 'ArrowLeft':
                    e.preventDefault();
                    this.navigateToImage(this.currentIndex - 1);
                    break;
                case 'ArrowRight':
                    e.preventDefault();
                    this.navigateToImage(this.currentIndex + 1);
                    break;
                case 'Home':
                    e.preventDefault();
                    this.navigateToImage(0);
                    break;
                case 'End':
                    e.preventDefault();
                    this.navigateToImage(this.totalImages - 1);
                    break;
                case 'Escape':
                    if (this.isSelecting) {
                        this.cancelIdentifyMode();
                    }
                    break;
            }
        });
        
        // Selection events
        this.imageWrapper.addEventListener('mousedown', (e) => this.startSelection(e));
        this.imageWrapper.addEventListener('mousemove', (e) => this.updateSelection(e));
        this.imageWrapper.addEventListener('mouseup', (e) => this.endSelection(e));
        this.cancelSelection.addEventListener('click', () => this.cancelIdentifyMode());
        
        // Metadata actions
        this.addFieldBtn.addEventListener('click', () => this.showAddFieldModal());
        this.saveBtn.addEventListener('click', () => this.saveMetadata());
        
        // Modal actions
        this.addFieldConfirm.addEventListener('click', () => this.addCustomField());
        this.addFieldCancel.addEventListener('click', () => this.hideAddFieldModal());
        
        // Close modals on outside click
        this.addFieldModal.addEventListener('click', (e) => {
            if (e.target === this.addFieldModal) {
                this.hideAddFieldModal();
            }
        });
        
        this.folderBrowserModal.addEventListener('click', (e) => {
            if (e.target === this.folderBrowserModal) {
                this.hideFolderBrowser();
            }
        });
    }
    
    async showFolderBrowser() {
        this.folderBrowserModal.classList.remove('hidden');
        // Start from user's home directory
        await this.browseTo(null);
    }
    
    hideFolderBrowser() {
        this.folderBrowserModal.classList.add('hidden');
        this.selectedFolderPath = null;
        this.selectFolderBtn.disabled = true;
    }
    
    async browseTo(path) {
        try {
            const url = path ? `/api/browse_folders?path=${encodeURIComponent(path)}` : '/api/browse_folders';
            const response = await fetch(url);
            const result = await response.json();
            
            if (result.success) {
                this.currentBrowserPath = result.current_path;
                this.currentPath.textContent = result.current_path;
                this.displayFolderTree(result.items);
            } else {
                alert(`Error browsing folders: ${result.error}`);
            }
        } catch (error) {
            alert(`Error: ${error.message}`);
        }
    }
    
    displayFolderTree(items) {
        this.folderTree.innerHTML = '';
        
        items.forEach(item => {
            const itemDiv = document.createElement('div');
            itemDiv.className = `folder-item ${item.type}`;
            itemDiv.dataset.path = item.path;
            
            const icon = document.createElement('span');
            icon.className = 'folder-icon';
            
            if (item.type === 'parent') {
                icon.textContent = '↰';
            } else if (item.is_dir) {
                icon.textContent = '📁';
            } else {
                icon.textContent = '🖼️';
            }
            
            const name = document.createElement('span');
            name.className = 'folder-name';
            name.textContent = item.name;
            
            itemDiv.appendChild(icon);
            itemDiv.appendChild(name);
            
            // Add image count for directories
            if (item.is_dir && item.type !== 'parent' && typeof item.image_count !== 'undefined') {
                const count = document.createElement('span');
                count.className = 'image-count';
                count.textContent = item.image_count === 0 ? 'empty' : `${item.image_count} images`;
                itemDiv.appendChild(count);
            }
            
            // Click handlers
            if (item.is_dir) {
                itemDiv.addEventListener('click', () => {
                    if (item.type === 'parent') {
                        this.browseTo(item.path);
                    } else {
                        this.selectFolder(itemDiv, item.path);
                    }
                });
                
                itemDiv.addEventListener('dblclick', () => {
                    this.browseTo(item.path);
                });
            }
            
            this.folderTree.appendChild(itemDiv);
        });
    }
    
    selectFolder(itemDiv, path) {
        // Remove previous selection
        this.folderTree.querySelectorAll('.folder-item').forEach(item => {
            item.classList.remove('selected');
        });
        
        // Select current item
        itemDiv.classList.add('selected');
        this.selectedFolderPath = path;
        this.selectFolderBtn.disabled = false;
    }
    
    selectCurrentFolder() {
        if (this.selectedFolderPath) {
            this.selectedPath.textContent = this.selectedFolderPath;
            this.loadFolderBtn.disabled = false;
            this.hideFolderBrowser();
        }
    }
    
    async loadFolder() {
        const folderPath = this.selectedPath.textContent;
        if (!folderPath || folderPath === 'No folder selected') {
            alert('Please select a folder first');
            return;
        }
        
        // Reset interface state before loading new folder
        this.resetInterface();
        
        try {
            const response = await fetch('/api/load_folder', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ folder_path: folderPath })
            });
            
            const result = await response.json();
            
            if (result.success) {
                // Completely reset state for new folder
                this.totalImages = result.count;
                this.currentIndex = 0;
                this.currentMetadata = {};
                
                if (this.totalImages > 0) {
                    this.showMainContent();
                    await this.loadCurrentImage();
                } else {
                    alert('No supported image files found in the selected folder.');
                }
            } else {
                alert(`Error loading folder: ${result.error}`);
            }
        } catch (error) {
            alert(`Error: ${error.message}`);
        }
    }
    
    resetInterface() {
        // Clear current image
        this.currentImage.src = '';
        this.imageInfo.textContent = '';
        this.imageCounter.textContent = '';
        
        // Clear metadata container
        this.metadataContainer.innerHTML = '';
        
        // Reset selection state
        this.cancelIdentifyMode();
        
        // Reset navigation state
        this.currentIndex = 0;
        this.totalImages = 0;
        this.currentMetadata = {};
        
        // Disable navigation buttons
        this.firstBtn.disabled = true;
        this.prevBtn.disabled = true;
        this.nextBtn.disabled = true;
        this.lastBtn.disabled = true;
        
        console.log('Interface reset for new folder');
    }
    
    showMainContent() {
        this.welcomeMessage.classList.add('hidden');
        this.mainContent.classList.remove('hidden');
    }
    
    async navigateToImage(index) {
        if (index < 0 || index >= this.totalImages) return;
        
        this.currentIndex = index;
        await this.loadCurrentImage();
    }
    
    async loadCurrentImage() {
        try {
            const response = await fetch(`/api/image/${this.currentIndex}`);
            const imageData = await response.json();
            
            if (imageData.error) {
                alert(`Error loading image: ${imageData.error}`);
                return;
            }
            
            // Update image display with cache busting
            const timestamp = new Date().getTime();
            this.currentImage.src = `/api/image_file/${this.currentIndex}?t=${timestamp}`;
            this.imageInfo.textContent = `${imageData.dimensions} • ${imageData.size_mb} MB`;
            this.imageCounter.textContent = `${imageData.index + 1} of ${imageData.total} - ${imageData.filename}`;
            
            // Update navigation buttons
            this.updateNavigationButtons();
            
            // Load metadata
            this.currentMetadata = imageData.metadata || {};
            this.displayMetadata();
            
            // Automatically extract footer data if temperature or camera ID is missing
            const hasTemperatureC = this.currentMetadata.Temperature_C;
            const hasTemperatureF = this.currentMetadata.Temperature_F;
            const hasCameraID = this.currentMetadata.Camera_ID;
            
            if (!hasTemperatureC || !hasTemperatureF || !hasCameraID) {
                this.addDebugOutput(`Loading image ${imageData.filename}`);
                this.addDebugOutput(`Missing metadata - extracting footer data...`);
                await this.extractFooterDataSilent();
            } else {
                this.addDebugOutput(`Image ${imageData.filename} loaded - metadata complete`);
            }
            
        } catch (error) {
            this.addDebugOutput(`Error loading image: ${error.message}`);
            alert(`Error loading image: ${error.message}`);
        }
    }
    
    updateNavigationButtons() {
        this.firstBtn.disabled = this.currentIndex === 0;
        this.prevBtn.disabled = this.currentIndex === 0;
        this.nextBtn.disabled = this.currentIndex === this.totalImages - 1;
        this.lastBtn.disabled = this.currentIndex === this.totalImages - 1;
    }
    
    displayMetadata() {
        this.metadataContainer.innerHTML = '';
        
        // Define readonly fields
        const readonlyFields = ['filename', 'size_mb', 'dimensions'];
        
        // Common camera trap fields
        const commonFields = [
            'Species', 'Count', 'Behavior', 'Weather', 'Temperature_C', 'Temperature_F',
            'Location', 'Camera_ID', 'Researcher', 'Notes'
        ];
        
        // Add existing metadata fields
        for (const [key, value] of Object.entries(this.currentMetadata)) {
            const isReadonly = readonlyFields.includes(key.toLowerCase());
            this.createMetadataField(key, value, isReadonly);
        }
        
        // Add common fields if they don't exist
        for (const field of commonFields) {
            if (!this.currentMetadata.hasOwnProperty(field)) {
                this.createMetadataField(field, '');
            }
        }
    }
    
    createMetadataField(label, value, readonly = false) {
        const fieldDiv = document.createElement('div');
        fieldDiv.className = `metadata-field ${readonly ? 'readonly' : ''}`;
        
        const labelSpan = document.createElement('span');
        labelSpan.className = 'field-label';
        labelSpan.textContent = `${label}:`;
        
        const input = document.createElement('input');
        input.type = 'text';
        input.className = 'field-input';
        input.value = value;
        input.readOnly = readonly;
        input.dataset.field = label;
        
        fieldDiv.appendChild(labelSpan);
        fieldDiv.appendChild(input);
        
        // Add delete button for custom fields
        if (!readonly && !this.isCommonField(label)) {
            const deleteBtn = document.createElement('button');
            deleteBtn.className = 'delete-field';
            deleteBtn.innerHTML = '×';
            deleteBtn.title = 'Delete field';
            deleteBtn.addEventListener('click', () => {
                fieldDiv.remove();
                delete this.currentMetadata[label];
            });
            fieldDiv.appendChild(deleteBtn);
        }
        
        this.metadataContainer.appendChild(fieldDiv);
    }
    
    isCommonField(fieldName) {
        const commonFields = [
            'Species', 'Count', 'Behavior', 'Weather', 'Temperature_C', 'Temperature_F',
            'Location', 'Camera_ID', 'Researcher', 'Notes'
        ];
        return commonFields.includes(fieldName);
    }
    
    showAddFieldModal() {
        this.fieldName.value = '';
        this.fieldValue.value = '';
        this.addFieldModal.classList.remove('hidden');
        this.fieldName.focus();
    }
    
    hideAddFieldModal() {
        this.addFieldModal.classList.add('hidden');
    }
    
    addDebugOutput(message) {
        // Add timestamp to message
        const timestamp = new Date().toLocaleTimeString();
        const formattedMessage = `[${timestamp}] ${message}\n`;
        
        // Add to buffer
        this.debugBuffer += formattedMessage;
        
        // Trim to last 500 characters
        if (this.debugBuffer.length > 500) {
            this.debugBuffer = this.debugBuffer.slice(-500);
        }
        
        // Update the textarea
        this.debugOutput.value = this.debugBuffer;
        
        // Auto-scroll to bottom
        this.debugOutput.scrollTop = this.debugOutput.scrollHeight;
    }
    
    addCustomField() {
        const name = this.fieldName.value.trim();
        const value = this.fieldValue.value.trim();
        
        if (!name) {
            alert('Please enter a field name');
            return;
        }
        
        if (this.currentMetadata.hasOwnProperty(name)) {
            alert('A field with this name already exists');
            return;
        }
        
        this.createMetadataField(name, value);
        this.hideAddFieldModal();
    }
    
    async saveMetadata() {
        // Collect current metadata from form fields
        const metadata = {};
        const inputs = this.metadataContainer.querySelectorAll('.field-input:not([readonly])');
        
        inputs.forEach(input => {
            const fieldName = input.dataset.field;
            const value = input.value.trim();
            if (value) {
                metadata[fieldName] = value;
            }
        });
        
        try {
            const response = await fetch('/api/save_metadata', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    index: this.currentIndex,
                    metadata: metadata
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                // Show success feedback with EXIF info
                const originalText = this.saveBtn.textContent;
                this.saveBtn.textContent = 'Saved to File & EXIF!';
                this.saveBtn.style.background = '#4CAF50';
                
                // Show detailed message if provided
                if (result.message) {
                    console.log(result.message);
                }
                
                setTimeout(() => {
                    this.saveBtn.textContent = originalText;
                    this.saveBtn.style.background = '';
                }, 3000);
            } else {
                alert(`Failed to save metadata: ${result.error || 'Unknown error'}`);
            }
        } catch (error) {
            alert(`Error saving metadata: ${error.message}`);
        }
    }
    
    async extractFooterDataSilent() {
        if (this.totalImages === 0) {
            return;
        }
        
        try {
            this.addDebugOutput('🤖 Extracting footer metadata...');
            const response = await fetch(`/api/extract_footer/${this.currentIndex}`);
            const result = await response.json();
            
            if (result.success) {
                const footerData = result.footer_metadata;
                
                if (Object.keys(footerData).length > 0) {
                    // Update metadata fields with extracted data
                    let updatedFields = [];
                    
                    if (footerData.Temperature_C) {
                        const tempCInput = this.metadataContainer.querySelector('[data-field="Temperature_C"]');
                        if (tempCInput) {
                            tempCInput.value = footerData.Temperature_C;
                            updatedFields.push(`Temperature_C: ${footerData.Temperature_C}`);
                        }
                    }
                    
                    if (footerData.Temperature_F) {
                        const tempFInput = this.metadataContainer.querySelector('[data-field="Temperature_F"]');
                        if (tempFInput) {
                            tempFInput.value = footerData.Temperature_F;
                            updatedFields.push(`Temperature_F: ${footerData.Temperature_F}`);
                        }
                    }
                    
                    if (footerData.Camera_ID) {
                        const cameraInput = this.metadataContainer.querySelector('[data-field="Camera_ID"]');
                        if (cameraInput) {
                            cameraInput.value = footerData.Camera_ID;
                            updatedFields.push(`Camera_ID: ${footerData.Camera_ID}`);
                        }
                    }
                    
                    if (footerData.DateTime) {
                        this.addDebugOutput(`✅ DateTime: ${footerData.DateTime}`);
                    }
                    
                    if (updatedFields.length > 0) {
                        this.addDebugOutput(`✅ Extracted: ${updatedFields.join(', ')}`);
                    } else {
                        this.addDebugOutput('⚠️ Footer data extracted but no matching fields found');
                    }
                } else {
                    this.addDebugOutput('❌ No footer data could be extracted');
                }
            } else {
                this.addDebugOutput(`❌ Footer extraction failed: ${result.error}`);
            }
        } catch (error) {
            this.addDebugOutput(`❌ Error extracting footer data: ${error.message}`);
        }
    }
    

    
    toggleIdentifyMode() {
        if (this.isSelecting) {
            this.cancelIdentifyMode();
        } else {
            this.startIdentifyMode();
        }
    }
    
    startIdentifyMode() {
        this.isSelecting = true;
        this.identifyBtn.classList.add('active');
        this.identifyBtn.textContent = 'Cancel Identify';
        this.imageWrapper.classList.add('selecting');
        this.selectionInfo.classList.remove('hidden');
        
        // Disable navigation during selection
        this.firstBtn.disabled = true;
        this.prevBtn.disabled = true;
        this.nextBtn.disabled = true;
        this.lastBtn.disabled = true;
    }
    
    cancelIdentifyMode() {
        this.isSelecting = false;
        this.identifyBtn.classList.remove('active');
        this.identifyBtn.textContent = 'Identify Species';
        this.imageWrapper.classList.remove('selecting');
        this.selectionInfo.classList.add('hidden');
        this.selectionBox.style.display = 'none';
        this.currentSelection = null;
        
        // Re-enable navigation
        this.updateNavigationButtons();
    }
    
    startSelection(e) {
        if (!this.isSelecting) return;
        
        e.preventDefault();
        const rect = this.currentImage.getBoundingClientRect();
        const wrapperRect = this.imageWrapper.getBoundingClientRect();
        
        this.selectionStart = {
            x: e.clientX - wrapperRect.left,
            y: e.clientY - wrapperRect.top
        };
        
        this.selectionBox.style.display = 'block';
        this.selectionBox.style.left = this.selectionStart.x + 'px';
        this.selectionBox.style.top = this.selectionStart.y + 'px';
        this.selectionBox.style.width = '0px';
        this.selectionBox.style.height = '0px';
    }
    
    updateSelection(e) {
        if (!this.isSelecting || !this.selectionStart) return;
        
        e.preventDefault();
        const wrapperRect = this.imageWrapper.getBoundingClientRect();
        
        const currentX = e.clientX - wrapperRect.left;
        const currentY = e.clientY - wrapperRect.top;
        
        const left = Math.min(this.selectionStart.x, currentX);
        const top = Math.min(this.selectionStart.y, currentY);
        const width = Math.abs(currentX - this.selectionStart.x);
        const height = Math.abs(currentY - this.selectionStart.y);
        
        this.selectionBox.style.left = left + 'px';
        this.selectionBox.style.top = top + 'px';
        this.selectionBox.style.width = width + 'px';
        this.selectionBox.style.height = height + 'px';
    }
    
    async endSelection(e) {
        if (!this.isSelecting || !this.selectionStart) return;
        
        e.preventDefault();
        const wrapperRect = this.imageWrapper.getBoundingClientRect();
        const imageRect = this.currentImage.getBoundingClientRect();
        
        const currentX = e.clientX - wrapperRect.left;
        const currentY = e.clientY - wrapperRect.top;
        
        const selectionWidth = Math.abs(currentX - this.selectionStart.x);
        const selectionHeight = Math.abs(currentY - this.selectionStart.y);
        
        // Minimum selection size
        if (selectionWidth < 20 || selectionHeight < 20) {
            this.cancelIdentifyMode();
            return;
        }
        
        // Calculate selection relative to actual image coordinates
        const imageLeft = imageRect.left - wrapperRect.left;
        const imageTop = imageRect.top - wrapperRect.top;
        
        const selectionLeft = Math.min(this.selectionStart.x, currentX) - imageLeft;
        const selectionTop = Math.min(this.selectionStart.y, currentY) - imageTop;
        
        // Scale to original image dimensions
        const scaleX = this.currentImage.naturalWidth / this.currentImage.clientWidth;
        const scaleY = this.currentImage.naturalHeight / this.currentImage.clientHeight;
        
        this.currentSelection = {
            x: Math.max(0, selectionLeft * scaleX),
            y: Math.max(0, selectionTop * scaleY),
            width: selectionWidth * scaleX,
            height: selectionHeight * scaleY
        };
        
        // Perform identification
        await this.identifySpecies();
    }
    
    async identifySpecies() {
        if (!this.currentSelection) return;
        
        // Show loading state
        this.identifyBtn.textContent = 'Identifying...';
        this.identifyBtn.disabled = true;
        
        try {
            const response = await fetch('/api/identify_species', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    image_index: this.currentIndex,
                    selection: this.currentSelection
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.handleIdentificationResult(result.identification);
            } else {
                alert(`Identification failed: ${result.error}`);
            }
        } catch (error) {
            alert(`Error during identification: ${error.message}`);
        } finally {
            this.identifyBtn.disabled = false;
            this.cancelIdentifyMode();
        }
    }
    
    handleIdentificationResult(identification) {
        // Update species field if available
        const speciesInput = this.metadataContainer.querySelector('[data-field="Species"]');
        if (speciesInput && identification.species && identification.species !== 'Unknown') {
            speciesInput.value = identification.species;
        }
        
        // Update count field if available
        const countInput = this.metadataContainer.querySelector('[data-field="Count"]');
        if (countInput && identification.count > 0) {
            countInput.value = identification.count.toString();
        }
        
        // Add AI confidence as a custom field
        if (identification.confidence) {
            this.createMetadataField('AI_Confidence', identification.confidence);
        }
        
        // Add scientific name if available
        if (identification.scientific_name) {
            this.createMetadataField('Scientific_Name', identification.scientific_name);
        }
        
        // Add habitat information if available
        if (identification.habitat) {
            this.createMetadataField('Habitat', identification.habitat);
        }
        
        // Add AI description as notes
        if (identification.description) {
            const notesInput = this.metadataContainer.querySelector('[data-field="Notes"]');
            if (notesInput) {
                const existingNotes = notesInput.value.trim();
                const aiNote = `AI (Namibia): ${identification.description}`;
                notesInput.value = existingNotes ? `${existingNotes}\n${aiNote}` : aiNote;
            }
        }
        
        // Show success message
        alert(`Species identification complete!\n\nSpecies: ${identification.species}\nConfidence: ${identification.confidence}\n\nMetadata has been updated. Don't forget to save your changes.`);
    }
}

// Initialize the application when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new CameraTrapApp();
});