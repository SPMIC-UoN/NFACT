from pathlib import Path
import nibabel as nib
import numpy as np
import pytest
from nibabel import cifti2


@pytest.fixture
def mock_fsldir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """
    Fixture to create a mock FSLDIR environment with required binaries
    and standard reference image directories.

    Parameters
    ----------
    tmp_path: Path
        Pytest temporary directory path.
    monkeypatch: pytest.MonkeyPatch
        Pytest monkeypatch fixture.

    Returns
    -------
    Path: Path
        Path to the simulated FSLDIR directory.
    """
    fsl_directory = tmp_path / "mock_fsl"
    bin_directory = fsl_directory / "bin"
    standard_directory = fsl_directory / "data" / "standard"
    atlas_directory = fsl_directory / "data" / "atlases" / "HarvardOxford"

    bin_directory.mkdir(parents=True, exist_ok=True)
    standard_directory.mkdir(parents=True, exist_ok=True)
    atlas_directory.mkdir(parents=True, exist_ok=True)

    dummy_binaries = [
        "probtrackx2",
        "probtrackx2_gpu",
        "fsl_sub",
        "fsl_sub_report",
        "surf2surf",
        "flirt",
        "fslmaths",
    ]
    for binary_name in dummy_binaries:
        binary_file = bin_directory / binary_name
        binary_file.write_text("#!/bin/sh\nexit 0\n")
        binary_file.chmod(0o755)

    standard_volume = np.ones((10, 10, 10), dtype=np.float32)
    standard_image = nib.Nifti1Image(standard_volume, np.eye(4))
    standard_path = standard_directory / "MNI152_T1_2mm_brain.nii.gz"
    nib.save(standard_image, str(standard_path))

    atlas_volume = np.zeros((10, 10, 10), dtype=np.int32)
    atlas_volume[2:4, 2:4, 2:4] = 3
    atlas_volume[5:7, 5:7, 5:7] = 14
    atlas_image = nib.Nifti1Image(atlas_volume, np.eye(4))
    atlas_path = atlas_directory / "HarvardOxford-sub-maxprob-thr0-2mm.nii.gz"
    nib.save(atlas_image, str(atlas_path))

    monkeypatch.setenv("FSLDIR", str(fsl_directory))
    return fsl_directory


@pytest.fixture
def synthetic_nifti_seed(tmp_path: Path) -> str:
    """
    Fixture to create a synthetic 3D NIfTI volume seed mask.

    Parameters
    ----------
    tmp_path: Path
        Pytest temporary directory path.

    Returns
    -------
    str: str
        Absolute path to the created synthetic NIfTI mask.
    """
    seed_volume = np.zeros((10, 10, 10), dtype=np.float32)
    seed_volume[3:7, 3:7, 3:7] = 1.0
    seed_image = nib.Nifti1Image(seed_volume, np.eye(4))
    output_path = tmp_path / "seed_volume.nii.gz"
    nib.save(seed_image, str(output_path))
    return str(output_path)


@pytest.fixture
def synthetic_gifti_surface_and_roi(tmp_path: Path) -> dict:
    """
    Fixture to create synthetic left and right GIFTI surface and ROI files.

    Parameters
    ----------
    tmp_path: Path
        Pytest temporary directory path.

    Returns
    -------
    dict: dict
        Dictionary containing file paths for surfaces and ROI masks.
    """
    number_vertices = 50
    surface_data = np.ones((number_vertices, 1), dtype=np.float32)

    roi_data = np.ones(number_vertices, dtype=np.float32)
    roi_data[:10] = 0.0

    left_surface_file = tmp_path / "L.surf.gii"
    right_surface_file = tmp_path / "R.surf.gii"
    left_roi_file = tmp_path / "L.roi.shape.gii"
    right_roi_file = tmp_path / "R.roi.shape.gii"

    surface_darray = nib.gifti.GiftiDataArray(
        data=surface_data,
        datatype="NIFTI_TYPE_FLOAT32",
        intent=2001,
    )
    left_image = nib.GiftiImage(darrays=[surface_darray])
    right_image = nib.GiftiImage(darrays=[surface_darray])
    left_image.to_filename(str(left_surface_file))
    right_image.to_filename(str(right_surface_file))

    roi_darray = nib.gifti.GiftiDataArray(
        data=roi_data,
        datatype="NIFTI_TYPE_FLOAT32",
        intent=2001,
    )
    left_roi_image = nib.GiftiImage(darrays=[roi_darray])
    right_roi_image = nib.GiftiImage(darrays=[roi_darray])
    left_roi_image.to_filename(str(left_roi_file))
    right_roi_image.to_filename(str(right_roi_file))

    return {
        "seeds": [str(left_surface_file), str(right_surface_file)],
        "rois": [str(left_roi_file), str(right_roi_file)],
    }


@pytest.fixture
def synthetic_lookup_and_coords(tmp_path: Path) -> dict:
    """
    Fixture to create synthetic lookup tractspace volume and coordinate text files.

    Parameters
    ----------
    tmp_path: Path
        Pytest temporary directory path.

    Returns
    -------
    dict: dict
        Dictionary containing paths to lookup volume and coordinates files.
    """
    tractspace_volume = np.zeros((10, 10, 10), dtype=np.int32)
    tractspace_coordinates = []
    lookup_index = 1
    for coord_x in range(2, 6):
        for coord_y in range(2, 6):
            for coord_z in range(2, 6):
                tractspace_volume[coord_x, coord_y, coord_z] = lookup_index
                tractspace_coordinates.append([coord_x, coord_y, coord_z])
                lookup_index += 1

    lookup_image = nib.Nifti1Image(tractspace_volume, np.eye(4))
    lookup_file = tmp_path / "lookup_tractspace_fdt_matrix2.nii.gz"
    nib.save(lookup_image, str(lookup_file))

    tract_coordinates_array = np.array(tractspace_coordinates, dtype=int)
    tract_coords_file = tmp_path / "tract_space_coords_for_fdt_matrix2"
    np.savetxt(str(tract_coords_file), tract_coordinates_array, fmt="%i")

    seed_coordinates = []
    for voxel_index in range(20):
        seed_coordinates.append([voxel_index % 10, (voxel_index * 2) % 10, 1, 0, 1])
    for voxel_index in range(20):
        seed_coordinates.append([voxel_index % 10, (voxel_index * 3) % 10, 2, 1, 1])

    coords_array = np.array(seed_coordinates, dtype=int)
    coords_file = tmp_path / "coords_for_fdt_matrix2"
    np.savetxt(str(coords_file), coords_array, fmt="%i")

    return {
        "lookup_volume": str(lookup_file),
        "tract_coords": str(tract_coords_file),
        "coords": str(coords_file),
        "num_tract_voxels": len(tractspace_coordinates),
        "num_seed_voxels": len(seed_coordinates),
    }


@pytest.fixture
def synthetic_cifti_dscalar(
    tmp_path: Path,
    synthetic_gifti_surface_and_roi: dict,
) -> str:
    """
    Fixture to create a synthetic CIFTI dscalar image file.

    Parameters
    ----------
    tmp_path: Path
        Pytest temporary directory path.
    synthetic_gifti_surface_and_roi: dict
        Dictionary of surface and ROI file paths.

    Returns
    -------
    str: str
        Absolute path to the created CIFTI dscalar file.
    """
    left_surface_mask = np.ones(50, dtype=bool)
    right_surface_mask = np.ones(50, dtype=bool)

    brain_model_left = cifti2.BrainModelAxis.from_mask(
        left_surface_mask, name="CIFTI_STRUCTURE_CORTEX_LEFT"
    )
    brain_model_right = cifti2.BrainModelAxis.from_mask(
        right_surface_mask, name="CIFTI_STRUCTURE_CORTEX_RIGHT"
    )
    combined_brain_model = brain_model_left + brain_model_right

    scalar_axis = cifti2.cifti2_axes.ScalarAxis(np.array(["comp_0", "comp_1"]))
    cifti_header = cifti2.Cifti2Header.from_axes((scalar_axis, combined_brain_model))

    cifti_matrix = np.random.rand(2, 100).astype(np.float32)
    cifti_image = cifti2.Cifti2Image(cifti_matrix, cifti_header)

    output_cifti_path = tmp_path / "synthetic.dscalar.nii"
    nib.save(cifti_image, str(output_cifti_path))
    return str(output_cifti_path)
