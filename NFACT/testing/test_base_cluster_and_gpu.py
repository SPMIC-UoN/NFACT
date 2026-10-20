"""
Unit tests for NFACT cluster support and GPU detection modules.
"""

from pathlib import Path
import subprocess
from unittest.mock import MagicMock
import pytest
from NFACT.base.cluster_support import (
    Cluster_parameters,
    NoClusterQueuesException,
    Queue_Monitoring,
    base_command,
    cluster_submission,
    fsl_sub_cluster_command,
    no_cluster_queues,
    processing_cluster,
    run_fsl_sub,
)
from NFACT.base.gpu import _get_busy_uuids, find_free_gpu_uuid


def test_base_command_and_fsl_sub_cluster_command(mock_fsldir: Path) -> None:
    """
    Function to test assembly of base cluster command and fsl_sub options.

    Parameters
    ----------
    mock_fsldir: Path
        Path to synthetic FSLDIR.

    Returns
    -------
    None
    """
    cmd_base = base_command(
        cluster_time="300",
        cluster_ram="32",
        log_directory="/tmp/logs",
        log_name="test_job",
    )
    expected_fsl_sub = str(mock_fsldir / "bin" / "fsl_sub")
    assert cmd_base == [
        expected_fsl_sub,
        "-T",
        "300",
        "-R",
        "32",
        "-N",
        "test_job",
        "-l",
        "/tmp/logs",
    ]

    full_cmd = fsl_sub_cluster_command(
        cluster_command=cmd_base.copy(),
        command_to_run=["echo", "pipeline_test"],
        queue="gpu.q",
        qos='--extra "--qos=express"',
        gpu=True,
        parallel=8,
    )
    assert '--extra "--qos=express"' in full_cmd
    assert "-q" in full_cmd
    assert "gpu.q" in full_cmd
    assert "-c" in full_cmd
    assert "cuda" in full_cmd
    assert "-s" in full_cmd
    assert "8" in full_cmd
    assert "echo pipeline_test" in full_cmd


def test_cluster_parameters_processing(
    mock_fsldir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    Function to test Cluster_parameters processing and queue detection.

    Parameters
    ----------
    mock_fsldir: Path
        Path to synthetic FSLDIR.
    monkeypatch: pytest.MonkeyPatch
        Pytest monkeypatch fixture.

    Returns
    -------
    None
    """

    def mock_run_fsl_sub_success(command: list) -> dict:
        """
        Mock fsl_sub calls for queue availability and config check.

        Parameters
        ----------
        command: list
            List containing command arguments.

        Returns
        -------
        dict: dict
            Dictionary representing command output.
        """
        if "--has_queues" in command:
            return {"stdout": "Yes", "stderr": ""}
        if "--show_config" in command:
            return {"stdout": "short.q\nlong.q\ngpu.q", "stderr": ""}
        return {"stdout": "", "stderr": ""}

    monkeypatch.setattr(
        "NFACT.base.cluster_support.run_fsl_sub", mock_run_fsl_sub_success
    )

    arguments_cpu = {
        "cluster_ram": None,
        "cluster_time": None,
        "cluster_qos": "normal",
        "cluster_queue": "short.q",
        "gpu": False,
    }
    processed_cpu = Cluster_parameters(arguments_cpu).process_parameters()
    assert processed_cpu["cluster_ram"] == "60"
    assert processed_cpu["cluster_time"] == "600"
    assert processed_cpu["cluster_qos"] == '--extra "--qos=normal"'

    arguments_gpu = {
        "cluster_ram": "40",
        "cluster_time": None,
        "cluster_qos": None,
        "cluster_queue": "unknown.q",
        "gpu": True,
    }
    processed_gpu = Cluster_parameters(arguments_gpu).process_parameters()
    assert processed_gpu["cluster_ram"] == "40"
    assert processed_gpu["cluster_time"] == "160"

    def mock_run_fsl_sub_no_queues(command: list) -> dict:
        """
        Mock fsl_sub reporting no queues.

        Parameters
        ----------
        command: list
            Command arguments.

        Returns
        -------
        dict: dict
            Dictionary indicating no queues.
        """
        return {"stdout": "No", "stderr": ""}

    monkeypatch.setattr(
        "NFACT.base.cluster_support.run_fsl_sub", mock_run_fsl_sub_no_queues
    )
    with pytest.raises(NoClusterQueuesException):
        Cluster_parameters(arguments_cpu).process_parameters()


def test_queue_monitoring(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Function to test Queue_Monitoring loop with mocked sleep and report.

    Parameters
    ----------
    monkeypatch: pytest.MonkeyPatch
        Pytest monkeypatch fixture.

    Returns
    -------
    None
    """
    monkeypatch.setattr("time.sleep", lambda duration: None)

    call_counts = {"count": 0}

    def mock_fsl_report(command: list) -> dict:
        """
        Mock fsl_sub_report output.

        Parameters
        ----------
        command: list
            Report command arguments.

        Returns
        -------
        dict: dict
            Dictionary indicating job completion.
        """
        call_counts["count"] += 1
        if "fail_job" in command:
            return {"stdout": "Failed: memory limit", "stderr": ""}
        return {"stdout": "Finished successfully", "stderr": ""}

    monkeypatch.setattr("NFACT.base.cluster_support.run_fsl_sub", mock_fsl_report)

    monitor_instance = Queue_Monitoring()
    monitor_instance.monitor(["job_101", "fail_job"])
    assert call_counts["count"] >= 2


def test_run_fsl_sub_and_cluster_submission(
    mock_fsldir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    Function to test run_fsl_sub wrapper and cluster_submission helper.

    Parameters
    ----------
    mock_fsldir: Path
        Path to synthetic FSLDIR.
    monkeypatch: pytest.MonkeyPatch
        Pytest monkeypatch fixture.

    Returns
    -------
    None
    """
    mock_result_success = MagicMock()
    mock_result_success.stdout = b"job_id_9999\n"
    mock_result_success.stderr = b""
    mock_result_success.returncode = 0

    monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: mock_result_success)

    output_dict = run_fsl_sub(["fsl_sub", "echo", "test"])
    assert output_dict["stdout"] == "job_id_9999"

    submitted_job_id = cluster_submission(
        command=["python3", "script.py"],
        cluster_time="120",
        cluster_ram="16",
        cluster_queue="short.q",
        log_name="run_log",
        log_location="/tmp/logs",
        cluster_qos=None,
        gpu=False,
    )
    assert submitted_job_id == "job_id_9999"

    mock_result_error = MagicMock()
    mock_result_error.stdout = b""
    mock_result_error.stderr = b"Queue does not exist"
    mock_result_error.returncode = 1
    monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: mock_result_error)
    with pytest.raises(SystemExit) as exit_error:
        run_fsl_sub(["fsl_sub", "invalid"])
    assert exit_error.value.code == 1


def test_processing_cluster_and_no_cluster_queues(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Function to test processing_cluster fallback and no_cluster_queues helper.

    Parameters
    ----------
    monkeypatch: pytest.MonkeyPatch
        Pytest monkeypatch fixture.

    Returns
    -------
    None
    """
    assert no_cluster_queues() is None

    def mock_process_parameters_success(self: Cluster_parameters) -> dict:
        """
        Mock process_parameters success.

        Parameters
        ----------
        self: Cluster_parameters
            Instance of Cluster_parameters.

        Returns
        -------
        dict: dict
            Processed arguments dictionary.
        """
        self.arg["cluster_processed"] = True
        return self.arg

    monkeypatch.setattr(
        Cluster_parameters, "process_parameters", mock_process_parameters_success
    )
    test_arguments_success = {"cluster": True}
    processed_arguments = processing_cluster(test_arguments_success)
    assert processed_arguments.get("cluster_processed") is True

    def mock_process_parameters_exception(self: Cluster_parameters) -> dict:
        """
        Mock process_parameters raising NoClusterQueuesException.

        Parameters
        ----------
        self: Cluster_parameters
            Instance of Cluster_parameters.

        Returns
        -------
        dict: dict
            Processed arguments dictionary.
        """
        raise NoClusterQueuesException()

    monkeypatch.setattr(
        Cluster_parameters,
        "process_parameters",
        mock_process_parameters_exception,
    )
    test_arguments_no_queue = {"cluster": True}
    fallback_arguments = processing_cluster(test_arguments_no_queue)
    assert fallback_arguments["cluster"] is None


def test_get_busy_uuids(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Function to test _get_busy_uuids parsing and exception handling.

    Parameters
    ----------
    monkeypatch: pytest.MonkeyPatch
        Pytest monkeypatch fixture.

    Returns
    -------
    None
    """
    monkeypatch.setattr(
        subprocess,
        "check_output",
        lambda *args, **kwargs: b"GPU-uuid-1\nMIG-uuid-2\n",
    )
    busy_uuids = _get_busy_uuids()
    assert busy_uuids == {"GPU-uuid-1", "MIG-uuid-2"}

    def mock_check_output_error(*args: list, **kwargs: dict) -> bytes:
        """
        Mock check_output raising exception.

        Parameters
        ----------
        args: list
            Positional arguments.
        kwargs: dict
            Keyword arguments.

        Returns
        -------
        bytes: bytes
            Binary output.
        """
        raise subprocess.SubprocessError("Query failed")

    monkeypatch.setattr(subprocess, "check_output", mock_check_output_error)
    assert _get_busy_uuids() == set()


def test_find_free_gpu_uuid_user_override(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Function to test find_free_gpu_uuid with user MIG override.

    Parameters
    ----------
    monkeypatch: pytest.MonkeyPatch
        Pytest monkeypatch fixture.

    Returns
    -------
    None
    """
    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", "MIG-user-override-1234")
    assert find_free_gpu_uuid() == "MIG-user-override-1234"


def test_find_free_gpu_uuid_priority_probing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Function to test idle MIG preference over idle GPU and busy devices.

    Parameters
    ----------
    monkeypatch: pytest.MonkeyPatch
        Pytest monkeypatch fixture.

    Returns
    -------
    None
    """
    monkeypatch.delenv("CUDA_VISIBLE_DEVICES", raising=False)

    def mock_smi_output(command: list, **kwargs: dict) -> bytes:
        """
        Mock nvidia-smi -L output.

        Parameters
        ----------
        command: list
            Command passed to check_output.
        kwargs: dict
            Keyword arguments.

        Returns
        -------
        bytes: bytes
            Mock stdout bytes.
        """
        if "-L" in command:
            return (
                b"GPU 0: NVIDIA A100-SXM4-40GB (UUID: GPU-00000000-0000)\n"
                b"  MIG 3g.20gb Device 0: (UUID: MIG-11111111-1111)\n"
                b"  MIG 3g.20gb Device 1: (UUID: MIG-22222222-2222)\n"
            )
        return b"MIG-11111111-1111\n"

    monkeypatch.setattr(subprocess, "check_output", mock_smi_output)

    probed_devices = []

    def mock_check_call(command: list, env: dict, **kwargs: dict) -> int:
        """
        Mock python cuda verification call.

        Parameters
        ----------
        command: list
            Command passed to check_call.
        env: dict
            Environment dictionary containing CUDA_VISIBLE_DEVICES.
        kwargs: dict
            Keyword arguments.

        Returns
        -------
        int: int
            Zero exit code.
        """
        target_device = env.get("CUDA_VISIBLE_DEVICES")
        probed_devices.append(target_device)
        return 0

    monkeypatch.setattr(subprocess, "check_call", mock_check_call)

    selected_gpu = find_free_gpu_uuid()
    assert selected_gpu == "MIG-22222222-2222"
    assert probed_devices[0] == "MIG-22222222-2222"


def test_find_free_gpu_uuid_no_nvidia_smi(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Function to test find_free_gpu_uuid when nvidia-smi is unavailable.

    Parameters
    ----------
    monkeypatch: pytest.MonkeyPatch
        Pytest monkeypatch fixture.

    Returns
    -------
    None
    """
    monkeypatch.delenv("CUDA_VISIBLE_DEVICES", raising=False)

    def mock_smi_not_found(*args: list, **kwargs: dict) -> bytes:
        """
        Mock missing nvidia-smi executable.

        Parameters
        ----------
        args: list
            Arguments.
        kwargs: dict
            Keyword arguments.

        Returns
        -------
        bytes: bytes
            Binary output.
        """
        raise FileNotFoundError("nvidia-smi not found")

    monkeypatch.setattr(subprocess, "check_output", mock_smi_not_found)
    assert find_free_gpu_uuid() is None
