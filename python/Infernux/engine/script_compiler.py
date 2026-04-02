"""
ScriptCompiler - validation for user script sources.

Supports:
- Python syntax validation for legacy ``.py`` scripts
- C# project compilation for ``.cs`` scripts via ``dotnet build``
"""

from __future__ import annotations

import ast
import os
import py_compile
import re
import subprocess
from dataclasses import dataclass
from typing import List, Optional

from Infernux.engine.csharp_tooling import ensure_csharp_tooling
from Infernux.debug import Debug
from Infernux.engine.project_context import get_project_root


@dataclass
class ScriptError:
    """Represents a script compilation error."""

    file_path: str
    line_number: int
    column: int
    message: str
    error_type: str

    def __str__(self) -> str:
        return f"{os.path.basename(self.file_path)}:{self.line_number}:{self.column}: {self.message}"


class ScriptCompiler:
    """Validates Python and C# scripts for errors."""

    _DOTNET_ERROR_RE = re.compile(
        r"^(?P<file>.+?)\((?P<line>\d+),(?P<col>\d+)\):\s+"
        r"(?P<severity>error|warning)\s+"
        r"(?P<code>[A-Za-z]+\d+):\s+"
        r"(?P<message>.+?)"
        r"(?:\s+\[.*\])?$",
        re.MULTILINE,
    )

    def __init__(self):
        self._last_errors: List[ScriptError] = []

    def check_file(self, file_path: str) -> List[ScriptError]:
        errors: List[ScriptError] = []

        if not os.path.exists(file_path):
            errors.append(
                ScriptError(
                    file_path=file_path,
                    line_number=0,
                    column=0,
                    message="File not found",
                    error_type="file",
                )
            )
            return errors

        lower_path = file_path.lower()
        if lower_path.endswith(".py"):
            errors = self._check_python_file(file_path)
        elif lower_path.endswith(".cs"):
            errors = self._check_csharp_project(file_path)

        self._last_errors = errors
        return errors

    def _check_python_file(self, file_path: str) -> List[ScriptError]:
        errors: List[ScriptError] = []

        with open(file_path, "r", encoding="utf-8") as f:
            source_code = f.read()

        syntax_errors = self._check_python_syntax(file_path, source_code)
        errors.extend(syntax_errors)
        if syntax_errors:
            return errors

        errors.extend(self._check_python_compile(file_path))
        return errors

    def _check_python_syntax(self, file_path: str, source_code: str) -> List[ScriptError]:
        errors: List[ScriptError] = []
        try:
            ast.parse(source_code, filename=file_path)
        except SyntaxError as e:
            errors.append(
                ScriptError(
                    file_path=file_path,
                    line_number=e.lineno or 0,
                    column=e.offset or 0,
                    message=str(e.msg) if hasattr(e, "msg") else str(e),
                    error_type="syntax",
                )
            )
        except Exception as e:
            errors.append(
                ScriptError(
                    file_path=file_path,
                    line_number=0,
                    column=0,
                    message=f"Unexpected error during syntax check: {e}",
                    error_type="syntax",
                )
            )
        return errors

    def _check_python_compile(self, file_path: str) -> List[ScriptError]:
        errors: List[ScriptError] = []
        try:
            py_compile.compile(file_path, doraise=True)
        except py_compile.PyCompileError as e:
            errors.append(
                ScriptError(
                    file_path=file_path,
                    line_number=getattr(e, "lineno", 0) or 0,
                    column=0,
                    message=str(e),
                    error_type="compile",
                )
            )
        except Exception as e:
            errors.append(
                ScriptError(
                    file_path=file_path,
                    line_number=0,
                    column=0,
                    message=f"Unexpected compile error: {e}",
                    error_type="compile",
                )
            )
        return errors

    def _check_csharp_project(self, file_path: str) -> List[ScriptError]:
        csproj_path = self._find_csharp_project(file_path)
        if not csproj_path:
            return [
                ScriptError(
                    file_path=file_path,
                    line_number=0,
                    column=0,
                    message="No C# script project found. Expected Scripts/Infernux.GameScripts.csproj.",
                    error_type="project",
                )
            ]

        try:
            ensure_csharp_tooling(os.path.dirname(os.path.dirname(csproj_path)))
        except Exception as exc:
            return [
                ScriptError(
                    file_path=file_path,
                    line_number=0,
                    column=0,
                    message=f"Failed to refresh generated C# tooling: {exc}",
                    error_type="tooling",
                )
            ]

        try:
            completed = subprocess.run(
                ["dotnet", "build", csproj_path, "-nologo", "-clp:ErrorsOnly"],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=180,
            )
            if completed.returncode == 0:
                return []
        except FileNotFoundError:
            return [
                ScriptError(
                    file_path=file_path,
                    line_number=0,
                    column=0,
                    message="dotnet CLI was not found. Install .NET SDK to validate C# scripts.",
                    error_type="tooling",
                )
            ]
        except subprocess.TimeoutExpired:
            return [
                ScriptError(
                    file_path=file_path,
                    line_number=0,
                    column=0,
                    message="dotnet build timed out while validating C# scripts.",
                    error_type="compile",
                )
            ]
        except subprocess.CalledProcessError as exc:
            output = "\n".join(part for part in (exc.stdout, exc.stderr) if part)
            parsed = self._parse_dotnet_errors(output, file_path)
            if parsed:
                return parsed
            return [
                ScriptError(
                    file_path=file_path,
                    line_number=0,
                    column=0,
                    message=(output.strip() or "dotnet build failed"),
                    error_type="compile",
                )
            ]

        return []

    def _find_csharp_project(self, file_path: str) -> str:
        project_root = get_project_root()
        if project_root:
            try:
                ensure_csharp_tooling(project_root)
            except Exception:
                pass
            default_path = os.path.join(project_root, "Scripts", "Infernux.GameScripts.csproj")
            if os.path.isfile(default_path):
                return default_path

        current = os.path.abspath(os.path.dirname(file_path))
        while True:
            direct_candidates = sorted(
                name for name in os.listdir(current) if name.lower().endswith(".csproj")
            ) if os.path.isdir(current) else []
            if direct_candidates:
                return os.path.join(current, direct_candidates[0])

            scripts_dir = os.path.join(current, "Scripts")
            if os.path.isdir(scripts_dir):
                script_candidates = sorted(
                    name for name in os.listdir(scripts_dir) if name.lower().endswith(".csproj")
                )
                if script_candidates:
                    return os.path.join(scripts_dir, script_candidates[0])

            parent = os.path.dirname(current)
            if parent == current:
                break
            current = parent

        return ""

    def _parse_dotnet_errors(self, output: str, fallback_file: str) -> List[ScriptError]:
        errors: List[ScriptError] = []
        for match in self._DOTNET_ERROR_RE.finditer(output or ""):
            severity = match.group("severity").lower()
            if severity != "error":
                continue
            message = f"{match.group('code')}: {match.group('message').strip()}"
            errors.append(
                ScriptError(
                    file_path=os.path.abspath(match.group("file")) if match.group("file") else fallback_file,
                    line_number=int(match.group("line")),
                    column=int(match.group("col")),
                    message=message,
                    error_type="compile",
                )
            )

        if errors:
            return errors

        text = (output or "").strip()
        if not text:
            return []
        return [
            ScriptError(
                file_path=fallback_file,
                line_number=0,
                column=0,
                message=text.splitlines()[-1],
                error_type="compile",
            )
        ]

    def check_and_report(self, file_path: str) -> bool:
        errors = self.check_file(file_path)
        if not errors:
            Debug.log_internal(f"[OK] Script compiled: {os.path.basename(file_path)}")
            return True

        for error in errors:
            error_msg = (
                f"[{error.error_type.upper()}] {error.file_path}:{error.line_number}:{error.column}\n"
                f"{error.message}"
            )
            Debug.log_error(
                error_msg,
                source_file=error.file_path,
                source_line=error.line_number,
            )
        return False


_compiler: Optional[ScriptCompiler] = None


def get_script_compiler() -> ScriptCompiler:
    """Get the global ScriptCompiler instance."""
    global _compiler
    if _compiler is None:
        _compiler = ScriptCompiler()
    return _compiler
