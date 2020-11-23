import random, time, re, os
import cv2
import numpy as np

from helper import load_descriptors, save_to_pickle, DATASET_DIR, CLASSES, CODEBOOK_FILE_TRAIN, SMALL_CODEBOOK_FILE_TRAIN


################################################################################
# Step 2. Dictionary generation
################################################################################
def find_closest_neighbour_idx(neighbours, candidate):
    closest_idx = 0
    curr_dist = np.sum(abs(neighbours[closest_idx] - candidate))

    for i in range(len(neighbours)):
        if np.sum(abs(neighbours[i] - candidate)) < curr_dist:
            closest_idx = i
            curr_dist = np.sum(abs(neighbours[closest_idx] - candidate))

    return closest_idx

def gen_dictionary(feature_descriptors, num_words=500):
    start_time = time.time()

    codebook = []
    # Initialise. Randomly choose num_words features as cluster centres.
    random_idxs = np.random.choice(len(feature_descriptors), num_words)
    for i in random_idxs:
        # :TODO: Remove from the list here?
        # descriptor = feature_descriptors.pop(i)
        descriptor = feature_descriptors[i]
        codebook.append(descriptor)

    # Do, while there were any changes in any cluster.
    # Use the L1 norm to check for closeness.
    # l1_norm = lambda v : np.sum(abs(v))
    no_change = False
    max_iter = 100
    iteration = 0
    while not no_change and iteration < max_iter:
        iteration += 1
        no_change = True

        for descriptor in feature_descriptors:
            closest_cluster_idx = find_closest_neighbour_idx(codebook, descriptor)

            # Update cluster center and increase count.
            new_center = (codebook[closest_cluster_idx] + descriptor) / 2

            # Stop when the improvements become negligable.
            delta_for_change = 10
            if np.any(abs(codebook[closest_cluster_idx] - new_center) > delta_for_change):
                codebook[closest_cluster_idx] = new_center
                no_change = False

        print(f'Finished iteration {iteration} at minute {(time.time() - start_time)/60}.')

    return codebook

################################################################################
# Main
################################################################################
if __name__ == "__main__":
    start_time = time.time()

    # Merge the descriptors from one class into a single list.
    # training_descriptors will hold ['class_name': descriptors_list] pairs
    training_descriptors = load_descriptors(test_or_train='Training', merge_in_class=True)

    # A single list for all feature descriptors from all classes.
    # Pick the same number of descriptors from each class to prevent bias in the code book.
    min_len_descriptors = min(map(len, training_descriptors.values()))
    all_descriptors = []
    for descriptors in training_descriptors.values():
        all_descriptors += random.sample(descriptors, min_len_descriptors)

    # Generate one codebook for all classes.
    codebook = gen_dictionary(descriptors)
    save_to_pickle(CODEBOOK_FILE_TRAIN, codebook)

    small_codebook = gen_dictionary(descriptors, num_words=20)
    save_to_pickle(SMALL_CODEBOOK_FILE_TRAIN, small_codebook)


    print(f'Finished program in {(time.time() - start_time)/60} minutes.')
