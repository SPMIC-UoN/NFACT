from NFACT.base.utils import error_and_exit, colours
from NFACT.base.imagehandling import check_files_are_imaging_files
from NFACT.base.filesystem import write_to_file, load_json
import os
from NFACT.preprocess.nfactpp_setup import check_provided_img


def seedref(seedref: str) -> str:
    """
    Function to provide seedref.
    Default is human MNI space.

    Parameteres
    -----------
    seedref: str
        path to a seed reference.
        If None defaults to
        FSL MNI152_T1_2mm_brain.nii.gz

    Returns
    -------
    seedref: str
        path to seed ref

    """
    col = colours()
    if seedref:
        check_provided_img(seedref, "Cannot find seed ref image")
        print(
            f"{col['darker_pink']}Seed Reference Space:{col['reset']} {os.path.basename(seedref)}"
        )
        return seedref
    seedref = os.path.join(
        os.getenv("FSLDIR"), "data", "standard", "MNI152_T1_2mm_brain.nii.gz"
    )
    print(
        f"{col['darker_pink']}Seed Reference Space:{col['reset']} {os.path.basename(seedref)}"
    )
    return seedref


def get_file(img_file: list, sub: str, absolute: bool = False) -> list:
    """
    Function to get an imaging file
    type and returns it. Checks that file
    is correct file type and exists.

    Parameters
    ----------
    img_file: list
        a list of imaging files
    sub: str
        path to subjects directory.
    absolute: bool
        are imaging to be treated
        as absolute paths. If not
        then paths are treated as relative
        and appended to subject path

    Returns
    -------
    img_files: list
        list of imging files

    """
    if not absolute:
        img_files = [os.path.join(sub, file.lstrip("/")) for file in img_file]
    else:
        img_files = img_file
    [
        error_and_exit(
            os.path.exists(path), f"Unable to find {path}. Please check it exists"
        )
        for path in img_files
    ]
    [check_files_are_imaging_files(path) for path in img_files]
    return img_files


def filetree_get_files(filetree: object, sub: str, hemi: str, file: str) -> str:
    """
    Function to get files from filetree.

    Parameters
    ----------
    filetree: FileTree object
        loaded tree
    sub: str
        subject string
    hemi: str
        string of hemishpere
    file: str
        name of file

    Returns
    -------
    file_path: str
        file path
    """
    return filetree.update(sub=sub, hemi=hemi).get(file)


def process_filetree_args(arg: dict, sub: str) -> dict:
    """
    Function to process filetree arguments

    Parameteres
    -----------
    arg: dict
        dictionary of command
        line arguments
    sub: str
        string of subject id

    Returns
    -------
    arg: dict
        dictionary of processed
        arguments
    """
    del arg["seed"]
    try:
        del arg["roi"]
    except KeyError:
        pass

    arg["seed"] = list(
        dict.fromkeys(
            [
                filetree_get_files(arg["file_tree"], sub, hemi, "seed")
                for hemi in ["L", "R"]
            ]
        )
    )

    if "add_seed1" in arg["file_tree"].template_keys():
        arg["seed"] = arg["seed"] + get_additional_seeds(arg["file_tree"], sub)

    if "waypoints" in arg["file_tree"].template_keys():
        arg["waypoints"] = filetree_get_files(arg["file_tree"], sub, "L", "waypoints")

    arg["warps"] = [
        filetree_get_files(arg["file_tree"], sub, "L", "std2diff"),
        filetree_get_files(arg["file_tree"], sub, "L", "diff2std"),
    ]
    arg["bpx_path"] = filetree_get_files(arg["file_tree"], sub, "L", "bedpostX")
    if arg["surface"]:
        arg["roi"] = [
            filetree_get_files(arg["file_tree"], sub, hemi, "roi")
            for hemi in ["L", "R"]
        ]
    return arg


def update_seeds_file(file_path: str) -> None:
    """
    Function to update file extension
    in seeds.txt. Updates surface asc to
    gii.

    Parameters
    ----------
    file_path: str
        string to file path

    Returns
    -------
    None
    """
    try:
        with open(file_path, "r") as file:
            content = file.read()
            update_extensions = content.replace(".asc", ".gii")
        with open(file_path, "w") as file:
            file.write(update_extensions)
    except Exception as e:
        error_and_exit(False, f"Unable to change seeds file due to {e}")


def get_additional_seeds(files_tree: object, subject: str) -> list:
    """
    Function to get additional seeds from
    filetree

    Parameters
    ----------
    files_tree: object
        FSL.filetree object
    subject: str
        str of subject

    Returns
    -------
    list: list object
        list of paths for additional
        seeds
    """
    add_seed_keys = sorted(
        (key for key in files_tree.template_keys() if key.startswith("add_seed")),
        key=lambda x: int(x.replace("add_seed", "")),
    )
    return [
        filetree_get_files(files_tree, subject, "L", file) for file in add_seed_keys
    ]


def get_stop_files_filestree(files_tree: object, subject: str) -> dict:
    """
    Function to get stopping files path
    from filetree

    Parameters
    ----------
    files_tree: object
        FSL.filetree object
    subject: str
        str of subject

    Returns
    -------
    dict: dictionary object
        dict of list wtstop_mask
        and stopping_mask

    """
    return {
        "wtstop_mask": [
            filetree_get_files(files_tree, subject, "L", file)
            for file in files_tree.template_keys()
            if "wtstop" in file
        ],
        "stopping_mask": [
            filetree_get_files(files_tree, subject, "L", file)
            for file in files_tree.template_keys()
            if file.startswith("stop")
        ],
    }


def stoppage(img_file_path: str, file_directory: str, paths_dict: dict) -> list:
    """
    function to write stoppage and wtstop masks
    to file and return the probtrackx commands

    Parameters
    -----------
    img_file_path: str
        path to subject imging file
    file_directory:
        path to nfact_pp/sub/files
        directory
    paths_dict: dict
        dictionary of paths to stoppage and
        wstop masks.

    Returns
    -------
    list: list_oject
        list of additional ptx options
        with --stop and --wtstop
    """

    write_to_file(
        file_directory,
        "stop",
        [
            os.path.join(img_file_path, file + "\n")
            for file in paths_dict["stopping_mask"]
        ],
        text_is_list=True,
    )
    write_to_file(
        file_directory,
        "wtstop",
        [
            os.path.join(img_file_path, file + "\n")
            for file in paths_dict["wtstop_mask"]
        ],
        text_is_list=True,
    )

    return [
        f"--stop={os.path.join(file_directory, 'stop')}",
        f"--wtstop={os.path.join(file_directory, 'wtstop')}",
    ]


def stop_masks(arg: dict, nfactpp_diretory: str, sub: str, sub_id: str) -> list:
    """
    Function to process stop masks

    Parameters
    ----------
    arg: dict,
       cmd processes
    nfactpp_diretory: str
        path to nfactpp_directory
    sub: str
        path to sub dirs
    sub_id: str
        subject id

    Returns
    -------
    list: list object
        list of stop and wtstop
        arguments
    """
    if arg["file_tree"]:
        stop_files = get_stop_files_filestree(arg["file_tree"], sub_id)
    else:
        stop_files = load_json(arg["stop"])
    return stoppage(sub, os.path.join(nfactpp_diretory, "files"), stop_files)


def create_files_for_decomp(nfact_directory: str, seeds: list, roi: list) -> None:
    """
    Function to write seeds and roi for
    decomp.

    Parameters
    ----------
    nfact_directory: str
        subjects nfact_directory
    seeds: list
        list of seeds
    roi: list
        list of roi files

    Returns
    -------
    None
    """
    seed_filename = "seeds_for_decomp"
    roi_filename = "roi_for_decomp"
    base_nfact_dir = os.path.dirname(nfact_directory)
    if not os.path.exists(os.path.join(base_nfact_dir, f"{seed_filename}.txt")):
        seed_text = "\n".join(seeds)
        write_options_to_file(base_nfact_dir, seed_text, seed_filename)

    if roi:
        if not os.path.exists(os.path.join(base_nfact_dir, f"{roi_filename}.txt")):
            mw_text = "\n".join(
                [
                    os.path.join(nfact_directory, "files", os.path.basename(mw))
                    for mw in roi
                ]
            )
            write_options_to_file(base_nfact_dir, mw_text, roi_filename)


def write_options_to_file(file_path: str, text_to_save: str, name_of_file: str):
    """
    Function to write seeds
    and ptx_options to file

    Parmeters
    ---------
    file_path: str
        file path for nfact_PP
        directory
    seed_txt: str
        path of string to go into
        seed directory

    Returns
    --------
    bool: boolean
        true if successful
        else False

    """
    file_written = write_to_file(file_path, f"{name_of_file}.txt", text_to_save + "\n")
    if not file_written:
        return False
    return True
