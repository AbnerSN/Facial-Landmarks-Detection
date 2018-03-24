#!/bin/python3.6
import pickle, dill
import os, sys
import numpy as np
import cv2, dlib
import argparse
from multiprocessing import Pool, cpu_count
from imutils import resize

parser = argparse.ArgumentParser(description='Prepares a dataset for the facial landmarks algorithm\'s training process.')
parser.add_argument('images_path', help='directory to read the images from.')
parser.add_argument('annotations_path', help='directory to read the annotations from.')
parser.add_argument('--output', help='output file', default='data.bin')
args = parser.parse_args()

print('reading images from directory')
images = {}
for file_name in os.listdir(args.images_path):
    path = os.path.join(args.images_path, file_name)
    img = cv2.imread(path, 0)
    images[file_name] = img

print('reading annotations')
annotations = {}
for annotation_file in os.listdir(args.annotations_path):
    path = os.path.join(args.annotations_path, annotation_file)
    with open(path, 'r') as csv_file:
        image_file = csv_file.readline().rstrip()
        if image_file in images.keys():
            points = []
            for line in csv_file:
                [point_x, point_y] = line.split(' , ')
                point = (float(point_x), float(point_y))
                points.append(point)
            annotations[image_file] = np.array(points)

detector = dlib.get_frontal_face_detector()
def process(item):
    file_name, image = item
    annotation = annotations[file_name]

    # Use dlib to detect faces
    faces = detector(image)

    # If dlib can't detect a face, a bounding box
    # will be used as the face region.
    if len(faces) == 0:
        print('no faces on {}'.format(file_name))
        min_x = np.min(annotation[:, 0])
        min_y = np.min(annotation[:, 1])
        max_x = np.max(annotation[:, 0])
        max_y = np.max(annotation[:, 1])
        width = abs(max_x - min_x)
        height = abs(max_y - min_y)
        top_left = np.array([min_x, min_y])
    # If it detects one, the data will be collected
    # from it.
    elif len(faces) == 1:
        print('one face on {}'.format(file_name))
        face = faces[0]
        top_left = np.array([face.left(), face.top()])
        width = face.width()
        height = face.height()
    # If it detects more than one, the face that is closest to
    # the annotations will be picked.
    else:
        print('more than one faces on {}'.format(file_name))
        annotation_center = np.mean(annotation, axis=0)
        closest_distance = float('inf')
        closest_index = 0
        for i, face in enumerate(faces):
            top_left = np.array([face.left(), face.top()])
            bottom_right = np.array([face.right(), face.bottom()])
            face_center = (top_left + bottom_right) / 2
            distance = np.sum(np.power(face_center - annotation_center, 2))
            if distance <= closest_distance:
                closest_distance = distance
                closest_index = i
        face = faces[closest_index]
        top_left = np.array([face.left(), face.top()])
        width = face.width()
        height = face.height()

    return (file_name, {
        'image': image,
        'annotations': annotation,
        'top_left': top_left.astype(int),
        'width': int(round(width)),
        'height': int(round(height))
    })


p = Pool(cpu_count())
data = dict(p.map(process, images.items()))

with open(args.output, 'wb') as f:
    dill.dump(data, f)

print('finished processing')