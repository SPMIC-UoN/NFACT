from NFACT.base.logging import NFACT_logs
from NFACT.base.utils import Timer, colours, nprint
from NFACT.base.signithandler import Signit_handler
from NFACT.base.filesystem import delete_folder
from NFACT.base.matrix_handling import save_matrix
from NFACT.base.setup import (
    check_subject_exist,
    check_algo,
    get_subjects,
    process_input_imgs,
    check_arguments,
    check_seeds_surfaces,
    check_rois,
)
from NFACT.decomp.setup.args import nfact_decomp_args, nfact_decomp_splash
from NFACT.decomp.setup.file_setup import (
    create_folder_set_up,
    get_group_average_files,
)
from NFACT.decomp.setup.configure_setup import (
    check_config_file,
    load_config_file,
)
from NFACT.decomp.decomposition.matrix_decomposition import (
    matrix_decomposition,
    get_parameters,
)
from NFACT.decomp.decomposition.matrix_handling import (
    process_fdt_matrix2,
    load_previous_matrix,
)
from NFACT.decomp.pipes.image_handling import (
    winner_takes_all,
    save_images,
    save_components_to_disk,
)
from NFACT.base.matrix_handling import thresholding_components
from NFACT.decomp.setup.arg_check import process_command_args
import os


def nfact_decomp_main(args: dict = None) -> None:
    """
    Main nfact function

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
    # Setting up nfact

    Signit_handler()
    to_exit = False
    if not args:
        args = nfact_decomp_args()
        to_exit = True
    col = colours()
    os.environ["PYTHONWARNINGS"] = "ignore"
    if args["cifti"]:
        print(
            f"{col['plum']}Cifti option given:{col['reset']} Seeds must be in correct order"
        )
    if args["matrix"]:
        args["list_of_subjects"] = os.path.join(args["matrix"], "average_matrix2.npy")

    # Do argument checking
    check_arguments(args, ["list_of_subjects", "dim", "seeds", "outdir"])
    args["algo"] = check_algo(args["algo"])
    args = process_command_args(args)

    # check subjects exist
    args = get_subjects(args)
    check_subject_exist(args["ptxdir"])
    number_subjects = "User Overide Matrix" if args["matrix"] else len(args["ptxdir"])
    print(f"{col['plum']}Number of Subjects:{col['reset']}", number_subjects)

    group_mode = True if len(args["ptxdir"]) > 1 else False
    # process seeds
    args["seeds"] = process_input_imgs(args["seeds"])
    args["surface"] = check_seeds_surfaces(args["seeds"])
    args = check_rois(args)
    if args["config"]:
        args["config"] = load_config_file(args["config"], args["algo"])
        check_config_file(args["config"], args["algo"])

    # Build out folder structure
    if args["overwrite"]:
        delete_folder(os.path.join(args["outdir"], "nfact_decomp"))
    create_folder_set_up(args["outdir"])
    print(f"{col['plum']}NFACT folder:{col['reset']} {args['outdir']}")

    # Get hyperparameters
    parameters = get_parameters(args["config"], args["algo"], args["dim"])

    # Set up log
    log = NFACT_logs(args["algo"], "decomp", len(args["ptxdir"]))
    log.set_up_logging(os.path.join(args["outdir"], "nfact_decomp", "logs"))
    log.inital_log(nfact_decomp_splash())
    log.log_break("input")
    log.log_arguments(args)
    log.log_parameters(parameters)
    log.log_break("nfact decomp workflow")
    print(
        f"{col['plum']}Log file:{col['reset']} {os.path.join(args['outdir'], 'nfact_decomp', 'logs')}"
    )

    get_group_average_files(
        args["ptxdir"][0],
        os.path.join(args["outdir"], "nfact_decomp", "group_averages"),
    )

    # load matrix
    nprint("\nLOADING MATRIX")
    nprint("-" * 100)
    matrix_time = Timer()
    matrix_time.tic()
    print_str = f"{col['pink']}NFACT Matrix:{col['reset']}"
    fdt_2_conn = None

    if args["matrix"]:
        nprint(f"{print_str} Loading user given matrix")
        fdt_2_conn = load_previous_matrix(
            os.path.join(args["matrix"], "average_matrix2.npy")
        )

    if os.path.exists(
        os.path.join(
            args["outdir"], "nfact_decomp", "group_averages", "average_matrix2.npy"
        )
    ):
        nprint(f"{print_str} Loading previously saved")

        fdt_2_conn = load_previous_matrix(
            os.path.join(
                args["outdir"], "nfact_decomp", "group_averages", "average_matrix2.npy"
            )
        )

    if fdt_2_conn is None:
        nprint(f"{print_str} Averaging") if group_mode else nprint(
            f"{print_str} Loading Single Matrix"
        )
        save_directory = os.path.join(args["outdir"], "nfact_decomp", "group_averages")
        fdt_2_conn = process_fdt_matrix2(args["ptxdir"], group_mode)
        save_matrix(fdt_2_conn, save_directory, "average_matrix2")
        nprint(f"{col['pink']}Saving Matrix:{col['reset']} {save_directory}")
    nprint(
        f"{col['pink']}Matrix Loading Time:{col['reset']} {matrix_time.how_long()} \n"
    )

    # Run the decomposition
    decomposition_timer = Timer()
    decomposition_timer.tic()

    nprint("DECOMPOSING MATRIX")
    nprint("-" * 100)
    nprint(f"{col['pink']}NFACT method:{col['reset']} {args['algo'].upper()}")

    components = matrix_decomposition(fdt_2_conn, parameters, args)
    nprint(
        f"{col['pink']}Decomposition time:{col['reset']} {decomposition_timer.how_long()}\n"
    )
    if args["wta"]:
        # Save winner-takes-all maps
        nprint("Saving winner-take-all maps\n")
        winner_takes_all(
            components,
            args["wta_zthr"],
            args["algo"].upper(),
            os.path.join(
                args["outdir"],
                "nfact_decomp",
            ),
            args["seeds"],
            args["dim"],
            args["roi"],
            args["cifti"],
        )
    components = thresholding_components(
        int(args["threshold"]),
        os.path.join(
            args["outdir"], "nfact_decomp", "group_averages", "coords_for_fdt_matrix2"
        ),
        args["seeds"],
        components,
    )

    if args["disk"]:
        save_components_to_disk(
            components,
            os.path.join(args["outdir"], "nfact_decomp"),
            args["algo"].upper(),
            args["dim"],
        )
    else:
        # Save the results
        save_images(
            components,
            os.path.join(
                args["outdir"],
                "nfact_decomp",
            ),
            args["seeds"],
            args["algo"].upper(),
            args["dim"],
            args["roi"],
            args["cifti"],
        )

    nprint(f"{col['darker_pink']}NFACT decomp has finished{col['reset']}")

    log.clear_logging()

    if to_exit:
        exit(0)


if __name__ == "__main__":
    nfact_decomp_main()
    exit(0)
