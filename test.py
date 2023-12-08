import cv2
from skimage.metrics import structural_similarity as ssim
import math
import numpy as np

# very time costly
def compare_images(imageA_path, imageB_path):
    imageA = cv2.imread(imageA_path, cv2.IMREAD_GRAYSCALE)
    imageB = cv2.imread(imageB_path, cv2.IMREAD_GRAYSCALE)
    standard_size = [3508,2480]
    zoom1 = [standard_size[0] / imageA.shape[0], standard_size[1] / imageA.shape[1]]
    zoom2 = [standard_size[0] / imageB.shape[0], standard_size[1] / imageB.shape[1]]
    imageA = scipy.ndimage.zoom(imageA, zoom1, order=2)
    # print(imageA.shape)
    imageB = scipy.ndimage.zoom(imageB, zoom2, order=2)
    # print(imageB.shape)

    if imageA.shape != imageB.shape:
        raise ValueError("Input images must have the same dimensions.")

    score, _ = ssim(imageA, imageB, full=True)
    return score

print(compare_image_similarity("./testpaper/image_save/jdg1.pdf.png", "./testpaper/image_save/jdg2.pdf.png"))