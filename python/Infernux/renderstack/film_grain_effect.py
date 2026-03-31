"""
FilmGrainEffect — Cinematic noise overlay.

Aligned with Unity URP Film Grain (simplified white noise type).
Operates in LDR space (after_post_process) to match URP behaviour
where grain is applied after tone mapping.

Parameters:
    intensity — grain strength (0 = off, 1 = heavy)
    response  — luminance response (0 = uniform, 1 = highlights only)
"""

from __future__ import annotations

import time as _time
from typing import List, TYPE_CHECKING

from Infernux.renderstack.fullscreen_effect import FullScreenEffect
from Infernux.components.serialized_field import serialized_field

if TYPE_CHECKING:
    from Infernux.rendergraph.graph import RenderGraph
    from Infernux.renderstack.resource_bus import ResourceBus


class FilmGrainEffect(FullScreenEffect):
    """URP-aligned Film Grain post-processing effect."""

    name = "Film Grain"
    injection_point = "after_post_process"
    default_order = 800
    menu_path = "Post-processing/Film Grain"

    intensity: float = serialized_field(default=0.2, range=(0.0, 1.0), slider=False)
    response: float = serialized_field(default=0.8, range=(0.0, 1.0), slider=False)

    def get_shader_list(self) -> List[str]:
        return ["fullscreen_triangle", "film_grain"]

    def setup_passes(self, graph: "RenderGraph", bus: "ResourceBus") -> None:
        from Infernux.rendergraph.graph import Format

        self.apply_single_source_effect(
            graph,
            bus,
            output_name="_filmgrain_out",
            pass_name="FilmGrain_Apply",
            shader_name="film_grain",
            format=Format.RGBA16_SFLOAT,
            params={
                "intensity": self.intensity,
                "response": self.response,
                "time": float(_time.perf_counter() % 1000.0),
            },
        )
