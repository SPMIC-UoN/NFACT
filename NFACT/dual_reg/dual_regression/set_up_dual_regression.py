from NFACT.dual_reg.nfact_dr_functions import get_subject_id, get_group_level_components
from NFACT.dual_reg.dual_regression.run_dual_regression import dual_regression_pipeline
from NFACT.base.utils import nprint, error_and_exit, colours
from NFACT.base.cluster_support import cluster_submission, Queue_Monitoring
from pathlib import Path
import os
import sys


def get_python_path() -> str:
    """
    Function to return python path.
    If running in virtualenv then
    will use that else will use the
    fsl python path

    Parameteres
    -----------
    None

    Returns
    -------
    str: string object
        path for python
    """
    if sys.prefix != sys.base_prefix:
        return sys.executable
    return os.path.join(os.environ["FSLDIR"], "bin", "python3")


def get_cluster_script_path() -> str:
    """
    Function to return path of
    cluster script.

    Parameters
    ----------
    None

    Returns
    -------
    str: str object
        Path to cluster
        script
    """
    return os.path.join(Path(__file__).parent, "run_dual_regression.py")


def build_cluster_command(
    fdt_path: str,
    output_dir: str,
    component_path: str,
    group_average_path: str,
    algo: str,
    seeds: str,
    sub_id: str,
    roi: str,
    threshold_val: str,
    parallel: str,
    normalise: bool,
    dscalar: bool,
) -> list:
    """
    Function to build out cluster
    command.

    Parameters
    ----------
    fdt_path: str
        path to subjects fdt_path
    output_dir: str
        path to output dir
    component_path: str
        path to components
    group_average_path: str
        path to group averages
    algo: str
        whaich algo, NMF or ICA
    seeds: str
        seeds to use
    sub_id: str
        subject id
    roi: str
        rois to use
    threshold_val: str
        value to threshold components at
    parallel: str
        number of parallelizations.
    normalise: bool
        should noramlized maps be saved
    dscalar: bool
        is this a cifti
    Returns
    -------
    list: list object
        list of command
    """
    python_path = get_python_path()
    cluster_script = get_cluster_script_path()
    command = [
        python_path,
        cluster_script,
        "--fdt_path",
        str(fdt_path),
        "--output_dir",
        str(output_dir),
        "--component_path",
        str(component_path),
        "--group_average_path",
        str(group_average_path),
        "--algo",
        str(algo),
        "--seeds",
        *seeds,
        "--id",
        str(sub_id),
        "--roi",
        *roi,
        "--threshold",
        str(threshold_val),
    ]
    if parallel:
        command.extend(["--parallel", str(parallel)])
    if normalise:
        command.extend(["--normalise"])
    if dscalar:
        command.extend(["--dscalar"])
    return command


def submit_to_cluster(args: dict, paths: dict) -> list:
    """
    Function to submit jobs to cluster
    using fsl_sub
    Function to run jobs on cluster

    Parameters
    ----------
    args: dict
        cmd arguments
    paths: dict
        dictionary of paths

    Returns
    -------
    job_ids: list
        list of job ids
    """
    job_ids = []
    for sub in args["ptxdir"]:
        sub_id = get_subject_id(sub)
        nprint(f"Submittng {sub_id}")
        cluster_command = build_cluster_command(
            sub,
            os.path.join(args["outdir"], "nfact_dr"),
            paths["component_path"],
            paths["group_average_path"],
            args["algo"],
            args["seeds"],
            sub_id,
            args["roi"],
            args["threshold"],
            args["n_cores"],
            args["normalise"],
            args["cifti"],
        )
        id = cluster_submission(
            cluster_command,
            args["cluster_time"],
            args["cluster_ram"],
            args["cluster_queue"],
            f"{sub_id}_nfact_dr",
            os.path.join(args["outdir"], "nfact_dr", "logs"),
            args["cluster_qos"],
            gpu=False,
            parallel=args["n_cores"],
        )
        job_ids.append(id)
    return job_ids


def run_on_cluster(args: dict, paths: dict) -> None:
    """
    Function to run dual regression
    on the cluster

    Parameters
    ----------
    args: dict
        cmd arguments
    paths: dict
        dictionary of paths

    Returns
    -------
    None
    """

    col = colours()
    nprint(f"{col['pink']}Running{col['reset']}: Cluster")
    method = "Regression" if args["algo"] == "ica" else "Non-negative Regression"
    nprint(f"{col['pink']}DR Method:{col['reset']} {method}")
    nprint(f"{col['pink']}Submtting to{col['reset']}: {args['cluster_queue']}")
    ids = submit_to_cluster(args, paths)
    queue = Queue_Monitoring()
    queue.monitor(ids)


def run_locally(args: dict, paths: dict) -> None:
    """
    Function to run dual regression
    locally

    Parameters
    ----------
    args: dict
        dictionary of cmd args
    paths: dict
        path to images

    Returns
    -------
    None
    """
    col = colours()

    nprint(f"{col['pink']}Running:{col['reset']} Locally")
    method = "Regression" if args["algo"] == "ica" else "Non-negative Regression"
    nprint(f"{col['pink']}DR Method:{col['reset']} {method}")
    nprint(f"{col['pink']}Obtaining:{col['reset']} Components")

    try:
        components = get_group_level_components(
            paths["component_path"],
            paths["group_average_path"],
            args["seeds"],
            args["roi"],
        )
    except Exception as e:
        error_and_exit(False, f"Unable to find components due to {e}")

    for subject in args["ptxdir"]:
        subject_id = get_subject_id(subject)
        dual_regression_pipeline(
            fdt_path=subject,
            output_dir=os.path.join(args["outdir"], "nfact_dr"),
            component_path=paths["component_path"],
            group_average_path=paths["group_average_path"],
            algo=args["algo"],
            seeds=args["seeds"],
            sub_id=subject_id,
            roi=args["roi"],
            parallel=args["n_cores"],
            components=components,
            dscalar=args["cifti"],
            threshold=args["threshold"],
            normalise=args["normalise"],
        )
