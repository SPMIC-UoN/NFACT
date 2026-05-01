import numpy as np
import pandas as pd
import os
import nibabel as nb
from glob import glob
from NFACT.base.imagehandling import imaging_type


def threshold_by_zscore(data, z_score=2):
    """
    Calculates the raw value for a specific z-score and
    returns the data filtered above that value.
    """
    mu = np.mean(data)
    sigma = np.std(data)
    threshold_value = mu + (z_score * sigma)
    return threshold_value


def dice_score(array1: np.ndarray, array2: np.ndarray) -> float:
    """
    Calculate the DICE similarity coefficient between two binary arrays.

    The DICE score measures the overlap between two arrays and is defined as:
        DICE = (2 * |A ∩ B|) / (|A| + |B|)

    A score of 1.0 indicates perfect overlap, 0.0 indicates no overlap.

    Parameters
    ----------
    array1 : np.ndarray
        First input array. Non-zero values are treated as 1 (binarised internally).
    array2 : np.ndarray
        Second input array. Must have the same shape as array1. Non-zero values
        are treated as 1 (binarised internally).

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
    array1 = (np.asarray(array1) != 0).astype(int)
    array2 = (np.asarray(array2) != 0).astype(int)

    if array1.shape != array2.shape:
        raise ValueError(
            f"Input arrays must have the same shape, "
            f"got {array1.shape} and {array2.shape}."
        )

    intersection = np.logical_and(array1, array2).sum()
    total = array1.sum() + array2.sum()

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


def get_group_images(directory: str) -> list:
    """
    Glob a directory and return all image files whose
    filename begins with the ``G_`` prefix.

    Searches for the three standard neuroimaging extensions:
    NIfTI (``.nii.gz``, ``.nii``), GIFTI (``.func.gii``, ``.gii``),
    and CIFTI (``.dscalar.nii``, ``.dtseries.nii``).

    Parameters
    ----------
    directory : str
        Path to the directory to search.

    Returns
    -------
    list
        Sorted list of absolute file paths matching the ``G_*`` prefix.
        Returns an empty list if no files are found.
    """

    patterns = [
        "G_*.nii.gz",
        "G_*.nii",
        "G_*.gii",
        "G_*.dscalar.nii",
    ]
    found = set()
    for pattern in patterns:
        found.update(glob(os.path.join(directory, pattern)))
    return sorted(found)


def get_image_type(file_path: str) -> str:
    """
    Determine whether an image file is a CIFTI, GIFTI, or NIfTI.

    Delegates to the project-wide ``imaging_type`` utility in
    ``NFACT.base.imagehandling``, which inspects the file suffix(es)
    and returns one of ``'cifti'``, ``'gifti'``, or ``'nifti'``.

    Parameters
    ----------
    file_path : str
        Absolute or relative path to the imaging file.

    Returns
    -------
    str
        One of ``'cifti'``, ``'gifti'``, or ``'nifti'``.
    """
    return imaging_type(file_path)


def load_group_images(image_files: list) -> np.ndarray:
    """
    Load a list of G_ image files and return a single 2D array
    of shape ``(n_spatial, n_components)``.

    Each file is loaded according to its imaging type:

    * **NIfTI** – ``nibabel.load().get_fdata()``

      * 4-D ``(x, y, z, n)`` → reshaped to ``(x*y*z, n)``
      * 3-D ``(x, y, z)``     → reshaped to ``(x*y*z, 1)``

    * **GIFTI** – ``darrays`` stacked column-wise

      * Each ``darray.data`` has shape ``(n_vertices,)``
      * Result: ``(n_vertices, n_darrays)``

    * **CIFTI** – ``get_fdata()`` transposed

      * Raw shape ``(n_maps, n_greyordinates)`` → ``(n_greyordinates, n_maps)``

    All per-file arrays are vertically stacked so the final array has
    shape ``(total_spatial_elements, n_components)``.

    Parameters
    ----------
    image_files : list
        List of file paths as returned by ``get_group_images``.

    Returns
    -------
    np.ndarray
        2-D array of shape ``(n_spatial, n_components)``.
    """

    arrays = []
    for file_path in image_files:
        img_type = get_image_type(file_path)

        if img_type == "nifti":
            data = nb.load(file_path).get_fdata()
            if data.ndim == 4:
                data = data.reshape(-1, data.shape[-1])
            else:
                data = data.reshape(-1, 1)

        elif img_type == "gifti":
            img = nb.load(file_path)
            data = np.column_stack([d.data for d in img.darrays])

        elif img_type == "cifti":
            img = nb.load(file_path)
            data = img.get_fdata(dtype=np.float32).T
        arrays.append(data)
    return np.vstack(arrays)


def get_atlas_value(labels: pd.DataFrame, label_name: str) -> list:
    """
    Function to index for a network given a set name

    Parameters
    -----------
    labels: pd.DataFrame
        dataframe with two
        columns named
        Network Name and
        Network Order
    label_name: str
        network name

    Returns
    --------
    list: list
       list of indices
    """
    return labels[labels["Network Name"].str.contains(label_name)][
        "Network Order"
    ].values.tolist()


def get_atlas_indices(label_name: str, labels: pd.DataFrame, atlas: np.ndarray) -> dict:
    """
    Function to get indices of a network indices

    Parameters
    ----------
    label_name: str
        string of label name
    labels: pd.DataFrame
        dataframe of label name
        with two columns Network Name
        and Network Order
    left_atlas: np.ndarray
        array of values representing
        networks
    right_atlas: np.ndarray
        array of values representing
        networks

    Returns
    -------
    dict: dictionary
        dictionary of indices
        associated with a network
        divided into left and right
    """
    label_val = get_atlas_value(labels, label_name)
    return np.where(np.isin(atlas, label_val))


def define_components(
    data: np.ndarray,
    atlas_labels: pd.DataFrame,
    atlas: np.ndarray,
    threshold_value: int,
) -> dict:
    """
    Function to define components by getting the median value of
    the nmf by network

    Parameters
    ----------
    networks: list
        list of networks
    g_nmf_data: dict
        dictionary of grey matter data
    component_range: int
        number of components
    label_name: str
        string of label name
    labels: pd.DataFrame
        dataframe of label name
        with two columns Network Name
        and Network Order
    atlas: np.ndarray
        array of values representing
        networks
    threshold_value: int
        theshold value

    Returns
    -------
    dict: dictionary
        dict of component and median
        value of network
    """
    component_range = data.shape[1]
    comp_dict = dict(
        zip(
            [comp for comp in range(component_range)],
            [{} for _ in range(component_range)],
        )
    )
    for comp in range(component_range):
        component_data = data[:, comp]
        for label in atlas_labels:
            index = get_atlas_indices(atlas_labels, label, atlas)
            atlas_mask = np.zeros_like(component_data, dtype=int)
            atlas_mask[index] = 1
            normalised_comp = normalization(component_data)
            soft_dice = soft_dice_score(normalised_comp, atlas_mask)
            thresholded_comp = np.where(
                component_data > threshold_by_zscore(data, threshold_value), 1, 0
            )
            hard_dice = dice_score(thresholded_comp, atlas_mask)
            comp_dict[comp][label] = {"soft_dice": soft_dice, "hard_dice": hard_dice}
    return comp_dict


def interpret_main(args: dict):
    labels = pd.read_csv(args["labels"])
    group_img = get_group_images(
        os.path.join(args["decomp_folder"], "components", "NMF", "decomp", "")
    )
    group_data = load_group_images(group_img)

    define_components()
