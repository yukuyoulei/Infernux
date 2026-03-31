# Light

<div class="class-info">
class in <b>Infernux.components.builtin</b>
</div>

**Inherits from:** [BuiltinComponent](Component.md)

## Description

A Light component that illuminates the scene.

<!-- USER CONTENT START --> description

<!-- USER CONTENT END -->

## Properties

| Name | Type | Description |
|------|------|------|
| light_type | `int` | The type of light (Directional, Point, or Spot). |
| color | `List[float]` | The color of the light. |
| intensity | `float` | The brightness of the light. |
| range | `float` | The range of the light in world units. |
| spot_angle | `float` | The inner cone angle of the spot light in degrees. |
| outer_spot_angle | `float` | The outer cone angle of the spot light in degrees. |
| shadows | `int` | The shadow casting mode of the light. |
| shadow_strength | `float` | The strength of the shadows cast by this light. |
| shadow_bias | `float` | Bias value to reduce shadow acne artifacts. |

<!-- USER CONTENT START --> properties

<!-- USER CONTENT END -->

## Public Methods

| Method | Description |
|------|------|
| `get_light_view_matrix() → Any` | Return the light's view matrix for shadow mapping. |
| `get_light_projection_matrix(shadow_extent: float = ..., near_plane: float = ..., far_plane: float = ...) → Any` | Return the light's projection matrix for shadow mapping. |
| `serialize() → str` | Serialize the component to a JSON string. |

<!-- USER CONTENT START --> public_methods

<!-- USER CONTENT END -->

## Lifecycle Methods

| Method | Description |
|------|------|
| `on_draw_gizmos_selected() → None` | Draw a type-specific gizmo when the light is selected. |

<!-- USER CONTENT START --> lifecycle_methods

<!-- USER CONTENT END -->

## Example

<!-- USER CONTENT START --> example
```python
# TODO: Add example for Light
```
<!-- USER CONTENT END -->

## See Also

<!-- USER CONTENT START --> see_also

<!-- USER CONTENT END -->
