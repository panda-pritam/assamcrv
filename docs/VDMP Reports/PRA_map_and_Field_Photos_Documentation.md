# VDMP Reports - PRA Map and Field Photos Module

## Overview
This module handles the generation of PRA (Participatory Rural Appraisal) maps and field photographs section in VDMP reports. It processes and displays categorized field images with proper scaling and formatting.

## Main Function
**Function:** `draw_PRA_map_and_field_photos(elements, village_id)`

## Purpose
Generates Section 7 of VDMP reports containing PRA maps and categorized field photographs for comprehensive village documentation.

## Database Tables Used

### Primary Table
- **FieldImage**: Main table for field photographs
  - `village_id` - Village identifier (Foreign Key)
  - `category` - Image category classification
  - `image` - Image file path/reference
  - `upload_datetime` - Timestamp for ordering
  - `name` - Optional image caption/description

### Related Tables
- **tblVillage**: Village information (imported but not directly used)
- **task_force.models**: Task force related models (imported)

## Image Categories

| Category | Section Title | Description |
|----------|---------------|-------------|
| PRA Map | Field photographs – PRA Map | Participatory Rural Appraisal maps |
| PRA and field consultations | Field photographs – PRA and field consultations | Community consultation images |
| housing | Field photographs – housing | Housing and residential structures |
| Infrastructure | Field photographs – Infrastructure | Village infrastructure facilities |
| River bank protection/erosion | Field photographs – River bank protection/erosion | Erosion control and riverbank images |
| Educational facilities | Field photographs – Educational facilities | Schools and educational infrastructure |
| Livelihood | Field photographs – Livelihood | Livelihood activities and resources |

## Key Features

### Image Processing
- **Adaptive Scaling**: Images scaled based on aspect ratio
  - High aspect ratio (>1.2): max height 4.5 inches
  - Normal aspect ratio: max height 3.8 inches
- **EXIF Orientation**: Automatic rotation correction using `ImageOps.exif_transpose()`
- **Format Optimization**: JPEG compression with 75% quality for file size optimization
- **Aspect Ratio Preservation**: Maintains original proportions during scaling

### Image Resolution Logic
```python
def get_scaled_image(img_path):
    # Adaptive height based on aspect ratio
    if aspect > 1.2:
        local_max_height = 4.5 * inch
    else:
        local_max_height = 3.8 * inch
    
    # Scale to fit within bounds
    width = min(max_width, iw)
    height = width * aspect
    
    if height > local_max_height:
        height = local_max_height
        width = height / aspect
```

### Path Resolution
- **Primary Path**: Direct file system path via `img_obj.image.path`
- **Fallback Path**: Media root + relative path construction
- **Cross-platform**: Handles both forward and backslashes
- **Existence Validation**: Checks file existence before processing

### Layout Management
- **Sequential Display**: Images displayed one below another
- **Spacing Control**: 8-point spacing between images
- **Section Numbering**: Auto-incremented sub-sections (7.1, 7.2, etc.)
- **Center Alignment**: All images centered on page

## Error Handling

### Image Processing Errors
- File not found handling
- Corrupt image file handling
- Path resolution failures
- Memory optimization for large images

### Graceful Degradation
- Continues processing if individual images fail
- Displays error messages for failed images
- Shows "No data available" message if no images exist
- Logs errors without breaking report generation

## Technical Specifications

### Image Constraints
- **Maximum Width**: Full page width (A4)
- **Maximum Height**: 4.2 inches (adaptive)
- **Format**: JPEG with 75% quality
- **Color Mode**: RGB conversion
- **Alignment**: Center-aligned

### Dependencies
- **ReportLab**: PDF generation and image handling
- **PIL (Pillow)**: Image processing and optimization
- **Django**: ORM and file handling
- **BytesIO**: In-memory image buffer management

## Usage Example

```python
from .PRA_map_and_Field_Photos import draw_PRA_map_and_field_photos

# Add PRA maps and field photos to report
elements = []
village_id = 123
draw_PRA_map_and_field_photos(elements, village_id)
```

## Data Flow

```
Village ID Input
       ↓
Query FieldImage by Category
       ↓
For Each Category:
   ├── Check Image Existence
   ├── Create Sub-section Header
   └── Process Images:
       ├── Resolve File Path
       ├── Scale and Optimize
       ├── Add to Elements
       └── Apply Spacing
       ↓
Generate Section 7 Content
```

## Section Structure

```
7. PRA map and Field Photos
├── 7.1 Field photographs – PRA Map
├── 7.2 Field photographs – PRA and field consultations  
├── 7.3 Field photographs – housing
├── 7.4 Field photographs – Infrastructure
├── 7.5 Field photographs – River bank protection/erosion
├── 7.6 Field photographs – Educational facilities
└── 7.7 Field photographs – Livelihood
```

## Performance Optimizations

### Memory Management
- **BytesIO Buffers**: In-memory processing to avoid temporary files
- **Image Compression**: 75% JPEG quality reduces file size
- **Lazy Loading**: Images processed only when needed
- **Buffer Cleanup**: Automatic memory cleanup after processing

### File System Optimization
- **Path Caching**: Resolved paths cached during processing
- **Existence Checks**: File existence validated before processing
- **Cross-platform Paths**: Handles different OS path separators

## Configuration

### Styling Constants
- `blue_heading`: Main section heading style
- `blue_sub_heading`: Sub-section heading style  
- `normal_style`: Default text style
- `image_title`: Image caption style (unused in current implementation)

### Layout Constants
- `max_width`: Page width constraint
- `max_height`: Base image height (4.2 inches)
- `page_width`, `page_height`: A4 page dimensions

## Error Messages
- "Image error: {error_details}" - Individual image processing failure
- "No field photographs or PRA maps are available for this village." - No data available
- Console logging for section processing errors