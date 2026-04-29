import pathlib
import os
import nibabel as nb
from nibabel import cifti2
import numpy as np
import re
from NFACT.base.utils import error_and_exit, nprint, colours


class ImageError(Exception):
    """
    Custom Exception class
    to raise errors with imaging
    problems.
    """

    pass


def imaging_type(path: str) -> str:
    """
    Function to return imaging
    type based on extension.

    Parameters
    ----------
    path: str
        path to str

    Return
    ------
    str: string
        str of nifit or gifti
    """
    file_extensions = get_imaging_details_from_path(path)["file_extensions"]
    mapping_type = {".dscalar": "cifti", ".nii": "nifti", ".gii": "gifti"}
    img_type = next(
        (mapping_type[ext] for ext in file_extensions if ext in mapping_type), None
    )
    error_and_exit(
        img_type,
        "Unable to determine imaging type. Please make sure files have correct imging extension",
    )
    return img_type


def mat2vol(
    matrix: np.ndarray, x_y_z_coords: np.array, img_dim: tuple, number_of_comp: int
) -> np.ndarray:
    """
    Function to reshape a matrix
    to be saved as a volume.

    Parameters
    ----------
    matrix: np.ndarray
        array to  be saved as volume
    x_y_z_coords: np.ndarray
        array of coords
    img_dim: tuple
        dim of image
    lut_vol: ndarray
        data from lookup volume

    Returns
    -------
    matvol: np.ndarray
        array reformatted to be converted to
        a volume
    """
    matvol = np.zeros(
        (img_dim[0], img_dim[1], img_dim[2], number_of_comp), dtype=matrix.dtype
    )
    x, y, z = x_y_z_coords.T
    matvol[x, y, z, :] = matrix.T
    return matvol


def get_imaging_details_from_path(path: str) -> dict:
    """
    Function to return imaging suffix,
    subject and file from a path.

    Parameters
    ----------
    path: str
        path as a string

    Returns
    --------
    dict: dictionary
        dict of file extension,
        subject and file.
    """
    return {
        "file_extensions": pathlib.Path(path).suffixes,
        "subject": re.findall(r"\b(sub(?:ject)?-?\d+)\b", path),
        "file": os.path.basename(path),
    }


def check_files_are_imaging_files(path: str) -> bool:
    """
    Function to check that imaging files
    are actually imaging files.

    Parameters
    ----------
    path: str
        file path

    Returns
    -------
    None
    """
    file_details = get_imaging_details_from_path(path)
    error_and_exit(
        [
            file
            for file in file_details["file_extensions"]
            if file in [".gii", ".nii", ".mat"]
        ],
        f"{file_details['file']} for {file_details['subject']} is an incorrect file type",
    )


def save_volume(base_volume: object, data_to_save: np.ndarray, filename: str) -> None:
    """
    Function wrapper around saving Nifti1Image

    Parameters
    ----------
    base_volume: object
        Nifti1Image to get affine
        and header information
    data_to_save: np.ndarray
        np array of data to save to
        volume
    filename: str
        string of name of volume
        to save. Must include full
        filepath

    Returns
    -------
    None
    """
    nb.Nifti1Image(
        data_to_save.astype(float), header=base_volume.header, affine=base_volume.affine
    ).to_filename(filename)


def save_white_matter(
    white_matter_components: np.ndarray,
    path_to_lookup_vol: str,
    coords_path: str,
    out_file: str,
) -> None:
    """
    Function to save white matter compponents
    as a volume.

    Parameters
    ----------
    white_matter_components: np.ndarray
        The white matter components from ICA/NFM
        to save
    path_to_lookup_vol: str
        path to look up volume from probtrackx
    coords_path: str
        path to coords text file
    out_file: str
        string to path to save images
    Returns
    -------
    None

    """

    lut_vol = nb.load(path_to_lookup_vol)
    coords = np.loadtxt(coords_path, dtype=int)
    white_matter_vol = mat2vol(
        white_matter_components, coords, lut_vol.shape, white_matter_components.shape[0]
    )
    save_volume(lut_vol, white_matter_vol, f"{out_file}.nii.gz")


def save_grey_matter_volume(
    grey_matter_component: np.ndarray,
    file_name: str,
    seed: str,
    x_y_z_coordinates: np.ndarray,
) -> None:
    """

    Function to save grey matter component as
    a volume

    Parameters
    ----------
    grey_matter_component: np.ndarray
        grey matter component for a
        single seed
    file_name: str
        file name
    seed: str
        path to seed
    x_y_z_coordinates: np.ndarray
        array of x, y, z co-ordinates

    Returns
    -------
    None
    """

    vol = nb.load(seed)
    xyz_idx = np.ravel_multi_index(x_y_z_coordinates.T, vol.shape)
    ncols = grey_matter_component.shape[1]
    out = np.zeros(vol.shape + (ncols,)).reshape(-1, ncols)
    for idx, col in enumerate(grey_matter_component.T):
        out[xyz_idx, idx] = col
    save_volume(vol, out.reshape(vol.shape + (ncols,)), file_name)


def add_medial_wall(m_wall: np.ndarray, grey_component: np.ndarray) -> np.ndarray:
    """
    Function to add in an empty medial wall
    to the grey matter component

    Parameters
    ----------
    m_wall: np.ndarry
        medial wall data
    grey_component: np.ndarray
        grey matter component
    Returns
    --------
    grey_matter_component: np.ndarray
        grey matter component with empty
        medial wall
    """
    grey_matter_component = np.zeros((m_wall.shape[0], grey_component.shape[1]))
    grey_matter_component[m_wall == 1, :] = grey_component
    return grey_matter_component


def save_grey_matter_gifit(
    grey_component: np.ndarray, file_name: str, seed: str, roi: str
) -> None:
    """
    Function to save grey matter as gifti

    Parameters
    ----------
    grey_matter_component: np.ndarray
        grey matter component for a
        single seed
    file_name: str
        file name
    seed: str
        path to seed
    roi: str
        str to roi path

    Returns
    -------
    None
    """
    surf = nb.load(seed)
    m_wall = nb.load(roi).darrays[0].data != 0
    grey_matter_component = add_medial_wall(m_wall, grey_component)

    darrays = [
        nb.gifti.GiftiDataArray(
            data=np.array(col, dtype=float),
            datatype="NIFTI_TYPE_FLOAT32",
            intent=2001,
            meta=surf.darrays[0].meta,
        )
        for col in grey_matter_component.T
    ]
    nb.GiftiImage(darrays=darrays, meta=surf.darrays[0].meta).to_filename(
        f"{file_name}.func.gii"
    )


def rename_seed(seeds: list) -> list:
    """
    Function to renmae seed. Either
    will rename it as left_seed or
    right_seed. Or removes unecessary extensions

    Parameters
    ----------
    seed: list
        list of seed names

    Returns
    -------
    seed: list
        list of processed seed names.
    """

    return [
        (
            "left_seed"
            if "L" in (seed_extension := os.path.basename(seed).split("."))
            else "right_seed"
            if "R" in seed_extension
            else re.sub(r".gii|.surf", "", os.path.basename(seed))
        )
        for seed in seeds
        if (seed_extension := seed.split("."))
    ]


def name_seed(seed: str, nfact_path: str, directory: str, prefix: str, dim: int) -> str:
    """
    Function to return file path of seed.
    Correctly names seed

    Parameters
    -----------
    seed: str
        name of seed
    nfact_path: str
        path to nfact directory
    directory: str
        path to directory to save
        file
    prefix:
        prefix of seed
    dim: int
        number of dimensions from
        decomp

    Returns
    -------
    str: string
        renamed seed
    """
    seed_name = rename_seed([seed])[0]
    file_name = f"{prefix}_dim{dim}_{seed_name}"
    return os.path.join(
        nfact_path,
        directory,
        file_name,
    )


def save_grey_matter_components(
    grey_matter_components: np.ndarray,
    nfact_path: str,
    seeds: list,
    directory: str,
    dim: int,
    coord_path: str,
    roi: list,
    prefix: str = "G",
    cifti_save: bool = False,
) -> None:
    """
    Function wrapper to save grey matter
    components.

    Parameters
    ----------
    grey_matter_components: ndarray
        grey_matter_component matrix
    nfact_path: str
        str to nfact directory
    seeds: list
        list of seeds
    directory: str
        str of directory to save component to
    dim: int
        number of dimensions
        used for naming output
    roi: list
        list of roi path
    cifti_save: bool
        should save type be

    Returns
    -------
    None
    """

    coord_mat2 = np.loadtxt(coord_path, dtype=int)
    seeds_id = coord_mat2[:, -2]
    if cifti_save:
        try:
            save_cifti(
                seeds,
                roi,
                grey_matter_components,
                coord_mat2,
                seeds_id,
                os.path.join(nfact_path, directory, f"{prefix}_dim{dim}.dscalar.nii"),
            )
            return None
        except Exception as e:
            col = colours()
            nprint(f"{col['red']} Unable to save as Cifti due to: {e}")
            nprint(f"Saving as gii/nii.gz files{col['reset']}")
    for idx, seed in enumerate(seeds):
        save_type = imaging_type(seed)
        mask_to_get_seed = seeds_id == idx
        grey_matter_seed = grey_matter_components[mask_to_get_seed, :]
        file_name = re.sub(
            r"_gii|_nii", "", name_seed(seed, nfact_path, directory, prefix, dim)
        ).replace("_gz", "")
        if save_type == "gifti":
            save_grey_matter_gifit(grey_matter_seed, file_name, seed, roi[idx])
        elif save_type == "nifti":
            save_grey_matter_volume(
                grey_matter_seed, file_name, seed, coord_mat2[mask_to_get_seed, :3]
            )
        else:
            raise ValueError(f"Unsupported imaging type: {save_type}")


def add_nifti(seeds: list, brainmodel: object, coords: np.ndarray) -> object:
    """
    Function to added
    nifti component to cifti

    Parameters
    -----------
    seeds: list
        list of seeds (assumes surfaces)
    brainmodel: BrainModelAxis
        brain model axis to
        add to
    coords: np.ndarray
        array of ndarry co-ordinates

    Returns
    -------
    brainmodel: BrainModelAxis
        brain model axis

    """
    seed_ref = nb.load(seeds[2])
    for idx, seed in enumerate(seeds):
        if idx < 2:
            continue
        seed_name = re.sub(r".nii.gz|.nii", "", os.path.basename(seed))
        if "CIFTI_STRUCTURE_" not in seed_name:
            seed_name = "OTHER"
        number_of_voxels = coords[coords[:, 3] == idx][:, :3]
        brainmodel += cifti2.BrainModelAxis(
            name=seed_name,
            voxel=number_of_voxels,
            affine=seed_ref.affine,
            volume_shape=seed_ref.shape,
        )
    return brainmodel


def create_surface_brain_masks(left_seed: np.ndarray, right_seed: np.ndarray) -> object:
    """
    Function to create surface brain model axis
    from numpy array

    Parameters
    ----------
    left_seed: np.ndarray
        left surface data
    right_seed: np.ndarray
        right surface data

    Returns
    -------
    brainmodel: BrainModelAxis
        brain model axis
    """
    bm_l = cifti2.BrainModelAxis.from_mask(
        left_seed, name="CIFTI_STRUCTURE_CORTEX_LEFT"
    )
    bm_r = cifti2.BrainModelAxis.from_mask(
        right_seed, name="CIFTI_STRUCTURE_CORTEX_RIGHT"
    )
    return bm_l + bm_r


def cifti_surfaces(seeds: list) -> object:
    """
    Function to add surfaces
    to brain model axis from mask

    Parameters
    ----------
    seeds: list
        list of seeds, expected that the first
        seed is the left side
        and right is second

    Returns
    -------
    brainmodel: BrainModelAxis
        brain model axis
    """

    left_seed = nb.load(seeds[0]).darrays[0].data != 0
    right_seed = nb.load(seeds[1]).darrays[0].data != 0
    return create_surface_brain_masks(left_seed[:, 0], right_seed[:, 0])


def cifit_medial_wall(
    grey_component: np.ndarray, rois: list, seeds_id: np.ndarray
) -> np.ndarray:
    """
    Function for adding in medial wall
    to grey_component to save as a cifti

    Parameters
    ----------
    grey_matter_component: np.ndarray
        grey matter component
    rois: list
        list of rois. Expected to match
        the first two elements of
        the seeds
    seeds_id: np.ndarray
        seed id from coords file
    Returns
    -------
    np.ndarray: array
        grey matter component
        with added in medial wall

    """
    m_wall = np.concatenate([(nb.load(roi).darrays[0].data != 0) for roi in rois])
    gm = add_medial_wall(m_wall, grey_component[(seeds_id == 0) | (seeds_id == 1), :])
    return np.concatenate([gm, grey_component[(seeds_id != 0) & (seeds_id != 1), :]])


def create_dscalar(
    cifti_data: np.ndarray, scalar_shape: int, brainmodel: object
) -> object:
    """
    Function to create dscalar

    Parameters
    ----------
    cifti_data: np.ndarray
        cifti data to store
    scalar_shape: int
        shape for the dscalar
    brainmodel: BrainModelAxis
        brain model axis

    Returns
    --------
    object: Cifti2Image
        Cifti2Image with
        correct headers
    """
    scalar = cifti2.cifti2_axes.ScalarAxis(
        np.linspace(0, scalar_shape, scalar_shape, dtype="int")
    )
    header = cifti2.Cifti2Header.from_axes((scalar, brainmodel))
    return cifti2.Cifti2Image(cifti_data, header)


def save_cifti(
    seeds: list,
    rois: list,
    grey_matter_component: np.ndarray,
    coords: np.ndarray,
    seeds_id: np.ndarray,
    save_path: str,
) -> None:
    """
    Function to create and save a cifti
    dscalar file

    Parameters
    ----------
    seeds: list,
        list of seeds, expected that the first
        seed is the left side
        and right is second
    rois: list
        list of rois. Expected to match
        the first two elements of
        the seeds
    grey_matter_component: np.ndarray
        grey matter component
    coords: np.ndarray
        coordinates matrix
    seeds_id: np.ndarray
        seed id from coords file
    save_path: str
        path to save file to

    Returns
    -------
    None
    """
    grey_comp = cifit_medial_wall(grey_matter_component, rois, seeds_id)
    brainmodel = cifti_surfaces(seeds)
    if len(seeds) > 2:
        brainmodel = add_nifti(seeds, brainmodel, coords)
    dscalar_object = create_dscalar(grey_comp.T, grey_comp.shape[1], brainmodel)
    nb.save(dscalar_object, save_path)


def surf_data_from_cifti(data: np.ndarray, axis: object, surf_name: str) -> np.ndarray:
    """
    Function to get surface data from cifti

    Parameters
    ----------
    data: np.ndarray
        np.array of imaging data
    axis: nbabel.cifti2.cifti2_axes.BrainModelAxis
    surf_name: str
        string of surface name.

    Returns
    -------
    surf_data: np.ndarray
        np.array of surface data
    """
    for name, data_indices, model in axis.iter_structures():
        if name == surf_name:
            data = data.T[data_indices]
            vtx_indices = model.vertex
            surf_data = np.zeros(
                (vtx_indices.max() + 1,) + data.shape[1:], dtype=data.dtype
            )
            surf_data[vtx_indices] = data
            return surf_data


def volume_from_cifti(data: np.ndarray, axis: object) -> object:
    """
    Function to return the nifti from a cifti

    Parameters
    ----------
    data: np.ndarray
        np.array of imaging data
    axis: nbabel.cifti2.cifti2_axes.BrainModelAxis

    Returns
    -------
    object: nb.Nifti1Image
        nifti image
    """
    data = data.T[axis.volume_mask]
    vox_indices = tuple(axis.voxel[axis.volume_mask].T)
    vol_data = np.zeros(axis.volume_shape + data.shape[1:], dtype=data.dtype)
    vol_data[vox_indices] = data
    return nb.Nifti1Image(vol_data, axis.affine)


def get_cifti_data(img_path: object) -> dict:
    """
    Function to get cifti data

    Parameters
    ----------
    img_path: path
        path to cifti object

    Returns
    -------
    dict: dictionary
        dict of volume and L/R
        surfaces
    """
    img = nb.load(img_path)
    data = img.get_fdata(dtype=np.float32)
    brain_models = img.header.get_axis(1)
    cifti_data = {
        "L_surf": surf_data_from_cifti(
            data, brain_models, "CIFTI_STRUCTURE_CORTEX_LEFT"
        ),
        "R_surf": surf_data_from_cifti(
            data, brain_models, "CIFTI_STRUCTURE_CORTEX_RIGHT"
        ),
    }
    try:
        cifti_data["vol"] = volume_from_cifti(data, brain_models)
        return cifti_data
    except Exception:
        return cifti_data


def get_volume_data(img_path: str) -> np.ndarray:
    """
    Function to get volume data

    Parameters
    -----------
    img_path: str
        str to volume image

    Returns
    -------
    np.ndarray: array
        array of volume data
    """
    vol = nb.load(img_path)
    return vol.get_fdata().astype(np.int32)


def get_surface_data(img_path: str) -> np.ndarray:
    """
    Function to get surface data

    Parameters
    -----------
    img_path: str
        str to surface image

    Returns
    -------
    np.ndarray: array
        array of surface data
    """
    surface = nb.load(img_path)

    return np.array(
        [surface.darrays[idx].data for idx, _ in enumerate(surface.darrays)]
    )
