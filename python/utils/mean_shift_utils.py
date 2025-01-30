import numpy as np
@staticmethod
def lin_norm(X: np.ndarray):
        """Linear normalization of X

        Args:
            X (np.ndarray[<float>]): np.ndarray of values to normalize.

        Returns:
            (np.ndarray[<float>]): A normalized np.ndarray of the values contained in the input np.ndarray.
        """
        MAX = max(X)
        MIN = min(X)
        
        return ((X - MIN) / (MAX - MIN))