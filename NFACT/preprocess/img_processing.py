import subprocess
import os
from itertools import product
from NFACT.base.utils import error_and_exit
from NFACT.preprocess.nfactpp_functions import filetree_get_files
from NFACT.base.setup import check_seeds_surfaces


def seeds_to_ascii(surfin: str, roi: str, surfout: str) -> None:
    """
    Function to create seeds from
    surfaces.

    Parameters
    ----------
    surfin: str
        input surface
    roi: str,
        roi to restrict seeding
    surfout: str
        name of output surface.
        Needs to be full path

    Returns
    -------
    None
    """

    try:
        run = subprocess.run(
            [
                "surf2surf",
                "-i",
                surfin,
                "-o",
                surfout,
                f"--values={roi}",
                "--outputtype=ASCII",
            ],
            capture_output=True,
        )

    except subprocess.CalledProcessError as error:
        error_and_exit(False, f"Error in calling surf2surf: {error}")
    except KeyboardInterrupt:
        run.kill()

    if run.returncode != 0:
        error_and_exit(
            False,
            f"FSL surf2surf failure due to {run.stderr}. Unable to create asc surface",
        )


def downsample_volume(
    target_img: str,
    output_dir: str,
    resolution: str,
    reference_img: str,
    interpolation_strategy: str,
) -> None:
    """
    Function to create target2 image

    Parameters
    ----------
    target_img: str
        string to target image
    output: str
        string to output directory
    resolution: str
        resolution of target2
    reference_img: str
        reference input
    interpolation_strategy: str
        interpolation, either
        trilinear,
        nearestneighbour,
        sinc,
        spline

    Returns
    -------
    None
    """

    try:
        run = subprocess.run(
            [
                "flirt",
                "-in",
                target_img,
                "-out",
                output_dir,
                "-applyisoxfm",
                str(resolution),
                "-ref",
                reference_img,
                "-interp",
                interpolation_strategy,
            ],
            capture_output=True,
        )
    except FileNotFoundError:
        error_and_exit(False, "Unable to find reference image. Please check it exists")
    except subprocess.CalledProcessError as error:
        error_and_exit(False, f"Error in calling FSL flirt: {error}")
    except KeyboardInterrupt:
        run.kill()

    if run.returncode != 0:
        error_and_exit(
            False, f"FSL FLIRT failure due to {run.stderr}. Unable to build target2"
        )


def wb_cmd(command: list) -> None:
    """
    Wrapper function around workbench

    Parameters
    ----------
    command: list
        workbench command

    Returns
    -------
    None
    """
    command.insert(0, "wb_command")
    try:
        run = subprocess.run(command, capture_output=True)
    except subprocess.CalledProcessError as error:
        error_and_exit(False, f"Error in calling Workbench: {error}")
    except KeyboardInterrupt:
        run.kill()
    if run.returncode != 0:
        error_and_exit(False, f"Workbench failed due to {run.stderr}.")


def fslmaths_cmd(command: list) -> None:
    """
    Wrapper function around fslmaths

    Parameters
    ----------
    command: list
        fslmaths command

    Returns
    -------
    None
    """
    command.insert(0, "fslmaths")
    try:
        run = subprocess.run(command, capture_output=True)
    except subprocess.CalledProcessError as error:
        error_and_exit(False, f"Error in calling fslmaths: {error}")
    except KeyboardInterrupt:
        run.kill()

    if run.returncode != 0:
        error_and_exit(False, f"fslmaths failed due to {run.stderr}.")


def clean_target2(nfactpp_diretory: str, default_ref: str) -> None:
    """
    Wrapper function around a bunch
    of fslmaths commands to remove
    ventricles from target2 img.

    Parameters
    ----------
    nfactpp_diretory: str
       path to nfact directory
    default_ref: str
        default reference image

    Returns
    -------
    None
    """
    mask = os.path.join(
        os.getenv("FSLDIR"),
        "data",
        "atlases",
        "HarvardOxford",
        "HarvardOxford-sub-maxprob-thr0-2mm.nii.gz",
    )
    # Get ventricle from HarvardOxford
    fslmaths_cmd(
        [
            mask,
            "-thr",
            "14",
            "-uthr",
            "14",
            "-bin",
            f"{nfactpp_diretory}/ventricle_1",
        ]
    )
    # Get other ventricle from HarvardOxford
    fslmaths_cmd(
        [
            mask,
            "-thr",
            "3",
            "-uthr",
            "3",
            "-bin",
            f"{nfactpp_diretory}/ventricle_2",
        ]
    )
    # Add them together
    fslmaths_cmd(
        [
            f"{nfactpp_diretory}/ventricle_1",
            "-add",
            f"{nfactpp_diretory}/ventricle_2",
            "-bin",
            f"{nfactpp_diretory}/ven_mask",
        ]
    )
    # Dilate the mask
    fslmaths_cmd(
        [
            f"{nfactpp_diretory}/ven_mask",
            "-dilM",
            f"{nfactpp_diretory}/ven_mask_dilated",
        ]
    )
    # Invert the mask
    fslmaths_cmd(
        [f"{nfactpp_diretory}/ven_mask_dilated", "-binv", f"{nfactpp_diretory}/ven_inv"]
    )
    # Subtract the masks from the img by multiplication
    fslmaths_cmd(
        [
            default_ref,
            "-mul",
            f"{nfactpp_diretory}/ven_inv",
            f"{nfactpp_diretory}/target2",
        ]
    )
    # Remove all intermediate files
    files_to_delete = [
        "ven_mask_dilated",
        "ventricle_1",
        "ventricle_2",
        "ven_mask",
        "ven_inv",
    ]
    [
        os.remove(os.path.join(nfactpp_diretory, f"{file}.nii.gz"))
        for file in files_to_delete
    ]


def binarise_target2(target2_path: str) -> None:
    """
    Function to binarize target2 mask

    Parameters
    ----------
    target2_path: str
        path to target2 image

    Returns
    --------
    None
    """
    fslmaths_cmd([target2_path, "-thr", "1.0", target2_path])
    fslmaths_cmd([target2_path, "-bin", target2_path])


def create_sphere(seed_directory: str, nvertx: int) -> None:
    """
    Function to create sphere for downsampling

    Parameters
    -----------
    seed_directory: str
        directory where seeds are
    nvertx: int
        numb of vertexs

    Returns
    -------
    None
    """

    wb_cmd(
        [
            "-surface-create-sphere",
            f"{nvertx}",
            os.path.join(seed_directory, "R.surf.gii"),
        ]
    )
    wb_cmd(
        [
            "-surface-flip-lr",
            os.path.join(seed_directory, "R.surf.gii"),
            os.path.join(seed_directory, "L.surf.gii"),
        ]
    )
    wb_cmd(
        ["-set-structure", os.path.join(seed_directory, "R.surf.gii"), "CORTEX_RIGHT"]
    )
    wb_cmd(
        ["-set-structure", os.path.join(seed_directory, "L.surf.gii"), "CORTEX_LEFT"]
    )


def downsample_roi(
    atlas_roi: str,
    high_res_sphere: str,
    low_res_sphere: str,
    seed_directory: str,
) -> None:
    """
    Function to downsample ROI.

    Parameters
    ----------
    atlas_roi: str
        the ROI to downsample
    high_res_sphere: str
        the high resolution sphere
    low_res_sphere: str,
        the low resolution sphere
    seed_directory: str
        directory to save output in

    Returns
    -------
    None
    """
    wb_cmd(
        [
            "-metric-resample",
            atlas_roi,
            high_res_sphere,
            low_res_sphere,
            "BARYCENTRIC",
            os.path.join(seed_directory, os.path.basename(atlas_roi)),
        ]
    )
    wb_cmd(
        [
            "-metric-math",
            "round(m)",
            os.path.join(seed_directory, os.path.basename(atlas_roi)),
            "-var",
            "m",
            os.path.join(seed_directory, os.path.basename(atlas_roi)),
        ]
    )


def downsample_suface(
    surface: str,
    high_res_sphere: str,
    low_res_sphere: str,
    seed_directory: str,
) -> None:
    """
    Function to downsample surface.

    Parameters
    ----------
    surface: str
        the surface to downsample
    high_res_sphere: str
        the high resolution sphere
    low_res_sphere: str,
        the low resolution sphere
    seed_directory: str
        directory to save output in

    Returns
    -------
    None
    """
    wb_cmd(
        [
            "-surface-resample",
            surface,
            high_res_sphere,
            low_res_sphere,
            "BARYCENTRIC",
            os.path.join(seed_directory, os.path.basename(surface)),
        ]
    )


def downsample_surface_seed(
    surface: str,
    atlas_roi: str,
    high_res_sphere: str,
    side: str,
    seed_directory: str,
    nvertx: int,
) -> None:
    """
    Function to downsample surface seeds
    and the medial ROI.

    Parameters
    ----------
    surface: str
        the surface to downsample
    high_res_sphere: str
        the high resolution sphere
    side: str
        which hemishpere
    seed_directory: str
        directory to save output in
    nvertx: int
        number of vertexes to downsample to

    Returns
    -------
    None
    """

    create_sphere(seed_directory, nvertx)
    low_res_sphere = os.path.join(seed_directory, f"{side}.surf.gii")
    downsample_roi(atlas_roi, high_res_sphere, low_res_sphere, side, seed_directory)
    downsample_suface(surface, high_res_sphere, low_res_sphere, side, seed_directory)


def downsampling(
    seeds: list,
    rois: list,
    seed_directory: str,
    filetree: object,
    sub: str,
    nvertx: int,
    nvoxels: int,
) -> None:
    """
    Function to downsample seeds

    Parameters
    ----------
    seeds: list
        list of seeds
    rois: list
        list of rois
    filetree: object
        filetree object with paths to
        sphere
    seed_directory: str
        directory to save output in
    sub: str
        string of subject being processed
    nvertx: int
        number of vertexes to downsample to
    nvoxels: int
        voxel resolution to downsample to
    Returns
    -------
    None
    """
    for seed, roi in product(seeds, rois):
        if check_seeds_surfaces([seed]):
            side = (
                "L"
                if "L" in (seed_extension := os.path.basename(seed).split("."))
                else "R"
                if "R" in seed_extension
                else "U"
            )
            if side == "U":
                error_and_exit(
                    False,
                    "Unable to Downsample as cannot workout if seed is left or right side",
                )

            try:
                highres = os.path.join(
                    sub,
                    filetree_get_files(filetree, os.path.basename(sub), side, "sphere"),
                )
            except Exception as e:
                error_and_exit(
                    False,
                    f"Unable to find sphere in file structure due to {e}. \n Unable to downsample",
                )
            downsample_surface_seed(seed, roi, highres, side, seed_directory, nvertx)
        else:
            downsample_volume(
                seed,
                os.path.join(seed_directory, os.path.basename(seed)),
                nvoxels,
                seed,
                "nearestneighbour",
            )
