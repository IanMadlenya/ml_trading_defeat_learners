"""A simple wrapper for Decision Tree regression"""

import numpy as np
import pandas as pd
from scipy.stats import pearsonr
from copy import deepcopy


class DTLearner(object):

    def __init__(self, leaf_size=1, verbose=False, tree=None):
        self.leaf_size = leaf_size
        self.verbose = verbose
        self.tree = deepcopy(tree)
        if verbose:
            self.get_learner_info()
        

    def __build_tree(self, dataX, dataY):
        """Builds the Decision Tree recursively by choosing the best feature to split on and 
        the splitting value. The best feature has the highest absolute correlation with dataY. 
        If all features have the same absolute correlation, choose the first feature. 
        The splitting value is the median of the data according to the best feature

        Parameters:
        dataX: A numpy ndarray of X values at each node
        dataY: A numpy 1D array of Y training values at each node
        
        Returns:
        tree: A numpy ndarray. Each row represents a node and four columns are feature indices 
        (int type; index for a leaf is -1), splitting values, and starting rows, from the current 
        root, for its left and right subtrees (if any)

        """
        # Get the number of samples (rows) and features (columns) of dataX
        num_samples = dataX.shape[0]
        num_feats = dataX.shape[1]

        # If there are <= leaf_size samples or all data in dataY are the same, return leaf
        if num_samples <= self.leaf_size or len(pd.unique(dataY)) == 1:
            return np.array([-1, dataY.mean(), np.nan, np.nan])
        else:
            # Initialize best feature index and best feature correlation
            best_feat_i = 0
            best_abs_corr = 0.0

            # Determine best feature to split on, using correlation between features and dataY
            for feat_i in range(num_feats):
                abs_corr = abs(pearsonr(dataX[:, feat_i], dataY)[0])
                if abs_corr > best_abs_corr:
                    best_abs_corr = abs_corr
                    best_feat_i = feat_i
            
            # Split the data according to the best feature
            split_val = np.median(dataX[:, best_feat_i])

            # Logical arrays for indexing
            left_index = dataX[:, best_feat_i] <= split_val
            right_index = dataX[:, best_feat_i] > split_val

            # Build left and right branches and the root
            lefttree = self.__build_tree(dataX[left_index], dataY[left_index])
            righttree = self.__build_tree(dataX[right_index], dataY[right_index])

            # Set the starting row for the right subtree of the current root
            if lefttree.ndim == 1:
                righttree_start = 2 # The right subtree starts 2 rows down
            elif lefttree.ndim > 1:
                righttree_start = lefttree.shape[0] + 1
            root = np.array([best_feat_i, split_val, 1, righttree_start])

            return np.vstack((root, lefttree, righttree))
        

    def __tree_search(self, point, row):
        """A private function to be used with query. It recursively searches 
        the decision tree matrix and returns a predicted value for point

        Parameters:
        point: A numpy 1D array of test query
        row: The row of the decision tree matrix to search
    
        Returns 
        pred: The predicted value
        """

        # Get the feature on the row and its corresponding splitting value
        feat, split_val = self.tree[row, 0:2]
        
        # If splitting value of feature is -1, we have reached a leaf so return it
        if feat == -1:
            return split_val

        # If the corresponding feature's value from point <= split_val, go to the left tree
        elif point[int(feat)] <= split_val:
            pred = self.__tree_search(point, row + int(self.tree[row, 2]))

        # Otherwise, go to the right tree
        else:
            pred = self.__tree_search(point, row + int(self.tree[row, 3]))
        
        return pred


    def addEvidence(self, dataX, dataY):
        """Add training data to learner

        Parameters:
        dataX: A numpy ndarray of X values of data to add
        dataY: A numpy 1D array of Y training values

        Returns: An updated tree matrix for DTLearner
        """

        new_tree = self.__build_tree(dataX, dataY)

        # If self.tree is currently None, simply assign new_tree to it
        if self.tree is None:
            self.tree = new_tree

        # Otherwise, append new_tree to self.tree
        else:
            self.tree = np.vstack((self.tree, new_tree))
        
        if self.verbose:
            self.get_learner_info()
        
        
    def query(self, points):
        """Estimates a set of test points given the model we built
        
        Parameters:
        points: A numpy ndarray of test queries

        Returns: 
        preds: A numpy 1D array of the estimated values
        """

        preds = []
        for point in points:
            preds.append(self.__tree_search(point, row=0))
        return np.asarray(preds)


    def get_learner_info(self):
        print ("Info about this Decision Tree Learner:")
        print ("leaf_size =", self.leaf_size)
        if self.tree is not None:
            print ("tree shape =", self.tree.shape)
            print ("tree as a matrix: \n", self.tree)
            # Create a dataframe from tree for a user-friendly view
            df_tree = pd.DataFrame(self.tree, columns=["factor", "split_val", "left", "right"])
            df_tree.index.name = "node"
            print (df_tree)
        else:
            print ("Tree has no data")


if __name__=="__main__":
    print ("This is a Decision Tree Learner")

    # Some data to test the DTLearner
    x0 = np.array([0.885, 0.725, 0.560, 0.735, 0.610, 0.260, 0.500, 0.320])
    x1 = np.array([0.330, 0.390, 0.500, 0.570, 0.630, 0.630, 0.680, 0.780])
    x2 = np.array([9.100, 10.900, 9.400, 9.800, 8.400, 11.800, 10.500, 10.000])
    x = np.array([x0, x1, x2]).T
    
    y = np.array([4.000, 5.000, 6.000, 5.000, 3.000, 8.000, 7.000, 6.000])

    # Create a tree learner from given train X and y
    dtl = DTLearner(verbose=True)
    dtl.addEvidence(x, y)

    # Create a tree learner from an existing tree
    dtl2 = DTLearner(tree=dtl.tree)

    # dtl2 should have the same tree as dtl
    assert np.any(dtl.tree == dtl2.tree)

    dtl2.get_learner_info()

    # Modify the dtl2.tree and assert that this doesn't affect dtl.tree
    dtl2.tree[0] = np.arange(dtl2.tree.shape[1])
    assert np.any(dtl.tree != dtl2.tree)

    # Querry data with dummy data
    dtl.query(np.array([[1, 2, 3], [0.2, 12, 12]]))