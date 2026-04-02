"""ResourcesManager - file-system watcher for live asset reloading.

Monitors the project's asset directory for changes and triggers
shader / script validation automatically.

Example::

    mgr = ResourcesManager(project_path, engine)
    mgr.start()
    # in frame loop:
    mgr.process_pending_reloads()
    # on shutdown:
    mgr.cleanup()
"""

from __future__ import annotations

from typing import Callable, Optional


class ResourcesManager:
    """Watches the project file system and dispatches asset reload events."""

    @classmethod
    def instance(cls) -> Optional[ResourcesManager]:
        """Return the singleton, or ``None`` if not yet created."""
        ...

    def __init__(self, project_path: str, engine: object) -> None: ...

    def start(self) -> None:
        """Start the file-system observer thread."""
        ...

    def stop(self) -> None:
        """Stop the observer thread."""
        ...

    def is_running(self) -> bool: ...

    def cleanup(self) -> None:
        """Stop the observer and release all resources."""
        ...

    def process_pending_reloads(self) -> None:
        """Process pending script / shader reload requests (call per frame)."""
        ...

    def register_script_reload_callback(self, file_path: str, callback: Callable) -> None:
        """Register a callback for when *file_path* is modified.

        Args:
            file_path: Absolute path to the script.
            callback: Callable invoked on file change.
        """
        ...

    def unregister_script_reload_callback(self, callback: Callable) -> None: ...

    def register_script_catalog_callback(self, callback: Callable) -> None:
        """Register a callback for script-source creation/deletion events."""
        ...

    def unregister_script_catalog_callback(self, callback: Callable) -> None: ...

    def notify_script_catalog_changed(self, file_path: str, event_type: str) -> None: ...

    def register_shader_cache_callback(self, callback: Callable) -> None: ...


class ResourceChangeHandler:
    """File-system event handler that triggers asset reloads."""

    def __init__(self, engine: object) -> None: ...
    def on_created(self, event: object) -> None: ...
    def on_deleted(self, event: object) -> None: ...
    def on_modified(self, event: object) -> None: ...
    def on_moved(self, event: object) -> None: ...
    def process_pending_reloads(self) -> None: ...
    def register_shader_cache_callback(self, callback: Callable) -> None: ...
