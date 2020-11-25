import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import cv2
import fnmatch, os, collections, re, math
from typing import List, Dict, Set

################################################################################
# Constants
################################################################################

DATASET_DIR = 'COMP338_Assignment1_Dataset'
CLASSES = [
    'airplanes',
    'cars',
    'dog',
    'faces',
    'keyboard',
]
TRAINING_PATH  = f'{DATASET_DIR}/Training'
TEST_PATH = f'{DATASET_DIR}/Test'

# Codebooks
CODEBOOK_FILE_TRAIN = f'{DATASET_DIR}/Training/codebook.npy'
SMALL_CODEBOOK_FILE_TRAIN = f'{DATASET_DIR}/Training/codebook_small.npy'
UNLIMITED_CODEBOOK_FILE_TRAIN = f'{DATASET_DIR}/Training/codebook_unlimited.npy'
UNLIMITED_SMALL_CODEBOOK_FILE_TRAIN = f'{DATASET_DIR}/Training/codebook_small_unlimited.npy'

SAD_CODEBOOK_FILE_TRAIN = f'{DATASET_DIR}/Training/codebook_sad.npy'
SAD_SMALL_CODEBOOK_FILE_TRAIN = f'{DATASET_DIR}/Training/codebook_small_sad.npy'
SAD_UNLIMITED_CODEBOOK_FILE_TRAIN = f'{DATASET_DIR}/Training/codebook_unlimited_sad.npy'
SAD_UNLIMITED_SMALL_CODEBOOK_FILE_TRAIN = f'{DATASET_DIR}/Training/codebook_small_unlimited_sad.npy'

MAP_KPS_TO_CODEBOOK_FILE = f'{DATASET_DIR}/map_kps_to_codewords.npy'
MAP_KPS_TO_SMALL_CODEBOOK_FILE = f'{DATASET_DIR}/map_kps_to_codewords_small.npy'
MAP_KPS_TO_SAD_CODEBOOK_FILE = f'{DATASET_DIR}/map_kps_to_codewords_sad.npy'
MAP_KPS_TO_SMALL_SAD_CODEBOOK_FILE = f'{DATASET_DIR}/map_kps_to_codewords_small_sad.npy'

SMALL_HISTOGRAM_BINARY_FORMAT = "*histogram_small.npy"
LARGE_HISTOGRAM_BINARY_FORMAT = "*histogram.npy"


################################################################################
# Common math functions
################################################################################

def euclidean_distance(vec1, vec2):
    # assert len(vec1) == len(vec2), 'vec1 and vec2 not same length.'

    total = 0
    for i in range(len(vec1)):
        total += pow(vec1[i] - vec2[i], 2)

    return math.sqrt(total)

def sad(vec1, vec2):
    # assert len(vec1) == len(vec2), 'vec1 and vec2 not same length.'

    total = 0
    for i in range(len(vec1)):
        total += abs(vec1[i] - vec2[i])

    return total

def mean(vectors):
    """
    Given a list of vectors, return the average vector.
    """
    return np.sum(vectors, 0) / len(vectors)

################################################################################
# Get directory or file paths
################################################################################

def get_training_histogram_keys():
    return [(CLASSES[i], f'{TRAINING_PATH}/{CLASSES[i]}') for i in range(len(CLASSES))]

def get_test_histogram_keys():
    return [(CLASSES[i], f'{TEST_PATH}/{CLASSES[i]}') for i in range(len(CLASSES))]

def get_image_paths(image_format: str, path=TEST_PATH):
    image_paths = collections.defaultdict(list)

    for class_name in CLASSES:
        directory = f'{path}/{class_name}'
        for file in os.listdir(directory):
            if fnmatch.fnmatch(file, f'*.{image_format}'):
                image_paths[(class_name, directory)].append(file)
    return image_paths

def get_histogram_paths(normal=False):
    training_histogram_paths = collections.defaultdict(list)
    test_histogram_paths = collections.defaultdict(list)

    histogram_file_extension = LARGE_HISTOGRAM_BINARY_FORMAT if normal else SMALL_HISTOGRAM_BINARY_FORMAT

    for class_name in CLASSES:
        training_directory, test_directory = f'{TRAINING_PATH}/{class_name}', f'{TEST_PATH}/{class_name}'

        for file in os.listdir(training_directory):
            if fnmatch.fnmatch(file, histogram_file_extension):
                training_histogram_paths[(class_name, training_directory)].append(file)

        for file in os.listdir(test_directory):
            if fnmatch.fnmatch(file, histogram_file_extension):
                test_histogram_paths[(class_name, test_directory)].append(file)

    return test_histogram_paths, training_histogram_paths

################################################################################
# Read/write binary files
################################################################################

def load_pickled_list(fname) -> List:
    l = []
    with open(fname, 'rb') as f:
        l = np.load(f, allow_pickle=True)
    return l.tolist()


def load_all_histograms(histograms_file_paths):
    histogram_values = collections.defaultdict(list)

    for path_key in histograms_file_paths:
        for file in histograms_file_paths[path_key]:
            load_histograms_values = np.load(f'{path_key[1]}/{file}', allow_pickle=True)
            histogram_values[path_key].append(load_histograms_values.tolist())

    return histogram_values

def load_single_histogram(histogram_file_paths, filter_key=None):
    histogram_values = collections.defaultdict(list)

    for file in histogram_file_paths[filter_key]:
        load_histograms_values = np.load(f'{filter_key[1]}/{file}', allow_pickle=True)
        histogram_values[filter_key].append(load_histograms_values.tolist())

    return histogram_values if filter_key else load_all_histograms(histogram_file_paths)

def load_images_in_directory(path) -> Dict[str, List]:
    images = {}
    for filename in os.listdir(path):
        img = cv2.imread(os.path.join(path, filename), cv2.IMREAD_GRAYSCALE)
        if img is not None:
            images[filename] = img

    return images

def load_np_pickles_in_directory(path, regex=r'.*.(npy|npc)'):
    """
    Given a {path} to a directory load all numpy pickle files in that directory that match {regex}.
    Return a dictionary, {fname: np.load(fname)}, where fname includes only the part before '.' and '_'.
    """
    result = {}
    for filename in os.listdir(path):
        if re.match(regex, filename):
            # Get rid of file extensions and (keypoints|descriptors) annotations.
            key = filename.split('.')[0].split('_')[0]
            result[key] = np.load(path + filename, allow_pickle=True)

    return result

def load_descriptors(test_or_train, merge_in_class=False):
    """
    Read the descriptors from the {test_or_train} dataset.
    Return a dictionary with the class names as keys.
    If {merge_in_class} is True, then a single class will have a list of all descriptors as the value.
    Otherwise, it will have a list of dictionaries as values, where the dictionaries have
    the individual img filename as key and their list of descriptors as values.

    if not merge_in_class:
    descriptors = {
        cars: {
            img0: [descriptor1, descriptor2, ....],
            img1: [descriptor1, descriptor2, ....],
            ...
        },
        airplanes: {...}
        ...
    }
    """
    descriptors = {}
    for class_name in CLASSES:
        match_descriptors = r'.*_descriptors' + re.escape('.npy')
        load_from = f'{DATASET_DIR}/{test_or_train}/{class_name}/'
        descriptors_dict = load_np_pickles_in_directory(load_from, match_descriptors)

        if merge_in_class:
            # Merge all img descriptors from tge same class into one list.
            # We ignore the individual img file names here.
            class_descriptors = []
            for img_descriptors in descriptors_dict.values():
                for d in img_descriptors:
                    class_descriptors.append(d)

            descriptors[class_name] = class_descriptors
        else:
            descriptors[class_name] = descriptors_dict

    return descriptors

def load_keypoints(test_or_train, merge_in_class=False):
    """
    Read the keypoints from the {test_or_train} dataset.
    Return a dictionary with the class names as keys.
    If {merge_in_class} is True, then a single class will have a list of all keypoints as the value.
    Otherwise, it will have a list of dictionaries as values, where the dictionaries have
    the individual img filename as key and their list of keypoints as values.
    """
    keypoints = {}
    for class_name in CLASSES:
        match_keypoints = r'.*_keypoints' + re.escape('.npy')
        load_from = f'{DATASET_DIR}/{test_or_train}/{class_name}/'
        keypoints_dict = load_np_pickles_in_directory(load_from, match_keypoints)

        if merge_in_class:
            # Merge all img keypoints from tge same class into one list.
            # We ignore the individual img file names here.
            class_keypoints = []
            for img_keypoints in keypoints_dict.values():
                for d in img_keypoints:
                    class_keypoints.append(d)

            keypoints[class_name] = class_keypoints
        else:
            keypoints[class_name] = keypoints_dict

    return keypoints


def save_to_pickle(pickle_fname, data):
    with open(pickle_fname, 'wb') as f:
        np.save(f, data)


################################################################################
# Result visualisations
################################################################################

def display_image_with_label(label, image_path):
    img = mpimg.imread(image_path)
    imgplot = plt.imshow(img)
    plt.title(label)
    plt.show()

def display_multiple_image_with_labels(class_type, images_and_labels):
    rows = 2
    cols = len(images_and_labels) // 2
    figure, ax = plt.subplots(nrows=rows, ncols=cols)

    for i, image_label_object in enumerate(images_and_labels):
        img = mpimg.imread(f'{class_type[1]}/{image_label_object[1]}')
        label = f'{image_label_object[0]} \n {image_label_object[1]}'
        ax.ravel()[i].imshow(img)
        ax.ravel()[i].set_title(label)
        ax.ravel()[i].set_axis_off()

    plt.tight_layout()
    plt.show()