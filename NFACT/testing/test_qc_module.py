"""
Unit tests for NFACT QC module, hitmap generation, and masking functions.
"""

from pathlib import Path
import time
import nibabel as nb
import numpy as np
import pytest
from NFACT.qc.__main__ import nfactQc_main
from NFACT.qc.nfactQc_args import nfact_Qc_splash
from NFACT.qc.nfactQc_functions import (
    binary_mask,
    check_Qc_dir,
    create_gifti_hitmap,
    create_nifti_hitmap,
    extract_seeds_from_log,
    get_data,
    get_images,
    get_img_name,
    get_latest_log_file,
    hitcount,
    nfactQc_dir,
    normalization,
    save_gifti,
    save_nifti,
    scoring,
    surface_hitcount_maps,
    volume_hitcount_maps,
)


def test_nfact_qc_splash() -> None:
    """
    Function to test nfact_Qc_splash text rendering.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    splash_text = nfact_Qc_splash()
    assert len(splash_text) > 0


def test_extract_seeds_and_latest_log(tmp_path: Path) -> None:
    """
    Function to test log parsing for seeds and latest log resolution.

    Parameters
    ----------
    tmp_path: Path
        Pytest temporary directory path.

    Returns
    -------
    None
    """
    log_folder = tmp_path / "logs"
    log_folder.mkdir()

    old_log = log_folder / "run_2026_01_01.log"
    old_log.write_text("old run")

    time.sleep(0.01)
    new_log = log_folder / "run_2026_01_02.log"
    new_log.write_text('Some info\n"seeds": ["left.surf.gii", "right.surf.gii"]\n')

    latest_log = get_latest_log_file(str(log_folder))
    assert latest_log.name == new_log.name

    extracted_seeds = extract_seeds_from_log(str(latest_log))
    assert extracted_seeds == ["left.surf.gii", "right.surf.gii"]

    empty_folder = tmp_path / "empty_logs"
    empty_folder.mkdir()
    with pytest.raises(FileNotFoundError):
        get_latest_log_file(str(empty_folder))

    with pytest.raises(ValueError):
        extract_seeds_from_log(str(old_log))


def test_normalization_and_scoring() -> None:
    """
    Function to test image data normalization and scoring thresholding.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    test_image_data = np.zeros((4, 4, 4, 2), dtype=np.float32)
    test_image_data[1:3, 1:3, 1:3, 0] = np.array(
        [[[1.0, 2.0], [3.0, 4.0]], [[5.0, 6.0], [7.0, 8.0]]]
    )
    test_image_data[1:3, 1:3, 1:3, 1] = test_image_data[1:3, 1:3, 1:3, 0] * 2.0

    normalized_data = normalization(test_image_data)
    assert normalized_data.shape == test_image_data.shape
    assert normalized_data[0, 0, 0, 0] == 0.0

    normalized_scores = scoring(test_image_data, normalize=True, threshold=2)
    assert normalized_scores["threshold"] == 2
    assert "scores" in normalized_scores

    raw_scores = scoring(test_image_data, normalize=False, threshold=2)
    assert raw_scores["threshold"] == 0
    assert np.array_equal(raw_scores["scores"], test_image_data)


def test_hitcount_and_binary_mask() -> None:
    """
    Function to test hitcount accumulation and binary mask collapsing.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    component_scores = np.array(
        [[[1.0, 3.5], [0.5, 0.2]], [[4.0, 5.0], [0.0, 0.0]]], dtype=np.float32
    )
    hit_results = hitcount(component_scores, threshold=2)
    assert hit_results["hitcount"][0, 0] == 1
    assert hit_results["hitcount"][1, 0] == 2
    assert hit_results["hitcount"][1, 1] == 0

    collapsed_mask = binary_mask(hit_results["bin_mask"])
    assert collapsed_mask[0, 0] == 1
    assert collapsed_mask[1, 0] == 1
    assert collapsed_mask[1, 1] == 0


def test_volume_and_surface_hitcount_maps() -> None:
    """
    Function to test volume and surface hitcount map calculators.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    volume_data = np.random.uniform(0.0, 5.0, size=(5, 5, 5, 3)).astype(np.float32)
    volume_maps = volume_hitcount_maps(volume_data, threshold=1, normalize=False)
    assert "hitcount" in volume_maps
    assert "bin_mask" in volume_maps
    assert volume_maps["hitcount"].shape == (5, 5, 5)

    surface_data = np.random.uniform(0.0, 5.0, size=(3, 50)).astype(np.float32)
    surface_map = surface_hitcount_maps(surface_data, threshold=1, normalize=False)
    assert surface_map.shape == (50,)


def test_save_nifti_and_save_gifti(tmp_path: Path) -> None:
    """
    Function to test save_nifti and save_gifti output writing.

    Parameters
    ----------
    tmp_path: Path
        Pytest temporary directory path.

    Returns
    -------
    None
    """
    nifti_data = np.ones((6, 6, 6), dtype=np.float32)
    affine_matrix = np.eye(4)
    target_nifti_file = tmp_path / "saved.nii.gz"
    save_nifti(str(target_nifti_file), affine_matrix, nifti_data)
    assert target_nifti_file.exists()
    loaded_nifti = nb.load(str(target_nifti_file))
    assert loaded_nifti.shape == (6, 6, 6)

    gifti_data = np.ones(40, dtype=np.float32)
    meta_dict = nb.gifti.GiftiMetaData({"Name": "test"})
    target_gifti_prefix = str(tmp_path / "saved_surface")
    save_gifti(target_gifti_prefix, meta_dict, gifti_data)
    assert (tmp_path / "saved_surface.func.gii").exists()


def test_get_data_and_create_hitmaps(tmp_path: Path, synthetic_nifti_seed: str) -> None:
    """
    Function to test get_data loader and create_nifti_hitmap output files.

    Parameters
    ----------
    tmp_path: Path
        Pytest temporary directory path.
    synthetic_nifti_seed: str
        Path to synthetic volume seed.

    Returns
    -------
    None
    """
    loaded_volume = get_data("nifti", synthetic_nifti_seed)
    assert loaded_volume.ndim in (3, 4)

    qc_output_dir = tmp_path / "nfactQc"
    qc_output_dir.mkdir()
    hitmap_target = str(qc_output_dir / "target_volume")

    create_nifti_hitmap(
        loaded_volume,
        hitmap_target,
        threshold=1,
        meta_data=np.eye(4),
        normalize=False,
    )
    assert (qc_output_dir / "hitmap_target_volume.nii.gz").exists()
    assert (qc_output_dir / "mask_target_volume.nii.gz").exists()

    gifti_data = np.ones((2, 30), dtype=np.float32)
    meta_dict = nb.gifti.GiftiMetaData({"Name": "test"})
    create_gifti_hitmap(
        gifti_data,
        str(qc_output_dir / "surface_qc"),
        threshold=1,
        meta_data=meta_dict,
        normalize=False,
    )
    assert (qc_output_dir / "surface_qc.func.gii").exists()


def test_nfactqc_dir_check_and_main(tmp_path: Path) -> None:
    """
    Function to test nfactQc_dir, check_Qc_dir, get_img_name, and nfactQc_main.

    Parameters
    ----------
    tmp_path: Path
        Pytest temporary directory path.

    Returns
    -------
    None
    """
    qc_dir = tmp_path / "qc_check"
    nfactQc_dir(str(qc_dir), overwrite=False)
    assert qc_dir.exists()

    dummy_existing_wm = qc_dir / "hitmap_W_NMF_dim2.nii.gz"
    dummy_existing_wm.write_text("existing")
    with pytest.raises(SystemExit) as exit_exists:
        check_Qc_dir(str(qc_dir), "W_NMF_dim2")
    assert exit_exists.value.code == 1

    assert get_img_name("/path/to/my_image.nii.gz") == "my_image"

    decomp_study = tmp_path / "decomp_study"
    decomp_target_folder = decomp_study / "components" / "NMF" / "decomp"
    decomp_target_folder.mkdir(parents=True)

    test_volume_data = np.ones((5, 5, 5, 2), dtype=np.float32)
    test_image = nb.Nifti1Image(test_volume_data, np.eye(4))
    nb.save(
        test_image,
        str(decomp_target_folder / "W_NMF_dim2.nii.gz"),
    )
    nb.save(
        test_image,
        str(decomp_target_folder / "G_NMF_dim2.nii.gz"),
    )

    discovered_images = get_images(str(decomp_study), "2", "NMF")
    assert len(discovered_images["grey_images"]) == 1
    assert len(discovered_images["white_image"]) == 1

    qc_main_args = {
        "nfact_folder": str(decomp_study),
        "dim": "2",
        "algo": "NMF",
        "threshold": 1,
        "overwrite": True,
    }
    nfactQc_main(qc_main_args)
    assert (decomp_study / "nfactQc").exists()
    assert len(list((decomp_study / "nfactQc").glob("*.nii.gz"))) > 0
