import random, time
import cv2
import numpy as np
import multiprocessing as mp

import helper as hp

################################################################################
# Step 2. Dictionary generation
################################################################################
def find_closest_neighbour_idx(neighbours_candidate_dist_func):
    """
    Given a tuple of (neighbours, candidate, dist_func),
    return the index of the 1-kNN of candidate in neighbours.
    """
    neighbours, candidate, dist_func = neighbours_candidate_dist_func

    closest_idx = 0
    curr_dist = dist_func(candidate, neighbours[closest_idx])

    for i in range(len(neighbours)):
        this_dist = dist_func(candidate, neighbours[i])

        if this_dist < curr_dist:
            closest_idx = i
            curr_dist = this_dist

    return closest_idx

def gen_codebook(feature_descriptors, fname, dist_func=hp.euclidean_distance, num_words=500):
    start_time = time.time()

    # Initialise. Randomly choose num_words feature descriptors as cluster centres.
    codebook = []
    random_idxs = np.random.choice(len(feature_descriptors), num_words)
    for i in random_idxs:
        codebook.append(feature_descriptors[i])

    # Do clustering while there are any changes in any cluster centre, but not more than max_iter.
    max_iter = 10
    for iteration in range(1, max_iter+1):
        # Find the indexes of the nearest cluster for each descriptor.
        # This step is easily parallelizable.
        with mp.Pool(mp.cpu_count()) as pool:
            # pool.map takes one argument.
            map_input = [(codebook, descriptor, dist_func) for descriptor in feature_descriptors]
            closest_cluster_idxs = pool.map(find_closest_neighbour_idx, map_input)

        # Collect all the descrtiptors mapped to the same keyword from the calculated indexes.
        cluster_vectors_map = [[word] for word in codebook]
        for i in range(len(closest_cluster_idxs)):
            # pool.map results are ordered,
            # i.e. the output closest_cluster_idxs[i] corresponds to the descriptor[i]
            cluster_vectors_map[closest_cluster_idxs[i]].append(feature_descriptors[i])

        # Calculate new cluster centers. This is also easily parallelizable.
        with mp.Pool(mp.cpu_count()) as pool:
            new_centers = pool.map(hp.mean, cluster_vectors_map)

        # Stop if there are no more improvements to be made.
        if np.all(np.array(codebook) == np.array(new_centers)):
            break

        # Assign new centers.
        for i in range(len(codebook)):
            codebook[i] = new_centers[i]
        hp.save_to_pickle(fname, codebook)
        print(f'Finished iteration {iteration} at minute {(time.time() - start_time)/60}.')


    return codebook

################################################################################
# Main
################################################################################
if __name__ == "__main__":
    start_time = time.time()

    # Merge the descriptors from one class into a single list.
    # training_descriptors will hold ['class_name': descriptors_list] pairs
    training_descriptors = hp.load_descriptors(test_or_train='Training', merge_in_class=True)

    # A single list for all feature descriptors from all classes.
    # Pick the same number of descriptors from each class to prevent bias in the code book.
    min_len_descriptors = min(map(len, training_descriptors.values()))
    all_descriptors = []
    capped_descriptors = []
    for descriptors in training_descriptors.values():
        capped_descriptors += random.sample(descriptors, min_len_descriptors)
        all_descriptors += descriptors

    gen_codebook(capped_descriptors, fname=hp.SAD_CODEBOOK_FILE_TRAIN, dist_func=hp.sad, num_words=500)
    gen_codebook(capped_descriptors, fname=hp.SAD_SMALL_CODEBOOK_FILE_TRAIN, dist_func=hp.sad, num_words=20)

    gen_codebook(capped_descriptors, fname=hp.CODEBOOK_FILE_TRAIN, dist_func=hp.euclidean_distance, num_words=500)
    gen_codebook(capped_descriptors, fname=hp.SMALL_CODEBOOK_FILE_TRAIN, dist_func=hp.euclidean_distance, num_words=20)

    gen_codebook(all_descriptors, fname=hp.SAD_UNLIMITED_CODEBOOK_FILE_TRAIN, dist_func=hp.sad, num_words=500)
    gen_codebook(all_descriptors, fname=hp.SAD_UNLIMITED_SMALL_CODEBOOK_FILE_TRAIN, dist_func=hp.sad, num_words=20)

    gen_codebook(all_descriptors, fname=hp.UNLIMITED_CODEBOOK_FILE_TRAIN, dist_func=hp.euclidean_distance, num_words=500)
    gen_codebook(all_descriptors, fname=hp.UNLIMITED_SMALL_CODEBOOK_FILE_TRAIN, dist_func=hp.euclidean_distance, num_words=20)

    print(f'Finished program in {(time.time() - start_time)/60} minutes.')
