from google.cloud import vision

def process_image_ocr(image_bytes : bytes) -> str:
    """
    Process an image using Google Cloud Vision API OCR.
    
    Args:
        image_bytes: Raw image data as bytes
        
    Returns:
        Extracted text from the image as a string
    """
    client : vision.ImageAnnotatorClient = vision.ImageAnnotatorClient()
    image  : vision.Image = vision.Image(content=image_bytes)
    
    response = client.text_detection(image=image)
    texts = response.text_annotations
    
    if not texts:
        return ""
    
    full_text : str = texts[0].description
    if response.error.message:
        raise Exception(f"Error in OCR processing: {response.error.message}")
        
    return full_text

