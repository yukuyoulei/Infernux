"""Type stubs for Infernux.components.script_loader."""

from __future__ import annotations

from typing import Dict, List, Optional, Type

from .component import InxComponent


class ScriptLoadError(Exception):
    """Raised when a script cannot be loaded or contains no valid components."""
    ...


def set_script_error(file_path: str, message: str) -> None: ...
def get_script_errors() -> Dict[str, str]: ...
def has_script_errors() -> bool: ...
def get_script_error_by_path(file_path: str) -> Optional[str]: ...


def get_component_names_from_file(file_path: str, asset_database: Optional[object] = ...) -> List[str]:
    """Return attachable component names declared by a script file."""
    ...


def load_component_from_file(file_path: str) -> Type[InxComponent]:
    """Load the single attachable component class from a script file."""
    ...


def load_all_components_from_file(file_path: str) -> List[Type[InxComponent]]:
    """Load all attachable component classes from a script file."""
    ...


def create_component_instance(component_class: Type[InxComponent]) -> InxComponent: ...


def load_and_create_component(
    file_path: str,
    asset_database: Optional[object] = ...,
    type_name: str = ...,
) -> Optional[InxComponent]:
    """Load a component from file and create an instance."""
    ...


def get_component_info(component_class: Type[InxComponent]) -> dict: ...
