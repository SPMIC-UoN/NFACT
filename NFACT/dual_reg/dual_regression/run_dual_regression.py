from NFACT.dual_reg.nfact_dr_functions import get_group_level_components
from NFACT.base.matrix_handling import load_fdt_matrix
from NFACT.dual_reg.dual_regression.dual_regression_methods import (
    nmf_dual_regression,
    ica_dual_regression,
    run_decomp,
)
from NFACT.dual_reg.nfact_dr_functions import save_dual_regression_images
from NFACT.base.utils import colours, error_and_exit, nprint, Timer
from NFACT.base.matrix_handling import thresholding_components, normalise_components
import argparse
import os
from NFACT.base.gpu import find_free_gpu_uuid
import numpy as np


def cluster_mode_args() -> dict:
    """
    Function to pass cmd
    arguements to the dual_regression_pipeline
    pipeline if ran directly.

    Parameters
    ----------
    None

    Returns
    -------
    dict: dictionary
        dict of cmd options
    """
    parser = argparse.ArgumentParser(description="Run Dual Regression")
    parser.add_argument(
        "--fdt_path", required=True, help="Directory to individual subject fdt path"
    )
    parser.add_argument(
        "--output_dir", required=True, help="Directory to save the output components."
    )
    parser.add_argument(
        "--component_path", required=True, help="Directory to components path."
    )
    parser.add_argument(
        "--group_average_path", required=True, help="Path to group averages."
    )
    parser.add_argument("--algo", required=True, help="Which algo has been run")
    parser.add_argument("--seeds", required=True, nargs="+", help="Path to seed(s).")
    parser.add_argument("--id", required=True, help="Subject ID.")
    parser.add_argument("--roi", nargs="+", default=False, help="Path to roi(s).")
    parser.add_argument(
        "--parallel", default=1, type=int, help="Number of cores to parallel with"
    )
    parser.add_argument(
        "--dscalar", default=False, action="store_true", help="Save as dscalar"
    )
    parser.add_argument(
        "--threshold", default=3, type=int, help="threshold the components"
    )
    parser.add_argument(
        "--normalise",
        default=False,
        action="store_true",
        help="Save a normalised version of the components",
    )
    parser.add_argument(
        "--gpu",
        default=False,
        action="store_true",
        help="Use GPU-accelerated NNLS (NMF only). Requires PyTorch + CUDA.",
    )
    return vars(parser.parse_args())


def dual_regression_pipeline(
    fdt_path: str,
    output_dir: str,
    component_path: str,
    group_average_path: str,
    algo: str,
    seeds: str,
    sub_id: str,
    roi: str,
    parallel: int = 1,
    components: np.ndarray = False,
    dscalar: bool = False,
    threshold: int = 3,
    normalise: bool = False,
    use_gpu: bool = False,
) -> None:
    """
    The dual regression pipeline function.
    This function either runs the pipeline
    locally or can be submitted directly
    to the cluster

    Parameters
    ----------
    fdt_path: str
        path to fdt matrix
    output_dir: str
        output directory
    component_path: str,
        path to group components
    group_average_path: str
        path to group averages
    algo: str
        which algo was used in
        the decomposition
    seeds: str
        seeds used in the decomposition
    sub_id: str
        subject id
    roi: str
        roi to restict seeding to
    parallel: int = 1
        how many to parallel
        process to.
    components: np.ndarray
        group components.
        Can be False (default)
        and pipeline will get group
        components
    dscalar: bool
        save gm as dscalar.
        Default is False
    threshold: int = 3
        value to threshold components
        at.
    normalise: bool = False
        save a normalised version
        of the components
    use_gpu: bool = False
        use GPU-accelerated NNLS (NMF only).
        Requires PyTorch + CUDA.

    Returns
    -------
    None
    """
    col = colours()
    if use_gpu: 
        try:
            os.environ["CUDA_VISIBLE_DEVICES"] = find_free_gpu_uuid()
        except Exception as e:
            nprint(f"{col['red']}Cannot find GPU ({e}){col['reset']}: Using CPU", to_flush=True)
            use_gpu = False
    nprint("-" * 100)
    if not components:
        nprint(
            f"{col['pink']}Obtaining{col['reset']}: Group Level Components",
            to_flush=True,
        )

        try:
            components = get_group_level_components(
                component_path,
                group_average_path,
                seeds,
                roi,
            )
        except Exception as e:
            error_and_exit(False, f"Unable to find components due to {e}")
    t_timer = Timer()
    t_timer.tic()
    nprint(f"{col['pink']}Subject ID{col['reset']}: {sub_id}", to_flush=True)
    nprint(f"{col['pink']}Obtaining{col['reset']}: FDT Matrix")

    try:
        matrix_file = next(
            (
                os.path.join(fdt_path, fname)
                for fname in ("fdt_matrix2.dot.lz4", "fdt_matrix2.dot")
                if os.path.exists(os.path.join(fdt_path, fname))
            ),
            None,
        )
        matrix = load_fdt_matrix(matrix_file)
    except Exception:
        error_and_exit(False, f"Unable to load {sub_id} fdt matrix")

    method = nmf_dual_regression if algo.lower() == "nmf" else ica_dual_regression
    try:
        dr_results = run_decomp(method, components, matrix, parallel, use_gpu=use_gpu)
    except Exception as e:
        error_and_exit(False, f"Dual regression failed due to {e}")

    dr_results = thresholding_components(
        int(threshold),
        os.path.join(fdt_path, "coords_for_fdt_matrix2"),
        seeds,
        dr_results,
    )
    if normalise:
        normalised = normalise_components(
            dr_results["grey_components"], dr_results["white_components"]
        )
        dr_results["normalised_white"] = normalised["white_matter"]
        dr_results["normalised_grey"] = normalised["grey_matter"]

    nprint(f"{col['pink']}Saving{col['reset']}: Components", to_flush=True)
    

    try:
        save_dual_regression_images(
            dr_results,
            output_dir,
            seeds,
            algo.upper(),
            dr_results["white_components"].shape[0],
            sub_id,
            fdt_path,
            roi,
            dscalar,
        )
    except Exception as e:
        error_and_exit(False, f"Unable to save images due to {e}")

    nprint(f"{col['pink']}Run Time:{col['reset']}: {t_timer.how_long()}", to_flush=True)
    nprint(f"{col['pink']}Completed{col['reset']}: {sub_id}", to_flush=True)
    return None


if __name__ == "__main__":

    os.environ["OMP_NUM_THREADS"] = "1"
    os.environ["MKL_NUM_THREADS"] = "1"
    os.environ["OPENBLAS_NUM_THREADS"] = "1"
    args = cluster_mode_args()
    dual_regression_pipeline(
        fdt_path=args["fdt_path"],
        output_dir=args["output_dir"],
        component_path=args["component_path"],
        group_average_path=args["group_average_path"],
        algo=args["algo"],
        seeds=args["seeds"],
        sub_id=args["id"],
        roi=args["roi"],
        parallel=args["parallel"],
        dscalar=args["dscalar"],
        threshold=args["threshold"],
        normalise=args["normalise"],
        use_gpu=args["gpu"],
    )
