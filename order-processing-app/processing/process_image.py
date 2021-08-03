from typing import Tuple
from processing.canny_edge_detector import CannyEdgeDetector
from PIL import Image
import numpy as np

edge_detector = CannyEdgeDetector(lowthreshold=0.04, highthreshold=0.13)
TARGET_SIZE_PX = 500_000

def process_image(pic: Image.Image) -> Tuple[int, Image.Image]:
    pixels = np.array(_normalise_size(pic))
    
    edges = edge_detector.detect(pixels)
    edginess = _calculate_edginess(edges)

    result_img = Image.fromarray(edges).convert("RGB")

    return (edginess, result_img)

def _normalise_size(pic: Image.Image) -> Image.Image:
    size = pic.width * pic.height
    scale_factor = TARGET_SIZE_PX / size
    return pic.resize((int(pic.width * scale_factor), int(pic.height * scale_factor)), Image.LANCZOS)

def _calculate_edginess(edge_pixels: np.ndarray):
    return 100 * np.count_nonzero(edge_pixels) / TARGET_SIZE_PX
