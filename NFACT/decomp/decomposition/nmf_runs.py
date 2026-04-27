import numpy as np
from NFACT.base.matrix_handling import load_initialisation
from NFACT.base.utils import colours, error_and_exit
from NFACT.decomp.decomposition.sso.nmfsso import sso_run
from sklearn.decomposition import NMF
from sklearn.utils._testing import ignore_warnings
from sklearn.exceptions import ConvergenceWarning

import os
import subprocess
import sys
import warnings
import torch
from torchnmf.nmf import NMF as GPU_NMF

warnings.filterwarnings("ignore", message=".*Attempting to run cuBLAS.*")


def find_free_gpu_uuid() -> str:
    """
    Function to find a free GPU partition.

    Parameters
    -----------
    None

    Returns
    -------
    str: uuid of free GPU partition
    """
    try:
        smi_out = subprocess.check_output(["nvidia-smi", "-L"]).decode("utf-8")
        all_uuids = [
            line.split("UUID: ")[1].strip().strip(")")
            for line in smi_out.split("\n")
            if "UUID: " in line
        ]
    except Exception as e:
        print(f"Warning: Failed to run nvidia-smi: {e}")
        return None

    for uuid in all_uuids:
        try:
            env = os.environ.copy()
            env["CUDA_VISIBLE_DEVICES"] = uuid
            subprocess.check_call(
                [
                    sys.executable,
                    "-c",
                    "import torch; assert torch.cuda.is_available()",
                ],
                env=env,
                stderr=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
            )
            return uuid
        except Exception:
            return False


def nmf_gpu_run(
    parameters: dict,
    fdt_matrix: np.ndarray,
    W_mat: np.ndarray = None,
    H_mat: np.ndarray = None,
) -> dict:
    """
    Function to run nmf on GPU.

    Parameters
    ----------
    parameters: dict
        dictionary of hyperparameters
    fdt_matrix: np.ndarray
        fdt_matrix to decompose
    W_mat: np.ndarray
        initialisation matrix for W
    H_mat: np.ndarray
        initialisation matrix for H

    Returns
    -------
    dict: dictionary
        dictionary of grey and white matter
        components
    """
    device = torch.device("cuda")
    torch.set_default_dtype(torch.float16)
    tensor_dtype = torch.float16
    fdt_tensor = torch.from_numpy(fdt_matrix).to(tensor_dtype)
    fdt_tensor = fdt_tensor.to(device)
    nmf_kwargs = {
        "rank": parameters["components"],
        "W": (fdt_matrix.shape[1], parameters["components"]),
        "H": (fdt_matrix.shape[0], parameters["components"]),
    }

    if W_mat is not None and H_mat is not None:
        nmf_kwargs["W"] = torch.tensor(W_mat, dtype=tensor_dtype, device=device)
        nmf_kwargs["H"] = torch.tensor(H_mat, dtype=tensor_dtype, device=device)

    model = GPU_NMF(**nmf_kwargs).to(device)
    model.fit(
        fdt_tensor, beta=2, alpha=parameters["alpha"], l1_ratio=parameters["l1_ratio"]
    )
    return {
        "grey_components": model.W.detach().cpu().numpy(),
        "white_components": model.H.detach().cpu().numpy(),
    }


@ignore_warnings(category=ConvergenceWarning)
def nmf_decomp(
    parameters: dict,
    fdt_matrix: np.ndarray,
    W_mat: np.ndarray = None,
    H_mat: np.ndarray = None,
) -> dict:
    """
    Function to perform NMF.

    Parameters
    ----------
    parameters: dict
        dictionary of hyperparameters
    fdt_matrix: np.ndarray
        matrix to perform decomposition
        on
    W_mat: ndarray
        previous W matrix to initiate
        an NMF run on
    H_mat: ndarray
        previous H matrix to initiate
        an NMF run on

    Returns
    -------
    dict: dictionary
        dictionary of grey and white matter
        components
    """
    if W_mat is not None and H_mat is not None:
        parameters = parameters.copy()
        parameters["init"] = "custom"

    decomp = NMF(**parameters)
    try:
        grey_matter = decomp.fit_transform(fdt_matrix, W=W_mat, H=H_mat)
    except Exception as e:
        error_and_exit(False, f"Unable to perform NMF due to {e}")
    return {"grey_components": grey_matter, "white_components": decomp.components_}


def which_nmf(gpu: bool) -> object:
    """
    Function to return the correct nmf function based on gpu

    Parameters
    ----------
    gpu: bool
        whether to use gpu

    Returns
    -------
    object: nmf function
        which nmf function to use
    """
    return nmf_gpu_run if gpu else nmf_decomp


def nmf_run(fdt_matrix: np.ndarray, parameters: dict, args: dict) -> dict:
    """
    Function to run nmf, either sso run
    or singular run.

    Parameters
    ----------
    fdt_matrix: np.ndarray
        fdt_matrix to decompose
    parameters: dict
        NMF parameters
    args: dict
        cmd arguments

    Returns
    -------
    dict: dictionary
        dictionary of grey and white matter
        components
    """
    col = colours()
    nmf = which_nmf(args["gpu"])
    nmf_string = f"{col['pink']}NMF Mode:{col['reset']} "
    if args["no_sso"] and (args["gm_matrix"] or args["wm_matrix"]):
        error_and_exit(
            False,
            "Unlcear which type of run to perform. Either use --no-sso or give initialisation matricies not both",
        )
    if args["wm_matrix"] or args["gm_matrix"]:
        intialisation_mat = load_initialisation(args["gm_matrix"], args["wm_matrix"])

        if intialisation_mat:
            print(nmf_string + "Initialisation Run")
            parameters["n_components"] = intialisation_mat["wm_mat"].shape[0]
            return nmf(
                parameters,
                fdt_matrix,
                W_mat=np.ascontiguousarray(intialisation_mat["gm_mat"]),
                H_mat=np.ascontiguousarray(intialisation_mat["wm_mat"]),
            )
    if args["no_sso"]:
        print(nmf_string + "Single Run")
        return nmf(parameters, fdt_matrix)

    print(nmf_string + "SSO")
    return sso_run(fdt_matrix, parameters, args, col)
