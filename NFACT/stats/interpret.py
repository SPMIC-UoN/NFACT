import numpy as np


def dice_score(array1: np.ndarray, array2: np.ndarray) -> float:
    """
    Calculate the DICE similarity coefficient between two binary arrays.

    The DICE score measures the overlap between two arrays and is defined as:
        DICE = (2 * |A ∩ B|) / (|A| + |B|)

    A score of 1.0 indicates perfect overlap, 0.0 indicates no overlap.

    Parameters
    ----------
    array1 : np.ndarray
        First input array. Will be binarised (non-zero elements treated as True).
    array2 : np.ndarray
        Second input array. Must have the same shape as array1. Will be binarised.

    Returns
    -------
    float
        DICE similarity score in the range [0.0, 1.0].

    Raises
    ------
    ValueError
        If array1 and array2 do not have the same shape.

    Examples
    --------
    >>> import numpy as np
    >>> a = np.array([1, 1, 0, 0, 1])
    >>> b = np.array([1, 0, 0, 1, 1])
    >>> dice_score(a, b)
    0.6666666666666666
    """
    array1 = np.asarray(array1)
    array2 = np.asarray(array2)

    if array1.shape != array2.shape:
        raise ValueError(
            f"Input arrays must have the same shape, "
            f"got {array1.shape} and {array2.shape}."
        )

    binary1 = array1 != 0
    binary2 = array2 != 0

    intersection = np.logical_and(binary1, binary2).sum()
    total = binary1.sum() + binary2.sum()

    if total == 0:
        return 1.0

    return float(2 * intersection / total)


def normalization(array: np.ndarray) -> np.ndarray:
    """
    Apply min-max normalization to an array, scaling values to the range [0, 1].

    The transformation is defined as:
        x_norm = (x - x_min) / (x_max - x_min)

    Parameters
    ----------
    array : np.ndarray
        Input array to normalise.

    Returns
    -------
    np.ndarray
        Normalised array with values in [0.0, 1.0], same shape as input.
        If all values in the array are identical (zero range), returns an
        array of zeros.

    Examples
    --------
    >>> import numpy as np
    >>> a = np.array([2.0, 4.0, 6.0, 8.0])
    >>> normalization(a)
    array([0.        , 0.33333333, 0.66666667, 1.        ])
    """
    array = np.asarray(array, dtype=float)
    x_min = array.min()
    x_max = array.max()
    value_range = x_max - x_min

    if value_range == 0:
        return np.zeros_like(array)

    return (array - x_min) / value_range


def soft_dice_score(array1: np.ndarray, array2: np.ndarray) -> float:
    """
    Calculate the soft DICE similarity coefficient between two continuous arrays.

    Unlike the hard DICE score, this variant does not binarise the inputs and
    instead works directly with continuous (e.g. probabilistic) values:

        Soft DICE = (2 * Σ(A * B)) / (Σ(A) + Σ(B))

    This makes it suitable for comparing probability maps, Z-score images, or
    any non-binary spatial overlap measure.  A score of 1.0 indicates perfect
    overlap and 0.0 indicates no overlap.

    Parameters
    ----------
    array1 : np.ndarray
        First input array of continuous values (e.g. probabilities or weights).
    array2 : np.ndarray
        Second input array. Must have the same shape as array1.

    Returns
    -------
    float
        Soft DICE score in the range [0.0, 1.0].

    Raises
    ------
    ValueError
        If array1 and array2 do not have the same shape.

    Examples
    --------
    >>> import numpy as np
    >>> a = np.array([0.9, 0.8, 0.1, 0.0])
    >>> b = np.array([0.8, 0.7, 0.2, 0.1])
    >>> soft_dice_score(a, b)
    0.9354838709677419
    """
    array1 = np.asarray(array1, dtype=float)
    array2 = np.asarray(array2, dtype=float)

    if array1.shape != array2.shape:
        raise ValueError(
            f"Input arrays must have the same shape, "
            f"got {array1.shape} and {array2.shape}."
        )

    numerator = 2.0 * np.sum(array1 * array2)
    denominator = np.sum(array1) + np.sum(array2)

    if denominator == 0:
        return 1.0

    return float(numerator / denominator)
