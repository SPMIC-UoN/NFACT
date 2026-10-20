"""
Unit tests for NFACT dual regression module, NNLS solver, and pipeline integration.
"""

from pathlib import Path
import numpy as np
import pytest
from NFACT.dual_reg.dual_regression.dual_regression_methods import (
    NNLS,
    ica_dual_regression,
    run_decomp,
)
from NFACT.dual_reg.dual_regression.run_dual_regression import (
    dual_regression_pipeline,
)
from NFACT.dual_reg.dual_regression.set_up_dual_regression import (
    build_cluster_command,
    get_cluster_script_path,
    get_python_path,
)
from NFACT.dual_reg.nfact_dr_functions import (
    convert_volume_to_component_matrix,
    create_nfact_dr_folder_set_up,
    get_key_to_organise_list,
    get_subject_id,
    remove_medial_wall,
    reorder_file_inputs,
    reorder_lists_order,
    sort_coord_file,
    vol2mat,
)


def test_nfact_dr_folder_setup(tmp_path: Path) -> None:
    """
    Function to test create_nfact_dr_folder_set_up directory hierarchy creation.

    Parameters
    ----------
    tmp_path: Path
        Pytest temporary directory path.

    Returns
    -------
    None
    """
    dr_base = tmp_path / "study_dr"
    dr_base.mkdir()
    create_nfact_dr_folder_set_up(str(dr_base))

    assert (dr_base / "nfact_dr" / "logs").exists()
    assert (dr_base / "nfact_dr" / "ICA" / "normalised").exists()
    assert (dr_base / "nfact_dr" / "NMF" / "normalised").exists()

    with pytest.raises(SystemExit) as exit_missing_dir:
        create_nfact_dr_folder_set_up(str(tmp_path / "does_not_exist"))
    assert exit_missing_dir.value.code == 1


def test_get_key_and_reorder_lists() -> None:
    """
    Function to test seed orientation key extraction and list reordering.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    left_key = get_key_to_organise_list("/path/to/left.surf.gii")
    assert "left" in left_key
    assert "l" in left_key

    right_key = get_key_to_organise_list("/path/to/right-seed.gii")
    assert "right" in right_key
    assert "r" in right_key

    unordered_list = ["G_NMF_R.gii", "G_NMF_L.gii"]
    reordered_by_left = reorder_lists_order(unordered_list, ["left", "l"])
    assert reordered_by_left[0] == "G_NMF_L.gii"

    reordered_files = reorder_file_inputs(
        "/path/L.surf.gii", ["subcort.nii.gz", "L.surf.gii"]
    )
    assert reordered_files[0] == "L.surf.gii"


def test_get_subject_id_variants() -> None:
    """
    Function to test get_subject_id regex extraction for different path formats.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    assert get_subject_id("/data/study/sub_001/omatrix2/fdt_matrix2.dot") == "sub_001"
    assert get_subject_id("/data/study/MR999_session1/omatrix2") == "MR999"
    assert get_subject_id("/data/study/patient42/omatrix2") == "patient42"


def test_vol2mat_and_convert_volume_to_component_matrix() -> None:
    """
    Function to test vol2mat mapping and convert_volume_to_component_matrix extraction.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    lookup_volume = np.zeros((5, 5, 5), dtype=np.int32)
    lookup_volume[1, 1, 1] = 1
    lookup_volume[2, 2, 2] = 2

    matrix_volume = np.zeros((5, 5, 5, 2), dtype=np.float32)
    matrix_volume[1, 1, 1, 0] = 10.0
    matrix_volume[1, 1, 1, 1] = 20.0
    matrix_volume[2, 2, 2, 0] = 30.0
    matrix_volume[2, 2, 2, 1] = 40.0

    converted_matrix = vol2mat(matrix_volume, lookup_volume)
    assert converted_matrix.shape == (2, 2)
    assert converted_matrix[0, 0] == 10.0
    assert converted_matrix[1, 0] == 20.0
    assert converted_matrix[0, 1] == 30.0
    assert converted_matrix[1, 1] == 40.0

    coordinates = np.array([[1, 1, 1], [2, 2, 2]])
    extracted_components = convert_volume_to_component_matrix(
        matrix_volume, coordinates
    )
    assert extracted_components.shape == (2, 2)
    assert extracted_components[0, 0] == 10.0
    assert extracted_components[1, 1] == 40.0


def test_remove_medial_wall_and_sort_coords(
    tmp_path: Path, synthetic_gifti_surface_and_roi: dict
) -> None:
    """
    Function to test remove_medial_wall filtering and sort_coord_file grouping.

    Parameters
    ----------
    tmp_path: Path
        Pytest temporary directory path.
    synthetic_gifti_surface_and_roi: dict
        Dictionary of surface and ROI paths.

    Returns
    -------
    None
    """
    grey_components = np.ones((50, 2), dtype=np.float32)
    roi_file = synthetic_gifti_surface_and_roi["rois"][0]
    filtered_grey = remove_medial_wall(grey_components, roi_file)
    assert filtered_grey.shape == (40, 2)

    coords_data = np.array(
        [
            [1, 1, 1, 0, 0],
            [1, 1, 2, 0, 0],
            [2, 2, 2, 1, 0],
            [2, 2, 3, 1, 0],
        ],
        dtype=int,
    )
    coords_file = tmp_path / "coords_for_fdt_matrix2"
    np.savetxt(str(coords_file), coords_data, fmt="%d")

    sorted_coordinates = sort_coord_file(str(tmp_path))
    assert 0 in sorted_coordinates
    assert 1 in sorted_coordinates
    assert sorted_coordinates[0].shape == (2, 3)
    assert sorted_coordinates[1].shape == (2, 3)


def test_nnls_class_batch_sizing_and_execution() -> None:
    """
    Function to test NNLS class batch size computation and parallel execution.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    np.random.seed(42)
    number_rows = 20
    number_cols = 30
    number_components = 3

    components = np.random.uniform(0.1, 1.0, size=(number_rows, number_components))
    connectivity_matrix = np.random.uniform(0.1, 1.0, size=(number_rows, number_cols))

    nnls_instance = NNLS(
        components,
        connectivity_matrix,
        n_jobs=2,
        batch_size=None,
        data_type="WM",
    )
    computed_batch_size = nnls_instance.get_batch_size(
        number_cols, min_size=5, max_size=50, fraction=0.1
    )
    assert computed_batch_size == 5

    nnls_results = nnls_instance.run()
    assert nnls_results.shape == (number_cols, number_components)
    assert np.all(nnls_results >= 0.0)


def test_decomp_methods_error_handling() -> None:
    """
    Function to test run_decomp error handling for incompatible matrix shapes.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    incompatible_components = {
        "grey_components": np.ones((10, 2)),
        "white_components": np.ones((2, 10)),
    }
    incompatible_connectivity = np.ones((5, 5))

    with pytest.raises(SystemExit) as exit_error:
        run_decomp(
            ica_dual_regression,
            incompatible_components,
            incompatible_connectivity,
        )
    assert exit_error.value.code == 1


def test_build_cluster_command_and_paths() -> None:
    """
    Function to test build_cluster_command arguments assembly.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    python_binary = get_python_path()
    assert "python" in python_binary

    script_path = get_cluster_script_path()
    assert script_path.endswith("run_dual_regression.py")

    cluster_cmd = build_cluster_command(
        fdt_path="/data/sub-01/omatrix2",
        output_dir="/data/output",
        component_path="/data/components",
        group_average_path="/data/group_avg",
        algo="NMF",
        seeds=["seed1.nii.gz"],
        sub_id="sub-01",
        roi=["roi1.nii.gz"],
        threshold_val="3",
        parallel="4",
        normalise=True,
        dscalar=False,
    )
    assert "--fdt_path" in cluster_cmd
    assert "--output_dir" in cluster_cmd
    assert "--algo" in cluster_cmd
    assert "NMF" in cluster_cmd
    assert "--id" in cluster_cmd
    assert "sub-01" in cluster_cmd


def test_dual_regression_pipeline_end_to_end(
    tmp_path: Path, synthetic_lookup_and_coords: dict, synthetic_nifti_seed: str
) -> None:
    """
    Function to test dual_regression_pipeline end-to-end for NMF and ICA.

    Parameters
    ----------
    tmp_path: Path
        Pytest temporary directory path.
    synthetic_lookup_and_coords: dict
        Dictionary of lookup volume and coords paths.
    synthetic_nifti_seed: str
        Path to synthetic NIfTI seed.

    Returns
    -------
    None
    """
    fdt_dir = tmp_path / "subject_omatrix2"
    fdt_dir.mkdir()

    coords_data = np.loadtxt(synthetic_lookup_and_coords["coords"], dtype=int)
    np.savetxt(str(fdt_dir / "coords_for_fdt_matrix2"), coords_data, fmt="%d")

    tract_coords_data = np.loadtxt(
        synthetic_lookup_and_coords["tract_coords"], dtype=int
    )
    np.savetxt(
        str(fdt_dir / "tract_space_coords_for_fdt_matrix2"),
        tract_coords_data,
        fmt="%d",
    )

    lookup_source = Path(synthetic_lookup_and_coords["lookup_volume"])
    (fdt_dir / "lookup_tractspace_fdt_matrix2.nii.gz").write_bytes(
        lookup_source.read_bytes()
    )

    number_seed_voxels = coords_data.shape[0]
    number_tract_voxels = tract_coords_data.shape[0]
    number_components = 2

    synthetic_matrix = np.random.uniform(
        0.1, 1.0, size=(number_seed_voxels, number_tract_voxels)
    ).astype(np.float32)
    matrix_dot_file = fdt_dir / "fdt_matrix2.dot"
    sparse_rows, sparse_cols = np.nonzero(synthetic_matrix)
    sparse_data = np.column_stack(
        [
            sparse_rows + 1,
            sparse_cols + 1,
            synthetic_matrix[sparse_rows, sparse_cols],
        ]
    )
    np.savetxt(str(matrix_dot_file), sparse_data, fmt="%d %d %.4f")

    (fdt_dir / "waytotal").write_text("100000000\n")

    output_dir = tmp_path / "dual_reg_output"
    output_dir.mkdir()
    create_nfact_dr_folder_set_up(str(output_dir))

    known_components = {
        "grey_components": np.random.uniform(
            0.1, 1.0, size=(number_seed_voxels, number_components)
        ).astype(np.float32),
        "white_components": np.random.uniform(
            0.1, 1.0, size=(number_components, number_tract_voxels)
        ).astype(np.float32),
    }

    dual_regression_pipeline(
        fdt_path=str(fdt_dir),
        output_dir=str(output_dir / "nfact_dr"),
        component_path="",
        group_average_path="",
        algo="NMF",
        seeds=[synthetic_nifti_seed],
        sub_id="sub-01",
        roi=[],
        components=known_components,
        parallel=1,
        normalise=True,
        threshold=0,
    )
    assert (
        output_dir / "nfact_dr" / "NMF" / f"W_sub-01_dim{number_components}.nii.gz"
    ).exists()

    ica_direct_results = ica_dual_regression(known_components, synthetic_matrix)
    assert ica_direct_results["grey_components"].shape == (
        number_seed_voxels,
        number_components,
    )
    assert ica_direct_results["white_components"].shape == (
        number_components,
        number_tract_voxels,
    )

    with pytest.raises(SystemExit) as exit_ica:
        dual_regression_pipeline(
            fdt_path=str(fdt_dir),
            output_dir=str(output_dir / "nfact_dr"),
            component_path="",
            group_average_path="",
            algo="ICA",
            seeds=[synthetic_nifti_seed],
            sub_id="sub-01",
            roi=[],
            components=known_components,
            parallel=1,
            normalise=False,
            threshold=0,
        )
    assert exit_ica.value.code == 1
