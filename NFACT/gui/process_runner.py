"""
Subprocess execution runner with background thread streaming and SIGINT termination.
"""

import os
import queue
import signal
import subprocess
import sys
import threading
import time
from typing import Callable, Optional


class ProcessRunner:
    """
    Class to manage non-blocking execution of CLI commands with thread-safe output streaming.

    Usage
    -----
    runner = ProcessRunner()
    runner.start_process(command_list, workdir, on_line, on_complete)
    runner.terminate_process()
    """

    def __init__(self) -> None:
        """
        Initialize the process runner instance.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        self.process: Optional[subprocess.Popen] = None
        self.reader_thread: Optional[threading.Thread] = None
        self.is_running = False
        self.start_timestamp = 0.0
        self.command_queue: queue.Queue = queue.Queue()
        self.current_command: list = []

    def start_process(
        self,
        command_list: list,
        working_directory: str,
        on_line_callback: Callable[[str], None],
        on_complete_callback: Callable[[int, float], None],
        environment_override: dict = None,
    ) -> bool:
        """
        Start an external process asynchronously and stream its stdout/stderr.

        Parameters
        ----------
        command_list: list
            Command arguments to execute.
        working_directory: str
            Working directory path.
        on_line_callback: Callable
            Function invoked with each line of output.
        on_complete_callback: Callable
            Function invoked when process terminates (returncode, elapsed_seconds).
        environment_override: dict, optional
            Optional environment variables to inject.

        Returns
        -------
        started: bool
            True if process was successfully spawned, False otherwise.
        """
        if self.is_running:
            return False

        # If the first token is one of the NFACT scripts, execute via sys.executable -m
        executable_command = list(command_list)
        first_token = executable_command[0]

        module_mapping = {
            "nfact": "NFACT.pipeline",
            "nfact_pp": "NFACT.preprocess",
            "nfact_decomp": "NFACT.decomp",
            "nfact_Qc": "NFACT.qc",
            "nfact_dr": "NFACT.dual_reg",
            "nfact_stats": "NFACT.stats",
            "nfact_config": "NFACT.config",
        }

        if first_token in module_mapping:
            executable_command = [
                sys.executable,
                "-m",
                module_mapping[first_token],
            ] + executable_command[1:]

        environment = os.environ.copy()
        environment["PYTHONUNBUFFERED"] = "1"
        if environment_override:
            environment.update(environment_override)

        try:
            self.process = subprocess.Popen(
                executable_command,
                cwd=working_directory,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True,
                env=environment,
            )
            self.is_running = True
            self.start_timestamp = time.time()
            self.current_command = command_list
        except Exception as error_exception:
            on_line_callback(
                f"\x1b[1;31mFailed to start process: {error_exception}\x1b[0;0m\n"
            )
            on_complete_callback(1, 0.0)
            return False

        def stream_worker() -> None:
            """
            Background worker function to read stdout line by line.

            Parameters
            ----------
            None

            Returns
            -------
            None
            """
            try:
                for line in iter(self.process.stdout.readline, ""):
                    on_line_callback(line)
            except Exception:
                pass
            finally:
                if self.process:
                    self.process.stdout.close()
                    exit_code = self.process.wait()
                else:
                    exit_code = 1

                elapsed_duration = time.time() - self.start_timestamp
                self.is_running = False
                on_complete_callback(exit_code, elapsed_duration)

        self.reader_thread = threading.Thread(target=stream_worker, daemon=True)
        self.reader_thread.start()
        return True

    def terminate_process(self) -> None:
        """
        Request cancellation of the running process via SIGINT, escalating to SIGKILL if necessary.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        if not self.is_running or not self.process:
            return

        try:
            # Send SIGINT first to allow NFACT's Signit_handler to clean up
            if os.name == "nt":
                self.process.terminate()
            else:
                self.process.send_signal(signal.SIGINT)

            # Wait up to 2 seconds for graceful exit
            self.process.wait(timeout=2.0)
        except subprocess.TimeoutExpired:
            # Escalate to termination
            try:
                self.process.terminate()
                self.process.wait(timeout=1.0)
            except Exception:
                # Force kill if still unresponsive
                try:
                    self.process.kill()
                except Exception:
                    pass
        except Exception:
            pass
        finally:
            self.is_running = False
