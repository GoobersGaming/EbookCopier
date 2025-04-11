import cv2
import numpy as np
from PIL import Image
import logging
logger = logging.getLogger(__name__)


"""Functions For Comparing And Manipulating Images"""
# TODO:Compare Images, Should Be Is It An Exact Copy And Not A %ALIKE.
# convert_to_pil needed?

def pil_to_cv2(image):
    if isinstance(image, Image.Image):
        img_np = np.array(image)
        img_cv2 = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
        return img_cv2
    elif isinstance(image, np.ndarray):
        return image
    else:
        logging.error("Only CV2 or PIL immage formats accepted")
        raise TypeError("Only CV2 or PIL image formats accepted")

def is_blank(image, edge_threshold=0.01):
    # edge_threshold: Ratio of edge pixels (e.g., 0.01 = 1% edges).
    if image is None:
        return True
    image_cv2 = pil_to_cv2(image)
    gray = cv2.cvtColor(image_cv2, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    edge_pixels = np.sum(edges > 0)
    total_pixels = edges.shape[0] * edges.shape[1]
    
    edge_ratio = edge_pixels / total_pixels
    logging.debug(f"is_blank, edge_ratio: {edge_ratio}, edge_threshold: {edge_threshold}, result: {edge_ratio < edge_threshold}")
    return edge_ratio < edge_threshold  # True if Too few edges = empty

def convert_to_pil(image):
    """Ensure the image is in a format suitable fr saving to a PDF"""
    if isinstance(image, Image.Image):  #Already PIL Image
        return image
    elif isinstance(image, np.ndarray): #OpenCV Image
        return Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    else:
        raise ValueError("Unsupported image format")

# def compare_images(current_image, previous_image, threshold=0.95):
#     #logs.LOOGGER.info("Comparing images")
#     #convert imaeg to numpy arrays
#     current_image_np = np.array(current_image)
#     previous_image_np = np.array(previous_image)

#     #convert to grayscale
#     current_image_gray = cv2.cvtColor(current_image_np, cv2.COLOR_RGB2GRAY)
#     previous_image_gray = cv2.cvtColor(previous_image_np, cv2.COLOR_RGB2GRAY)

#     #compute ssim
#     score, _ = ssim(current_image_gray, previous_image_gray, full=True)
#     #logs.LOOGGER.info(f"Image Duplicate: {score >=threshold}")
#     #logs.LOOGGER.debug(f"compare_images score: {score}, threshold: {threshold}, result {score >= threshold}")
#     return score >= threshold #Returns True if similarity is above threshold

def compare_images(current_image, previous_image):
    """Look to see if pictures are identical by pixel"""
    current_np = np.array(current_image)
    previous_np = np.array(previous_image)
    result = np.array_equal(current_np, previous_np)
    return result