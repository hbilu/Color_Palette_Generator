from PIL import Image, ImageOps
import numpy as np
from collections import defaultdict
from flask import Flask, render_template, request, url_for
import os
from werkzeug.utils import secure_filename

def open_and_convert_to_rgb(path):
    """
    Opens an image file at the specified path and converts it to RGB mode.
    Args:
        path (str): Path to the image file.
    Returns:
        PIL.Image.Image: Image object in RGB mode.
    """
    img = Image.open(path).convert('RGB')
    return img

def scale_image_if_needed(img):
    """
    Scales the input image if its dimensions exceed predefined thresholds.
    Args:
        img (PIL.Image.Image): Input image object.
    Returns:
        PIL.Image.Image: Scaled image object, if scaling is applied; otherwise, the original image.
    """
    thresholds = [400, 600, 800, 1200]
    factors = [0.2, 0.4, 0.5, 0.6]
    size = img.size
    for threshold, factor in zip(thresholds, factors):
        if size[0] >= threshold or size[1] >= threshold:
            img = ImageOps.scale(img, factor=factor)
            break  # Stop after first applicable scale
    return img

# Function to reduce the number of bits per color channel (3 bits per channel) in the image
def reduce_bits_per_channel(img):
    img = ImageOps.posterize(img, 3)
    return img

# Function to convert the image into a numpy array
def convert_to_numpy_array(img):
    image_array = np.array(img)
    return image_array

def get_top_15_colors(image_array):
    """
    Retrieves the top 15 most occurring colors from the input image array.
    Args:
        image_array (numpy.ndarray): Numpy array representing the image.
    Returns:
        list: List of RGB tuples representing the top 15 most frequent colors in the image.
    """
    # Initialize a defaultdict to store color frequencies
    unique_color_counts = defaultdict(int)
    # Count occurrences of each color tuple in the image array
    for column in image_array:
        for rgb in column:
            unique_color_counts[tuple(rgb)] += 1
    # Sort the dictionary items based on the count of each color tuple in descending order
    sorted_unique_colors = sorted(unique_color_counts.items(), key=lambda x: x[1], reverse=True)
    # Extract the top 15 most frequent color tuples from the sorted list
    top_15 = [color[0] for color in sorted_unique_colors[:15]]
    return top_15

def rgb_to_hex(rgb):
    """
    Converts an RGB tuple to its hexadecimal representation.
    Args:
        rgb (tuple): Tuple containing RGB values (r, g, b).
    Returns:
        str: Hexadecimal representation of the RGB color.
    """
    return '{:02x}{:02x}{:02x}'.format(rgb[0], rgb[1], rgb[2])

def rgb_to_cmyk(rgb):
    """
    Converts an RGB tuple to its CMYK representation.
    Args:
        rgb (tuple): Tuple containing RGB values (r, g, b).
    Returns:
        tuple: CMYK representation of the RGB color.
    """
    r, g, b = [x / 255.0 for x in rgb]
    k = 1 - max(r, g, b)
    if k < 1:
        c = (1 - r - k) / (1 - k)
        m = (1 - g - k) / (1 - k)
        y = (1 - b - k) / (1 - k)
    else:
        c = 0
        m = 0
        y = 0
    return (round(c,2), round(m,2), round(y,2), round(k,2))

def analyze_image_colors(path, code):
    """
    Analyzes the colors of an image located at the given path.
    Args:
        path (str): Path to the image file.
        code (str): Color code format desired ('hex' for hexadecimal, 'cmyk' for CMYK, anything else for RGB tuples).
    Returns:
        list: List of top 10 colors in the specified format.
    """
    img = open_and_convert_to_rgb(path)
    img = scale_image_if_needed(img)
    img = reduce_bits_per_channel(img)
    image_array = convert_to_numpy_array(img)
    top_15_colors = get_top_15_colors(image_array)
    if code == 'hex':
        return [rgb_to_hex(color) for color in top_15_colors]
    elif code == 'cmyk':
        return [rgb_to_cmyk(color) for color in top_15_colors]
    else:
        return top_15_colors

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

upload_folder = 'env/static/images/'

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = upload_folder

@app.route('/', methods=['GET', 'POST']) 
def index(): 
    """
    Renders the index.html template for GET requests and processes image analysis for POST requests.
    Returns:
        str: Rendered HTML template displaying color analysis results.
    """
    if request.method == 'POST':
        if 'image' not in request.files:
            return 'No file part' 
        f = request.files['image'] 
        if f.filename == '':
            return 'No selected file'
        if f and allowed_file(f.filename):
            filename = secure_filename(f.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            f.save(filepath)
            color_code = request.form['code']
            colors = analyze_image_colors(filepath, color_code)
            return render_template('index.html', color_list=colors, code=color_code, uploaded_image=filename)
    return render_template('index.html')
  
if __name__ == '__main__': 
    app.run(debug=True) 