import numpy as np
from NFACT.base.matrix_handling import load_initialisation
from NFACT.base.utils import colours, error_and_exit
from NFACT.decomp.decomposition.sso.nmfsso import sso_run
from sklearn.decomposition import NMF
from sklearn.utils._testing import ignore_warnings
from sklearn.exceptions import ConvergenceWarning

import os
import time
import subprocess
import sys
import warnings
import torch
from torchnmf.nmf import NMF

# Suppress the harmless cuBLAS warning caused by the on-the-fly CUDA initialization
warnings.filterwarnings("ignore", message=".*Attempting to run cuBLAS.*")


def find_free_gpu_uuid():
    """Finds a MIG partition or GPU that has no running processes."""
    print("Searching for a free GPU partition...")
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

    print(
        "Error: No free GPUs available! Please kill zombie processes.", file=sys.stderr
    )
    sys.exit(1)


# Auto-assign a free GPU before importing PyTorch!
if "CUDA_VISIBLE_DEVICES" not in os.environ:
    free_gpu = find_free_gpu_uuid()
    if free_gpu:
        os.environ["CUDA_VISIBLE_DEVICES"] = free_gpu


def main():
    # Detect device before loading any numpy libraries to prevent OpenMP/CUDA initialization conflicts
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(device)
    if device == "cpu":
        sys.exit(1)
    args = parse_args()

    # Create output directory if it doesn't exist
    os.makedirs(args.output, exist_ok=True)

    print(f"Loading matrix from {args.matrix}...")
    try:
        # Load matrix as a numpy array
        matrix_np = np.load(args.matrix)

        # Handle cases where the loaded data is an object array or structured
        if matrix_np.dtype == object:
            raise ValueError(
                "Loaded numpy array has dtype object, please ensure it contains numeric data."
            )

    except Exception as e:
        print(f"Error loading matrix: {e}")
        print("Please provide a valid numpy .npy file.")
        return

    # Enable 16-bit precision by default to halve GPU memory usage
    print("Enabling 16-bit precision (FP16)...")
    torch.set_default_dtype(torch.float16)
    tensor_dtype = torch.float16

    # Convert numpy array to torch tensor, avoid copying in memory first
    print("Preparing data...")
    V = torch.from_numpy(matrix_np).to(tensor_dtype)

    # Ensure all values are non-negative
    if torch.any(V < 0):
        print("Warning: Input matrix contains negative values. Clipping to 0 for NMF.")
        V = torch.clamp(V, min=0.0)

    print(f"Moving data to {device}...")
    V = V.to(device)

    print(f"Initializing torchnmf NMF model with rank={args.components}...")

    # torchnmf's NMF class overrides W and H if Vshape is provided, so we manually build kwargs
    nmf_kwargs = {"rank": args.components}

    if args.init_w:
        print(f"Loading initial W matrix from {args.init_w}...")
        w_np = np.load(args.init_w)
        nmf_kwargs["W"] = torch.tensor(w_np, dtype=tensor_dtype, device=device)
    else:
        nmf_kwargs["W"] = (V.shape[1], args.components)

    if args.init_h:
        print(f"Loading initial H matrix from {args.init_h}...")
        h_np = np.load(args.init_h)
        nmf_kwargs["H"] = torch.tensor(h_np, dtype=tensor_dtype, device=device)
    else:
        nmf_kwargs["H"] = (V.shape[0], args.components)

    # Initialize the torchnmf NMF model
    model = NMF(**nmf_kwargs).to(device)

    print("Fitting NMF model...")
    start_time = time.time()

    # Fit the model
    # Note: torchnmf's fit() uses max_iter to control iterations
    # Using beta=2 for Frobenius norm, alpha=0.1, and l1_ratio=1.0
    model.fit(V, max_iter=args.max_iter, tol=0.0001, beta=2, alpha=0.1, l1_ratio=1.0)

    print(f"Completed in {time.time() - start_time:.2f} seconds.")

    # Retrieve learned matrices W and H and move them to CPU -> numpy
    W_np = model.W.detach().cpu().numpy()
    H_np = model.H.detach().cpu().numpy()

    w_out_path = os.path.join(args.output, "W.npy")
    h_out_path = os.path.join(args.output, "H.npy")

    print(f"Saving W matrix to {w_out_path}")
    np.save(w_out_path, W_np)

    print(f"Saving H matrix to {h_out_path}")
    np.save(h_out_path, H_np)

    print("Done!")


if __name__ == "__main__":
    main()


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
            return nmf_decomp(
                parameters,
                fdt_matrix,
                W_mat=np.ascontiguousarray(intialisation_mat["gm_mat"]),
                H_mat=np.ascontiguousarray(intialisation_mat["wm_mat"]),
            )
    if args["no_sso"]:
        print(nmf_string + "Single Run")
        return nmf_decomp(parameters, fdt_matrix)

    print(nmf_string + "SSO")
    return sso_run(fdt_matrix, parameters, args, col)
