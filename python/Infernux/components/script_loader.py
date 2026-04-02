"""
Script component loading helpers.

Supports:
- Engine/internal Python component sources (kept for editor internals)
- Project C# script components via editor-side placeholder component types

Project-authored Python scripts are no longer supported as gameplay components.
"""

from __future__ import annotations

import hashlib
import importlib
import importlib.util
import inspect
import os
import re
import sys
from typing import Optional, Type

from Infernux.engine.project_context import (
    get_assets_root,
    get_script_module_aliases,
    resolve_script_path,
    temporary_script_import_paths,
)

from .component import InxComponent


class ScriptLoadError(Exception):
    """Raised when a script cannot be loaded or doesn't contain valid components."""


# Maps normalized absolute path -> error message string
_script_errors: dict[str, str] = {}

# Cache for editor-side placeholder classes representing external script types.
_external_component_types: dict[tuple[str, str, str], Type[InxComponent]] = {}

_CS_COMPONENT_RE = re.compile(
    r"^\s*(?:(?:public|internal|protected|private|abstract|sealed|static|partial)\s+)*"
    r"class\s+([A-Za-z_][A-Za-z0-9_]*)\s*:\s*[^{\n]*\bInxComponent\b",
    re.MULTILINE,
)


def _normalize_path(file_path: str) -> str:
    return os.path.normcase(os.path.normpath(os.path.abspath(file_path)))


def _is_python_script(file_path: str) -> bool:
    return file_path.lower().endswith((".py", ".pyc"))


def _is_csharp_script(file_path: str) -> bool:
    return file_path.lower().endswith(".cs")


def _is_project_user_python_script(file_path: str) -> bool:
    assets_root = get_assets_root()
    if not assets_root:
        return False
    resolved = _normalize_path(file_path)
    assets_root = _normalize_path(assets_root)
    try:
        return os.path.commonpath([resolved, assets_root]) == assets_root
    except ValueError:
        return False


def _read_text(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def _split_csv(value: str) -> list[str]:
    return [part.strip() for part in (value or "").split(",") if part.strip()]


def _get_asset_database(asset_database=None):
    if asset_database is not None:
        return asset_database
    try:
        from Infernux.core.assets import AssetManager

        return getattr(AssetManager, "_asset_database", None)
    except Exception:
        return None


def _try_get_script_meta(file_path: str, asset_database=None):
    db = _get_asset_database(asset_database)
    if db is None:
        return None

    resolved = resolve_script_path(file_path)
    if not resolved:
        return None

    try:
        if not db.get_guid_from_path(resolved):
            db.import_asset(resolved)
    except Exception:
        pass

    try:
        return db.get_meta_by_path(resolved)
    except Exception:
        return None


def _get_script_language(file_path: str, asset_database=None) -> str:
    resolved = resolve_script_path(file_path) or file_path
    meta = _try_get_script_meta(resolved, asset_database=asset_database)
    if meta is not None and meta.has_key("language"):
        language = (meta.get_string("language") or "").strip().lower()
        if language:
            return language
    if _is_csharp_script(resolved):
        return "csharp"
    if _is_python_script(resolved):
        return "python"
    return "script"


def _parse_csharp_component_names(file_path: str) -> list[str]:
    source = _read_text(file_path)
    return [match.group(1) for match in _CS_COMPONENT_RE.finditer(source)]


def _unique_module_name_for_path(file_path: str) -> str:
    """Build a fallback module name for scripts without a valid import path."""
    normalized_path = os.path.normcase(os.path.normpath(file_path))
    module_name = os.path.splitext(os.path.basename(file_path))[0]
    path_hash = hashlib.md5(normalized_path.encode()).hexdigest()[:8]
    return f"infernux_script_{module_name}_{path_hash}"


def _clear_loaded_script_modules(module_names: list[str]) -> None:
    """Drop cached script modules and clear serialized-field metadata."""
    if not module_names:
        return

    from .serialized_field import clear_serialized_fields_cache

    seen_module_ids: set[int] = set()
    for module_name in module_names:
        old_module = sys.modules.get(module_name)
        if old_module is None or id(old_module) in seen_module_ids:
            continue
        seen_module_ids.add(id(old_module))

        old_module_name = getattr(old_module, "__name__", "")
        for _, obj in inspect.getmembers(old_module, inspect.isclass):
            if getattr(obj, "__module__", None) != old_module_name:
                continue
            if "_serialized_fields_" in obj.__dict__:
                clear_serialized_fields_cache(obj)
                obj._serialized_fields_ = {}

    for module_name in module_names:
        sys.modules.pop(module_name, None)


def _record_script_error(file_path: str, exc: Exception) -> None:
    """Record that *file_path* failed to load with *exc*."""
    import traceback

    norm = _normalize_path(file_path)
    tb_str = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    _script_errors[norm] = tb_str
    try:
        from Infernux.debug import Debug

        Debug.log_error(tb_str, source_file=file_path, source_line=0)
    except ImportError:
        print(tb_str, file=sys.stderr)


def set_script_error(file_path: str, message: str) -> None:
    """Record an error message for a script (no exception object needed)."""
    _script_errors[_normalize_path(file_path)] = message


def _clear_script_error(file_path: str) -> None:
    """Clear any previously recorded error for *file_path*."""
    _script_errors.pop(_normalize_path(file_path), None)


def get_script_errors() -> dict[str, str]:
    """Return a snapshot of all currently broken scripts {path: traceback}."""
    return dict(_script_errors)


def has_script_errors() -> bool:
    """Return True if any loaded script has unresolved errors."""
    return bool(_script_errors)


def get_script_error_by_path(file_path: str) -> Optional[str]:
    """Return the error string for *file_path*, or ``None`` if it loaded OK."""
    return _script_errors.get(_normalize_path(file_path))


def _get_external_component_class(
    type_name: str,
    *,
    language: str,
    script_path: str,
) -> Type[InxComponent]:
    normalized_path = _normalize_path(script_path)
    cache_key = (language, normalized_path, type_name)
    cached = _external_component_types.get(cache_key)
    if cached is not None:
        return cached

    module_hash = hashlib.md5(f"{language}:{normalized_path}:{type_name}".encode("utf-8")).hexdigest()[:10]
    module_name = f"infernux_external_{module_hash}"
    component_class = type(
        type_name,
        (InxComponent,),
        {
            "__module__": module_name,
            "__doc__": f"Editor placeholder for external {language} script component '{type_name}'.",
            "_component_category_": "Scripts",
            "_external_script_language_": language,
            "_external_script_path_": normalized_path,
            "_external_script_component_": True,
        },
    )
    _external_component_types[cache_key] = component_class
    return component_class


def _load_python_component_classes(file_path: str) -> list[Type[InxComponent]]:
    """Load all InxComponent subclasses from an internal Python script file."""
    if _is_project_user_python_script(file_path):
        raise ScriptLoadError(
            "Project Python scripts are no longer supported. Use C# scripts (.cs) instead."
        )

    module_aliases = get_script_module_aliases(file_path)
    primary_module_name = module_aliases[0] if module_aliases else _unique_module_name_for_path(file_path)
    modules_to_clear = list(module_aliases)
    legacy_unique_name = _unique_module_name_for_path(file_path)
    if legacy_unique_name not in modules_to_clear:
        modules_to_clear.append(legacy_unique_name)
    _clear_loaded_script_modules(modules_to_clear)

    importlib.invalidate_caches()

    try:
        with temporary_script_import_paths(file_path):
            if module_aliases:
                module = importlib.import_module(primary_module_name)
            else:
                spec = importlib.util.spec_from_file_location(primary_module_name, file_path)
                if spec is None or spec.loader is None:
                    raise ScriptLoadError(f"Failed to create module spec for {file_path}")
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
    except Exception as exc:
        _record_script_error(file_path, exc)
        return []

    _clear_script_error(file_path)

    sys.modules[primary_module_name] = module
    for alias in module_aliases[1:]:
        sys.modules[alias] = module

    components = []
    for _, obj in inspect.getmembers(module, inspect.isclass):
        if issubclass(obj, InxComponent) and obj is not InxComponent:
            if obj.__module__ == primary_module_name:
                components.append(obj)
    return components


def get_component_names_from_file(file_path: str, asset_database=None) -> list[str]:
    """Return attachable component type names declared by *file_path*."""
    file_path = resolve_script_path(file_path)
    if not file_path or not os.path.exists(file_path):
        raise ScriptLoadError(f"Script file not found: {file_path}")

    if _is_python_script(file_path):
        return [cls.__name__ for cls in _load_python_component_classes(file_path)]

    if _is_csharp_script(file_path):
        meta = _try_get_script_meta(file_path, asset_database=asset_database)
        if meta is not None and meta.has_key("component_classes"):
            component_names = _split_csv(meta.get_string("component_classes"))
            if component_names:
                return component_names
        return _parse_csharp_component_names(file_path)

    raise ScriptLoadError(f"Unsupported script file: {file_path}")


def load_component_from_file(file_path: str) -> Type[InxComponent]:
    """
    Load the first attachable component class from a script file.

    For C# scripts this returns an editor-side placeholder component type with
    the same class name so scenes can reference and serialize it.
    """
    components = load_all_components_from_file(file_path)
    if not components:
        raise ScriptLoadError(f"No InxComponent subclasses found in {file_path}")
    if len(components) > 1:
        names = ", ".join(cls.__name__ for cls in components)
        raise ScriptLoadError(
            f"Script '{file_path}' defines multiple InxComponent classes ({names}). "
            "Dragging or attaching by script file requires exactly one component class."
        )
    return components[0]


def load_all_components_from_file(file_path: str) -> list[Type[InxComponent]]:
    """
    Load all attachable component classes declared by *file_path*.

    Project C# scripts produce placeholder component classes; internal Python
    scripts are still imported normally for editor-only systems.
    """
    file_path = resolve_script_path(file_path)
    if not file_path or not os.path.exists(file_path):
        raise ScriptLoadError(f"Script file not found: {file_path}")

    if _is_python_script(file_path):
        return _load_python_component_classes(file_path)

    if _is_csharp_script(file_path):
        type_names = get_component_names_from_file(file_path)
        language = _get_script_language(file_path)
        return [
            _get_external_component_class(type_name, language=language, script_path=file_path)
            for type_name in type_names
        ]

    raise ScriptLoadError(f"Unsupported script file: {file_path}")


def load_component_class_from_file(file_path: str, type_name: str = "") -> Optional[Type[InxComponent]]:
    """Load a specific component class from a script file."""
    components = load_all_components_from_file(file_path)
    if not components:
        return None

    if type_name:
        for component_class in components:
            if component_class.__name__ == type_name:
                return component_class
        return None

    if len(components) != 1:
        return None

    return components[0]


def create_component_instance(component_class: Type[InxComponent]) -> InxComponent:
    """Create an instance of a component class."""
    return component_class()


def load_and_create_component(file_path: str, asset_database=None, type_name: str = "") -> Optional[InxComponent]:
    """
    Load a component from *file_path* and create an instance.

    Returns ``None`` if the script has errors or declares no matching component.
    """
    if asset_database is None:
        raise ScriptLoadError("AssetDatabase is required for script components (GUID-only mode)")

    try:
        component_class = load_component_class_from_file(file_path, type_name=type_name)
    except ScriptLoadError:
        return None

    if component_class is None:
        return None

    instance = create_component_instance(component_class)
    resolved_path = resolve_script_path(file_path) or file_path
    guid = asset_database.get_guid_from_path(resolved_path)
    if not guid:
        guid = asset_database.import_asset(resolved_path)
    if not guid:
        raise ScriptLoadError(f"Failed to resolve GUID for script: {resolved_path}")
    instance._script_guid = guid
    return instance


def get_component_info(component_class: Type[InxComponent]) -> dict:
    """Extract metadata from a component class."""
    from .serialized_field import get_serialized_fields

    return {
        "name": component_class.__name__,
        "module": component_class.__module__,
        "docstring": inspect.getdoc(component_class) or "",
        "fields": list(get_serialized_fields(component_class).keys()),
    }


if __name__ == "__main__":
    if len(sys.argv) > 1:
        script_path = sys.argv[1]
        print(f"Loading components from: {script_path}")

        components = load_all_components_from_file(script_path)
        print(f"Found {len(components)} component(s):")

        for comp_class in components:
            info = get_component_info(comp_class)
            print(f"\n  - {info['name']}")
            print(f"    Doc: {info['docstring'][:50]}...")
            print(f"    Fields: {info['fields']}")

            instance = create_component_instance(comp_class)
            print("    [OK] Instantiation successful")

    else:
        print("Usage: python script_loader.py <path_to_script>")
