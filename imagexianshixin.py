"""
图片相似性检测算法
"""

from PIL import Image
import numpy as np
import os
import cv2
from skimage.metrics import structural_similarity as ssim


# 读取两张图片
def read_images(image_path1, image_path2):
    with open(image_path1, 'rb') as f:
        img1 = f.read()
    with open(image_path2, 'rb') as f:
        img2 = f.read()
    return img1, img2

def hash_image(image,size=8):
    img = image.resize((size, size)).convert('L')  # 转为灰度图
    pixels = np.array(img)
    avg = pixels.mean()
    hash_str = ''.join(['1' if pixel > avg else '0' for row in pixels for pixel in row])
    return hash_str

def hamming_distance(hash1, hash2):
    return sum(c1 != c2 for c1, c2 in zip(hash1, hash2))

# 平均hash算法计算图片相似度
def calculate_similarity(image_path1, image_path2):
    hash1 = hash_image(Image.open(image_path1))
    hash2 = hash_image(Image.open(image_path2))
    distance = hamming_distance(hash1, hash2)
    similarity = 1 - distance / (len(hash1))
    return similarity

def pHash(image_path,size=32,small_size=8):
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    img = cv2.resize(img, (size, size))
    dct = cv2.dct(np.float32(img))
    dct_low_freq = dct[:small_size, :small_size]
    avg = dct_low_freq.mean()
    hash_bits = dct_low_freq > avg
    return ''.join(['1' if bit else '0' for bit in hash_bits.flatten()])

def phash_similarity(image_path1, image_path2):
    hash1 = pHash(image_path1)
    hash2 = pHash(image_path2)
    distance = hamming_distance(hash1, hash2)
    similarity = 1 - distance / (len(hash1))
    return similarity

def ssim_similarity(image_path1, image_path2):
    img1 = cv2.imread(image_path1, cv2.IMREAD_GRAYSCALE)
    img2 = cv2.imread(image_path2, cv2.IMREAD_GRAYSCALE)
    img1 = cv2.resize(img1, (256, 256))
    img2 = cv2.resize(img2, (256, 256))
    score, _ = ssim(img1, img2, full=True)
    return score

if __name__ == "__main__":
    image_path1 = './178-3840x2160.jpg'
    # image_path2 = './423-3840x2160.jpg'
    # image_path2 = './19-3840x2160.jpg'
    # image_path2 = './829-3840x2160.jpg'
    image_path2 = './178-3840x2160.jpg'
    
    similarity = calculate_similarity(image_path1, image_path2)
    print(f"初步图片相似度: {similarity:.2%}")
    if (similarity >= .5):
        similarity = phash_similarity(image_path1, image_path2)
        print(f"进一步图片相似度: {similarity:.2%}")
    if(similarity >= .5):
        print("经过上面的检测还是相似,通过SSIM再看下")
        similarity = ssim_similarity(image_path1, image_path2)
        print(f"最终图片相似度: {similarity:.2%}")
    