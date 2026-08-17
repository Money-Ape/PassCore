import json, os, queue, subprocess, threading
from pathlib import Path
from threading import Lock

class PassCoreUtilityError(Exception):
    pass

class PassCoreUtility:
    DEFAULT_TIMEOUT = 30  # seconds

    def __init__(self):
        root = Path(__file__).resolve().parent
        exe_name = "PassCore.Utilities.exe" if os.name == "nt" else "PassCore.Utilities"

        self.utility = (
            root
            / "utilities"
            / "PassCore.Utilities"
            / "bin"
            / "Debug"
            / "net10.0"
            / exe_name
        )
        if not self.utility.exists():
            raise FileNotFoundError(
                f"PassCore utility executable not found:\n"
                f"{self.utility}\n\n"
                f"Build it first with:\n"
                f"dotnet build"
            )

        self.process = subprocess.Popen(
            [str(self.utility)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            bufsize=1,
        )

        self._stdout_queue: "queue.Queue[str]" = queue.Queue()
        self._stderr_lines: list[str] = []
        self._request_lock = Lock()

        self._stdout_thread = threading.Thread(target=self._read_stdout, daemon=True)
        self._stdout_thread.start()

        self._stderr_thread = threading.Thread(target=self._read_stderr, daemon=True)
        self._stderr_thread.start()

    def _read_stdout(self):
        if self.process.stdout is None:
            return

        for line in self.process.stdout:
            self._stdout_queue.put(line)

        self._stdout_queue.put("")  # signals EOF to _request()

    def _read_stderr(self):
        if self.process.stderr is None:
            return
        for line in self.process.stderr:
            self._stderr_lines.append(line)

    def _dead_process_error(self):
        exit_code = self.process.poll()
        stderr = "".join(self._stderr_lines)
        return PassCoreUtilityError(
            f"PassCore utility process is no longer running "
            f"(exit code {exit_code}).\n{stderr}"
        )

    def _request(self, operation, timeout=DEFAULT_TIMEOUT, **kwargs):
        request = {
            "operation": operation,
            **kwargs,
        }

        if self.process.stdin is None:
            raise PassCoreUtilityError("Utility stdin is unavailable.")

        with self._request_lock:
            if self.process.poll() is not None:
                raise self._dead_process_error()

            try:
                self.process.stdin.write(json.dumps(request) + "\n")
                self.process.stdin.flush()
            except OSError as exc:
                if self.process.poll() is not None:
                    raise self._dead_process_error() from exc
                raise PassCoreUtilityError(f"Failed to write to PassCore utility: {exc}") from exc

            try:
                response_line = self._stdout_queue.get(timeout=timeout)
            except queue.Empty:
                raise PassCoreUtilityError(
                    f"PassCore utility did not respond within {timeout} seconds."
                )

            if not response_line:
                stderr = "".join(self._stderr_lines)
                raise PassCoreUtilityError(
                    f"PassCore utility stopped unexpectedly.\n{stderr}"
                )

            try:
                response = json.loads(response_line)
            except json.JSONDecodeError as exc:
                raise PassCoreUtilityError(
                    f"Invalid response from PassCore utility:\n{response_line}"
                ) from exc

        if not response.get("success", False):
            raise PassCoreUtilityError(
                response.get(
                    "error",
                    "Unknown PassCore utility error."
                )
            )

        return response.get("data")

    def vault_health(self):
        return self._request("vault_health")

    def images_health(self):
        return self._request("images_health")

    def mark_vault_changed(self):
        return self._request("backup_mark_changed")

    def create_backup(self, force=False):
        return self._request("backup_create", force=force)

    def restore_backup(self, path):
        return self._request("backup_restore", path=str(path), timeout=120)

    def export_pcv(self, destination):
        return self._request("vault_export", destination=str(destination), timeout=120)

    def import_pcv(self, path):
        return self._request("vault_import", path=str(path), timeout=120)

    def close(self):
        if self.process.stdin is not None:
            try:
                self.process.stdin.close()
            except OSError:
                pass

        if self.process.poll() is None:
            self.process.terminate()

            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()