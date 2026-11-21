import subprocess
from pathlib import Path
from typing import Any, Callable


class MinecraftProcessService:
    def __init__(
        self,
        job_api: Any,
        process_api: Any = subprocess,
    ) -> None:
        self.job_api = job_api
        self.process_api = process_api

    def run(
        self,
        command: list[str],
        working_directory: str | Path,
        debug: bool,
        log_path: str | Path,
        on_started: Callable[[Any, Any], None],
        on_output: Callable[[str], None] | None = None,
    ) -> tuple[Any, Any]:
        log_file = Path(log_path).open("w+", encoding="utf-8")
        started = False
        try:
            job = self.job_api.CreateJobObject(None, "PLauncher_Job")
            job_info = self.job_api.QueryInformationJobObject(
                job,
                self.job_api.JobObjectExtendedLimitInformation,
            )
            job_info["BasicLimitInformation"]["LimitFlags"] = (
                self.job_api.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
            )
            self.job_api.SetInformationJobObject(
                job,
                self.job_api.JobObjectExtendedLimitInformation,
                job_info,
            )

            creation_flags = 0
            if not debug:
                creation_flags = getattr(self.process_api, "CREATE_NO_WINDOW", 0)

            process = self.process_api.Popen(
                command,
                cwd=str(working_directory),
                creationflags=creation_flags,
                stdout=self.process_api.PIPE,
                stderr=self.process_api.STDOUT,
                bufsize=-1,
            )
            self.job_api.AssignProcessToJobObject(job, int(process._handle))
            on_started(process, log_file)
            started = True

            for line_bytes in process.stdout:
                try:
                    line = line_bytes.decode("utf-8")
                except UnicodeDecodeError:
                    line = line_bytes.decode("cp1251", errors="replace")
                line = line.replace("\r\n", "\n")
                if on_output is not None:
                    on_output(line)
                log_file.write(line)

            process.wait()
            return process, log_file
        except Exception:
            if not started:
                log_file.close()
            raise

    def stop(self, process: Any, log_file: Any = None) -> None:
        if log_file is not None and not log_file.closed:
            log_file.close()
        if process is None:
            return
        process.terminate()
        try:
            process.wait(timeout=5)
        except self.process_api.TimeoutExpired:
            process.kill()
