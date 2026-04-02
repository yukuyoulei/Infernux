import datetime
import glob
import json
import os
import re
import shutil
import subprocess
import sys

from hub_utils import is_frozen, is_project_open
from Infernux.engine.csharp_tooling import (
    CSHARP_GENERATED_DIR,
    CSHARP_PROJECT_DIR,
    CSHARP_PROJECT_FILE,
    CSHARP_STUBS_FILE,
    DEFAULT_CSHARP_SCRIPT,
    ensure_csharp_tooling,
    sanitize_csharp_identifier,
)
from python_runtime import PythonRuntimeError, PythonRuntimeManager

# Suppress console windows for all child processes on Windows
_NO_WINDOW: int = 0x08000000 if sys.platform == "win32" else 0


def _popen_kwargs(*, capture_output: bool = False) -> dict:
    """Common subprocess kwargs: suppress console window for child processes."""
    kw: dict = {"stdin": subprocess.DEVNULL}
    if capture_output:
        kw["stdout"] = subprocess.PIPE
        kw["stderr"] = subprocess.PIPE
        kw["text"] = True
        kw["encoding"] = "utf-8"
        kw["errors"] = "replace"
    else:
        kw["stdout"] = subprocess.DEVNULL
        kw["stderr"] = subprocess.DEVNULL
    if sys.platform == "win32":
        kw["creationflags"] = _NO_WINDOW
    return kw


def _run_hidden(args: list[str], *, timeout: int) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            args,
            check=True,
            timeout=timeout,
            **_popen_kwargs(capture_output=True),
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(
            f"Command timed out after {timeout} s.\n{' '.join(args)}"
        ) from exc
    except subprocess.CalledProcessError as exc:
        details = _summarize_output(exc.stderr or exc.stdout)
        raise RuntimeError(
            f"Command failed (exit code {exc.returncode}).\n{' '.join(args)}\n{details}"
        ) from exc


def _summarize_output(output: str) -> str:
    text = (output or "").strip()
    if not text:
        return "No diagnostic output was produced."
    lines = text.splitlines()
    return "\n".join(lines[-20:])


_NATIVE_IMPORT_SMOKE_TEST = (
    "import Infernux.lib\n"
    "print('INFERNUX_NATIVE_IMPORT_OK')\n"
)


def _find_dev_wheel() -> str:
    """Find the Infernux wheel in the dist/ directory next to the engine source."""
    engine_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    dist_dir = os.path.join(engine_root, "dist")
    wheels = glob.glob(os.path.join(dist_dir, "infernux-*.whl"))
    if wheels:
        wheels.sort(key=os.path.getmtime, reverse=True)
        return wheels[0]
    return ""


class ProjectModel:
    CSHARP_PROJECT_DIR = CSHARP_PROJECT_DIR
    CSHARP_PROJECT_FILE = CSHARP_PROJECT_FILE
    CSHARP_GENERATED_DIR = CSHARP_GENERATED_DIR
    CSHARP_STUBS_FILE = CSHARP_STUBS_FILE
    DEFAULT_CSHARP_SCRIPT = DEFAULT_CSHARP_SCRIPT

    def __init__(self, db, version_manager=None, runtime_manager=None):
        self.db = db
        self.version_manager = version_manager
        self.runtime_manager = runtime_manager or PythonRuntimeManager()

    def add_project(self, name, path):
        return self.db.add_project(name, path)

    def delete_project(self, name):
        base_path = self.db.get_project_path(name)
        project_dir = os.path.join(base_path, name) if base_path else ""

        if project_dir and is_project_open(project_dir):
            raise RuntimeError(
                f"The project is currently open in Infernux and cannot be deleted:\n{project_dir}"
            )

        if project_dir and os.path.exists(project_dir):
            try:
                shutil.rmtree(project_dir)
            except OSError as exc:
                raise RuntimeError(
                    f"Failed to remove the project folder:\n{project_dir}\n{exc}"
                ) from exc

        self.db.delete_project(name)

    def init_project_folder(self, project_name: str, project_path: str, engine_version: str = ""):
        project_dir = os.path.join(project_path, project_name)
        os.makedirs(project_dir, exist_ok=True)

        for subdir in (
            "ProjectSettings",
            "Logs",
            "Library",
            "Assets",
            os.path.join("Assets", "Scripts"),
            self.CSHARP_PROJECT_DIR,
            self.CSHARP_GENERATED_DIR,
        ):
            os.makedirs(os.path.join(project_dir, subdir), exist_ok=True)

        readme_path = os.path.join(project_dir, "Assets", "README.md")
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(
                "# Project Assets\n\n"
                "This folder contains all the assets for the project.\n\n"
                "- Gameplay scripts default to C# and live under `Assets/Scripts/`.\n"
                f"- The generated script project is `{self.CSHARP_PROJECT_DIR}/{self.CSHARP_PROJECT_FILE}`.\n"
            )

        ini_path = os.path.join(project_dir, f"{project_name}.ini")
        now = datetime.datetime.now()
        with open(ini_path, "w", encoding="utf-8") as f:
            f.write("[Project]\n")
            f.write(f"name = {project_name}\n")
            f.write(f"path = {project_dir}\n")
            f.write(f"created_at = {now}\n")
            f.write(f"changed_at = {now}\n")
            f.write("scripting_language = csharp\n")

        if engine_version:
            from version_manager import VersionManager

            VersionManager.write_project_version(project_dir, engine_version)

        try:
            self._create_project_runtime(project_dir)
            self._install_infernux_in_runtime(project_dir, engine_version)
        except Exception:
            shutil.rmtree(os.path.join(project_dir, ".runtime"), ignore_errors=True)
            raise

        self._create_csharp_tooling(project_dir, project_name)
        self._create_vscode_workspace(project_dir)

    @staticmethod
    def _sanitize_csharp_identifier(name: str) -> str:
        return sanitize_csharp_identifier(name)

    def _create_csharp_tooling(self, project_dir: str, project_name: str) -> None:
        ensure_csharp_tooling(project_dir, project_name)

    @staticmethod
    def _get_project_python(project_dir: str) -> str:
        """Return the Python executable for the project."""
        if is_frozen():
            runtime_dir = os.path.join(project_dir, ".runtime", "python312")
            if sys.platform == "win32":
                return os.path.join(runtime_dir, "python.exe")
            return os.path.join(runtime_dir, "bin", "python")
        venv_dir = os.path.join(project_dir, ".venv")
        if sys.platform == "win32":
            return os.path.join(venv_dir, "Scripts", "python.exe")
        return os.path.join(venv_dir, "bin", "python")

    def _create_project_runtime(self, project_dir: str) -> None:
        if is_frozen():
            runtime_path = os.path.join(project_dir, ".runtime", "python312")
            try:
                self.runtime_manager.create_project_runtime(runtime_path)
            except PythonRuntimeError as exc:
                raise RuntimeError(str(exc)) from exc
            return

        venv_path = os.path.join(project_dir, ".venv")
        _run_hidden([sys.executable, "-m", "venv", "--copies", venv_path], timeout=600)

    def _install_infernux_in_runtime(self, project_dir: str, engine_version: str = ""):
        """Install the Infernux wheel into the project's Python environment."""
        project_python = ProjectModel._get_project_python(project_dir)
        if not os.path.isfile(project_python):
            raise RuntimeError(
                f"Project Python not found at {project_python}.\n"
                "The project runtime may not have been created correctly."
            )

        wheel = ""
        if engine_version and self.version_manager is not None:
            wheel = self.version_manager.get_wheel_path(engine_version) or ""
        if not wheel and not is_frozen():
            wheel = _find_dev_wheel()

        if not wheel:
            if is_frozen():
                raise RuntimeError(
                    f"No downloaded Infernux wheel was found for version {engine_version or '(unknown)'}.\n"
                    "Open the Installs page and install that engine version first."
                )
            raise RuntimeError(
                "No prebuilt Infernux wheel was found in dist/.\n"
                "Build a wheel first; project creation will not fall back to a source build."
            )

        pip_flags = [
            "--no-input",
            "--disable-pip-version-check",
            "--prefer-binary",
            "--only-binary=:all:",
        ]
        _run_hidden(
            [project_python, "-m", "pip", "install", "--force-reinstall", *pip_flags, wheel],
            timeout=600,
        )
        ProjectModel.validate_python_runtime(project_python)

    @staticmethod
    def validate_python_runtime(project_python: str) -> None:
        if not os.path.isfile(project_python):
            raise RuntimeError(
                f"Project Python not found at {project_python}.\n"
                "The project runtime may not have been created correctly."
            )
        _run_hidden([project_python, "-c", _NATIVE_IMPORT_SMOKE_TEST], timeout=120)

    @staticmethod
    def validate_project_runtime(project_dir: str) -> None:
        ProjectModel.validate_python_runtime(ProjectModel._get_project_python(project_dir))

    @staticmethod
    def _create_vscode_workspace(project_dir: str):
        """Create .vscode config aimed at the generated C# script project."""
        vscode_dir = os.path.join(project_dir, ".vscode")
        os.makedirs(vscode_dir, exist_ok=True)

        settings = {
            "editor.formatOnSave": True,
            "omnisharp.enableRoslynAnalyzers": True,
            "omnisharp.enableEditorConfigSupport": True,
            "dotnet.server.useOmnisharp": False,
            "files.exclude": {
                "**/__pycache__": True,
                "**/*.pyc": True,
                "**/*.meta": True,
                "**/bin": True,
                "**/obj": True,
                ".vs": True,
                ".venv": True,
                ".runtime": True,
                "Library": True,
                "Logs": True,
            },
        }
        settings_path = os.path.join(vscode_dir, "settings.json")
        with open(settings_path, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4, ensure_ascii=False)

        extensions = {
            "recommendations": [
                "ms-dotnettools.csdevkit",
                "ms-dotnettools.csharp",
            ]
        }
        extensions_path = os.path.join(vscode_dir, "extensions.json")
        with open(extensions_path, "w", encoding="utf-8") as f:
            json.dump(extensions, f, indent=4, ensure_ascii=False)
