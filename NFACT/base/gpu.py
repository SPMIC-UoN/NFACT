import os
import subprocess
import sys


def _get_busy_uuids() -> set:
    """
    Return the set of GPU/MIG UUIDs that currently have active compute
    processes, as reported by ``nvidia-smi --query-compute-apps``.
    Returns an empty set if the query fails (fail-open so we still try
    to pick a device rather than blocking entirely).

    Parameters
    ----------
    None

    Returns
    -------
    set: set of strings
        set of GPU/MIG UUIDs
    """
    try:
        out = subprocess.check_output(
            [
                "nvidia-smi",
                "--query-compute-apps=gpu_uuid",
                "--format=csv,noheader",
            ],
            stderr=subprocess.DEVNULL,
        ).decode("utf-8")
        return {line.strip() for line in out.splitlines() if line.strip()}
    except Exception:
        return set()


def find_free_gpu_uuid() -> str:
    """
    Function to find an idle GPU or MIG partition.

    Priority order
    --------------
    1. **User-specified MIG device** – if ``CUDA_VISIBLE_DEVICES`` is
       already set to a UUID beginning with ``MIG-``, that value is
       returned immediately (the user knows what they want).
    2. **Idle MIG instances** – ``nvidia-smi -L`` is queried for all
       MIG instance UUIDs, and those that currently have no active
       compute processes (checked via ``nvidia-smi --query-compute-apps``)
       are probed first. This ensures a large job is not queued behind
       an already-busy partition.
    3. **Idle whole-GPU UUIDs** – used as a fallback only if no idle
       MIG instance is available.

    Parameters
    -----------
    None

    Returns
    -------
    str: string object
        UUID of the idle GPU or MIG partition, or ``None`` if none
        could be found.
    """
    user_device = os.environ.get("CUDA_VISIBLE_DEVICES", "")
    if user_device.startswith("MIG-"):
        return user_device
    try:
        smi_out = subprocess.check_output(["nvidia-smi", "-L"]).decode("utf-8")
        all_uuids = [
            line.split("UUID: ")[1].strip().strip(")")
            for line in smi_out.split("\n")
            if "UUID: " in line
        ]
    except Exception as e:
        print(f"Warning: Failed to run nvidia-smi: {e}")
        return None

    busy = _get_busy_uuids()

    mig_uuids = [u for u in all_uuids if u.startswith("MIG-")]
    gpu_uuids = [u for u in all_uuids if not u.startswith("MIG-")]
    idle_mig = [u for u in mig_uuids if u not in busy]
    busy_mig = [u for u in mig_uuids if u in busy]
    idle_gpu = [u for u in gpu_uuids if u not in busy]
    busy_gpu = [u for u in gpu_uuids if u in busy]

    # Probe order: idle MIG → idle GPU → busy MIG → busy GPU (last resort).
    ordered_uuids = idle_mig + idle_gpu + busy_mig + busy_gpu

    for uuid in ordered_uuids:
        try:
            env = os.environ.copy()
            env["CUDA_VISIBLE_DEVICES"] = uuid
            subprocess.check_call(
                [
                    sys.executable,
                    "-c",
                    "import torch; assert torch.cuda.is_available()",
                ],
                env=env,
                stderr=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
            )
            return uuid
        except Exception:
            continue
    return None
