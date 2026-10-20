import os
from pathlib import Path
import lz4.frame
import nibabel as nib
import numpy as np
import pytest
from NFACT.base.imagehandling import (
    ImageError,
    add_medial_wall,
    add_nifti,
    check_files_are_imaging_files,
    cifit_medial_wall,
    create_dscalar,
    create_surface_brain_masks,
    get_cifti_data,
    get_imaging_details_from_path,
    get_surface_data,
    get_volume_data,
    imaging_type,
    mat2vol,
    name_seed,
    rename_seed,
    save_cifti,
    save_grey_matter_components,
    save_grey_matter_gifit,
    save_grey_matter_volume,
    save_volume,
    save_white_matter,
    surf_data_from_cifti,
    volume_from_cifti,
)
from NFACT.base.matrix_handling import (
    comp_disk_save,
    load_fdt_matrix,
    load_single_matrix,
    normalise_components,
    normalise_matrix,
    read_in_matrix,
    save_matrix,
    threshold_grey_components,
    thresholding,
    thresholding_components,
)
import scipy.sparse as sps


def test_normalise_components() -> None:
    """
    Function to test normalise_components standardises components.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    grey_matter = np.random.rand(50, 5) * 10.0 + 2.0
    white_matter = np.random.rand(5, 40) * 8.0 + 1.0

    normalised_dictionary = normalise_components(grey_matter, white_matter)
    assert "grey_matter" in normalised_dictionary
    assert "white_matter" in normalised_dictionary

    grey_normalised = normalised_dictionary["grey_matter"]
    white_normalised = normalised_dictionary["white_matter"]

    assert np.allclose(grey_normalised.mean(axis=0), 0.0, atol=1e-5)
    assert np.allclose(grey_normalised.std(axis=0), 1.0, atol=1e-5)
    assert np.allclose(white_normalised.mean(axis=1), 0.0, atol=1e-5)
    assert np.allclose(white_normalised.std(axis=1), 1.0, atol=1e-5)


def test_matrix_loading_and_normalisation(tmp_path: Path) -> None:
    """
    Function to test read_in_matrix, load_single_matrix, and load_fdt_matrix.

    Parameters
    ----------
    tmp_path: Path
        Pytest temporary directory path.

    Returns
    -------
    None
    """
    matrix_folder = tmp_path / "omatrix2"
    matrix_folder.mkdir()

    waytotal_file = matrix_folder / "waytotal"
    waytotal_file.write_text("1000000\n")

    matrix_rows = np.array(
        [
            [1, 1, 10],
            [1, 2, 20],
            [2, 2, 30],
            [2, 2, 0],
        ]
    )

    dot_file = matrix_folder / "fdt_matrix2.dot"
    np.savetxt(str(dot_file), matrix_rows, fmt="%i")

    lz4_file = matrix_folder / "fdt_matrix2.dot.lz4"
    with open(str(dot_file), "rb") as input_file:
        with lz4.frame.open(str(lz4_file), "wb") as output_compressed:
            output_compressed.write(input_file.read())

    raw_dot_matrix = read_in_matrix(str(dot_file))
    raw_lz4_matrix = read_in_matrix(str(lz4_file))
    assert np.array_equal(raw_dot_matrix, raw_lz4_matrix)

    sparse_matrix = load_single_matrix(str(dot_file))
    assert isinstance(sparse_matrix, sps.csc_matrix)
    assert sparse_matrix.shape == (2, 2)

    dense_matrix = load_fdt_matrix(str(dot_file))
    dense_lz4_matrix = load_fdt_matrix(str(lz4_file))
    assert isinstance(dense_matrix, np.ndarray)
    assert dense_matrix.shape == (2, 2)
    assert np.array_equal(dense_matrix, dense_lz4_matrix)

    direct_sparse = sps.csc_matrix([[1.0, 2.0], [3.0, 4.0]])
    scaled_sparse = normalise_matrix(str(waytotal_file), direct_sparse)
    expected_scale = 1e8 / 1000000.0
    assert np.isclose(scaled_sparse[0, 0], 1.0 * expected_scale)


def test_matrix_saving_and_comp_disk_save(tmp_path: Path) -> None:
    """
    Function to test save_matrix and comp_disk_save.

    Parameters
    ----------
    tmp_path: Path
        Pytest temporary directory path.

    Returns
    -------
    None
    """
    sample_matrix = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32)
    save_matrix(sample_matrix, str(tmp_path), "test_matrix")
    saved_path = tmp_path / "test_matrix.npy"
    assert saved_path.exists()
    assert np.array_equal(np.load(str(saved_path)), sample_matrix)

    comp_disk_save(
        sample_matrix,
        str(tmp_path),
        "Failed image fallback message",
        "disk_comp",
        to_exit=False,
    )
    assert (tmp_path / "disk_comp.npy").exists()


def test_thresholding_methods() -> None:
    """
    Function to test thresholding and threshold_grey_components.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    component_row = np.array([[0.0, 1.0, 2.0, 10.0, 100.0]], dtype=np.float32)
    thresholded_array = thresholding(component_row.copy(), zscore_val=1)
    assert thresholded_array[0, 0] == 0.0
    assert thresholded_array[0, 4] == 100.0

    grey_components = np.array(
        [[1.0, 2.0], [10.0, 20.0], [1.0, 1.0], [50.0, 60.0]], dtype=np.float32
    )
    coordinates_data = np.array(
        [[0, 0, 0, 0, 0], [1, 1, 1, 0, 0], [2, 2, 2, 1, 0], [3, 3, 3, 1, 0]]
    )
    coords_temp_file = Path("/tmp/test_coords_file.txt")
    np.savetxt(str(coords_temp_file), coordinates_data, fmt="%i")

    thresholded_grey = threshold_grey_components(
        grey_components.copy(),
        str(coords_temp_file),
        ["seed_0", "seed_1"],
        zscore_val=1,
    )
    assert thresholded_grey.shape == grey_components.shape

    components_dict = {
        "white_components": np.array([[1.0, 50.0], [2.0, 60.0]], dtype=np.float32),
        "grey_components": grey_components.copy(),
    }
    wrapped_components = thresholding_components(
        1, str(coords_temp_file), ["seed_0", "seed_1"], components_dict
    )
    assert "white_components" in wrapped_components
    assert "grey_components" in wrapped_components

    coords_temp_file.unlink(missing_ok=True)


def test_imaging_details_and_type_check() -> None:
    """
    Function to test imaging_type and get_imaging_details_from_path.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    assert imaging_type("/study/file.nii.gz") == "nifti"
    assert imaging_type("/study/file.func.gii") == "gifti"
    assert imaging_type("/study/file.dscalar.nii") == "cifti"

    with pytest.raises(SystemExit) as exit_info:
        imaging_type("/study/file.txt")
    assert exit_info.value.code == 1

    details = get_imaging_details_from_path("/study/sub-05/T1w.nii.gz")
    assert details["file"] == "T1w.nii.gz"
    assert details["subject"] == ["sub-05"]
    assert ".nii" in details["file_extensions"]

    check_files_are_imaging_files("/study/sub-01/brain.nii.gz")
    check_files_are_imaging_files("/study/sub-01/surface.gii")

    with pytest.raises(SystemExit):
        check_files_are_imaging_files("/study/sub-01/invalid.pdf")


def test_image_error_exception() -> None:
    """
    Function to test ImageError custom exception.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    with pytest.raises(ImageError):
        raise ImageError("Custom imaging exception")


def test_mat2vol_and_save_white_matter(
    tmp_path: Path, synthetic_lookup_and_coords: dict
) -> None:
    """
    Function to test mat2vol and save_white_matter.

    Parameters
    ----------
    tmp_path: Path
        Pytest temporary directory path.
    synthetic_lookup_and_coords: dict
        Dictionary of lookup volume and coords.

    Returns
    -------
    None
    """
    number_voxels = synthetic_lookup_and_coords["num_tract_voxels"]
    number_components = 2
    white_matrix = np.ones((number_components, number_voxels), dtype=np.float32)

    output_base = tmp_path / "test_wm"
    save_white_matter(
        white_matrix,
        synthetic_lookup_and_coords["lookup_volume"],
        synthetic_lookup_and_coords["tract_coords"],
        str(output_base),
    )
    saved_volume_path = f"{output_base}.nii.gz"
    assert os.path.exists(saved_volume_path)

    loaded_volume_data = get_volume_data(saved_volume_path)
    assert loaded_volume_data.shape == (10, 10, 10, number_components)


def test_save_grey_matter_volume_and_gifti(
    tmp_path: Path,
    synthetic_nifti_seed: str,
    synthetic_gifti_surface_and_roi: dict,
) -> None:
    """
    Function to test save_grey_matter_volume and save_grey_matter_gifit.

    Parameters
    ----------
    tmp_path: Path
        Pytest temporary directory path.
    synthetic_nifti_seed: str
        Path to synthetic volume seed.
    synthetic_gifti_surface_and_roi: dict
        Dictionary of synthetic surface and ROI paths.

    Returns
    -------
    None
    """
    coordinates = np.array([[3, 3, 3], [4, 4, 4], [5, 5, 5]], dtype=int)
    grey_volume_component = np.array(
        [[10.0, 20.0], [30.0, 40.0], [50.0, 60.0]], dtype=np.float32
    )

    volume_output_file = tmp_path / "gm_vol_out.nii.gz"
    save_grey_matter_volume(
        grey_volume_component,
        str(volume_output_file),
        synthetic_nifti_seed,
        coordinates,
    )
    assert volume_output_file.exists()

    left_surface_file = synthetic_gifti_surface_and_roi["seeds"][0]
    left_roi_file = synthetic_gifti_surface_and_roi["rois"][0]
    grey_surface_component = np.ones((40, 2), dtype=np.float32)

    gifti_output_base = tmp_path / "gm_gifti_out"
    save_grey_matter_gifit(
        grey_surface_component,
        str(gifti_output_base),
        left_surface_file,
        left_roi_file,
    )
    saved_gifti_file = f"{gifti_output_base}.func.gii"
    assert os.path.exists(saved_gifti_file)
    surface_arrays = get_surface_data(saved_gifti_file)
    assert len(surface_arrays) == 2


def test_add_medial_wall() -> None:
    """
    Function to test add_medial_wall inserts zero-padding for non-wall vertices.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    medial_wall_mask = np.array([0, 1, 1, 0, 1], dtype=np.int32)
    grey_component = np.array(
        [[10.0, 20.0], [30.0, 40.0], [50.0, 60.0]], dtype=np.float32
    )
    expanded_wall = add_medial_wall(medial_wall_mask, grey_component)
    assert expanded_wall.shape == (5, 2)
    assert expanded_wall[0, 0] == 0.0
    assert expanded_wall[1, 0] == 10.0


def test_mat2vol_and_save_volume(tmp_path: Path, synthetic_nifti_seed: str) -> None:
    """
    Function to test mat2vol and save_volume.

    Parameters
    ----------
    tmp_path: Path
        Pytest temporary directory path.
    synthetic_nifti_seed: str
        Path to synthetic NIfTI volume seed.

    Returns
    -------
    None
    """
    matrix_sample = np.ones((2, 3), dtype=np.float32)
    coords_sample = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]], dtype=int)
    volume_sample = mat2vol(matrix_sample, coords_sample, (10, 10, 10), 2)
    assert volume_sample.shape == (10, 10, 10, 2)
    assert volume_sample[1, 2, 3, 0] == 1.0

    base_volume_image = nib.load(synthetic_nifti_seed)
    data_array = np.zeros((10, 10, 10), dtype=np.float32)
    output_path = tmp_path / "custom_vol.nii.gz"
    save_volume(base_volume_image, data_array, str(output_path))
    assert output_path.exists()


def test_rename_and_name_seed(tmp_path: Path) -> None:
    """
    Function to test rename_seed and name_seed.

    Parameters
    ----------
    tmp_path: Path
        Pytest temporary directory path.

    Returns
    -------
    None
    """
    renamed_seeds = rename_seed(
        ["/path/L.pial.surf.gii", "/path/R.white.surf.gii", "/path/subcort.nii.gz"]
    )
    assert renamed_seeds == ["left_seed", "right_seed", "subcort.nii.gz"]

    generated_seed_path = name_seed(
        "/path/L.surf.gii", str(tmp_path), "components/NMF", "G", 50
    )
    assert "G_dim50_left_seed" in generated_seed_path


def test_cifti_operations_and_helpers(
    tmp_path: Path,
    synthetic_gifti_surface_and_roi: dict,
    synthetic_lookup_and_coords: dict,
    synthetic_nifti_seed: str,
) -> None:
    """
    Function to test CIFTI creation, medial wall handling, and data extraction.

    Parameters
    ----------
    tmp_path: Path
        Pytest temporary directory path.
    synthetic_gifti_surface_and_roi: dict
        Dictionary of surface and ROI paths.
    synthetic_lookup_and_coords: dict
        Dictionary of lookup volume and coords.
    synthetic_nifti_seed: str
        Path to synthetic volume seed.

    Returns
    -------
    None
    """
    left_mask = np.ones(50, dtype=bool)
    right_mask = np.ones(50, dtype=bool)
    brain_masks = create_surface_brain_masks(left_mask, right_mask)
    assert brain_masks is not None

    grey_components = np.ones((80, 2), dtype=np.float32)
    seeds_id = np.array([0] * 40 + [1] * 40)
    medial_walled = cifit_medial_wall(
        grey_components, synthetic_gifti_surface_and_roi["rois"], seeds_id
    )
    assert medial_walled.shape == (100, 2)

    cifti_dscalar_object = create_dscalar(medial_walled.T, 2, brain_masks)
    assert cifti_dscalar_object is not None

    cifti_save_path = tmp_path / "cifti_test.dscalar.nii"
    nib.save(cifti_dscalar_object, str(cifti_save_path))

    extracted_cifti = get_cifti_data(str(cifti_save_path))
    assert "L_surf" in extracted_cifti
    assert "R_surf" in extracted_cifti
    assert extracted_cifti["L_surf"].shape[0] == 50
    assert extracted_cifti["R_surf"].shape[0] == 50

    loaded_cifti = nib.load(str(cifti_save_path))
    cifti_raw_data = loaded_cifti.get_fdata(dtype=np.float32)
    brain_models_axis = loaded_cifti.header.get_axis(1)
    left_surface_extracted = surf_data_from_cifti(
        cifti_raw_data, brain_models_axis, "CIFTI_STRUCTURE_CORTEX_LEFT"
    )
    assert left_surface_extracted is not None

    combined_seeds = [
        synthetic_gifti_surface_and_roi["seeds"][0],
        synthetic_gifti_surface_and_roi["seeds"][1],
        synthetic_nifti_seed,
    ]
    volume_coords = np.array([[3, 3, 3, 2, 0], [4, 4, 4, 2, 0]], dtype=int)
    brain_masks_with_vol = add_nifti(combined_seeds, brain_masks, volume_coords)
    cifti_with_vol_object = create_dscalar(
        np.ones((2, 102), dtype=np.float32), 2, brain_masks_with_vol
    )
    cifti_vol_path = tmp_path / "cifti_with_vol.dscalar.nii"
    nib.save(cifti_with_vol_object, str(cifti_vol_path))

    loaded_vol_cifti = nib.load(str(cifti_vol_path))
    extracted_vol_image = volume_from_cifti(
        loaded_vol_cifti.get_fdata(dtype=np.float32),
        loaded_vol_cifti.header.get_axis(1),
    )
    assert extracted_vol_image is not None

    cifti_out_direct = tmp_path / "cifti_direct.dscalar.nii"
    save_cifti(
        synthetic_gifti_surface_and_roi["seeds"],
        synthetic_gifti_surface_and_roi["rois"],
        grey_components,
        np.loadtxt(synthetic_lookup_and_coords["coords"], dtype=int),
        seeds_id,
        str(cifti_out_direct),
    )
    assert cifti_out_direct.exists()

    components_out_folder = tmp_path / "gm_components_out"
    components_out_folder.mkdir()
    coords_for_gm = tmp_path / "coords_for_gm.txt"
    coords_80 = np.column_stack(
        [
            np.zeros(80, dtype=int),
            np.zeros(80, dtype=int),
            np.zeros(80, dtype=int),
            seeds_id,
            np.zeros(80, dtype=int),
        ]
    )
    np.savetxt(str(coords_for_gm), coords_80, fmt="%d")
    save_grey_matter_components(
        grey_components,
        str(components_out_folder),
        synthetic_gifti_surface_and_roi["seeds"],
        "",
        2,
        str(coords_for_gm),
        synthetic_gifti_surface_and_roi["rois"],
    )
    assert len(list(components_out_folder.glob("*.func.gii"))) > 0
