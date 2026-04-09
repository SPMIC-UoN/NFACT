from NFACT.base.imagehandling import get_cifti_data, save_volume
from NFACT.base.utils import colours
from NFACT.base.matrix_handling import thresholding
import nibabel as nib
from glob import glob
import numpy as np
import os


def subject_variability_map(group_comp: np.ndarray, sub_data: np.ndarray) -> np.ndarray:
    """
    Function to get calculate subject
    variability maps

    Parameters
    ----------
    group_comp: np.ndarray
        group components
    sub_data: np.ndarray
        subject components

    Returns
    -------
    np.ndarray: array
        array of subject variance
        from group
    """
    return (sub_data - np.mean(group_comp)) / np.std(group_comp)


def get_subjects(path: str, img_type: str) -> list:
    """
    Function to get subjects data
    of a given imaging type

    Parameters
    ----------
    path: str
        path of str
    img_type: str
        img type of

    Returns
    -------
    list: list object
        list of subjects
        by a given imaging type
    """
    return glob(os.path.join(path, f"{img_type}_*"))



def merge_components(
    data_to_merge: np.ndarray, comp: int, threshold: float, vol: bool = True
) -> np.ndarray:
    """
    Function to merge components

    Parameters
    ----------
    data_to_merge: np.ndarray
        components to merge
    comp: int
        component to merge
    threshold: float
        threshold to apply to components before merging
    vol: bool = True
        is data volume data
    """

    if vol:
        data = data_to_merge[:, :, :, comp]
        data = thresholding(data, threshold)
        return np.sum(data_to_merge[:, :, :, comp], axis=3)
    data = data_to_merge[:, comp]
    data = thresholding(data, threshold)          
    return np.sum(data, axis=1)


def create_vol_map(vol_path: str, comp: int, threshold: float) -> np.ndarray:
    """
    Function to create a volume
    stat map

    Parameters
    ----------
    vol_path: str
        path to volume image
    comp: int
        component to merge on
    threshold: float
        threshold to apply to components before merging
    Returns
    -------
    np.ndarray: array
        array of merged components  
    """
    vol_data = nib.load(vol_path).get_fdata()
    return merge_components(vol_data, comp, threshold)


def merge_volumes(subjects: list, comp: list, threshold: float) -> np.ndarray:
    """
    Function to merge subjects volumes
    given component number(s)

    Parameters
    ----------
    subjects: list
        list of subjects
    comp: list
        list of components
    threshold: float
        threshold to apply to components before merging

    Returns
    -------
    np.ndarray: array
        array of merged volumes
    """
    subject_maps = [create_vol_map(subj, comp, threshold) for subj in subjects]
    return np.stack(subject_maps, axis=3)


def get_group_maps(group_w: str, group_g: str, comp: int, threshold: float  ) -> np.ndarray:
    """
    Function to get group maps

    Parameters
    ----------
    group_w: str
        path to group white matter
        volume
    group_g: str
        path to group matter grey data
        (currently on ciftis supported)
    comp: int
        components to merge on
    threshold: float
        threshold to apply to components before merging
    Returns
    -------
    cifti_data: np.ndarray
        cifti_data
    """
    group = nib.load(group_w).get_fdata()
    group_comp = merge_components(group, comp, threshold)
    cifit_data = process_cifti(group_g, comp)
    cifit_data["wm"] = group_comp
    return cifit_data


def sub_variance(group_map: np.ndarray, subject_map: np.ndarray) -> np.ndarray:
    """
    Function to calculate subject variance

    Parameters
    ----------
    group_map: np.ndarray
        group data
    subject_map: np.ndarray
        subject data

    Returns
    -------
    cifti_data: np.ndarray
        cifti_data
    """
    val = (subject_map - group_map) * 2
    return normalization(val)


def normalization(data: np.ndarray) -> np.ndarray:
    """
    Function to normalise an array
    (min max normalization)

    Parameters
    ----------
    data: np.ndarray
        data to normalise

    Returns
    -------
    normalized: np.ndarray
        np.ndarray that is min-max normalised
    """
    normalized = np.zeros_like(data, dtype=np.float64)
    mask = data != 0
    nonzero_vals = data[mask]
    vmin = nonzero_vals.min()
    vmax = nonzero_vals.max()
    range_val = vmax - vmin
    if range_val == 0:
        normalized[mask] = 1
    else:
        normalized[mask] = (nonzero_vals - vmin) / range_val

    return normalized


def get_variance_maps(
    group_data: np.ndarray, subject_data: np.ndarray, vol: bool = True
) -> np.ndarray:
    """
    Function to get and stack variance maps

    Parameters
    ----------
    group_data: np.ndarray
        group level data
    subject_data: np.ndarray
        subject level data
    vol: bool
        is data volume data.
        Default is True

    Returns
    -------
    np.ndarray: array
        array of stacked variance maps
    """
    if vol:
        return np.stack(
            [
                sub_variance(group_data, subject_data[:, :, :, sub])
                for sub in range(subject_data.shape[3])
            ],
            axis=3,
        )
    return np.stack(
        [
            sub_variance(group_data, subject_data[:, sub])
            for sub in range(subject_data.shape[1])
        ],
        axis=1,
    )


def save_volume_wrapper(
    meta_data_nifit_path: str, vol_to_save: np.ndarray, outdir: str, cifti: bool = False
) -> None:
    """
    Function to save volumes

    Parameters
    ----------
    meta_data_nifit_path: str
        path to nifit to get metadata
    vol_to_save: np.ndarray
        volume array to save
    outdir: str
        where to save the image
    cifti: bool
        is volume array part of
        the cifti

    Returns
    -------
    None
    """
    if cifti:
        vol_info = get_cifti_data(meta_data_nifit_path)["vol"]
    else:
        vol_info = nib.load(meta_data_nifit_path)
    save_volume(vol_info, vol_to_save, outdir)


def save_gm_surf(darrays: list, file_name: str) -> None:
    """
    Function to save surfaces

    Parameters
    ----------
    darrays: list
        list of darrays to
        save
    file_name: str
        file name
    """
    nib.GiftiImage(darrays=darrays).to_filename(f"{file_name}.func.gii")


def process_cifti(cifti_path: str, comp: int, threshold: float) -> dict:
    """
    Function to process cifti by merging components

    Parameters
    ----------
    cifti_path: str
        cifti path to load
    comp: int
        components to merge on
    threshold: float
        threshold to apply to components before merging

    Returns
    --------
    dict: dictionary object
        dictionary with left, right and volume
        arrays
    """
    cifit_data = get_cifti_data(cifti_path)
    l_surf = merge_components(cifit_data["L_surf"], comp, threshold=threshold, vol=False)
    r_surf = merge_components(cifit_data["R_surf"], comp, threshold=threshold, vol=False)
    vol_comp = merge_components(cifit_data["vol"].get_fdata(), comp, threshold=threshold, vol=True)
    return {"l_surf": l_surf, "r_surf": r_surf, "vol": vol_comp}


def create_darray(gii_data: np.ndarray) -> list:
    """
    Function to create darrays to
    save gifti data

    Parameters
    ----------
    gii_data: np.ndarray
        surface data to save

    Returns
    -------
    list: list object
        list of darrays
    """
    return [
        nib.gifti.GiftiDataArray(
            data=gii_data, datatype="NIFTI_TYPE_FLOAT32", intent=2001
        )
    ]


def create_gm_maps(subjects: list, comp: list, threshold: float) -> dict:
    """
    Function to create grey matter maps

    Parameters
    ----------
    subjects: list
        list of subjects
    comp: list
        components to merge on
    threshold: float
        threshold to apply to components before merging

    Returns
    -------
    dict: dictionary object
        dict of left, right and vol
        data of np.ndarrays
    """
    results = [process_cifti(sub, comp, threshold) for sub in subjects]
    return {
        "l_surf": np.stack([dat["l_surf"] for dat in results], axis=1),
        "r_surf": np.stack([dat["r_surf"] for dat in results], axis=1),
        "vol": np.stack([dat["vol"] for dat in results], axis=3),
    }


def save_cifit_component(
    subjects: list, outdir: str, gm_data: np.ndarray, prefix: str
) -> None:
    """
    Function to save cifti component

    Parameters
    ----------
    subjects: list
        list of subjects
    outdir: str
        filepath to output
        dir
    gm_data: np.ndarray
        grey matter data
    prefix: str
        prefix to name the


    Returns
    -------
    None
    """

    ldarray = create_darray(gm_data["l_surf"])
    rdarray = create_darray(gm_data["r_surf"])
    save_volume_wrapper(
        subjects[0],
        gm_data["vol"],
        os.path.join(outdir, f"{prefix}_subcortical_stat_map.nii.gz"),
        cifti=True,
    )
    save_gm_surf(ldarray, os.path.join(os.path.join(outdir, f"{prefix}_L")))
    save_gm_surf(rdarray, os.path.join(os.path.join(outdir, f"{prefix}_R")))


def extract_id(path: str) -> str:
    """
    Extract subject ID from filepath

    Parameters
    ----------
    path: str
        file path

    Returns
    -------
    str: string object
        str of filepath
    """

    filename = path.split("/")[-1]
    parts = filename.split("_")
    if len(parts) >= 2:
        return parts[1]
    return None


def get_sort_index(path: str, order_dict: dict) -> str:
    """
    Function to return the index of the subject ID
    from a given dictionary, or inf if not found.

    Parameters
    ----------
    path: str
        str of file path
    order_dict: dict
        dictionary of ordered
        subjects

    Returns
    -------
    key: dictionary key
        str of subject id
    """

    sub_id = extract_id(path)
    return order_dict.get(sub_id, float("inf"))


def sort_paths_by_subject_order(file_paths: list, subject_order: list) -> list:
    """
    Function to sort a list of file
    paths according to subject ID


    Parameters
    -----------
    file_paths: list
        list of str full file paths
    subject_order: list
        list of subject IDs (str)

    Returns
    --------
    list: list object
        list of sorted file paths
    """

    order_dict = {sub_id: idx for idx, sub_id in enumerate(subject_order)}
    return sorted(file_paths, key=lambda path: get_sort_index(path, order_dict))


def statsmap_main(args: dict) -> None:
    """
    Main statsmap function.
    Creates statsmap

    Parameters
    ----------
    args: dict
        cmdline dictionary
        arguments

    Returns
    -------
    None
    """

    col = colours()
    if ".gz" in args["group_grey"] or ".nii.gz" in args["group_grey"]:
        print(
            f"{col['red']} Currently only cifits are accepted for component merging{col['reset']}"
        )
        return
    print(f"{col['darker_pink']}Merging components:{col['reset']}", *args["components"])
    group_mode = args.get("group-only", False)
    if group_mode:
        folder_path = os.path.join(
            args["nfact_decomp_dir"], "components", args["algo"], "decomp"
        )
    else:
        folder_path = os.path.dirname(args["dr_output"][0])

    if args["map_name"] == "":
        args["map_name"] = "stat_map"

    print(f"\n{col['plum']}Working on White matter{col['reset']}")
    print("-" * 100)
    subjects_w = get_subjects(folder_path, "W")

    if not group_mode:
        subjects_w = sort_paths_by_subject_order(subjects_w, args["dr_output"])
    subject_W_maps = merge_volumes(subjects_w, args["components"], args["threshold"])
    save_volume_wrapper(
        subjects_w[0],
        subject_W_maps,
        os.path.join(args["stats_dir"], f"W_{args['map_name']}.nii.gz"),
        
    )

    print(f"\n{col['plum']}Working on Grey matter files{col['reset']}")
    print("-" * 100)
    subjects_g = get_subjects(folder_path, "G")

    if not group_mode:
        subjects_g = sort_paths_by_subject_order(subjects_g, args["dr_output"])

    gm_data = create_gm_maps(subjects_g, args["components"], args["threshold"])
    save_cifit_component(
        subjects_g, args["stats_dir"], gm_data, f"G_{args['map_name']}"
    )

    if group_mode or args["skip"]:
        return
    
    print(f"\n{col['plum']}Calculating variance maps{col['reset']}")
    if args['dim'] is None:
        print(
            f"{col['red']}Unable to calculate variance maps. Dim argument is likely required{col['reset']}"
        )
        return
    group_maps = get_group_maps(
        args["group_white"],
        args["group_grey"][0],
        args["components"],
    )
    wm = get_variance_maps(group_maps["wm"], subject_W_maps)
    save_volume_wrapper(
        subjects_w[0],
        wm,
        os.path.join(args["stats_dir"], f"variance_W_{args['map_name']}.nii.gz"),
    )
    cifit_var = {
        "r_surf": get_variance_maps(group_maps["r_surf"], gm_data["r_surf"], vol=False),
        "l_surf": get_variance_maps(group_maps["l_surf"], gm_data["l_surf"], vol=False),
        "vol": get_variance_maps(group_maps["vol"], gm_data["vol"]),
    }
    save_cifit_component(
        subjects_g, args["stats_dir"], cifit_var, f"variance_G_{args['map_name']}"
    )
