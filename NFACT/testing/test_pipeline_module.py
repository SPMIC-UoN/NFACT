"""
Unit tests for NFACT top-level pipeline functions, config validation, and main coordinator.
"""

import json
from pathlib import Path
import pytest
from NFACT.pipeline import __main__ as pipeline_main_module
from NFACT.pipeline.nfact_pipeline_functions import (
    assign_nfact_decomp,
    assign_nfact_dr,
    assign_nfactpp,
    assign_outdir,
    build_args,
    build_module_arguments,
    compulsory_args_for_config,
    get_compulsory_arguments,
    non_compulsory_arguments,
    pipeline_args_check,
    roi_file,
    update_nfact_args,
)


def test_non_compulsory_arguments() -> None:
    """
    Function to test default non-compulsory argument list and extension.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    default_non_compulsory = non_compulsory_arguments()
    expected_defaults = [
        "target2",
        "config",
        "pp_skip",
        "dr_skip",
        "file_tree",
        "overwrite",
        "qc_skip",
    ]
    for flag_name in expected_defaults:
        assert flag_name in default_non_compulsory

    extended_list = non_compulsory_arguments(["extra_flag_1", "extra_flag_2"])
    assert "extra_flag_1" in extended_list
    assert "extra_flag_2" in extended_list


def test_get_compulsory_arguments_and_latent_bug() -> None:
    """
    Function to test get_compulsory_arguments assembly and surface latent list.extend bug.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    standard_args = {
        "cluster": {"cluster_time": "100", "cluster_ram": "20"},
        "input": {"pp_skip": False},
        "pre_process": {"file_tree": False},
    }
    compulsory_list = get_compulsory_arguments(standard_args)
    assert "cluster_time" in compulsory_list
    assert "roi" in compulsory_list
    assert "seedref" in compulsory_list

    # Test latent bug: pp_skip=True calls non_complusory_commands.extend(...) which returns None
    pp_skip_args = {
        "cluster": {"cluster_time": "100"},
        "input": {"pp_skip": True},
        "pre_process": {"file_tree": False},
    }
    with pytest.raises(TypeError):
        get_compulsory_arguments(pp_skip_args)


def test_pipeline_args_check() -> None:
    """
    Function to test pipeline_args_check validation and missing argument failure.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    valid_pipeline_args = {
        "cluster": {"cluster_time": "100", "cluster_ram": "20"},
        "input": {"pp_skip": False, "config": None, "target2": None},
        "pre_process": {"file_tree": False, "bpx_path": "/data/bpx", "warps": ["w1"]},
        "decomp": {"algo": "NMF", "dim": 10},
    }
    assert pipeline_args_check(valid_pipeline_args) is None

    invalid_pipeline_args = {
        "cluster": {"cluster_time": "100"},
        "input": {"pp_skip": False},
        "pre_process": {"file_tree": False},
        "decomp": {"algo": None},
    }
    with pytest.raises(SystemExit) as exit_error:
        pipeline_args_check(invalid_pipeline_args)
    assert exit_error.value.code == 1


def test_build_args_and_build_module_arguments() -> None:
    """
    Function to test build_args and build_module_arguments copying.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    source_args = {"learning_rate": 0.01, "batch_size": 32, "ignored_key": 99}
    target_module = {"learning_rate": None, "batch_size": None, "epochs": 10}

    updated_module = build_args(source_args, target_module)
    assert updated_module["learning_rate"] == 0.01
    assert updated_module["batch_size"] == 32
    assert updated_module["epochs"] == 10
    assert "ignored_key" not in updated_module

    nested_pipeline_args = {
        "input": {"outdir": "/tmp/out", "overwrite": True},
        "decomp": {"dim": 50, "algo": "NMF"},
    }
    base_decomp_target = {"outdir": None, "dim": None, "algo": None}
    built_arguments = build_module_arguments(
        base_decomp_target, nested_pipeline_args, "decomp"
    )
    assert built_arguments["outdir"] == "/tmp/out"
    assert built_arguments["dim"] == 50
    assert built_arguments["algo"] == "NMF"


def test_compulsory_args_for_config() -> None:
    """
    Function to test compulsory_args_for_config validation on config dictionaries.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    valid_config = {
        "global_input": {"seed": ["left.surf.gii"]},
        "nfact_pp": {"file_tree": False},
        "nfact_decomp": {"dim": 10},
    }
    assert compulsory_args_for_config(valid_config) is None

    config_missing_seed = {
        "global_input": {"seed": ["Required unless file_tree specified"]},
        "nfact_pp": {"file_tree": False},
    }
    with pytest.raises(SystemExit) as exit_seed_missing:
        compulsory_args_for_config(config_missing_seed)
    assert exit_seed_missing.value.code == 1

    config_with_required_placeholder = {
        "global_input": {"seed": ["left.surf.gii"]},
        "nfact_pp": {"file_tree": False},
        "nfact_decomp": {"dim": "Required"},
    }
    with pytest.raises(SystemExit) as exit_required_missing:
        compulsory_args_for_config(config_with_required_placeholder)
    assert exit_required_missing.value.code == 1


def test_pipeline_argument_assignment_helpers() -> None:
    """
    Function to test assign_outdir, assign_nfactpp, assign_nfact_decomp, assign_nfact_dr, and roi_file.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    test_pipeline_state = {
        "global_input": {
            "outdir": "/data/study",
            "folder_name": "run_01",
            "seed": ["seed1.nii.gz"],
            "list_of_subjects": "/data/sub.txt",
            "overwrite": True,
        },
        "cluster": {"cluster_time": "120"},
        "nfact_pp": {"roi": None, "file_tree": False},
        "nfact_decomp": {"roi": None, "algo": "NMF"},
        "nfact_dr": {},
    }

    assign_outdir(test_pipeline_state)
    expected_outdir = "/data/study/run_01"
    assert test_pipeline_state["nfact_pp"]["outdir"] == expected_outdir
    assert test_pipeline_state["nfact_decomp"]["outdir"] == expected_outdir
    assert test_pipeline_state["nfact_dr"]["outdir"] == expected_outdir

    assign_nfactpp(test_pipeline_state)
    assert test_pipeline_state["nfact_pp"]["seed"] == ["seed1.nii.gz"]
    assert test_pipeline_state["nfact_pp"]["cluster_time"] == "120"

    assign_nfact_decomp(test_pipeline_state)
    assert test_pipeline_state["nfact_decomp"]["overwrite"] is True

    assign_nfact_dr(test_pipeline_state)
    assert test_pipeline_state["nfact_dr"]["algo"] == "NMF"

    roi_file(test_pipeline_state)
    assert test_pipeline_state["nfact_dr"]["roi"] is False

    test_pipeline_state_roi = {
        "global_input": {
            "outdir": "/data/study",
            "folder_name": "run_01",
            "seed": ["seed1.nii.gz"],
            "list_of_subjects": "/data/sub.txt",
            "overwrite": True,
        },
        "cluster": {},
        "nfact_pp": {"roi": ["roi1.gii"], "file_tree": False},
        "nfact_decomp": {"roi": None, "algo": "NMF"},
        "nfact_dr": {},
    }
    roi_file(test_pipeline_state_roi)
    expected_roi_path = "/data/study/run_01/nfact_pp/roi_for_decomp.txt"
    assert test_pipeline_state_roi["nfact_decomp"]["roi"] == expected_roi_path
    assert test_pipeline_state_roi["nfact_dr"]["roi"] == expected_roi_path

    fresh_pipeline_state = {
        "global_input": {
            "outdir": "/data/study",
            "folder_name": "run_01",
            "seed": ["seed1.nii.gz"],
            "list_of_subjects": "/data/sub.txt",
            "overwrite": True,
        },
        "cluster": {},
        "nfact_pp": {"roi": None, "file_tree": False},
        "nfact_decomp": {"roi": None, "algo": "NMF"},
        "nfact_dr": {},
    }
    update_nfact_args(fresh_pipeline_state)
    assert fresh_pipeline_state["nfact_pp"]["outdir"] == expected_outdir


def test_nfact_pipeline_main_end_to_end_mocked(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    Function to test nfact_pipeline_main coordinator execution with mocked module runners.

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
    study_output_dir = tmp_path / "study_output"
    study_output_dir.mkdir()

    subjects_file = tmp_path / "subjects.sublist"
    subjects_file.write_text("/data/sub-01\n/data/sub-02\n")

    pipeline_config = {
        "global_input": {
            "list_of_subjects": str(subjects_file),
            "outdir": str(study_output_dir),
            "folder_name": "nfact_run",
            "seed": ["left.surf.gii", "right.surf.gii"],
            "overwrite": True,
            "pp_skip": True,
            "dr_skip": False,
            "qc_skip": False,
        },
        "cluster": {
            "cluster_ram": "30",
            "cluster_time": "120",
            "cluster_qos": None,
            "cluster_queue": None,
            "gpu": False,
        },
        "nfact_pp": {
            "file_tree": False,
            "roi": ["left.roi.gii", "right.roi.gii"],
            "warps": ["std2diff.nii.gz"],
            "bpx_path": "bpx",
            "n_cores": False,
        },
        "nfact_decomp": {
            "dim": 10,
            "algo": "NMF",
            "roi": False,
        },
        "nfact_dr": {
            "n_cores": False,
        },
        "nfact_qc": {
            "threshold": 2,
        },
    }
    config_file_path = tmp_path / "pipeline.config"
    config_file_path.write_text(json.dumps(pipeline_config))

    mock_cli_args = {
        "input": {
            "config": str(config_file_path),
            "pp_skip": True,
            "dr_skip": False,
            "qc_skip": False,
            "overwrite": True,
        }
    }
    monkeypatch.setattr("NFACT.pipeline.__main__.nfact_args", lambda: mock_cli_args)

    pp_called = []
    decomp_called = []
    qc_called = []
    dr_called = []

    monkeypatch.setattr(
        "NFACT.pipeline.__main__.nfact_pp_main",
        lambda args: pp_called.append(True),
    )
    monkeypatch.setattr(
        "NFACT.pipeline.__main__.nfact_decomp_main",
        lambda args: decomp_called.append(True),
    )
    monkeypatch.setattr(
        "NFACT.pipeline.__main__.nfactQc_main",
        lambda args: qc_called.append(True),
    )
    monkeypatch.setattr(
        "NFACT.pipeline.__main__.nfact_dr_main",
        lambda args: dr_called.append(True),
    )

    nfact_pp_stage_dir = study_output_dir / "nfact_run" / "nfact_pp"
    nfact_pp_stage_dir.mkdir(parents=True)

    with pytest.raises(SystemExit) as exit_pipeline:
        pipeline_main_module.nfact_pipeline_main()
    assert exit_pipeline.value.code == 0

    assert len(pp_called) == 0  # pp_skip is True
    assert len(decomp_called) == 1
    assert len(qc_called) == 1
    assert len(dr_called) == 1
