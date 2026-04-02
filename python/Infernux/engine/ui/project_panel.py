"""
Unity-style Project panel for browsing assets.

File operations and templates are in ``project_file_ops``.
Pure utilities are in ``project_utils``.
"""

import os
import ctypes
import shutil
import threading
import time
from collections import deque
from Infernux.lib import InxGUIContext, TextureLoader, InputManager
from Infernux.engine.i18n import t
import Infernux.resources as _resources
from .editor_panel import EditorPanel
from .panel_registry import editor_panel
from .theme import Theme, ImGuiCol, ImGuiStyleVar, ImGuiTreeNodeFlags
from . import project_file_ops as file_ops
from . import project_utils
from .imgui_keys import (KEY_F2, KEY_DELETE, KEY_ENTER, KEY_ESCAPE,
                         KEY_C, KEY_V, KEY_X,
                         KEY_LEFT_CTRL, KEY_RIGHT_CTRL,
                         KEY_LEFT_SHIFT, KEY_RIGHT_SHIFT)


# ---------------------------------------------------------------------------
# Module-level thumbnail pixel cache (survives panel re-creation / hot-reload)
# ---------------------------------------------------------------------------

def _downsample_texture(file_path: str, max_px: int):
    """Load *file_path* via stb and return ``(pixels, w, h)``.

    If the source image is larger than *max_px* in either dimension it is
    nearest-neighbour downsampled so the longest edge equals *max_px*.
    Returns ``list[int]`` suitable for ``upload_texture_for_imgui``.
    """
    tex_data = TextureLoader.load_from_file(file_path)
    if not tex_data or not tex_data.is_valid():
        raise ValueError("load failed")
    src_w, src_h = tex_data.width, tex_data.height
    if src_w > max_px or src_h > max_px:
        raw = tex_data.get_pixels()  # bytes – fast C++ transfer
        scale = max_px / max(src_w, src_h)
        w = max(1, int(src_w * scale))
        h = max(1, int(src_h * scale))
        pixels = []
        row_stride = src_w * 4
        for dy in range(h):
            sy = min(int((dy + 0.5) * src_h / h), src_h - 1)
            row_off = sy * row_stride
            for dx in range(w):
                sx = min(int((dx + 0.5) * src_w / w), src_w - 1)
                idx = row_off + sx * 4
                pixels.append(raw[idx])
                pixels.append(raw[idx + 1])
                pixels.append(raw[idx + 2])
                pixels.append(raw[idx + 3])
    else:
        pixels = tex_data.get_pixels_list()
        w, h = src_w, src_h
    return pixels, w, h


class _ThumbnailPixelCache:
    """Background pre-loader that holds downsampled RGBA pixels in memory.

    On ``start_preload`` a daemon thread walks the project tree, loads every
    image file via *stb*, downsamples to *max_px* and stores the pixel list.
    ``ProjectPanel._get_thumbnail`` queries this cache; if a hit is found the
    only remaining work is a fast GPU upload.
    """

    def __init__(self, max_px: int = 128):
        self._max_px = max_px
        self._lock = threading.Lock()
        # path -> (pixels: list[int], width, height, mtime_ns)
        self._data: dict = {}
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()

    # -- public API ---------------------------------------------------------

    def start_preload(self, root_path: str, extensions: set):
        """Begin (or restart) background scanning of *root_path*."""
        self.stop()
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._worker,
            args=(root_path, frozenset(extensions)),
            daemon=True,
            name="ThumbnailPreloader",
        )
        self._thread.start()

    def stop(self):
        if self._thread and self._thread.is_alive():
            self._stop.set()
            self._thread.join(timeout=3.0)
        self._thread = None

    def get(self, path: str, mtime_ns: int):
        """Return ``(pixels, w, h)`` if cached and fresh, else *None*."""
        with self._lock:
            entry = self._data.get(path)
        if entry is not None and entry[3] == mtime_ns:
            return entry[0], entry[1], entry[2]
        return None

    def put(self, path: str, pixels, w: int, h: int, mtime_ns: int):
        """Store pixel data produced by a foreground load."""
        with self._lock:
            self._data[path] = (pixels, w, h, mtime_ns)

    # -- background worker --------------------------------------------------

    def _worker(self, root_path: str, extensions: frozenset):
        import time
        for dirpath, _dirnames, filenames in os.walk(root_path):
            if self._stop.is_set():
                return
            for fname in filenames:
                if self._stop.is_set():
                    return
                ext = os.path.splitext(fname)[1].lower()
                if ext not in extensions:
                    continue
                fpath = os.path.join(dirpath, fname)
                try:
                    mtime = os.stat(fpath).st_mtime_ns
                except OSError:
                    continue
                # Already cached and fresh?
                with self._lock:
                    cached = self._data.get(fpath)
                if cached is not None and cached[3] == mtime:
                    continue
                try:
                    pixels, w, h = _downsample_texture(fpath, self._max_px)
                except Exception:
                    continue
                with self._lock:
                    self._data[fpath] = (pixels, w, h, mtime)
                # Yield GIL so the render thread stays responsive
                time.sleep(0.005)


_thumb_pixel_cache = _ThumbnailPixelCache(max_px=128)

_FILE_GRID_ICON_SIZE = 64
_FILE_GRID_PADDING = 10
_THUMBNAIL_REQUESTS_PER_FRAME = 1
_THUMBNAIL_RETRY_DELAY_SEC = 1.0


@editor_panel("Project", type_id="project", title_key="panel.project")
class ProjectPanel(EditorPanel):
    """
    Unity-style Project panel for browsing assets.
    Left: Folder tree view
    Right: File grid/list view
    Supports: Create folders, create scripts, double-click to open
    """
    
    WINDOW_TYPE_ID = "project"
    WINDOW_DISPLAY_NAME = "Project"
    
    # File extensions to hide
    HIDDEN_EXTENSIONS = {'.meta', '.pyc', '.pyo'}
    HIDDEN_PREFIXES = {'.', '__'}
    
    # Image extensions that support thumbnails
    IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.bmp', '.tga', '.gif'}
    
    # Material extensions that get CPU-rendered sphere previews
    MATERIAL_EXTENSIONS = {'.mat'}
    
    # Extension -> icon filename (without .png) mapping
    # Icons are 80x80 PNGs located in resources/icons/
    ICON_MAP = {
        # Directories
        '__dir__':  'folder',
        # Scripts
        '.py':      'script_py',
        '.lua':     'script_lua',
        '.cs':      'script_cs',
        '.cpp':     'script_cpp',
        '.c':       'script_cpp',
        '.h':       'script_cpp',
        # Shaders — each type has its own icon
        '.vert':    'shader_vert',
        '.frag':    'shader_frag',
        '.glsl':    'shader_glsl',
        '.hlsl':    'shader_hlsl',
        # Materials
        '.mat':     'material',
        # Images
        '.png':     'image',
        '.jpg':     'image',
        '.jpeg':    'image',
        '.bmp':     'image',
        '.tga':     'image',
        '.gif':     'image',
        # 3D models
        '.fbx':     'model_3d',
        '.obj':     'model_3d',
        '.gltf':    'model_3d',
        '.glb':     'model_3d',
        # Audio
        '.wav':     'audio',
        # Fonts
        '.ttf':     'font',
        '.otf':     'font',
        # Text / docs
        '.txt':     'text',
        '.md':      'readme',
        # Config
        '.json':    'config',
        '.yaml':    'config',
        '.yml':     'config',
        '.xml':     'config',
        # Scene
        '.scene':   'scene',
        # Prefab
        '.prefab':  'prefab',
    }
    
    SCRIPT_TEMPLATE = file_ops.SCRIPT_TEMPLATE
    VERTEX_SHADER_TEMPLATE = file_ops.VERTEX_SHADER_TEMPLATE
    FRAGMENT_SHADER_TEMPLATE = file_ops.FRAGMENT_SHADER_TEMPLATE
    MATERIAL_TEMPLATE = file_ops.MATERIAL_TEMPLATE

    # Thumbnail size for image previews (downsampled from original)
    THUMBNAIL_MAX_PX = 128

    # 3D model extensions that support sub-asset expansion
    MODEL_EXTENSIONS = {'.fbx', '.obj', '.gltf', '.glb', '.dae', '.3ds', '.ply', '.stl'}
    
    # Drag-drop: extension -> (payload_type, label_prefix)
    _DRAG_DROP_MAP = {
        '.cs':    ("SCRIPT_FILE",  "Script"),
        '.mat':   ("MATERIAL_FILE", "Material"),
        '.vert':  ("SHADER_FILE",  "Shader"),
        '.frag':  ("SHADER_FILE",  "Shader"),
        '.glsl':  ("SHADER_FILE",  "Shader"),
        '.hlsl':  ("SHADER_FILE",  "Shader"),
        '.png':   ("TEXTURE_FILE", "Texture"),
        '.jpg':   ("TEXTURE_FILE", "Texture"),
        '.jpeg':  ("TEXTURE_FILE", "Texture"),
        '.bmp':   ("TEXTURE_FILE", "Texture"),
        '.tga':   ("TEXTURE_FILE", "Texture"),
        '.gif':   ("TEXTURE_FILE", "Texture"),
        '.psd':   ("TEXTURE_FILE", "Texture"),
        '.hdr':   ("TEXTURE_FILE", "Texture"),
        '.pic':   ("TEXTURE_FILE", "Texture"),
        '.wav':   ("AUDIO_FILE",   "Audio"),
        '.ttf':   ("FONT_FILE",    "Font"),
        '.otf':   ("FONT_FILE",    "Font"),
        '.scene': ("SCENE_FILE",   "Scene"),
    }
    # Extensions that need GUID resolution for drag-drop
    _DRAG_DROP_GUID_MAP = {
        '.prefab': ("PREFAB_GUID", "PREFAB_FILE", "Prefab"),
        '.fbx':    ("MODEL_GUID",  "MODEL_FILE",  "Model"),
        '.obj':    ("MODEL_GUID",  "MODEL_FILE",  "Model"),
        '.gltf':   ("MODEL_GUID",  "MODEL_FILE",  "Model"),
        '.glb':    ("MODEL_GUID",  "MODEL_FILE",  "Model"),
        '.dae':    ("MODEL_GUID",  "MODEL_FILE",  "Model"),
        '.3ds':    ("MODEL_GUID",  "MODEL_FILE",  "Model"),
        '.ply':    ("MODEL_GUID",  "MODEL_FILE",  "Model"),
        '.stl':    ("MODEL_GUID",  "MODEL_FILE",  "Model"),
    }
    _PROJECT_ITEM_MOVE_TYPE = "PROJECT_PANEL_ITEM_PATH"
    _PROJECT_MOVE_PATH_TYPES = tuple(
        {payload[0] for payload in _DRAG_DROP_MAP.values()}
        | {payload[1] for payload in _DRAG_DROP_GUID_MAP.values()}
        | {_PROJECT_ITEM_MOVE_TYPE}
    )
    _PROJECT_MOVE_GUID_TYPES = tuple(payload[0] for payload in _DRAG_DROP_GUID_MAP.values())
    _PROJECT_MOVE_ACCEPT_TYPES = _PROJECT_MOVE_PATH_TYPES + _PROJECT_MOVE_GUID_TYPES

    def __init__(self, root_path: str = "", title: str = "Project", engine=None):
        super().__init__(title, window_id="project")
        self.__root_path = root_path
        # Default to Assets folder if it exists
        assets_path = os.path.join(root_path, "Assets") if root_path else ""
        if assets_path and os.path.exists(assets_path):
            self.__current_path = assets_path
        else:
            self.__current_path = root_path
        self.__selected_file = None
        self.__selected_files: list[str] = []  # Multi-select: ordered list of paths
        self.__on_file_selected = None
        self.__on_file_double_click = None
        self.__on_empty_area_clicked = None
        self.__on_state_changed = None
        self.__last_notified_current_path = self.__current_path

        # Cached breadcrumb text (avoids os.path.relpath every frame)
        self.__breadcrumb_path = ""
        self.__breadcrumb_text = ""
        
        # Engine and asset database reference
        self.__engine = engine
        self.__native_engine = None
        self.__asset_database = None
        if engine:
            self.set_engine(engine)
        
        # Directory snapshot cache: path -> snapshot dict keyed by dir mtime
        self.__dir_cache = {}
        self.__dir_tree_meta_cache = {}
        self.__augmented_items_cache = {}
        self.__label_layout_cache = {}
        self.__grid_text_line_height = 0.0

        # Thumbnail cache: path -> (texture_id, last_modified_time)
        self.__thumbnail_cache = {}
        self.__thumbnail_request_queue = deque()
        self.__thumbnail_request_keys = set()
        self.__thumbnail_retry_after = {}
        self.__thumbnail_queue_path = self.__current_path
        self.__material_mtime_cache = {}
        
        # File-type icon cache: icon_key (str) -> imgui texture id (int)
        self.__type_icon_cache = {}
        self.__type_icons_loaded = False
        
        # State for create dialogs
        self.__show_create_folder_popup = False
        self.__show_create_script_popup = False
        self.__new_item_name = ""
        self.__create_error = ""
        
        # Double-click detection state
        self.__last_clicked_file = None
        self.__last_click_time = 0.0

        # Rename state
        self.__renaming_path = None
        self.__renaming_name = ""
        self.__rename_focus_requested = False

        # Clipboard state (copy/cut)
        self.__clipboard_path = None   # Primary path of copied/cut selection
        self.__clipboard_paths: list[str] = []
        self.__clipboard_is_cut = False

        # Model asset expansion state: path -> expanded bool
        self.__expanded_models: set = set()
        # Model sub-asset cache: path -> {'slot_names': [...], 'submeshes': [...]} or None
        self.__model_sub_cache: dict = {}

        # Kick off background thumbnail pre-load
        if root_path:
            _thumb_pixel_cache.start_preload(root_path, self.IMAGE_EXTENSIONS)

    # ---- State persistence ----
    def save_state(self) -> dict:
        return {
            "current_path": self.__current_path,
        }

    def load_state(self, data: dict) -> None:
        path = data.get("current_path", "")
        if path and os.path.isdir(path):
            self.__current_path = path
    
    def set_root_path(self, path: str):
        self.__root_path = path
        self._invalidate_dir_cache()
        # Default to Assets folder
        assets_path = os.path.join(path, "Assets")
        if os.path.exists(assets_path):
            self.__current_path = assets_path
        else:
            self.__current_path = path
        # Restart background thumbnail pre-load for the new root
        if path:
            _thumb_pixel_cache.start_preload(path, self.IMAGE_EXTENSIONS)
    
    def set_on_file_selected(self, callback):
        self.__on_file_selected = callback

    def set_on_empty_area_clicked(self, callback):
        self.__on_empty_area_clicked = callback

    def set_on_state_changed(self, callback):
        self.__on_state_changed = callback

    def _notify_state_changed(self):
        if self.__on_state_changed:
            self.__on_state_changed()

    def _notify_selection_changed(self):
        if not self.__on_file_selected:
            return
        if len(self.__selected_files) == 1:
            self.__on_file_selected(self.__selected_files[0])
        else:
            self.__on_file_selected(None)

    def _get_selected_paths(self) -> list[str]:
        paths = [p for p in self.__selected_files if p and os.path.exists(p)]
        if paths:
            return paths
        if self.__selected_file and os.path.exists(self.__selected_file):
            return [self.__selected_file]
        return []

    def _has_clipboard_items(self) -> bool:
        return any(os.path.exists(path) for path in self.__clipboard_paths)

    def clear_selection(self):
        """Clear current file selection and notify listeners."""
        if self.__selected_file is not None or self.__selected_files:
            self.__selected_file = None
            self.__selected_files.clear()
            self._notify_selection_changed()

    def _notify_empty_area_clicked(self):
        if self.__on_empty_area_clicked:
            self.__on_empty_area_clicked()
    
    def set_on_file_double_click(self, callback):
        self.__on_file_double_click = callback
    
    def set_engine(self, engine):
        """Set the engine instance for resource management."""
        self.__engine = engine
        print(f"[ProjectPanel] set_engine called with: {type(engine)}")
        self.__native_engine = None
        if engine:
            # Try to get FileManager from engine
            if hasattr(engine, 'has_imgui_texture'):
                self.__native_engine = engine
            elif hasattr(engine, 'get_native_engine'):
                self.__native_engine = engine.get_native_engine()
            # Try to get AssetDatabase from engine
            if hasattr(engine, 'get_asset_database'):
                self.__asset_database = engine.get_asset_database()
            elif hasattr(engine, 'get_native_engine'):
                native = engine.get_native_engine()
                if native and hasattr(native, 'get_asset_database'):
                    self.__asset_database = native.get_asset_database()
    
    def _invalidate_dir_cache(self):
        self.__dir_cache.clear()
        self.__dir_tree_meta_cache.clear()
        self.__augmented_items_cache.clear()
        self.__label_layout_cache.clear()
        self.__model_sub_cache.clear()
        self._clear_thumbnail_request_queue()

    def _clear_thumbnail_request_queue(self):
        self.__thumbnail_request_queue.clear()
        self.__thumbnail_request_keys.clear()

    def _queue_thumbnail_request(self, kind: str, file_path: str):
        if not file_path:
            return

        retry_key = (kind, file_path)
        if self.__thumbnail_retry_after.get(retry_key, 0.0) > time.monotonic():
            return

        request = (self.__current_path, kind, file_path)
        if request in self.__thumbnail_request_keys:
            return

        self.__thumbnail_request_queue.append(request)
        self.__thumbnail_request_keys.add(request)

    def _get_material_mtime_ns(self, file_path: str):
        if not file_path:
            return None

        now = time.monotonic()
        cached = self.__material_mtime_cache.get(file_path)
        if cached is not None and (now - cached[1]) < 1.0:
            return cached[0]

        if not os.path.exists(file_path):
            return None

        mtime_ns = self._get_mtime_ns(file_path)
        self.__material_mtime_cache[file_path] = (mtime_ns, now)
        return mtime_ns

    def _process_pending_thumbnail_requests(self):
        native_engine = self._get_native_engine()
        if native_engine is None:
            return

        if self.__thumbnail_queue_path != self.__current_path:
            self.__thumbnail_queue_path = self.__current_path
            self._clear_thumbnail_request_queue()
            return

        remaining_budget = max(_THUMBNAIL_REQUESTS_PER_FRAME - self._thumbnails_loaded_this_frame, 0)
        while self.__thumbnail_request_queue and remaining_budget > 0:
            request = self.__thumbnail_request_queue.popleft()
            self.__thumbnail_request_keys.discard(request)
            request_dir, kind, file_path = request
            if request_dir != self.__current_path or not os.path.exists(file_path):
                continue

            retry_key = (kind, file_path)
            if self.__thumbnail_retry_after.get(retry_key, 0.0) > time.monotonic():
                continue

            if kind == 'image':
                mtime_ns = self._get_mtime_ns(file_path)
                if mtime_ns is None:
                    continue

                thumbnail_name = f"__thumb__{file_path}"
                cached_entry = self.__thumbnail_cache.get(file_path)
                if cached_entry is not None and cached_entry[1] == mtime_ns and cached_entry[0] != 0:
                    continue

                if native_engine.has_imgui_texture(thumbnail_name):
                    tex_id = native_engine.get_imgui_texture_id(thumbnail_name)
                    if tex_id != 0:
                        self.__thumbnail_cache[file_path] = (tex_id, mtime_ns)
                        continue

                cached_pixels = _thumb_pixel_cache.get(file_path, mtime_ns)
                if cached_pixels is None:
                    try:
                        pixels, w, h = _downsample_texture(file_path, self.THUMBNAIL_MAX_PX)
                    except Exception:
                        self.__thumbnail_retry_after[retry_key] = time.monotonic() + _THUMBNAIL_RETRY_DELAY_SEC
                        continue
                    _thumb_pixel_cache.put(file_path, pixels, w, h, mtime_ns)
                else:
                    pixels, w, h = cached_pixels

                tex_id = native_engine.upload_texture_for_imgui(thumbnail_name, pixels, w, h)
                if tex_id == 0:
                    self.__thumbnail_retry_after[retry_key] = time.monotonic() + _THUMBNAIL_RETRY_DELAY_SEC
                    continue

                self.__thumbnail_cache[file_path] = (tex_id, mtime_ns)
            elif kind == 'material':
                mtime_ns = self._get_material_mtime_ns(file_path)
                if mtime_ns is None:
                    continue

                thumbnail_name = f"__mat_thumb__{file_path}"
                cached_entry = self.__thumbnail_cache.get(file_path)
                if cached_entry is not None:
                    cached_id, cached_mtime = cached_entry
                    if cached_mtime == mtime_ns and cached_id != 0:
                        continue
                    if cached_mtime != mtime_ns:
                        if native_engine.has_imgui_texture(thumbnail_name):
                            native_engine.remove_imgui_texture(thumbnail_name)
                        self.__thumbnail_cache.pop(file_path, None)

                pixels = native_engine.render_material_preview_pixels(file_path, self.THUMBNAIL_MAX_PX)
                if pixels is None:
                    self.__thumbnail_retry_after[retry_key] = time.monotonic() + _THUMBNAIL_RETRY_DELAY_SEC
                    continue

                sq = self.THUMBNAIL_MAX_PX
                tex_id = native_engine.upload_texture_for_imgui(thumbnail_name, pixels, sq, sq)
                if tex_id == 0:
                    self.__thumbnail_retry_after[retry_key] = time.monotonic() + _THUMBNAIL_RETRY_DELAY_SEC
                    continue

                self.__thumbnail_cache[file_path] = (tex_id, mtime_ns)
            else:
                continue

            self.__thumbnail_retry_after.pop(retry_key, None)
            self._thumbnails_loaded_this_frame += 1
            remaining_budget -= 1

    @staticmethod
    def _normalize_path(path: str) -> str:
        return os.path.normcase(os.path.abspath(path))

    @classmethod
    def _is_path_within(cls, path: str, parent_path: str) -> bool:
        try:
            return os.path.commonpath([cls._normalize_path(path), cls._normalize_path(parent_path)]) == cls._normalize_path(parent_path)
        except ValueError:
            return False

    def _get_drag_move_sources(self, dragged_path: str) -> list[str]:
        selected_paths = self._get_selected_paths()
        if dragged_path in selected_paths:
            candidates = selected_paths
        else:
            candidates = [dragged_path]

        indexed = [(index, path) for index, path in enumerate(candidates) if path and os.path.exists(path)]
        indexed.sort(key=lambda entry: (entry[1].count(os.sep), len(entry[1]), entry[0]))

        kept: list[str] = []
        for _index, path in indexed:
            if any(self._is_path_within(path, existing) for existing in kept):
                continue
            kept.append(path)
        return kept

    def _resolve_project_move_path(self, payload_type: str, payload) -> str | None:
        if not isinstance(payload, str) or not payload:
            return None

        if payload_type in self._PROJECT_MOVE_PATH_TYPES:
            return payload if os.path.exists(payload) else None

        if payload_type in self._PROJECT_MOVE_GUID_TYPES and self.__asset_database:
            try:
                path = self.__asset_database.get_path_from_guid(payload)
            except Exception:
                return None
            return path if path and os.path.exists(path) else None

        return None

    def _move_project_items_to_folder(self, target_dir: str, payload_type: str, payload):
        from Infernux.debug import Debug

        if not target_dir or not os.path.isdir(target_dir):
            return

        dragged_path = self._resolve_project_move_path(payload_type, payload)
        if not dragged_path:
            return

        sources = [path for path in self._get_drag_move_sources(dragged_path)
                   if self._normalize_path(path) != self._normalize_path(target_dir)]
        if not sources:
            return

        moved_paths = []
        for source_path in sources:
            if os.path.isdir(source_path) and self._is_path_within(target_dir, source_path):
                Debug.log_warning("Cannot move a folder into itself or one of its children")
                continue

            new_path = file_ops.move_item_to_directory(source_path, target_dir, self.__asset_database)
            if new_path:
                moved_paths.append(new_path)

        if not moved_paths:
            return

        self._invalidate_dir_cache()
        self.__thumbnail_cache.clear()
        self.__selected_files = moved_paths
        self.__selected_file = moved_paths[-1]
        self._notify_selection_changed()

    @staticmethod
    def _get_mtime_ns(path: str):
        try:
            return os.stat(path).st_mtime_ns
        except OSError:
            return None

    def _get_dir_snapshot(self, path: str):
        """Return a cached directory snapshot for *path*."""
        if not path or not os.path.isdir(path):
            return None

        mtime_ns = self._get_mtime_ns(path)
        cached = self.__dir_cache.get(path)
        if cached is not None and cached.get('mtime_ns') == mtime_ns:
            return cached

        dirs = []
        files = []
        try:
            with os.scandir(path) as it:
                for entry in it:
                    name = entry.name
                    if not self._should_show(name):
                        continue

                    full_path = entry.path
                    try:
                        is_dir = entry.is_dir()
                    except OSError:
                        continue

                    if is_dir:
                        dirs.append({
                            'type': 'dir',
                            'name': name,
                            'path': full_path,
                            'ext': '',
                            'mtime_ns': None,
                        })
                        continue

                    ext = os.path.splitext(name)[1].lower()
                    file_mtime_ns = None
                    if ext in self.IMAGE_EXTENSIONS or ext in self.MATERIAL_EXTENSIONS:
                        try:
                            file_mtime_ns = entry.stat().st_mtime_ns
                        except OSError:
                            file_mtime_ns = None
                    files.append({
                        'type': 'file',
                        'name': name,
                        'path': full_path,
                        'ext': ext,
                        'mtime_ns': file_mtime_ns,
                    })
        except OSError:
            return None

        dirs.sort(key=lambda item: item['name'].lower())
        files.sort(key=lambda item: item['name'].lower())
        snapshot = {
            'mtime_ns': mtime_ns,
            'dirs': dirs,
            'files': files,
            'items': dirs + files,
        }
        self.__dir_cache[path] = snapshot
        self.__dir_tree_meta_cache[path] = {
            'has_subdirs': bool(dirs),
        }
        return snapshot

    def _get_dir_tree_meta(self, path: str):
        if not path:
            return None

        cached = self.__dir_tree_meta_cache.get(path)
        if cached is not None:
            return cached

        has_subdirs = False
        try:
            with os.scandir(path) as it:
                for entry in it:
                    if not self._should_show(entry.name):
                        continue
                    try:
                        if entry.is_dir():
                            has_subdirs = True
                            break
                    except OSError:
                        continue
        except OSError:
            return None

        meta = {
            'has_subdirs': has_subdirs,
        }
        self.__dir_tree_meta_cache[path] = meta
        return meta

    def _get_project_items(self, path: str, snapshot=None):
        """Return current folder items, including expanded virtual sub-assets."""
        if snapshot is None:
            snapshot = self._get_dir_snapshot(path)
        if snapshot is None:
            return None

        items = snapshot['items']
        if not self.__expanded_models:
            return items

        expanded_paths = tuple(
            item['path']
            for item in items
            if item['type'] == 'file'
            and item.get('ext', '') in self.MODEL_EXTENSIONS
            and item['path'] in self.__expanded_models
        )
        if not expanded_paths:
            return items

        cached = self.__augmented_items_cache.get(path)
        if (cached is not None
                and cached.get('mtime_ns') == snapshot.get('mtime_ns')
                and cached.get('expanded_paths') == expanded_paths):
            return cached['items']

        augmented = []
        for item in items:
            augmented.append(item)
            if item['type'] != 'file' or item.get('ext', '') not in self.MODEL_EXTENSIONS:
                continue
            if item['path'] not in self.__expanded_models:
                continue

            sub_assets = self._get_model_sub_assets(item['path'])
            if not sub_assets:
                continue

            for sub_index, submesh in enumerate(sub_assets['submeshes']):
                tri_count = submesh.get('index_count', 0) // 3
                vertex_count = submesh.get('vertex_count', 0)
                augmented.append({
                    'type': 'sub_mesh',
                    'name': (submesh.get('name', '') or f'SubMesh {sub_index}')
                            + f'  ({tri_count} tris, {vertex_count} verts)',
                    'path': f"{item['path']}##sub_mesh_{sub_index}",
                    'parent_path': item['path'],
                    'ext': '',
                    'mtime_ns': None,
                })
            for slot_index, slot_name in enumerate(sub_assets['slot_names']):
                augmented.append({
                    'type': 'sub_material',
                    'name': slot_name or f'Material {slot_index}',
                    'path': f"{item['path']}##sub_mat_{slot_index}",
                    'parent_path': item['path'],
                    'ext': '',
                    'mtime_ns': None,
                    'slot_index': slot_index,
                })

        self.__augmented_items_cache[path] = {
            'mtime_ns': snapshot.get('mtime_ns'),
            'expanded_paths': expanded_paths,
            'items': augmented,
        }
        return augmented

    def _get_grid_text_line_height(self, ctx: InxGUIContext) -> float:
        if self.__grid_text_line_height <= 0.0:
            self.__grid_text_line_height = max(ctx.calc_text_size('Ag')[1], 14.0)
        return self.__grid_text_line_height

    def _get_visible_grid_range(
            self,
            ctx: InxGUIContext,
            item_count: int,
            cols: int,
            row_height: float,
            start_y: float = 0.0):
        if item_count <= 0 or cols <= 0 or row_height <= 0.0:
            return 0, item_count, 0.0, 0.0

        scroll_y = max(ctx.get_scroll_y() - start_y, 0.0)
        viewport_h = max(ctx.get_content_region_avail_height(), row_height)
        total_rows = (item_count + cols - 1) // cols
        first_row = max(int(scroll_y // row_height) - 1, 0)
        visible_rows = max(int(viewport_h // row_height) + 3, 1)
        last_row = min(total_rows, first_row + visible_rows)

        top_spacer_h = first_row * row_height
        bottom_spacer_h = max(total_rows - last_row, 0) * row_height
        start_index = first_row * cols
        end_index = min(item_count, last_row * cols)
        return start_index, end_index, top_spacer_h, bottom_spacer_h

    def _get_cached_item_label(self, ctx: InxGUIContext, item: dict, text_region_w: float):
        item_path = item['path']
        item_type = item['type']
        item_name = item['name']
        ext = item.get('ext', '')
        is_expanded_model = (
            item_type == 'file'
            and ext in self.MODEL_EXTENSIONS
            and item_path in self.__expanded_models
        )
        cache_key = (item_type, item_path, item_name, is_expanded_model, int(text_region_w))
        cached = self.__label_layout_cache.get(cache_key)
        if cached is not None:
            return cached

        name_display = item_name
        if item_type == 'file':
            name_display = os.path.splitext(item_name)[0]
            if ext in self.MODEL_EXTENSIONS:
                name_display += '  \u25BC' if is_expanded_model else '  \u25B6'
        elif item_type in ('sub_mesh', 'sub_material'):
            name_display = f'\u21B3 {item_name}'

        max_text_w = text_region_w - 4
        text_w, _ = ctx.calc_text_size(name_display)
        if text_w > max_text_w:
            truncated = name_display
            while len(truncated) > 1:
                truncated = truncated[:-1]
                truncated_w, _ = ctx.calc_text_size(truncated + '\u2026')
                if truncated_w <= max_text_w:
                    name_display = truncated + '\u2026'
                    text_w = truncated_w
                    break
            else:
                name_display = '\u2026'
                text_w, _ = ctx.calc_text_size(name_display)

        offset_x = max((text_region_w - text_w) * 0.5, 0.0)
        cached = (name_display, offset_x)
        if len(self.__label_layout_cache) > 4096:
            self.__label_layout_cache.clear()
        self.__label_layout_cache[cache_key] = cached
        return cached

    def _get_thumbnail(self, file_path: str, size: float, cached_mtime_ns=None) -> int:
        """Return an ImGui texture id for a low-res thumbnail, or 0.

        Pixel data is served from the module-level ``_thumb_pixel_cache``
        (populated by the background pre-loader at startup).  Only the fast
        GPU upload happens on the render thread.
        """
        if not file_path:
            return 0

        ext = os.path.splitext(file_path)[1].lower()
        if ext not in self.IMAGE_EXTENSIONS:
            return 0

        thumbnail_name = f"__thumb__{file_path}"

        native_engine = self._get_native_engine()
        if not native_engine:
            return 0

        if cached_mtime_ns is None:
            if not os.path.exists(file_path):
                return 0
            cached_mtime_ns = self._get_mtime_ns(file_path)

        # 1. Python-side GPU-id cache (fastest)
        if file_path in self.__thumbnail_cache:
            cached_id, cached_mtime = self.__thumbnail_cache[file_path]
            if cached_mtime == cached_mtime_ns and cached_id != 0:
                return cached_id

        # 2. Engine-side GPU texture cache
        if native_engine.has_imgui_texture(thumbnail_name):
            tex_id = native_engine.get_imgui_texture_id(thumbnail_name)
            if tex_id != 0:
                self.__thumbnail_cache[file_path] = (tex_id, cached_mtime_ns)
                return tex_id

        self._queue_thumbnail_request('image', file_path)
        return 0
    
    def _get_material_thumbnail(self, file_path: str, size: float, cached_mtime_ns=None) -> int:
        """Return an ImGui texture id for a material sphere preview, or 0.

        Uses file mtime to detect changes.  The stat call is throttled to at
        most once per second per file via ``_mat_mtime_cache``.
        """
        if not file_path:
            return 0

        thumbnail_name = f"__mat_thumb__{file_path}"

        native_engine = self._get_native_engine()
        if not native_engine:
            return 0

        cached_mtime_ns = self._get_material_mtime_ns(file_path)
        if cached_mtime_ns is None:
            return 0

        # 1. Python-side GPU-id cache — valid only if mtime matches
        if file_path in self.__thumbnail_cache:
            cached_id, cached_mtime = self.__thumbnail_cache[file_path]
            if cached_mtime == cached_mtime_ns and cached_id != 0:
                return cached_id
            # mtime changed — evict stale GPU texture so we re-render
            if cached_mtime != cached_mtime_ns:
                if native_engine.has_imgui_texture(thumbnail_name):
                    native_engine.remove_imgui_texture(thumbnail_name)
                del self.__thumbnail_cache[file_path]
        
        self._queue_thumbnail_request('material', file_path)
        return 0

    def invalidate_material_thumbnail(self, file_path: str) -> None:
        """Drop cached preview state for a material so the next frame re-renders it."""
        if not file_path:
            return

        target_path = self._normalize_path(file_path)
        native_engine = self._get_native_engine()

        cached_paths = [
            path for path in list(self.__thumbnail_cache.keys())
            if self._normalize_path(path) == target_path
        ]
        for cached_path in cached_paths:
            if native_engine:
                thumb_name = f"__mat_thumb__{cached_path}"
                try:
                    if native_engine.has_imgui_texture(thumb_name):
                        native_engine.remove_imgui_texture(thumb_name)
                except Exception:
                    pass
            self.__thumbnail_cache.pop(cached_path, None)

        cached_paths = [
            path for path in list(self.__material_mtime_cache.keys())
            if self._normalize_path(path) == target_path
        ]
        for cached_path in cached_paths:
            self.__material_mtime_cache.pop(cached_path, None)

    def _reset_frame_counters(self):
        """Reset per-frame counters. Call at start of on_render."""
        self._thumbnails_loaded_this_frame = 0
    
    # ------------------------------------------------------------------ icons
    def _get_native_engine(self):
        """Resolve to the raw C++ Infernux object."""
        return self.__native_engine

    def _ensure_type_icons_loaded(self):
        """Lazily upload all file-type icons to GPU (once)."""
        if self.__type_icons_loaded:
            return
        native = self._get_native_engine()
        if native is None:
            return

        # Collect unique icon filenames we need
        needed = set(self.ICON_MAP.values())
        needed.add('file')  # generic fallback

        for icon_key in needed:
            tex_name = f"__typeicon__{icon_key}"
            # Already uploaded in a previous session / hot-reload?
            if native.has_imgui_texture(tex_name):
                self.__type_icon_cache[icon_key] = native.get_imgui_texture_id(tex_name)
                continue

            icon_path = os.path.join(_resources.file_type_icons_dir, f"{icon_key}.png")
            if not os.path.isfile(icon_path):
                continue  # user hasn't added this icon yet, will fall back to text

            tex_data = TextureLoader.load_from_file(icon_path)
            if tex_data and tex_data.is_valid():
                pixels = tex_data.get_pixels_list()
                tid = native.upload_texture_for_imgui(
                    tex_name, pixels, tex_data.width, tex_data.height)
                if tid != 0:
                    self.__type_icon_cache[icon_key] = tid

        self.__type_icons_loaded = True

    def _get_type_icon_id(self, item_type: str, ext: str) -> int:
        """Return the ImGui texture id for a file type, or 0 if not available."""
        if item_type == 'dir':
            key = self.ICON_MAP.get('__dir__')
        else:
            key = self.ICON_MAP.get(ext)
        if key is None:
            key = 'file'  # generic fallback
        tex_id = self.__type_icon_cache.get(key, 0)
        if tex_id == 0 and ext == '.cs':
            tex_id = self.__type_icon_cache.get('script_py', 0)
        return tex_id

    def _get_model_sub_assets(self, file_path: str):
        """Return cached sub-asset info for a model file, or None.

        Returns dict with keys ``slot_names`` (list[str]) and
        ``submeshes`` (list[dict]) on success, or *None* if the mesh
        cannot be loaded (e.g. not yet imported).
        """
        cached = self.__model_sub_cache.get(file_path)
        if cached is not None:
            return cached
        if not self.__asset_database:
            return None
        try:
            guid = self.__asset_database.get_guid_from_path(file_path)
        except Exception:
            return None
        if not guid:
            return None
        try:
            from Infernux.lib import AssetRegistry
            registry = AssetRegistry.instance()
            mesh = registry.load_mesh_by_guid(guid)
        except Exception:
            return None
        if mesh is None:
            return None
        slot_names = list(mesh.material_slot_names) if mesh.material_slot_names else []
        submeshes = []
        for i in range(mesh.submesh_count):
            try:
                submeshes.append(mesh.get_submesh_info(i))
            except Exception:
                break
        result = {'slot_names': slot_names, 'submeshes': submeshes,
                  'vertex_count': mesh.vertex_count, 'index_count': mesh.index_count}
        self.__model_sub_cache[file_path] = result
        return result

    def _delete_item(self, item_path: str):
        self._delete_items([item_path])

    def _delete_items(self, item_paths: list[str]):
        paths = []
        seen = set()
        for path in item_paths or []:
            if not path or not os.path.exists(path) or path in seen:
                continue
            seen.add(path)
            paths.append(path)
        if not paths:
            return

        title = t("project.delete_confirm_title")
        if len(paths) == 1:
            msg = t("project.delete_confirm_msg").replace("{name}", os.path.basename(paths[0]))
        else:
            msg = t("project.delete_confirm_multi_msg").replace("{count}", str(len(paths)))
        # MB_OKCANCEL (1) | MB_ICONWARNING (0x30) | MB_DEFBUTTON2 (0x100)
        # IDOK = 1
        result = ctypes.windll.user32.MessageBoxW(0, msg, title, 0x1 | 0x30 | 0x100)
        if result != 1:
            return

        deleted = False
        for item_path in sorted(paths, key=lambda p: (p.count(os.sep), len(p)), reverse=True):
            if not os.path.exists(item_path):
                continue
            file_ops.delete_item(item_path, self.__asset_database)
            deleted = True
            self.__thumbnail_cache.pop(item_path, None)

        if not deleted:
            return

        self._invalidate_dir_cache()
        if any(path in self.__selected_files for path in paths) or self.__selected_file in paths:
            self.__selected_file = None
            self.__selected_files.clear()
            self._notify_selection_changed()
    
    def _should_show(self, name: str) -> bool:
        return project_utils.should_show(name)
    
    def _open_file_with_system(self, file_path: str):
        project_utils.open_file_with_system(file_path, project_root=self.__root_path)
    
    def _create_folder(self, folder_name: str):
        ok, err = file_ops.create_folder(self.__current_path, folder_name)
        if not ok:
            self.__create_error = err
        else:
            self._invalidate_dir_cache()
        return ok, err
    
    def _create_script(self, script_name: str):
        ok, err = file_ops.create_script(self.__current_path, script_name,
                                         self.__asset_database)
        if not ok:
            self.__create_error = err
        else:
            self._invalidate_dir_cache()
        return ok, err
    
    def _create_shader(self, shader_name: str, shader_type: str):
        ok, err = file_ops.create_shader(self.__current_path, shader_name, shader_type,
                                         self.__asset_database)
        if not ok:
            self.__create_error = err
        else:
            self._invalidate_dir_cache()
        return ok, err
    
    def _create_material(self, material_name: str):
        ok, err = file_ops.create_material(self.__current_path, material_name,
                                           self.__asset_database)
        if not ok:
            self.__create_error = err
        else:
            self._invalidate_dir_cache()
        return ok, err

    def _create_scene(self, scene_name: str):
        """Create a new .scene file and return ``(True, path)`` or ``(False, error)``."""
        ok, result = file_ops.create_scene(self.__current_path, scene_name,
                                           self.__asset_database)
        if not ok:
            self.__create_error = result
            return False, result
        self._invalidate_dir_cache()
        return True, result

    def _create_prefab_from_hierarchy(self, obj_id: int):
        """Create a .prefab file from a hierarchy GameObject dragged onto the Project panel."""
        from Infernux.lib import SceneManager
        scene = SceneManager.instance().get_active_scene()
        if not scene:
            return
        game_object = scene.find_by_id(obj_id)
        if not game_object:
            return
        ok, result = file_ops.create_prefab_from_gameobject(
            game_object, self.__current_path, self.__asset_database
        )
        if ok:
            self._invalidate_dir_cache()
        else:
            from Infernux.debug import Debug
            Debug.log_warning(f"Failed to create prefab: {result}")

    def _open_scene_file(self, file_path: str):
        """Open a .scene file via the SceneFileManager."""
        from Infernux.debug import Debug
        from Infernux.engine.deferred_task import DeferredTaskRunner
        from Infernux.engine.play_mode import PlayModeManager
        from Infernux.engine.scene_manager import SceneFileManager

        def _open_after_stop() -> bool:
            sfm = SceneFileManager.instance()
            if sfm:
                return bool(sfm.open_scene(file_path))
            Debug.log_warning("SceneFileManager not initialized")
            return False

        play_mode = PlayModeManager.instance()
        if play_mode and play_mode.is_playing:
            runner = DeferredTaskRunner.instance()
            if runner.is_busy:
                Debug.log_warning("Cannot open scene while another deferred task is running")
                return

            def _open_when_stopped(ok: bool):
                if not ok:
                    Debug.log_warning("Play Mode stop did not complete; scene open cancelled")
                    return

                native_sm = None
                try:
                    from Infernux.lib import SceneManager as NativeSceneManager
                    native_sm = NativeSceneManager.instance()
                except Exception:
                    native_sm = None

                if play_mode.is_playing:
                    Debug.log_warning("Scene open cancelled because Play Mode is still active")
                    return
                if native_sm and native_sm.is_playing():
                    Debug.log_warning("Scene open cancelled because native Play Mode is still active")
                    return

                _open_after_stop()

            if not play_mode.exit_play_mode(on_complete=_open_when_stopped):
                Debug.log_warning("Failed to stop Play Mode before opening scene")
            return

        sfm = SceneFileManager.instance()
        if sfm:
            sfm.open_scene(file_path)
        else:
            Debug.log_warning("SceneFileManager not initialized")

    def _get_unique_name(self, base_name: str, extension: str = "") -> str:
        return file_ops.get_unique_name(self.__current_path, base_name, extension)
    
    def _do_rename(self):
        if not self.__renaming_path or not self.__renaming_name:
            self.__renaming_path = None
            return
        old_path = self.__renaming_path
        new_path = file_ops.do_rename(old_path, self.__renaming_name,
                                      self.__asset_database)
        if new_path:
            self._invalidate_dir_cache()
        if new_path and self.__selected_file == old_path:
            self.__selected_file = new_path
            self.__selected_files = [new_path]
        if new_path and self.__current_path == old_path:
            self.__current_path = new_path
        self.__renaming_path = None
    
    def _update_material_name_in_file(self, mat_path: str, new_name: str):
        project_utils.update_material_name_in_file(mat_path, new_name)

    def _create_and_rename(self, create_fn, base_name: str, extension: str = ""):
        """Create an item then immediately enter rename mode for it.

        *create_fn* is called with the generated name and must return ``(ok, ...)``.
        """
        name = self._get_unique_name(base_name, extension)
        ok, *_ = create_fn(name)
        if ok:
            file_name = name + extension if extension and not name.endswith(extension) else name
            new_path = os.path.join(self.__current_path, file_name)
            self.__selected_file = new_path
            self.__selected_files = [new_path]
            if self.__on_file_selected:
                self.__on_file_selected(new_path)
            # Enter rename mode
            self.__renaming_path = new_path
            disp = os.path.basename(new_path)
            if os.path.isfile(new_path):
                disp = os.path.splitext(disp)[0]
            self.__renaming_name = disp
            self.__rename_focus_requested = True

    def _reveal_in_file_explorer(self, path: str):
        """Open the OS file explorer and highlight *path*."""
        project_utils.reveal_in_file_explorer(path)

    # ── clipboard helpers ────────────────────────────────────────────────

    def _clipboard_copy(self, paths):
        if isinstance(paths, str):
            paths = [paths]
        self.__clipboard_paths = [p for p in paths or [] if p and os.path.exists(p)]
        self.__clipboard_path = self.__clipboard_paths[0] if self.__clipboard_paths else None
        self.__clipboard_is_cut = False

    def _clipboard_cut(self, paths):
        if isinstance(paths, str):
            paths = [paths]
        self.__clipboard_paths = [p for p in paths or [] if p and os.path.exists(p)]
        self.__clipboard_path = self.__clipboard_paths[0] if self.__clipboard_paths else None
        self.__clipboard_is_cut = True

    def _clipboard_paste(self):
        """Paste the clipboard file/folder into the current directory."""
        sources = [p for p in self.__clipboard_paths if os.path.exists(p)]
        if not sources:
            self.__clipboard_paths = []
            self.__clipboard_path = None
            return

        pasted_paths = []
        for src in sources:
            name = os.path.basename(src)
            dst = os.path.join(self.__current_path, name)
            is_same_path = os.path.abspath(src) == os.path.abspath(dst)
            if is_same_path and self.__clipboard_is_cut:
                continue

            if is_same_path or os.path.exists(dst):
                base, ext = os.path.splitext(name)
                if os.path.isdir(src):
                    ext = ""
                    base = name
                dst_name = file_ops.get_unique_name(self.__current_path, base, ext)
                dst = os.path.join(self.__current_path, dst_name + ext)

            try:
                if self.__clipboard_is_cut:
                    shutil.move(src, dst)
                elif os.path.isdir(src):
                    shutil.copytree(src, dst)
                else:
                    shutil.copy2(src, dst)
            except OSError:
                continue
            pasted_paths.append(dst)

        if not pasted_paths:
            return

        if self.__clipboard_is_cut:
            self.__clipboard_paths = []
            self.__clipboard_path = None

        self._invalidate_dir_cache()
        self.__selected_files = pasted_paths
        self.__selected_file = pasted_paths[-1] if len(pasted_paths) == 1 else pasted_paths[-1]
        self._notify_selection_changed()

    # ── external file drop (from Windows Explorer) ───────────────────────

    def _handle_external_file_drops(self):
        """Check InputManager for files dropped from the OS and copy them in."""
        try:
            mgr = InputManager.instance()
        except Exception:
            return
        if not mgr.has_dropped_files():
            return
        dropped = mgr.get_dropped_files()
        if not dropped or not self.__current_path:
            return
        last_path = None
        for src in dropped:
            if not os.path.exists(src):
                continue
            name = os.path.basename(src)
            dst = os.path.join(self.__current_path, name)
            if os.path.exists(dst):
                base, ext = os.path.splitext(name)
                if os.path.isdir(src):
                    ext = ""
                    base = name
                dst_name = file_ops.get_unique_name(self.__current_path, base, ext)
                dst = os.path.join(self.__current_path, dst_name + ext)
            try:
                if os.path.isdir(src):
                    shutil.copytree(src, dst)
                else:
                    shutil.copy2(src, dst)
                last_path = dst
            except OSError:
                continue
        if last_path:
            self._invalidate_dir_cache()
            self.__selected_file = last_path
            self.__selected_files = [last_path]
            if self.__on_file_selected:
                self.__on_file_selected(last_path)
    
    def _handle_item_click(self, item: dict, ctx=None):
        """Handle click on an item (file or folder) with ctrl/shift multi-select."""
        import time
        current_time = time.time()
        double_clicked = (self.__last_clicked_file == item['path'] and 
                          current_time - self.__last_click_time < 0.4)
        
        self.__last_clicked_file = item['path']
        self.__last_click_time = current_time

        path = item['path']

        # Detect modifier keys
        ctrl = False
        shift = False
        if ctx is not None:
            ctrl = ctx.is_key_down(KEY_LEFT_CTRL) or ctx.is_key_down(KEY_RIGHT_CTRL)
            shift = ctx.is_key_down(KEY_LEFT_SHIFT) or ctx.is_key_down(KEY_RIGHT_SHIFT)

        if ctrl and not double_clicked:
            # Ctrl+click: toggle this item in the selection
            if path in self.__selected_files:
                self.__selected_files.remove(path)
                self.__selected_file = self.__selected_files[-1] if self.__selected_files else None
            else:
                self.__selected_files.append(path)
                self.__selected_file = path
            self._notify_selection_changed()
            return
        elif shift and not double_clicked and self.__selected_file and hasattr(self, '_visible_items'):
            # Shift+click: range select from last selected to current
            try:
                paths = [it['path'] for it in self._visible_items]
                anchor_idx = paths.index(self.__selected_file)
                target_idx = paths.index(path)
                lo, hi = min(anchor_idx, target_idx), max(anchor_idx, target_idx)
                self.__selected_files = paths[lo:hi + 1]
                # Keep __selected_file as the anchor (don't change it)
            except ValueError:
                self.__selected_files = [path]
                self.__selected_file = path
            self._notify_selection_changed()
            return

        # Normal click (no modifier): single-select
        self.__selected_files = [path]
        self.__selected_file = path
        self._notify_selection_changed()
        
        if item['type'] == 'dir':
            if double_clicked:
                self.__current_path = item['path']
                self.__last_clicked_file = None
        elif item['type'] in ('sub_mesh', 'sub_material'):
            pass  # Sub-asset items: select only
        else:
            if double_clicked:
                ext = os.path.splitext(item['path'])[1].lower()
                if ext in self.MODEL_EXTENSIONS:
                    if item['path'] in self.__expanded_models:
                        self.__expanded_models.discard(item['path'])
                    else:
                        self.__expanded_models.add(item['path'])
                elif ext == '.scene':
                    self._open_scene_file(item['path'])
                elif ext == '.prefab':
                    from Infernux.engine.scene_manager import SceneFileManager
                    SceneFileManager.instance().open_prefab_mode(item['path'])
                else:
                    self._open_file_with_system(item['path'])

    def _render_context_menu(self, ctx: InxGUIContext):
        """Render right-click context menu for creating items."""
        if ctx.begin_popup_context_window("ProjectContextMenu", 1):
            if ctx.begin_menu(t("project.create_menu")):
                if ctx.selectable(t("project.create_folder"), False, 0, 0, 0):
                    self._create_and_rename(self._create_folder, "NewFolder")
                ctx.separator()
                if ctx.selectable(t("project.create_script"), False, 0, 0, 0):
                    self._create_and_rename(self._create_script, "NewComponent", ".cs")
                ctx.separator()
                if ctx.selectable(t("project.create_vert_shader"), False, 0, 0, 0):
                    self._create_and_rename(
                        lambda n: self._create_shader(n, "vert"), "NewShader", ".vert")
                if ctx.selectable(t("project.create_frag_shader"), False, 0, 0, 0):
                    self._create_and_rename(
                        lambda n: self._create_shader(n, "frag"), "NewShader", ".frag")
                ctx.separator()
                if ctx.selectable(t("project.create_material"), False, 0, 0, 0):
                    self._create_and_rename(self._create_material, "NewMaterial", ".mat")
                ctx.separator()
                if ctx.selectable(t("project.create_scene"), False, 0, 0, 0):
                    self._create_and_rename(self._create_scene, "NewScene", ".scene")
                ctx.end_menu()
            
            if self.__selected_file and os.path.exists(self.__selected_file):
                ctx.separator()
                if ctx.selectable(t("project.reveal_in_explorer"), False, 0, 0, 0):
                    self._reveal_in_file_explorer(self.__selected_file)
                ctx.separator()
                if ctx.selectable(t("project.copy"), False, 0, 0, 0):
                    self._clipboard_copy(self._get_selected_paths())
                if ctx.selectable(t("project.cut"), False, 0, 0, 0):
                    self._clipboard_cut(self._get_selected_paths())
                if self._has_clipboard_items():
                    if ctx.selectable(t("project.paste"), False, 0, 0, 0):
                        self._clipboard_paste()
                ctx.separator()
                can_rename = len(self._get_selected_paths()) == 1
                ctx.begin_disabled(not can_rename)
                if ctx.selectable(t("project.rename"), False, 0, 0, 0):
                    self.__renaming_path = self.__selected_file
                    name = os.path.basename(self.__selected_file)
                    if os.path.isfile(self.__renaming_path):
                        name = os.path.splitext(name)[0]
                    self.__renaming_name = name
                    self.__rename_focus_requested = True
                ctx.end_disabled()
                if ctx.selectable(t("project.delete"), False, 0, 0, 0):
                    self._delete_items(self._get_selected_paths())
            else:
                # No item selected — still offer paste & reveal on folder
                ctx.separator()
                if ctx.selectable(t("project.reveal_in_explorer"), False, 0, 0, 0):
                    self._reveal_in_file_explorer(self.__current_path)
                if self._has_clipboard_items():
                    if ctx.selectable(t("project.paste"), False, 0, 0, 0):
                        self._clipboard_paste()
            
            ctx.end_popup()
    
    def _render_folder_tree(self, ctx: InxGUIContext, path: str, depth: int = 0, snapshot=None):
        """Recursively render folder tree."""
        if snapshot is None:
            snapshot = self._get_dir_snapshot(path)
        if snapshot is None:
            return
        dirs = snapshot['dirs']

        for d in dirs:
            full_path = d['path']
            node_flags = (ImGuiTreeNodeFlags.OpenOnArrow
                          | ImGuiTreeNodeFlags.SpanAvailWidth
                          | ImGuiTreeNodeFlags.FramePadding)
            if self.__current_path == full_path:
                node_flags |= ImGuiTreeNodeFlags.Selected

            dir_meta = self._get_dir_tree_meta(full_path)
            has_subdirs = bool(dir_meta and dir_meta.get('has_subdirs'))
            if not has_subdirs:
                node_flags |= ImGuiTreeNodeFlags.Leaf | ImGuiTreeNodeFlags.NoTreePushOnOpen

            node_open = ctx.tree_node_ex(f"{d['name']}##{full_path}", node_flags)
            if ctx.is_item_clicked():
                self.__current_path = full_path
            if has_subdirs and node_open:
                self._render_folder_tree(ctx, full_path, depth + 1)
                ctx.tree_pop()
    
    def _get_file_type(self, filename: str) -> str:
        return project_utils.get_file_type(filename)
    
    # ------------------------------------------------------------------
    # EditorPanel hooks
    # ------------------------------------------------------------------

    def _initial_size(self):
        return (800, 250)

    def _pre_render(self, ctx):
        self._reset_frame_counters()
        self._ensure_type_icons_loaded()
        self._process_pending_thumbnail_requests()
        self._get_grid_text_line_height(ctx)
        if self.__current_path != self.__last_notified_current_path:
            self.__last_notified_current_path = self.__current_path
            self._notify_state_changed()

    def on_render_content(self, ctx: InxGUIContext):
            # Top toolbar with cached breadcrumb
            cur = self.__current_path
            if cur != self.__breadcrumb_path:
                self.__breadcrumb_path = cur
                rel = os.path.relpath(cur, self.__root_path) if self.__root_path else cur
                if rel == '.':
                    rel = os.path.basename(self.__root_path) if self.__root_path else 'Project'
                self.__breadcrumb_text = f"Path: {rel}"
            ctx.label(self.__breadcrumb_text)
            ctx.separator()
            
            # Left panel: Folder tree showing entire project (about 25% width)
            tree_width = 200
            if ctx.begin_child("FolderTree", tree_width, 0, False):
                # Show entire project root in tree
                root_snapshot = self._get_dir_snapshot(self.__root_path) if self.__root_path else None
                if root_snapshot is not None:
                    project_name = os.path.basename(self.__root_path)
                    root_flags = (ImGuiTreeNodeFlags.OpenOnArrow
                                  | ImGuiTreeNodeFlags.SpanAvailWidth
                                  | ImGuiTreeNodeFlags.FramePadding)
                    if self.__current_path == self.__root_path:
                        root_flags |= ImGuiTreeNodeFlags.Selected
                    ctx.set_next_item_open(True, Theme.COND_FIRST_USE_EVER)
                    node_open = ctx.tree_node_ex(f"{project_name}##{self.__root_path}", root_flags)
                    if ctx.is_item_clicked():
                        self.__current_path = self.__root_path
                    if node_open:
                        self._render_folder_tree(ctx, self.__root_path, snapshot=root_snapshot)
                        ctx.tree_pop()
                else:
                    ctx.label(t("project.no_project_path"))

                tree_remaining_h = ctx.get_content_region_avail_height()
                if tree_remaining_h > 4:
                    ctx.invisible_button("##folder_tree_empty_area",
                                         ctx.get_content_region_avail_width(), tree_remaining_h)
                    if ctx.is_item_clicked(0):
                        self.clear_selection()
                        self._notify_empty_area_clicked()
            ctx.end_child()
            
            ctx.same_line()
            
            # Right panel: File grid/list (use border=True so WindowPadding applies, hide border color)
            ctx.push_style_var_vec2(ImGuiStyleVar.WindowPadding, *Theme.PROJECT_PANEL_PAD)
            Theme.push_transparent_border(ctx)  # 1 colour
            if ctx.begin_child("FileGrid", 0, 0, True):
                # Right-click context menu for creating items
                self._render_context_menu(ctx)

                current_snapshot = self._get_dir_snapshot(self.__current_path) if self.__current_path else None
                if current_snapshot is not None:
                    items = self._get_project_items(self.__current_path, current_snapshot) or []

                    # Back button — stop at direct children of root (Assets, Logs, etc.)
                    parent = os.path.dirname(self.__current_path)
                    if self.__current_path != self.__root_path and parent != self.__root_path:
                        if ctx.selectable("[..]", False):
                            self.__current_path = parent

                    # Grid config
                    icon_size = _FILE_GRID_ICON_SIZE
                    padding = _FILE_GRID_PADDING
                    cell_width = icon_size + padding
                    avail_w = ctx.get_content_region_avail_width()
                    cols = int(avail_w / cell_width)
                    if cols < 1: cols = 1
                    row_height = icon_size + self._get_grid_text_line_height(ctx) + padding + 8.0

                    if not items and self.__current_path == self.__root_path:
                        ctx.label(t("project.empty_folder"))
                        ctx.label(t("project.right_click_hint"))

                    # Handle F2 for rename, Delete, Ctrl+C/X/V
                    selected_paths = self._get_selected_paths()
                    single_selected = len(selected_paths) == 1 and self.__selected_file and os.path.exists(self.__selected_file)
                    if selected_paths and not self.__renaming_path:
                        ctrl = ctx.is_key_down(KEY_LEFT_CTRL) or ctx.is_key_down(KEY_RIGHT_CTRL)
                        if ctx.is_key_pressed(KEY_F2) and single_selected:
                            self.__renaming_path = self.__selected_file
                            name = os.path.basename(self.__selected_file)
                            if os.path.isfile(self.__renaming_path):
                                name = os.path.splitext(name)[0]
                            self.__renaming_name = name
                            self.__rename_focus_requested = True
                        elif ctx.is_key_pressed(KEY_DELETE):
                            self._delete_items(selected_paths)
                        elif ctrl and ctx.is_key_pressed(KEY_C):
                            self._clipboard_copy(selected_paths)
                        elif ctrl and ctx.is_key_pressed(KEY_X):
                            self._clipboard_cut(selected_paths)
                        elif ctrl and ctx.is_key_pressed(KEY_V):
                            self._clipboard_paste()
                    elif not selected_paths and not self.__renaming_path:
                        ctrl = ctx.is_key_down(KEY_LEFT_CTRL) or ctx.is_key_down(KEY_RIGHT_CTRL)
                        if ctrl and ctx.is_key_pressed(KEY_V):
                            self._clipboard_paste()

                    # Handle external file drops from Windows Explorer
                    self._handle_external_file_drops()


                    grid_start_y = ctx.get_cursor_pos_y()
                    if ctx.begin_table("FileGrid", cols, 0, 0.0):
                        self._visible_items = items  # Store for shift-range
                        _sel_set = set(self.__selected_files)
                        start_index, end_index, top_spacer_h, bottom_spacer_h = self._get_visible_grid_range(
                            ctx, len(items), cols, row_height, grid_start_y)

                        if top_spacer_h > 0.0:
                            ctx.table_next_row()
                            ctx.table_set_column_index(0)
                            ctx.dummy(1.0, top_spacer_h)
                            ctx.table_next_row()

                        # ── Style push ONCE for all icon buttons ──
                        ctx.push_style_var_vec2(ImGuiStyleVar.FramePadding, *Theme.ICON_BTN_NO_PAD)
                        Theme.push_unselected_icon_style(ctx)  # 2 colours + 1 var(FrameBorderSize)

                        # Pre-fetch extension sets as locals for inner loop speed
                        _IMAGE_EXT = self.IMAGE_EXTENSIONS
                        _MAT_EXT = self.MATERIAL_EXTENSIONS
                        _MODEL_EXT = self.MODEL_EXTENSIONS
                        _type_icon_cache = self.__type_icon_cache
                        _expanded = self.__expanded_models
                        _renaming_path = self.__renaming_path
                        _get_thumbnail = self._get_thumbnail
                        _get_mat_thumbnail = self._get_material_thumbnail
                        _get_type_icon_id = self._get_type_icon_id
                        _handle_click = self._handle_item_click
                        _get_cached_label = self._get_cached_item_label
                        _sel_r, _sel_g, _sel_b, _sel_a = Theme.BTN_SELECTED

                        for item in items[start_index:end_index]:
                            ctx.table_next_column()
                            ctx.begin_group()

                            item_path = item['path']
                            item_type = item['type']
                            item_name = item['name']
                            ext = item.get('ext', '')
                            is_selected = item_path in _sel_set
                            cell_start_x = ctx.get_cursor_pos_x()

                            # Resolve display texture
                            if item_type == 'sub_mesh':
                                display_tex_id = _type_icon_cache.get('model_3d', 0)
                            elif item_type == 'sub_material':
                                display_tex_id = _type_icon_cache.get('material', 0)
                            elif item_type == 'file':
                                if ext in _IMAGE_EXT:
                                    display_tex_id = _get_thumbnail(item_path, icon_size, item.get('mtime_ns'))
                                elif ext in _MAT_EXT:
                                    display_tex_id = _get_mat_thumbnail(item_path, icon_size)
                                else:
                                    display_tex_id = 0
                                if display_tex_id == 0:
                                    display_tex_id = _get_type_icon_id(item_type, ext)
                            else:
                                display_tex_id = _get_type_icon_id(item_type, ext)

                            if display_tex_id != 0:
                                # Icon button (styles already pushed outside loop)
                                if ctx.image_button(f"##icon_{item_path}", display_tex_id, icon_size, icon_size):
                                    _handle_click(item, ctx)
                                if ctx.is_item_clicked(1):
                                    self.__selected_file = item_path
                                    if item_path not in self.__selected_files:
                                        self.__selected_files = [item_path]
                                    self._notify_selection_changed()
                                if is_selected:
                                    ctx.draw_filled_rect(
                                        ctx.get_item_rect_min_x(), ctx.get_item_rect_min_y(),
                                        ctx.get_item_rect_max_x(), ctx.get_item_rect_max_y(),
                                        _sel_r, _sel_g, _sel_b, _sel_a, 0.0)
                            else:
                                label_icon = self._get_file_type(item_name) if item_type != 'dir' else '[DIR]'
                                if ctx.selectable(f"{label_icon}\n##{item_path}", is_selected, 0, icon_size, icon_size):
                                    _handle_click(item, ctx)
                                if ctx.is_item_clicked(1):
                                    self.__selected_file = item_path
                                    if item_path not in self.__selected_files:
                                        self.__selected_files = [item_path]
                                    self._notify_selection_changed()

                            # Drag-drop source
                            if item_type == 'dir':
                                if ctx.begin_drag_drop_source(0):
                                    ctx.set_drag_drop_payload_str(self._PROJECT_ITEM_MOVE_TYPE, item_path)
                                    ctx.label(f"Folder: {item_name}")
                                    ctx.end_drag_drop_source()
                            elif item_type == 'file':
                                _dd = self._DRAG_DROP_MAP.get(ext)
                                _ddg = self._DRAG_DROP_GUID_MAP.get(ext)
                                if _dd is not None:
                                    payload_type = _dd[0]
                                    label_prefix = _dd[1]
                                    if ext == '.cs':
                                        try:
                                            from Infernux.components.script_loader import load_component_from_file, ScriptLoadError
                                            load_component_from_file(item_path)
                                        except ScriptLoadError:
                                            payload_type = self._PROJECT_ITEM_MOVE_TYPE
                                            label_prefix = "Item (script file not attachable)"
                                    if ctx.begin_drag_drop_source(0):
                                        ctx.set_drag_drop_payload_str(payload_type, item_path)
                                        ctx.label(f"{label_prefix}: {item_name}")
                                        ctx.end_drag_drop_source()
                                elif _ddg is not None:
                                    if ctx.begin_drag_drop_source(0):
                                        guid = ""
                                        if self.__asset_database:
                                            try:
                                                guid = self.__asset_database.get_guid_from_path(item_path)
                                            except Exception:
                                                guid = ""
                                        if guid:
                                            ctx.set_drag_drop_payload_str(_ddg[0], guid)
                                        else:
                                            ctx.set_drag_drop_payload_str(_ddg[1], item_path)
                                        ctx.label(f"{_ddg[2]}: {item_name}")
                                        ctx.end_drag_drop_source()
                                else:
                                    if ctx.begin_drag_drop_source(0):
                                        ctx.set_drag_drop_payload_str(self._PROJECT_ITEM_MOVE_TYPE, item_path)
                                        ctx.label(f"Item: {item_name}")
                                        ctx.end_drag_drop_source()

                            if item_type == 'dir':
                                from .igui import IGUI
                                IGUI.multi_drop_target(
                                    ctx,
                                    self._PROJECT_MOVE_ACCEPT_TYPES,
                                    lambda payload_type, payload, folder=item_path: self._move_project_items_to_folder(folder, payload_type, payload),
                                )

                            # Name or Rename Input
                            if _renaming_path == item_path:
                                if self.__rename_focus_requested:
                                    ctx.set_keyboard_focus_here()
                                    self.__rename_focus_requested = False

                                ctx.set_cursor_pos_x(cell_start_x)
                                ctx.set_next_item_width(icon_size)
                                new_name = ctx.text_input(f"##rename_{item_path}", self.__renaming_name, 256)
                                self.__renaming_name = new_name

                                if ctx.is_key_pressed(KEY_ENTER):
                                    self._do_rename()
                                elif ctx.is_key_pressed(KEY_ESCAPE):
                                    self.__renaming_path = None
                                elif ctx.is_item_deactivated():
                                    self._do_rename()

                            else:
                                name_display, offset_x = _get_cached_label(ctx, item, icon_size)
                                ctx.set_cursor_pos_x(cell_start_x + offset_x)
                                ctx.label(name_display)

                            ctx.end_group()

                        # ── Style pop ONCE after all items ──
                        ctx.pop_style_color(2)   # Button, ButtonHovered
                        ctx.pop_style_var(1)     # FrameBorderSize
                        ctx.pop_style_var(1)     # FramePadding

                        if bottom_spacer_h > 0.0:
                            ctx.table_next_row()
                            ctx.table_set_column_index(0)
                            ctx.dummy(1.0, bottom_spacer_h)

                        ctx.end_table()


                else:
                    ctx.label(t("project.invalid_path"))

                # Drop target: accept hierarchy GameObjects to create prefab files
                # (bottom fill area catches drops not on specific items)
                remaining_h = ctx.get_content_region_avail_height()
                if remaining_h > 10:
                    ctx.invisible_button("##drop_prefab_area",
                                         ctx.get_content_region_avail_width(), remaining_h)
                    if ctx.is_item_clicked(0):
                        self.clear_selection()
                        self._notify_empty_area_clicked()
                    from .igui import IGUI
                    IGUI.drop_target(ctx, "HIERARCHY_GAMEOBJECT",
                                     self._create_prefab_from_hierarchy,
                                     outline=False)

            ctx.end_child()
            ctx.pop_style_color(1)   # Border (from push_transparent_border)
            ctx.pop_style_var(1)     # WindowPadding
