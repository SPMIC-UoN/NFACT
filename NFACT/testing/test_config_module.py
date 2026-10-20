"""
Unit tests for NFACT configuration generation and subject discovery module.
"""

import json
from pathlib import Path
import lz4.frame
import pytest
from NFACT.config import __main__ as config_main_module
from NFACT.config.nfact_config_functions import (
    check_arguments,
    check_study_folder,
    create_combined_algo_dict,
    create_config,
    create_subject_list,
    delete_keys,
    filter_sublist,
    get_arguments,
    move_key_to_front,
    nfact_config_spalsh,
    nfact_dr_study_list,
    nfact_study_list,
    process_config_file,
    process_decomp_dictionary,
    process_global_arguments,
    reorganise_args,
    save_to_json,
    zip_nfact_pp_dir,
)
from sklearn.decomposition import FastICA


def test_nfact_config_splash() -> None:
    """
    Function to test nfact_config_spalsh string formatting.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    splash_text = nfact_config_spalsh()
    assert len(splash_text) > 0
    assert "\x1b" in splash_text


def test_get_arguments_and_create_combined_algo_dict() -> None:
    """
    Function to test extracting sklearn algorithm parameters and combined dict.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    ica_arguments = get_arguments(FastICA)
    assert "max_iter" in ica_arguments
    assert "tol" in ica_arguments

    combined_algorithms = create_combined_algo_dict()
    assert "ica" in combined_algorithms
    assert "nmf" in combined_algorithms
    assert "n_components" not in combined_algorithms["ica"]
    assert "n_components" not in combined_algorithms["nmf"]
    assert "max_iter" in combined_algorithms["ica"]
    assert "init" in combined_algorithms["nmf"]


def test_dictionary_manipulation_helpers() -> None:
    """
    Function to test delete_keys, move_key_to_front, and process_global_arguments.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    sample_dictionary = {"alpha": 1, "beta": 2, "gamma": 3}
    cleaned_dictionary = delete_keys(sample_dictionary, ["beta"])
    assert "beta" not in cleaned_dictionary
    assert "alpha" in cleaned_dictionary

    reordered_dictionary = move_key_to_front(cleaned_dictionary, "gamma")
    assert list(reordered_dictionary.keys())[0] == "gamma"

    empty_arguments = {}
    processed_arguments = process_global_arguments(empty_arguments)
    assert "global_input" in processed_arguments
    assert processed_arguments["global_input"]["list_of_subjects"] == "Required"
    assert processed_arguments["global_input"]["overwrite"] is False


def test_process_decomp_dictionary_and_reorganise_args() -> None:
    """
    Function to test process_decomp_dictionary and reorganise_args deduplication.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    decomp_dictionary = {"seed": "some_seed", "other_key": "val"}
    processed_decomp = process_decomp_dictionary(decomp_dictionary)
    assert processed_decomp["algo"] == "NMF"
    assert processed_decomp["dim"] == "Required"
    assert processed_decomp["roi"] is False
    assert list(processed_decomp.keys())[:3] == ["dim", "algo", "roi"]

    hierarchical_arguments = {
        "nfact_pp": {"list_of_subjects": "sub.txt", "step": 1},
        "nfact_decomp": {"seeds": ["s1"], "list_of_subjects": "sub.txt"},
        "nfact_dr": {"decomp_dir": "dir", "dim": 10},
    }
    reorganised_arguments = reorganise_args(hierarchical_arguments)
    assert "list_of_subjects" not in reorganised_arguments["nfact_pp"]
    assert "seeds" not in reorganised_arguments["nfact_decomp"]
    assert "decomp_dir" not in reorganised_arguments["nfact_dr"]
    assert reorganised_arguments["nfact_pp"]["step"] == 1


def test_create_config_and_process_config_file() -> None:
    """
    Function to test full config generation structure and process_config_file.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    synthetic_raw_args = {
        "nfact_pp": {"list_of_subjects": "sub.txt", "step": 1},
        "nfact_decomp": {"seeds": ["s1"], "list_of_subjects": "sub.txt"},
        "nfact_dr": {"decomp_dir": "dir", "dim": 10},
    }
    processed_custom_config = process_config_file(synthetic_raw_args)
    assert "global_input" in processed_custom_config
    assert processed_custom_config["global_input"]["folder_name"] == "nfact"

    full_config = create_config()
    expected_top_keys = [
        "global_input",
        "cluster",
        "nfact_pp",
        "nfact_decomp",
        "nfact_dr",
        "nfact_qc",
    ]
    for key_name in expected_top_keys:
        assert key_name in full_config
    assert full_config["global_input"]["folder_name"] == "nfact"
    assert full_config["nfact_decomp"]["algo"] == "NMF"


def test_save_to_json(tmp_path: Path) -> None:
    """
    Function to test save_to_json disk output.

    Parameters
    ----------
    tmp_path: Path
        Pytest temporary directory path.

    Returns
    -------
    None
    """
    payload_dictionary = {"test_key": "test_val", "numbers": [1, 2, 3]}
    output_filename = "test_config.json"
    save_to_json(str(tmp_path), payload_dictionary, output_filename)

    saved_file = tmp_path / output_filename
    assert saved_file.exists()
    with open(saved_file, "r") as json_handle:
        loaded_content = json.load(json_handle)
    assert loaded_content == payload_dictionary


def test_check_arguments_mutual_exclusivity() -> None:
    """
    Function to test check_arguments exclusivity validation.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    valid_single_argument = {
        "decomp_only": True,
        "config": False,
        "subject_list": False,
    }
    assert check_arguments(valid_single_argument) is None

    conflicting_arguments = {
        "decomp_only": True,
        "config": True,
        "subject_list": False,
    }
    with pytest.raises(SystemExit) as exit_error:
        check_arguments(conflicting_arguments)
    assert exit_error.value.code == 1


def test_check_study_folder_validation(tmp_path: Path) -> None:
    """
    Function to test check_study_folder error handling.

    Parameters
    ----------
    tmp_path: Path
        Pytest temporary directory path.

    Returns
    -------
    None
    """
    non_existent_path = str(tmp_path / "does_not_exist")
    with pytest.raises(SystemExit) as exit_error_missing:
        check_study_folder(non_existent_path)
    assert exit_error_missing.value.code == 1

    file_not_dir = tmp_path / "not_a_dir.txt"
    file_not_dir.write_text("hello")
    with pytest.raises(SystemExit) as exit_error_file:
        check_study_folder(str(file_not_dir))
    assert exit_error_file.value.code == 1

    empty_folder = tmp_path / "empty_dir"
    empty_folder.mkdir()
    with pytest.raises(SystemExit) as exit_error_empty:
        check_study_folder(str(empty_folder))
    assert exit_error_empty.value.code == 1

    valid_folder = tmp_path / "study_valid"
    valid_folder.mkdir()
    (valid_folder / "sub-01").mkdir()
    assert check_study_folder(str(valid_folder)) is None


def test_filter_sublist_and_nfact_study_list(tmp_path: Path) -> None:
    """
    Function to test filtering non-subject folders and omatrix2 appending.

    Parameters
    ----------
    tmp_path: Path
        Pytest temporary directory path.

    Returns
    -------
    None
    """
    candidate_folders = [
        "/data/study/sub-01\n",
        "/data/study/sub-02\n",
        "/data/study/derivatives\n",
        "/data/study/code\n",
        "/data/study/nfact_pp\n",
        "/data/study/sourcedata\n",
    ]
    filtered_folders = filter_sublist(candidate_folders)
    assert len(filtered_folders) == 2
    assert "/data/study/sub-01\n" in filtered_folders
    assert "/data/study/sub-02\n" in filtered_folders

    regular_study_dir = tmp_path / "regular_study"
    regular_study_dir.mkdir()
    (regular_study_dir / "sub-01").mkdir()
    (regular_study_dir / "sub-02").mkdir()
    (regular_study_dir / "code").mkdir()

    discovered_regular_list = nfact_study_list(str(regular_study_dir))
    assert len(discovered_regular_list) == 2

    nfact_pp_dir = tmp_path / "nfact_pp_study"
    nfact_pp_dir.mkdir()
    (nfact_pp_dir / "sub-01").mkdir()
    (nfact_pp_dir / "sub-02").mkdir()

    discovered_pp_list = nfact_study_list(str(nfact_pp_dir))
    assert len(discovered_pp_list) == 2
    for subject_line in discovered_pp_list:
        assert subject_line.endswith("/omatrix2\n")


def test_nfact_dr_study_list_extraction(tmp_path: Path) -> None:
    """
    Function to test subject prefix extraction for dual regression folders.

    Parameters
    ----------
    tmp_path: Path
        Pytest temporary directory path.

    Returns
    -------
    None
    """
    dr_folder = tmp_path / "nfact_dr_study"
    dr_folder.mkdir()
    (dr_folder / "W_sub01_dim10.nii.gz").write_text("w1")
    (dr_folder / "G_sub01_dim10.nii.gz").write_text("g1")
    (dr_folder / "W_sub02_dim10.nii.gz").write_text("w2")
    (dr_folder / "G_sub02_dim10.nii.gz").write_text("g2")

    dr_subject_list = nfact_dr_study_list(str(dr_folder))
    assert len(dr_subject_list) == 2
    assert any("sub01\n" in entry for entry in dr_subject_list)
    assert any("sub02\n" in entry for entry in dr_subject_list)


def test_create_subject_list(tmp_path: Path) -> None:
    """
    Function to test create_subject_list writing sublist files to disk.

    Parameters
    ----------
    tmp_path: Path
        Pytest temporary directory path.

    Returns
    -------
    None
    """
    study_folder = tmp_path / "raw_study"
    study_folder.mkdir()
    (study_folder / "sub-01").mkdir()
    (study_folder / "sub-02").mkdir()

    output_destination = tmp_path / "output_list"
    output_destination.mkdir()

    create_subject_list(str(study_folder), str(output_destination), "my_subjects")
    expected_file = output_destination / "my_subjects.sublist"
    assert expected_file.exists()
    content = expected_file.read_text().splitlines()
    assert len(content) == 2


def test_zip_nfact_pp_dir(tmp_path: Path) -> None:
    """
    Function to test lz4 compression and cleanup of fdt_matrix2.dot files.

    Parameters
    ----------
    tmp_path: Path
        Pytest temporary directory path.

    Returns
    -------
    None
    """
    subject_matrix_dir = tmp_path / "sub-01" / "omatrix2"
    subject_matrix_dir.mkdir(parents=True)
    raw_dot_file = subject_matrix_dir / "fdt_matrix2.dot"
    raw_data = b"1 2 4.5\n3 4 8.9\n"
    raw_dot_file.write_bytes(raw_data)

    zip_nfact_pp_dir(str(tmp_path))

    assert not raw_dot_file.exists()
    compressed_file = subject_matrix_dir / "fdt_matrix2.dot.lz4"
    assert compressed_file.exists()

    with lz4.frame.open(str(compressed_file), "rb") as lz4_handle:
        decompressed_data = lz4_handle.read()
    assert decompressed_data == raw_data


def test_nfact_config_main_cli_execution(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    Function to test nfact_config_main CLI entrypoint with different flags.

    Parameters
    ----------
    tmp_path: Path
        Pytest temporary directory path.
    monkeypatch: pytest.MonkeyPatch
        Pytest monkeypatch fixture.

    Returns
    -------
    None
    """
    decomp_args = [
        "nfact_config",
        "-D",
        "-o",
        str(tmp_path),
        "-f",
        "decomp_cfg",
    ]
    monkeypatch.setattr("sys.argv", decomp_args)
    with pytest.raises(SystemExit) as exit_decomp:
        config_main_module.nfact_config_main()
    assert exit_decomp.value.code == 0
    assert (tmp_path / "decomp_cfg.decomp").exists()

    pipeline_args = [
        "nfact_config",
        "-C",
        "-o",
        str(tmp_path),
        "-f",
        "pipeline_cfg",
    ]
    monkeypatch.setattr("sys.argv", pipeline_args)
    with pytest.raises(SystemExit) as exit_pipeline:
        config_main_module.nfact_config_main()
    assert exit_pipeline.value.code == 0
    assert (tmp_path / "pipeline_cfg.pipeline").exists()
