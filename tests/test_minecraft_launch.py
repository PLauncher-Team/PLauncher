import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from src.plauncher.services.minecraft_launch import MinecraftLaunchService


class MinecraftLaunchServiceTests(unittest.TestCase):
    def test_builds_command_with_memory_and_custom_arguments(self):
        launcher_api = SimpleNamespace(
            command=SimpleNamespace(get_minecraft_command=Mock(return_value=["java", "Minecraft"])),
            runtime=SimpleNamespace(get_version_runtime_information=Mock(return_value={"javaMajorVersion": 21})),
        )
        java_runtime = SimpleNamespace(get_any_java_exe=Mock(return_value="C:/Java/java.exe"))
        with tempfile.TemporaryDirectory() as directory:
            service = MinecraftLaunchService(
                minecraft_directory=directory,
                launcher_directory=directory,
                launcher_api=launcher_api,
                java_runtime=java_runtime,
                online=False,
            )
            command, options = service.build_command(
                selected_version="1.20.4",
                work_folder=directory,
                username="Alex",
                uuid="player-id",
                memory_megabytes="4096",
                custom_arguments=["-Dcustom=true"],
                java_choice="Latest",
                check_java=False,
                use_ely_by=False,
            )
            self.assertEqual(command, ["java", "Minecraft"])
            self.assertEqual(options["username"], "Alex")
            self.assertEqual(options["uuid"], "player-id")
            self.assertIn("-Xmx4096M", options["jvmArguments"])
            self.assertIn("-Dcustom=true", options["jvmArguments"])
            self.assertEqual(options["executablePath"], "C:/Java/java.exe")

    def test_explicit_java_path_is_used(self):
        launcher_api = SimpleNamespace(
            command=SimpleNamespace(get_minecraft_command=Mock(return_value=["java"])),
            runtime=SimpleNamespace(get_version_runtime_information=Mock()),
        )
        java_runtime = SimpleNamespace(get_any_java_exe=Mock())
        with tempfile.TemporaryDirectory() as directory:
            service = MinecraftLaunchService(directory, directory, launcher_api, java_runtime, False)
            _, options = service.build_command(
                "1.20.4",
                directory,
                "Alex",
                "player-id",
                "2048",
                [],
                "D:/Java/bin/java.exe",
                False,
                True,
            )
            self.assertEqual(options["executablePath"], "D:/Java/bin/java.exe")
            self.assertTrue(any(argument.startswith("-javaagent:") for argument in options["jvmArguments"]))


if __name__ == "__main__":
    unittest.main()
