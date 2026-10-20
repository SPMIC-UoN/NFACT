"""
Unit tests for NFACT statistics, component loadings, and statsmap modules.
"""

from pathlib import Path
import nibabel as nb
import numpy as np
import pandas as pd
import pytest
from NFACT.stats.nfactstats import (
    process_nfactstats_args,
)
from NFACT.stats.stats_args import (
    invalid_options,
    valid_options,
)
from NFACT.stats.stats_component_loadings import (
    Component_loading,
    save_components,
)
from NFACT.stats.statsmap import (
    create_vol_map,
    get_subjects,
    get_variance_maps,
    merge_components,
    merge_volumes,
    normalization,
    sub_variance,
    subject_variability_map,
)


def test_stats_options_validation() -> None:
    """
    Function to test valid_options and invalid_options exit behavior.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    allowed_options = valid_options()
    assert "loadings" in allowed_options
    assert "statsmap" in allowed_options

    with pytest.raises(SystemExit) as exit_invalid:
        invalid_options("unknown_cmd", allowed_options)
    assert exit_invalid.value.code == 1


def test_stats_component_loadings_run(tmp_path: Path) -> None:
    """
    Function to test Component_loading correlation computation against group components.

    Parameters
    ----------
    tmp_path: Path
        Pytest temporary directory path.

    Returns
    -------
    None
    """
    group_folder = tmp_path / "group_comps"
    group_folder.mkdir()

    number_components = 2
    affine_matrix = np.eye(4)

    group_wm_data = np.zeros((10, 10, 10, number_components), dtype=np.float32)
    group_wm_data[2:6, 2:6, 2:6, 0] = 1.0
    group_wm_data[2:6, 2:6, 2:6, 1] = 2.0
    group_wm_file = group_folder / "W_NMF_dim2.nii.gz"
    nb.save(nb.Nifti1Image(group_wm_data, affine_matrix), str(group_wm_file))

    group_gm_data = np.zeros((10, 10, 10, number_components), dtype=np.float32)
    group_gm_data[2:6, 2:6, 2:6, 0] = 3.0
    group_gm_data[2:6, 2:6, 2:6, 1] = 4.0
    group_gm_file = group_folder / "G_NMF_dim2.nii.gz"
    nb.save(nb.Nifti1Image(group_gm_data, affine_matrix), str(group_gm_file))

    subject_paths_dir = tmp_path / "subjects_dr"
    subject_paths_dir.mkdir()
    sub_wm_file = subject_paths_dir / "W_sub_01_dim2.nii.gz"
    sub_gm_file = subject_paths_dir / "G_sub_01_dim2.nii.gz"
    nb.save(nb.Nifti1Image(group_wm_data, affine_matrix), str(sub_wm_file))
    nb.save(nb.Nifti1Image(group_gm_data, affine_matrix), str(sub_gm_file))

    loading_calculator = Component_loading(
        white_group_component_path=str(group_wm_file),
        grey_group_component_path=[str(group_gm_file)],
        dim="2",
        threshold=0,
    )

    results = loading_calculator.run([str(subject_paths_dir / "sub_01")])
    assert "white_correlations" in results
    assert "grey_correlations" in results
    assert results["white_correlations"].shape == (1, number_components)
    assert np.allclose(results["white_correlations"][0], 1.0, atol=1e-2)
    assert np.allclose(results["grey_correlations"][0], 1.0, atol=1e-2)


def test_save_components_csv_and_npy(tmp_path: Path) -> None:
    """
    Function to test save_components writing .csv and .npy outputs.

    Parameters
    ----------
    tmp_path: Path
        Pytest temporary directory path.

    Returns
    -------
    None
    """
    matrix_data = np.array([[0.95, 0.88], [0.72, 0.65]], dtype=np.float32)
    subject_names = ["/data/sub_01", "/data/sub_02"]

    save_components(
        matrix_data,
        "W_loadings",
        str(tmp_path),
        subject_names,
        no_csv=False,
    )
    csv_file = tmp_path / "W_loadings.csv"
    assert csv_file.exists()
    loaded_dataframe = pd.read_csv(csv_file)
    assert list(loaded_dataframe.columns) == ["subject", "comp_0", "comp_1"]
    assert len(loaded_dataframe) == 2

    save_components(
        matrix_data,
        "W_loadings_raw",
        str(tmp_path),
        subject_names,
        no_csv=True,
    )
    npy_file = tmp_path / "W_loadings_raw.npy"
    assert npy_file.exists()
    loaded_numpy = np.load(str(npy_file))
    assert np.allclose(loaded_numpy, matrix_data)


def test_statsmap_normalization_min_max() -> None:
    """
    Function to test statsmap min-max normalization behavior on non-zero arrays.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    constant_data = np.array([0.0, 3.0, 3.0, 0.0], dtype=np.float64)
    normalized_constant = normalization(constant_data)
    assert normalized_constant[0] == 0.0
    assert normalized_constant[1] == 1.0
    assert normalized_constant[2] == 1.0
    assert normalized_constant[3] == 0.0

    varied_data = np.array([0.0, 2.0, 4.0, 6.0], dtype=np.float64)
    normalized_varied = normalization(varied_data)
    assert normalized_varied[0] == 0.0
    assert normalized_varied[1] == 0.0
    assert normalized_varied[2] == 0.5
    assert normalized_varied[3] == 1.0


def test_subject_variability_and_variance_maps() -> None:
    """
    Function to test subject_variability_map and get_variance_maps stacking.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    group_components = np.array([10.0, 20.0, 30.0], dtype=np.float64)
    subject_components = np.array([15.0, 25.0, 35.0], dtype=np.float64)
    variability = subject_variability_map(group_components, subject_components)
    expected_mean = np.mean(group_components)
    expected_std = np.std(group_components)
    expected_variability = (subject_components - expected_mean) / expected_std
    assert np.allclose(variability, expected_variability)

    group_map = np.ones((4, 4, 4), dtype=np.float64)
    subject_volume = np.stack([group_map * 1.5, group_map * 2.0], axis=3)
    variance_volumes = get_variance_maps(group_map, subject_volume, vol=True)
    assert variance_volumes.shape == (4, 4, 4, 2)

    group_surface = np.ones(50, dtype=np.float64)
    subject_surface = np.stack([group_surface * 1.5, group_surface * 2.0], axis=1)
    variance_surfaces = get_variance_maps(group_surface, subject_surface, vol=False)
    assert variance_surfaces.shape == (50, 2)

    direct_sub_variance = sub_variance(group_surface, subject_surface[:, 0])
    assert direct_sub_variance.shape == (50,)


def test_merge_components_and_create_vol_map(tmp_path: Path) -> None:
    """
    Function to test merge_components, create_vol_map, and merge_volumes.

    Parameters
    ----------
    tmp_path: Path
        Pytest temporary directory path.

    Returns
    -------
    None
    """
    volume_4d = np.ones((5, 5, 5, 3), dtype=np.float32)
    merged_vol = merge_components(volume_4d, comp=[0, 1], threshold=0, vol=True)
    assert merged_vol.shape == (5, 5, 5)

    surface_2d = np.ones((50, 3), dtype=np.float32)
    merged_surf = merge_components(surface_2d, comp=[0, 1], threshold=0, vol=False)
    assert merged_surf.shape == (50,)
    assert np.allclose(merged_surf, 2.0)

    target_vol_path = tmp_path / "test_vol.nii.gz"
    nb.save(nb.Nifti1Image(volume_4d, np.eye(4)), str(target_vol_path))

    loaded_merged = create_vol_map(str(target_vol_path), comp=[0, 1], threshold=0)
    assert loaded_merged.shape == (5, 5, 5)

    merged_all_subjects = merge_volumes(
        [str(target_vol_path), str(target_vol_path)],
        comp=[0, 1],
        threshold=0,
    )
    assert merged_all_subjects.shape == (5, 5, 5, 2)


def test_get_subjects_and_nfactstats_args(tmp_path: Path) -> None:
    """
    Function to test get_subjects discovery and process_nfactstats_args validation.

    Parameters
    ----------
    tmp_path: Path
        Pytest temporary directory path.

    Returns
    -------
    None
    """
    study_folder = tmp_path / "study_stats"
    study_folder.mkdir()
    (study_folder / "W_sub01.nii.gz").write_text("w1")
    (study_folder / "W_sub02.nii.gz").write_text("w2")

    discovered_group = get_subjects(str(study_folder), "W", group_mode=True)
    assert len(discovered_group) == 2

    sublist_file = tmp_path / "subjects.sublist"
    sublist_file.write_text(f"{study_folder}/sub01\n{study_folder}/sub02\n")
    discovered_from_sublist = get_subjects(str(sublist_file), "W", group_mode=False)
    assert len(discovered_from_sublist) == 2

    incomplete_args = {
        "list_of_subjects": None,
        "nfact_folder": None,
        "outdir": str(tmp_path),
        "algo": "NMF",
    }
    with pytest.raises(SystemExit) as exit_missing_args:
        process_nfactstats_args(incomplete_args)
    assert exit_missing_args.value.code == 1
