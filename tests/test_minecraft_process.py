import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from src.plauncher.services.minecraft_process import MinecraftProcessService


class MinecraftProcessServiceTests(unittest.TestCase):
    def test_streams_output_and_exposes_process(self):
        process = SimpleNamespace(
            _handle=10,
            stdout=[b"hello\r\n", b"world\n"],
            wait=Mock(return_value=0),
        )
        process_api = SimpleNamespace(
            Popen=Mock(return_value=process),
            PIPE=-1,
            STDOUT=-2,
            TimeoutExpired=TimeoutError,
        )
        job_api = SimpleNamespace(
            CreateJobObject=Mock(return_value="job"),
            QueryInformationJobObject=Mock(return_value={"BasicLimitInformation": {}}),
            JobObjectExtendedLimitInformation=1,
            JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE=2,
            SetInformationJobObject=Mock(),
            AssignProcessToJobObject=Mock(),
        )
        started = []
        output = []
        with tempfile.TemporaryDirectory() as directory:
            service = MinecraftProcessService(job_api, process_api)
            process_result, log_file = service.run(
                ["java"],
                directory,
                True,
                f"{directory}/minecraft.log",
                lambda current, stream: started.append((current, stream)),
                output.append,
            )
            self.assertIs(process_result, process)
            self.assertIs(started[0][0], process)
            self.assertEqual(output, ["hello\n", "world\n"])
            log_file.seek(0)
            self.assertEqual(log_file.read(), "hello\nworld\n")
            log_file.close()

    def test_stop_terminates_process(self):
        process = SimpleNamespace(
            terminate=Mock(),
            wait=Mock(return_value=0),
            kill=Mock(),
        )
        service = MinecraftProcessService(
            SimpleNamespace(),
            SimpleNamespace(TimeoutExpired=TimeoutError),
        )
        service.stop(process)
        process.terminate.assert_called_once()
        process.wait.assert_called_once_with(timeout=5)


if __name__ == "__main__":
    unittest.main()
