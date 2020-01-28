import os
import sys
parent_dir = os.path.dirname(os.path.abspath(__file__))
gparent_dir = os.path.dirname(parent_dir)
ggparent_dir = os.path.dirname(gparent_dir)
sys.path += [parent_dir, gparent_dir, ggparent_dir]
import cv2
import json
import timeit
from vision.blob.blobfind import BlobFinder, import_params

prefix = 'vision' if os.path.isdir("vision") else ''
img_folder = os.path.join(prefix, 'vision_images', 'blob')
config_filename = os.path.join(prefix, 'blob', 'config.json')

with open(config_filename, 'r') as config_file:
    config = json.load(config_file)

for img in os.listdir(img_folder):
    if img[-4:] not in ['.png', '.jpg']:
        continue

    image = cv2.imread(os.path.join(img_folder, os.fsdecode(img)))
    blob_finder = BlobFinder(image, params=import_params(config))
    print(img, image.shape, timeit.timeit(blob_finder.find, number=10) / 10)
