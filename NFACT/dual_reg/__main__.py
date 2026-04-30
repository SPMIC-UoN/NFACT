from NFACT.dual_reg.nfact_dr_args import nfactdr_args, nfact_dr_splash
from NFACT.dual_reg.dual_regression.set_up_dual_regression import (
    run_on_cluster,
    run_locally,
)
from NFACT.dual_reg.nfact_dr_functions import create_nfact_dr_folder_set_up
from NFACT.base.setup import (
    check_algo,
    get_subjects,
    check_subject_exist,
    check_arguments,
    process_input_imgs,
    check_seeds_surfaces,
    check_rois,
    get_paths,
    check_nfact_decomp_directory,
)
from NFACT.base.filesystem import delete_folder
from NFACT.base.cluster_support import processing_cluster
from NFACT.base.utils import colours, nprint
from NFACT.base.logging import NFACT_logs
from NFACT.base.setup import check_fsl_is_installed
from NFACT.base.signithandler import Signit_handler
import os


def nfact_dr_main(args: dict = None) -> None:
    """
    Main function for NFACT DR.

    Parameters
    ----------
    arg: dict
        Set of command line arguments
        from nfact_pipeline
        Default is None


    Returns
    -------
    None
    """

    Signit_handler()
    col = colours()
    to_exit = False

    if not args:
        args = nfactdr_args()
        to_exit = True
    # Do argument checking
    check_arguments(args, ["seeds", "list_of_subjects", "algo"])
    args["algo"] = check_algo(args["algo"])

    # Get component paths
    paths = get_paths(args)

    if args["overwrite"]:
        delete_folder(os.path.join(args["outdir"], "nfact_dr"))
    # check subjects exist
    args = get_subjects(args)
    check_subject_exist(args["ptxdir"])
    check_nfact_decomp_directory(paths["component_path"], paths["group_average_path"])

    if args["cluster"]:
        check_fsl_is_installed()
        # Needed for cluster checks. Hacky work around
        args = processing_cluster(args)

    # Set up directory
    create_nfact_dr_folder_set_up(args["outdir"])

    # Process seeds
    args["seeds"] = process_input_imgs(args["seeds"])
    args["surface"] = check_seeds_surfaces(args["seeds"])
    args = check_rois(args)

    # logging
    log = NFACT_logs(args["algo"], "DR", len(args["ptxdir"]))
    log.set_up_logging(os.path.join(args["outdir"], "nfact_dr", "logs"))
    log.inital_log(nfact_dr_splash())
    log.log(
        f"{col['plum']}Regresion Type{col['reset']}: {'Non-Negative' if args['algo'] == 'nmf' else 'Linear'}"
    )
    log.log_break("input")
    log.log_arguments(args)
    log.log_break("nfact decomp workflow")
    nprint(f"{col['plum']}Number of subject:{col['reset']} {len(args['ptxdir'])}")
    parallel_str = args["n_cores"] if args["n_cores"] else 1
    nprint(f"{col['plum']}Number of cores{col['reset']}: {parallel_str}")
    nprint("\nDual Regression")
    nprint("-" * 100)

    if args["cluster"]:
        run_on_cluster(args, paths)
    else:
        run_locally(args, paths)

    nprint(f"{col['darker_pink']}NFACT_DR has finished{col['reset']}")
    log.clear_logging()

    if to_exit:
        exit(0)


if __name__ == "__main__":
    nfact_dr_main()
