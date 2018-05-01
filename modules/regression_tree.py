import numpy as np
from scipy.spatial.distance import cdist as distance
from modules.procrustes import calculate_procrustes, mean_of_shapes, root_mean_square

class RegressionTree:

    @staticmethod
    def __split_node(node, split_params, data):
        index, point_u, point_v, threshold = split_params        
        left = []
        right = []
        for sample in node:
            intensity_data = data[label]['intensity_data']
            intensity_u = intensity_data[index][point_u]
            intensity_v = intensity_data[index][point_v]
            if intensity_u - intensity_v > threshold:
                left.append(label)
            else:
                right.append(label)
        return (left, right)


    def apply(self, data):
        param_index = 0
        split_params = self.splits[param_index]
        while param_index < len(self.splits):
            index, index_u, index_v, threshold = split_params
            intensity_u = data[index][index_u]
            intensity_v = data[index][index_v]
            if intensity_u - intensity_v <= threshold:
                param_index = param_index * 2 + 1
            else:
                param_index = param_index * 2 + 2
            if param_index < len(self.splits):
                split_params = self.splits[param_index]
        return param_index - (2 ** self.depth)

    def __predict_node(self, node, data):
        if len(node) == 0:
            return np.zeros(self.shape)

        prediction = np.zeros(self.shape)
        for label in node:
            regression_data = data[label]['regression_data']
            prediction += regression_data
        return prediction / len(node)


    def __calc_split(self, node, data):

        index, point_u, point_v = self.pairsQueue.pop(0)

        thresholds = np.random.randint(-70, 70, 20)

        maximum_diff = -float("inf")
        best_threshold = 0

        for threshold in thresholds:
            left, right = self.__split_node(node, index, point_u, point_v, threshold, data)
            prediction_left = self.__predict_node(left, data)
            prediction_right = self.__predict_node(right, data)
            diff = (len(left) * np.sum(np.power(prediction_left, 2))
                    + len(right) * np.sum(np.power(prediction_right, 2)))

            if diff > maximum_diff:
                maximum_diff = diff
                best_threshold = threshold

        return (index, point_u, point_v, best_threshold)


    def __grow(self, dataset):
        nodes_queue = [dataset]
        levels_queue = [0]
        for _ in range((2 ** self.depth) - 1):
            node = nodes_queue.pop(0)
            level = levels_queue.pop(0)
            split_params = self.__calc_split(node, dataset)
            self.splits.append(split_params)
            left, right = self.__split_node(node, split_params, dataset)
            nodes_queue.append(left)
            levels_queue.append(level + 1)

            nodes_queue.append(right)
            levels_queue.append(level + 1)
        for leaf in nodes_queue:
            self.predictions.append(self.__predict_node(leaf, dataset))
    

    def __init__(self, depth, dataset, model):
        self.depth = depth
        self.splits = []
        self.predictions = []
        self.model = model

        sample = dataset[0]

        self.shape = np.array(sample['regression_data']).shape
        self.number_of_points = len(sample['intensity_data'])

        self.pairsQueue = []
        indexes = np.arange(len(sample['sample_points']))
        points_per_landmark = len(sample['sample_points'][0])
        np.random.shuffle(indexes)
        for index in indexes:
            sub_indexes = np.arange(points_per_landmark)
            np.random.shuffle(sub_indexes)
            self.pairsQueue.append((index, sub_indexes[0], sub_indexes[1]))


        self.__grow(labels, dataset)
