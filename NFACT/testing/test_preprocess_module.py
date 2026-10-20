"""
Unit tests for NFACT preprocessing, probtrackx setup, and image utilities.
"""

from pathlib import Path
import subprocess
from unittest.mock import MagicMock
import nibabel as nib
import pytest
from NFACT.preprocess.img_processing import (
    clean_target2,
    downsample_volume,
    fslmaths_cmd,
    seeds_to_ascii,
    wb_cmd,
)
from NFACT.preprocess.nfactpp_functions import (
    create_files_for_decomp,
    get_file,
    seedref,
    stoppage,
    update_seeds_file,
    write_options_to_file,
)
from NFACT.preprocess.nfactpp_setup import (
    check_provided_img,
    check_ptx_options_are_valid,
    check_roi_seed_len,
    clean_ptx_options,
    load_file_tree,
    nfact_pp_folder_setup,
)
from NFACT.preprocess.probtrackx_functions import (
    build_probtrackx2_arguments,
    build_warp_options,
    check_bpx_dir,
    exclsuion_mask,
    fail_safe_for_nfact_pp,
    get_probtrackx_bin,
    get_target_mask,
)


def test_clean_ptx_options_and_check_valid(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Function to test cleaning and validating user-specified probtrackx2 flags.

    Parameters
    ----------
    monkeypatch: pytest.MonkeyPatch
        Pytest monkeypatch fixture.

    Returns
    -------
    None
    """
    raw_ptx_lines = ["--loopcheck\n", "-P 5000\n", "invalid_line_without_flag\n"]
    cleaned_flags = clean_ptx_options(raw_ptx_lines)
    assert cleaned_flags == ["--loopcheck", "-P"]

    def mock_ptx2_help() -> str:
        """
        Mock get_probtrack2_arguments help text.

        Parameters
        ----------
        None

        Returns
        -------
        str: str
            Probtrackx2 options text.
        """
        return "-P,--nsamples\t--loopcheck\t-x,--seed\t"

    monkeypatch.setattr(
        "NFACT.preprocess.nfactpp_setup.get_probtrack2_arguments",
        mock_ptx2_help,
    )

    assert check_ptx_options_are_valid(["-P", "--loopcheck"]) is None

    with pytest.raises(SystemExit) as exit_error:
        check_ptx_options_are_valid(["--nonexistent_flag"])
    assert exit_error.value.code == 1


def test_nfactpp_setup_helpers(tmp_path: Path, synthetic_nifti_seed: str) -> None:
    """
    Function to test check_roi_seed_len, check_provided_img, folder setup, and file tree.

    Parameters
    ----------
    tmp_path: Path
        Pytest temporary directory path.
    synthetic_nifti_seed: str
        Path to synthetic NIfTI volume.

    Returns
    -------
    None
    """
    seeds = ["left_surface.gii", "right_surface.gii"]
    rois = ["left_roi.shape.gii", "right_roi.shape.gii"]
    assert check_roi_seed_len(seeds, rois) is None

    with pytest.raises(SystemExit) as exit_roi_missing:
        check_roi_seed_len(seeds, [])
    assert exit_roi_missing.value.code == 1

    assert check_provided_img(synthetic_nifti_seed, "Missing image") is None
    with pytest.raises(SystemExit) as exit_img_missing:
        check_provided_img(str(tmp_path / "not_there.nii.gz"), "Missing")
    assert exit_img_missing.value.code == 1

    pp_folder = tmp_path / "pp_output"
    nfact_pp_folder_setup(str(pp_folder))
    assert (pp_folder / "logs").exists()
    assert (pp_folder / "files").exists()

    tree_object = load_file_tree("hcp")
    assert tree_object is not None


def test_seedref_default_and_custom(
    mock_fsldir: Path, synthetic_nifti_seed: str
) -> None:
    """
    Function to test seedref resolution with custom input and FSL fallback.

    Parameters
    ----------
    mock_fsldir: Path
        Path to synthetic FSLDIR.
    synthetic_nifti_seed: str
        Path to synthetic NIfTI image.

    Returns
    -------
    None
    """
    custom_reference = seedref(synthetic_nifti_seed)
    assert custom_reference == synthetic_nifti_seed

    default_reference = seedref(None)
    expected_mni = str(mock_fsldir / "data" / "standard" / "MNI152_T1_2mm_brain.nii.gz")
    assert default_reference == expected_mni


def test_nfactpp_functions_files_and_decomp(
    tmp_path: Path, synthetic_nifti_seed: str
) -> None:
    """
    Function to test get_file, update_seeds_file, stoppage, and create_files_for_decomp.

    Parameters
    ----------
    tmp_path: Path
        Pytest temporary directory path.
    synthetic_nifti_seed: str
        Path to synthetic NIfTI seed.

    Returns
    -------
    None
    """
    subject_directory = tmp_path / "sub-01"
    subject_directory.mkdir()
    relative_target = subject_directory / "mask.nii.gz"
    nib.save(
        nib.load(synthetic_nifti_seed),
        str(relative_target),
    )

    resolved_relative = get_file(["mask.nii.gz"], str(subject_directory))
    assert resolved_relative == [str(relative_target)]

    resolved_absolute = get_file(
        [str(relative_target)], str(subject_directory), absolute=True
    )
    assert resolved_absolute == [str(relative_target)]

    with pytest.raises(SystemExit) as exit_missing_file:
        get_file(["does_not_exist.nii.gz"], str(subject_directory))
    assert exit_missing_file.value.code == 1

    seeds_list_file = tmp_path / "seeds.txt"
    seeds_list_file.write_text("L.surf.asc\nR.surf.asc\n")
    update_seeds_file(str(seeds_list_file))
    assert ".asc" not in seeds_list_file.read_text()
    assert ".gii" in seeds_list_file.read_text()

    stoppage_files_dir = tmp_path / "files"
    stoppage_files_dir.mkdir()
    stop_paths_payload = {
        "stopping_mask": ["stop1.nii.gz"],
        "wtstop_mask": ["wtstop1.nii.gz"],
    }
    stoppage_commands = stoppage(
        str(subject_directory), str(stoppage_files_dir), stop_paths_payload
    )
    assert len(stoppage_commands) == 2
    assert (stoppage_files_dir / "stop").exists()
    assert (stoppage_files_dir / "wtstop").exists()

    decomp_study_dir = tmp_path / "subject_pipeline" / "nfact_pp"
    decomp_study_dir.mkdir(parents=True)
    create_files_for_decomp(
        str(decomp_study_dir),
        ["left.surf.gii", "right.surf.gii"],
        ["left.roi.shape.gii"],
    )
    assert (tmp_path / "subject_pipeline" / "seeds_for_decomp.txt").exists()
    assert (tmp_path / "subject_pipeline" / "roi_for_decomp.txt").exists()

    assert write_options_to_file(str(tmp_path), "sample_options", "options") is True


def test_probtrackx_functions_argument_builder(
    mock_fsldir: Path, tmp_path: Path
) -> None:
    """
    Function to test fail_safe, check_bpx_dir, build_warp_options, and probtrackx2 command builder.

    Parameters
    ----------
    mock_fsldir: Path
        Path to synthetic FSLDIR.
    tmp_path: Path
        Pytest temporary directory path.

    Returns
    -------
    None
    """
    assert fail_safe_for_nfact_pp("warp_file", "bedpostx_folder") is None
    with pytest.raises(SystemExit) as exit_failsafe:
        fail_safe_for_nfact_pp(None, "bedpostx_folder")
    assert exit_failsafe.value.code == 1

    bpx_folder = tmp_path / "sub-01" / "bpx"
    bpx_folder.mkdir(parents=True)
    nodiff_file = bpx_folder / "nodif_brain_mask.nii.gz"
    nodiff_file.write_text("mask")
    assert (
        check_bpx_dir(str(bpx_folder / "merged"), str(bpx_folder / "nodif_brain_mask"))
        is None
    )

    single_warp = build_warp_options(["std2diff.nii.gz"])
    assert single_warp == ["--xfm=std2diff.nii.gz"]

    dual_warp = build_warp_options(["std2diff.nii.gz", "diff2std.nii.gz"])
    assert dual_warp == ["--xfm=std2diff.nii.gz", "--invxfm=diff2std.nii.gz"]

    target_options_arg = {
        "target2": "custom_target2.nii.gz",
        "outdir": str(tmp_path),
    }
    custom_target = get_target_mask("/study/sub-01", target_options_arg)
    assert custom_target == "/study/sub-01/custom_target2.nii.gz"

    target_options_arg["target2"] = None
    default_target = get_target_mask("/study/sub-01", target_options_arg)
    assert default_target == str(tmp_path / "nfact_pp" / "target2.nii.gz")

    assert get_probtrackx_bin(use_gpu=False).endswith("probtrackx2")
    assert get_probtrackx_bin(use_gpu=True).endswith("probtrackx2_gpu")
    assert exclsuion_mask("/path/avoid.nii.gz") == ["--avoid=/path/avoid.nii.gz"]

    subject_folder = tmp_path / "sub-01"
    sub_omatrix_dir = tmp_path / "output" / "nfact_pp" / "sub-01"
    sub_omatrix_dir.mkdir(parents=True)
    (sub_omatrix_dir / "seeds.txt").write_text("seeds")

    pipeline_arguments = {
        "warps": ["diff2std.nii.gz"],
        "bpx_path": "bpx",
        "outdir": str(tmp_path / "output"),
        "seedref": "ref.nii.gz",
        "target2": None,
        "nsamples": 5000,
        "gpu": False,
        "exclusion": None,
        "stop": None,
        "dont_save_fdt_img": False,
    }
    constructed_command = build_probtrackx2_arguments(
        pipeline_arguments, str(subject_folder)
    )
    assert constructed_command[0].endswith("probtrackx2")
    assert "--omatrix2" in constructed_command
    assert "--nsamples=5000" in constructed_command


def test_img_processing_external_commands(
    mock_fsldir: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """
    Function to test external command wrappers: seeds_to_ascii, downsample, wb_cmd, fslmaths.

    Parameters
    ----------
    mock_fsldir: Path
        Path to synthetic FSLDIR.
    monkeypatch: pytest.MonkeyPatch
        Pytest monkeypatch fixture.
    tmp_path: Path
        Pytest temporary directory path.

    Returns
    -------
    None
    """
    executed_commands = []

    def mock_subprocess_run(command: list, **kwargs: dict) -> MagicMock:
        """
        Mock subprocess.run to intercept image processing commands.

        Parameters
        ----------
        command: list
            Command arguments.
        kwargs: dict
            Keyword arguments.

        Returns
        -------
        MagicMock: MagicMock
            Mocked CompletedProcess.
        """
        executed_commands.append(command)
        result = MagicMock()
        result.returncode = 0
        result.stderr = b""
        result.stdout = b""
        return result

    monkeypatch.setattr(subprocess, "run", mock_subprocess_run)

    seeds_to_ascii("surf.gii", "roi.gii", "surf.asc")
    assert executed_commands[-1][0] == "surf2surf"
    assert "--outputtype=ASCII" in executed_commands[-1]

    downsample_volume("in.nii.gz", "out.nii.gz", "2", "ref.nii.gz", "trilinear")
    assert executed_commands[-1][0] == "flirt"
    assert "-applyisoxfm" in executed_commands[-1]

    wb_cmd(["-surface-resample", "in.surf.gii"])
    assert executed_commands[-1][0] == "wb_command"

    fslmaths_cmd(["in.nii.gz", "-bin", "out.nii.gz"])
    assert executed_commands[-1][0] == "fslmaths"

    files_to_delete = [
        "ven_mask_dilated",
        "ventricle_1",
        "ventricle_2",
        "ven_mask",
        "ven_inv",
    ]
    for dummy_name in files_to_delete:
        (tmp_path / f"{dummy_name}.nii.gz").write_text("dummy")

    clean_target2(str(tmp_path), "default_ref.nii.gz")
    assert any(cmd[0] == "fslmaths" for cmd in executed_commands)
    for dummy_name in files_to_delete:
        assert not (tmp_path / f"{dummy_name}.nii.gz").exists()

    def mock_subprocess_failure(command: list, **kwargs: dict) -> MagicMock:
        """
        Mock subprocess.run returning non-zero returncode.

        Parameters
        ----------
        command: list
            Command arguments.
        kwargs: dict
            Keyword arguments.

        Returns
        -------
        MagicMock: MagicMock
            Failing CompletedProcess.
        """
        result = MagicMock()
        result.returncode = 1
        result.stderr = b"Command failed"
        return result

    monkeypatch.setattr(subprocess, "run", mock_subprocess_failure)
    with pytest.raises(SystemExit) as exit_flirt:
        downsample_volume("in.nii.gz", "out.nii.gz", "2", "ref.nii.gz", "trilinear")
    assert exit_flirt.value.code == 1
