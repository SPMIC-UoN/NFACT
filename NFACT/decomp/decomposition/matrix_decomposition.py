from NFACT.decomp.decomposition.matrix_handling import (
    melodic_incremental_group_pca,
)
from NFACT.base.utils import error_and_exit, nprint, Timer
from NFACT.base.matrix_handling import normalise_components
from NFACT.config.nfact_config_functions import create_combined_algo_dict
from NFACT.decomp.decomposition.sso.nmfsso import nmf_run
from sklearn.decomposition import FastICA, PCA
import numpy as np
from sklearn.utils._testing import ignore_warnings
from sklearn.exceptions import ConvergenceWarning
import warnings

warnings.filterwarnings("ignore")


@ignore_warnings(category=ConvergenceWarning)
def ica_decomp(
    parameters: dict, pca_matrix: np.ndarray, fdt_matrix: np.ndarray
) -> dict:
    """
    Function to perform ica decomposition

    Parameters
    ----------
    parameters: dict
        dictionary of hyperparameters
    pca_matrix: np.ndarray
        matrix that has been reduced.
    fdt_matrix: np.ndarray
        matrix to perform decomposition
        on

    Returns
    -------
    dict: dictionary
        dictionary of grey and white matter
        components
    """

    decomp = FastICA(**parameters)

    try:
        grey_matter = decomp.fit_transform(pca_matrix)
    except Exception as e:
        error_and_exit(False, f"Unable to perform ICA due to {e}")
    return {
        "grey_components": grey_matter,
        "white_components": np.linalg.pinv(grey_matter) @ fdt_matrix,
    }


def pca_reduction(n_components: int, fdt_matrix: np.ndarray) -> np.ndarray:
    """
    Function to conduct PCA for ICA using
    sckit learns implementation.

    Parameters
    ----------
    n_components: int
        number of components to retain
    fdt_matrix: np.array
        connectivity matrix
    """
    timer = Timer()
    timer.tic()
    pca_matrix = PCA(n_components).fit_transform(fdt_matrix)
    nprint(f"Old matrix size {fdt_matrix.shape[0]}x{fdt_matrix.shape[1]}")
    nprint(f"New matrix size now {pca_matrix.shape[0]}x{pca_matrix.shape[1]}")
    nprint(f"PCA finished in {timer.how_long()}\n")
    return pca_matrix


def get_parameters(parameters: dict, algo: str, n_components: int) -> dict:
    """
    Function to get parameters for
    decomp. If no parameters are
    given then for ICA will use sckit learn defaults
    for NFM it will use defaults aside from
    alpha_w, random_state, l1_ratio and init.

    Parameters
    ----------
    parameters: dict
       dictionary of parameters
    algo: str
       str of algo to use
    n_components: int
        number of components

    Returns
    -------
    parameters: dict
        dictionary of parameters
    """
    if parameters:
        parameters["n_components"] = n_components
        return parameters

    parameters = create_combined_algo_dict()[algo]
    parameters["n_components"] = n_components
    if algo == "nmf":
        parameters["alpha_W"] = 0.1
        parameters["init"] = "nndsvd"
        parameters["random_state"] = None
        parameters["l1_ratio"] = 1
    return parameters


def ica_decomposition(
    fdt_matrix: np.ndarray,
    pca_dim: int,
    pca_type: str,
    signflip: bool,
    parameters: dict,
) -> dict:
    """
    Function to do PCA/ICA decomposition

    Parameters
    ----------
    fdt_matrix: np.ndarray
        fdt_matrix to decomp
    pca_dim: int
        number of pca dimensions
    pca_type: str
        which type of PCA to do sckitlearn
        or MIGP
    signflip: bool,
        slipfip so heavy tail > 0
    parameters: dict
        ICA parameters in dict form

    Returns
    --------
    components: dict
        dictionary of components
    """
    if pca_type == "pca":
        nprint("Doing PCA reduction")
        pca_matrix = pca_reduction(pca_dim, fdt_matrix)
    else:
        pca_matrix = melodic_incremental_group_pca(fdt_matrix, pca_dim, pca_dim)

    components = ica_decomp(parameters, pca_matrix, fdt_matrix)
    if signflip:
        nprint("Sign-flipping components")
        components["grey_components"] = sign_flip(components["grey_components"].T).T
        components["white_components"] = sign_flip(components["white_components"])
    return components


def sign_flip(decomp_matrix: np.ndarray, thr: int = 0) -> np.ndarray:
    """
    Function to sign flip the rows of
    the decomp matrix so that the heavy tail
    is > 0.

    Parameters
    ----------
    decomp_matrix: np.array
        decomposition matrix

    thr: int=0
        threshold value

    Returns
    -------
    signflip_decomp_matrix: np.array
        array of signfliped matrix
    """

    signflip_decomp_matrix = np.empty_like(decomp_matrix)
    for index in range(decomp_matrix.shape[0]):
        row = decomp_matrix[index]
        rowthr = row[np.abs(row) > thr]

        if rowthr.size == 0 or np.min(np.abs(rowthr)) == 0:
            signflip_decomp_matrix[index] = row
            continue

        positive_elements = row[row > thr]
        negative_elements = row[row < -thr]

        positive_mean = np.mean(positive_elements) if positive_elements.size > 0 else 0
        negative_mean = -np.mean(negative_elements) if negative_elements.size > 0 else 0

        skew = np.sign(positive_mean - negative_mean)
        signflip_decomp_matrix[index] = row if skew == 0 else row * skew

    return signflip_decomp_matrix


def matrix_decomposition(
    fdt_matrix: np.ndarray,
    parameters: dict,
    args: dict,
) -> dict:
    """
    Wrapper function to decompose a matrix2 into
    grey * white matter components.

    Performs either ICA or NMF depending on input.
    Will normalise components.

    Parameters
    ----------
    fdt_matrix: np.ndarray
        matrix to decompose
    parameters: dict
        dictionary of decomp
        parameters
    args: dict
        cmd args

    Returns
    -------
    dict: dictionary
        dict of components
    """

    if args["algo"] == "ica":
        components = ica_decomposition(
            fdt_matrix,
            args["components"],
            args["pca_type"],
            args["sign_flip"],
            parameters,
        )

    if args["algo"] == "nmf":
        components = nmf_run(fdt_matrix, parameters, args)

    if args["normalise"]:
        normalised = normalise_components(
            components["grey_components"], components["white_components"]
        )
        components["normalised_white"] = normalised["white_matter"]
        components["normalised_grey"] = normalised["grey_matter"]

    return components
