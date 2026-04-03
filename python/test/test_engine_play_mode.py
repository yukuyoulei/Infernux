"""Tests for Infernux.engine.play_mode — PlayModeState, PlayModeEvent, PlayModeManager."""

import sys
from types import SimpleNamespace

from Infernux.engine.play_mode import PlayModeState, PlayModeEvent, PlayModeManager


class _FakeRuntimeGameObject:
    def __init__(self, object_id: int, name: str):
        self.id = object_id
        self.name = name
        self.transform = object()


# ══════════════════════════════════════════════════════════════════════
# PlayModeState enum
# ══════════════════════════════════════════════════════════════════════

class TestPlayModeState:
    def test_members_exist(self):
        assert PlayModeState.EDIT is not None
        assert PlayModeState.PLAYING is not None
        assert PlayModeState.PAUSED is not None

    def test_distinct_values(self):
        values = {PlayModeState.EDIT, PlayModeState.PLAYING, PlayModeState.PAUSED}
        assert len(values) == 3


# ══════════════════════════════════════════════════════════════════════
# PlayModeEvent
# ══════════════════════════════════════════════════════════════════════

class TestPlayModeEvent:
    def test_fields(self):
        evt = PlayModeEvent(
            old_state=PlayModeState.EDIT,
            new_state=PlayModeState.PLAYING,
            timestamp=1.0,
        )
        assert evt.old_state is PlayModeState.EDIT
        assert evt.new_state is PlayModeState.PLAYING
        assert evt.timestamp == 1.0


# ══════════════════════════════════════════════════════════════════════
# PlayModeManager
# ══════════════════════════════════════════════════════════════════════

class TestPlayModeManager:
    def test_initial_state_is_edit(self):
        mgr = PlayModeManager()
        assert mgr._state is PlayModeState.EDIT

    def test_singleton_instance(self):
        mgr = PlayModeManager()
        assert PlayModeManager.instance() is mgr

    def test_timing_defaults(self):
        mgr = PlayModeManager()
        assert mgr._delta_time == 0.0
        assert mgr._time_scale == 1.0
        assert mgr._total_play_time == 0.0

    def test_scene_backup_none_initially(self):
        mgr = PlayModeManager()
        assert mgr._scene_backup is None
        assert mgr._scene_path_backup is None

    def test_listener_list_empty(self):
        mgr = PlayModeManager()
        assert mgr._state_change_listeners == []

    def test_set_asset_database(self):
        mgr = PlayModeManager()
        mgr.set_asset_database("fake_db")
        assert mgr._asset_database == "fake_db"

    def test_register_runtime_hidden_object_tracks_ids(self):
        mgr = PlayModeManager()
        obj = _FakeRuntimeGameObject(404, "HiddenClone")

        mgr.register_runtime_hidden_object(obj)

        assert mgr.is_runtime_hidden_object_id(404)

    def test_rebuild_scene_clears_runtime_hidden_ids(self):
        mgr = PlayModeManager()
        mgr._runtime_hidden_object_ids = {1, 2, 3}

        assert not mgr._rebuild_active_scene(None, for_play=False)
        assert mgr._runtime_hidden_object_ids == set()

    def test_rebuild_scene_does_not_materialize_prefab_refs_for_play(self, monkeypatch):
        class _FakeScene:
            def __init__(self):
                self.playing = None

            def deserialize(self, snapshot):
                return bool(snapshot)

            def set_playing(self, playing):
                self.playing = playing

        class _FakeSceneManager:
            def __init__(self, scene):
                self._scene = scene

            def get_active_scene(self):
                return self._scene

        mgr = PlayModeManager()
        scene = _FakeScene()
        scene_manager = _FakeSceneManager(scene)
        materialized = False

        monkeypatch.setattr(mgr, "_get_scene_manager", lambda: scene_manager)
        monkeypatch.setattr(mgr, "_restore_pending_py_components", lambda: None)

        def _unexpected_materialize():
            nonlocal materialized
            materialized = True

        monkeypatch.setattr(mgr, "_materialize_prefab_references_for_play", _unexpected_materialize)

        assert mgr._rebuild_active_scene("snapshot", for_play=True)
        assert scene.playing is True
        assert not materialized

    def test_rebuild_scene_refreshes_managed_runtime_before_restoring_components(self, monkeypatch):
        class _FakeScene:
            def __init__(self):
                self.playing = None

            def deserialize(self, snapshot):
                return bool(snapshot)

            def set_playing(self, playing):
                self.playing = playing

        class _FakeSceneManager:
            def __init__(self, scene):
                self._scene = scene

            def get_active_scene(self):
                return self._scene

        mgr = PlayModeManager()
        scene = _FakeScene()
        scene_manager = _FakeSceneManager(scene)
        call_order = []

        monkeypatch.setattr(mgr, "_get_scene_manager", lambda: scene_manager)
        monkeypatch.setattr(mgr, "_restore_pending_py_components", lambda: call_order.append("restore"))
        monkeypatch.setitem(
            sys.modules,
            "Infernux.lib",
            SimpleNamespace(
                reload_managed_runtime_if_changed=lambda: call_order.append("reload") or True,
                get_managed_runtime_error=lambda: "",
            ),
        )

        assert mgr._rebuild_active_scene(
            "snapshot",
            for_play=True,
            reload_managed_runtime=True,
        )
        assert call_order == ["reload", "restore"]
        assert scene.playing is True

    def test_rebuild_scene_aborts_when_managed_runtime_refresh_fails(self, monkeypatch):
        class _FakeScene:
            def deserialize(self, snapshot):
                return bool(snapshot)

        class _FakeSceneManager:
            def __init__(self, scene):
                self._scene = scene

            def get_active_scene(self):
                return self._scene

        mgr = PlayModeManager()
        scene = _FakeScene()
        scene_manager = _FakeSceneManager(scene)
        restored = False

        monkeypatch.setattr(mgr, "_get_scene_manager", lambda: scene_manager)

        def _unexpected_restore():
            nonlocal restored
            restored = True

        monkeypatch.setattr(mgr, "_restore_pending_py_components", _unexpected_restore)
        monkeypatch.setitem(
            sys.modules,
            "Infernux.lib",
            SimpleNamespace(
                reload_managed_runtime_if_changed=lambda: False,
                get_managed_runtime_error=lambda: "reload failed",
            ),
        )

        assert not mgr._rebuild_active_scene(
            "snapshot",
            for_play=True,
            reload_managed_runtime=True,
        )
        assert not restored
