# NFACT functions
from NFACT.preprocess.nfactpp_setup import (
    nfact_pp_folder_setup,
    check_roi_seed_len,
    load_file_tree,
)
from NFACT.preprocess.nfactpp_functions import (
    get_file,
    filetree_get_files,
    process_filetree_args,
    create_files_for_decomp,
    write_options_to_file,
)
from NFACT.preprocess.probtrackx_functions import (
    build_probtrackx2_arguments,
    Probtrackx,
)
from NFACT.preprocess.img_processing import (
    clean_target2,
    binarise_target2,
    downsample_volume,
    seeds_to_ascii,
    downsampling,
)
from NFACT.base.utils import colours, error_and_exit
from NFACT.base.setup import check_seeds_surfaces
from NFACT.base.imagehandling import rename_seed
import os
import shutil


def change_file_path_to_nfactpp(nfact_directory: str, img_file_paths: list) -> list:
    """
    Function to change file path for imaging files
    used in seeding.

    Parameters
    -----------
    nfact_directory: str
        path to nfact directory
    img_file_paths: list
        list of imaging file paths

    Returns
    -------
    list: list object
        list of imaging paths
    """
    return [
        os.path.join(nfact_directory, "files", os.path.basename(img_file))
        for img_file in img_file_paths
    ]


def move_seeds(nfactpp_diretory: str, seed: list, roi: list) -> None:
    """
    Function to move seeds to nfact directory

    Parameters
    -----------
    nfact_directory: str
        path to nfact directory
    seed: list
        list of seed file paths
    roi: list
        list of rois file paths

    Returns
    -------
    None
    """
    for seed_location in seed:
        shutil.copyfile(
            seed_location,
            os.path.join(nfactpp_diretory, "files", os.path.basename(seed_location)),
        )
    if roi:
        for roi_location in roi:
            shutil.copyfile(
                roi_location,
                os.path.join(nfactpp_diretory, "files", os.path.basename(roi_location)),
            )


def setup_subject_directory(
    nfactpp_diretory: str, seed: list, roi: list, sub, arg, col
) -> None:
    """
    Function to set up the subjects
    directory

    Parameters
    ----------
    nfactpp_diretory: str
        nfactpp_diretory path
    seed: list
        list of seeds

    Returns
    -------
    None
    """
    nfact_pp_folder_setup(nfactpp_diretory)
    if arg["downsample"]:
        print(f"\n{col['pink']}Downsampling seeds{col['reset']}")
        downsampling(
            seed,
            roi,
            os.path.join(nfactpp_diretory, "files"),
            arg["file_tree"],
            sub,
            arg["vertex"],
            arg["voxel"],
        )
        return None
    move_seeds(nfactpp_diretory, seed, roi)


def process_surface(nfactpp_diretory: str, seed: list, roi: list) -> str:
    """
    Function to process surface seeds

    Parameters
    ----------
    nfactpp_diretory: str
        nfact_pp path
    seed: list
        list of seeds
    roi: list
        list of roi

    Returns
    -------
    str: str
        string of seeds names
    """
    seed_names = rename_seed(seed)
    col = colours()
    for img in range(len(seed_names)):
        if ".nii" not in seed[img]:
            print(
                f"{col['pink']}Working on seed surface:{col['reset']} {os.path.basename(seed[img])}"
            )
            seeds_to_ascii(
                seed[img],
                roi[img],
                os.path.join(nfactpp_diretory, "files", f"{seed_names[img]}_surf"),
            )
        else:
            print(
                f"{col['pink']}Adding additional seed:{col['reset']} {os.path.basename(seed[img])}"
            )
    surf_mode_seeds = [
        os.path.join(nfactpp_diretory, "files", f"{seed}_surf.asc")
        if ".nii" not in seed
        else os.path.join(nfactpp_diretory, "files", seed)
        for seed in seed_names
    ]
    return "\n".join(surf_mode_seeds)


def target_generation(arg: dict, nfactpp_diretory: str, col: dict) -> None:
    """
    Function to generate target2 image

    Parameters
    ----------
    arg: dict
        dict of command line arguments
    nfactpp_diretory: str
        str of nfact_pp directory
    col: dict
        dict of colour string

    Returns
    -------
    None
    """

    print(f"{col['darker_pink']}Creating:{col['reset']} Target2 Image")
    target_2_ref = arg["seedref"]
    default_ref = os.path.join(
        os.getenv("FSLDIR"), "data", "standard", "MNI152_T1_2mm_brain.nii.gz"
    )
    if arg["seedref"] == default_ref:
        clean_target2(nfactpp_diretory, default_ref)
    else:
        shutil.copy2(arg["seedref"], os.path.join(nfactpp_diretory, "target2.nii.gz"))

    target_2_ref = os.path.join(nfactpp_diretory, "target2")
    downsample_volume(
        target_2_ref,
        os.path.join(nfactpp_diretory, "target2"),
        arg["mm_res"],
        target_2_ref,
        "nearestneighbour",
    )
    binarise_target2(target_2_ref)


def print_to_screen(print_string: str) -> None:
    """
    Function to print to screen

    Parameters
    ----------
    print_string: str
        string to print

    Returns
    -------
    None
    """
    print("\n")
    print(f"{print_string}\n")
    print("-" * 100)


def process_subject(sub: str, arg: dict, col: dict) -> list:
    """
    Function to process subjects arguments.

    Parameters
    ----------
    sub: str
        path to subjects directory
    arg: dict
        dictionary of command line
        args
    col: dict
        dictionary of colours

    Returns
    -------
    list: list object
        list of subjects arguments
    """

    sub_id = os.path.basename(sub)
    print(f"\n{col['pink']}Setting up:{col['reset']} {sub_id}")

    if arg["file_tree"]:
        arg = process_filetree_args(arg, sub_id)

    seed = get_file(arg["seed"], sub, arg["absolute"])
    seed_text = "\n".join(seed)
    # using this function not to return a file but check it is an imaging file
    get_file(arg["warps"], sub)
    nfactpp_diretory = os.path.join(arg["outdir"], "nfact_pp", sub_id)
    roi = get_file(arg["roi"], sub, arg["absolute"]) if arg["surface"] else False
    setup_subject_directory(nfactpp_diretory, seed, roi, sub, arg, col)
    seed = change_file_path_to_nfactpp(nfactpp_diretory, seed)
    create_files_for_decomp(nfactpp_diretory, seed, roi)

    if arg["surface"]:
        roi = change_file_path_to_nfactpp(nfactpp_diretory, roi)
        seed_text = process_surface(nfactpp_diretory, seed, roi)

    error_and_exit(write_options_to_file(nfactpp_diretory, seed_text, "seeds"))

    return build_probtrackx2_arguments(
        arg,
        sub,
        ptx_options=arg["ptx_options"],
    )


def set_up_filestree(arg: dict) -> dict:
    """
    Function to set up filetree

    Parameters
    ----------
    arg: dict
        dictionary of cmd line args
    col: dict
        dict of colours

    Returns
    -------
    arg: dict
        dict of processed cmd line args
    """
    try:
        arg["file_tree"] = load_file_tree(arg["file_tree"])
    except Exception as e:
        error_and_exit(False, f"Unable to load filetree due to: {e}")

    # load a random subjects seed to check its type
    try:
        arg["seed"] = [filetree_get_files(arg["file_tree"], "sub1", "L", "seed")]
    except Exception as e:
        error_and_exit(False, f"Badly defined filetree. Error due to {e}")

    # Needed for checking if seed is surface
    arg["roi"] = ["filestree"]
    return arg


def pre_processing(arg: dict, handler: object) -> None:
    """
    Main function for nfact PP

    Parameters
    ----------
    arg: dict
       dictionary of command line
       arguments
    handler: object
        handler object for signit

    Returns
    -------
    None
    """
    col = colours()
    if arg["file_tree"]:
        arg = set_up_filestree(arg)

    arg["surface"] = check_seeds_surfaces(arg["seed"])

    if arg["surface"]:
        print(f"{col['darker_pink']}Mode:{col['reset']} Surface")
        check_roi_seed_len(arg["seed"], arg["roi"])
    else:
        print(f"{col['darker_pink']}Mode:{col['reset']} Volume")

    if not arg["target2"]:
        target_generation(arg, os.path.join(arg["outdir"], "nfact_pp"), col)
    else:
        print(f"{col['darker_pink']}Target2 img:{col['reset']} {arg['target2']}")

    print(
        f"{col['darker_pink']}Number of subjects:{col['reset']} {len(arg['list_of_subjects'])}"
    )
    print_to_screen("SUBJECT SETUP")
    subjects_commands = [
        process_subject(sub, arg, col) for sub in arg["list_of_subjects"]
    ]

    # This supresses the signit kill message or else it prints it off multiple times for each core
    if arg["n_cores"]:
        handler.set_suppress_messages = True

    # Running probtrackx2
    print_to_screen("TRACTOGRAPHY")
    probtrack = Probtrackx(
        subjects_commands,
        arg["cluster"],
        arg["cluster_time"],
        arg["cluster_queue"],
        arg["cluster_ram"],
        arg["cluster_qos"],
        arg["gpu"],
        arg["n_cores"],
    )
    probtrack.run()
