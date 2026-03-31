# Light

<div class="class-info">
类位于 <b>Infernux.components.builtin</b>
</div>

**继承自:** [BuiltinComponent](Component.md)

## 描述

为场景提供照明的光源组件。

<!-- USER CONTENT START --> description

<!-- USER CONTENT END -->

## 属性

| 名称 | 类型 | 描述 |
|------|------|------|
| light_type | `int` | 光源类型（0=方向光，1=点光源，2=聚光灯）。 |
| color | `List[float]` | 光源颜色（RGB）。 |
| intensity | `float` | 光源强度。 |
| range | `float` | 点光源或聚光灯的照射范围。 |
| spot_angle | `float` | 聚光灯的锥角（度）。 |
| outer_spot_angle | `float` | The outer cone angle of the spot light in degrees. |
| shadows | `int` | The shadow casting mode of the light. |
| shadow_strength | `float` | 阴影强度。 |
| shadow_bias | `float` | 阴影偏移量。 |

<!-- USER CONTENT START --> properties

<!-- USER CONTENT END -->

## 公共方法

| 方法 | 描述 |
|------|------|
| `get_light_view_matrix() → Any` | Return the light's view matrix for shadow mapping. |
| `get_light_projection_matrix(shadow_extent: float = ..., near_plane: float = ..., far_plane: float = ...) → Any` | Return the light's projection matrix for shadow mapping. |
| `serialize() → str` | Serialize the component to a JSON string. |

<!-- USER CONTENT START --> public_methods

<!-- USER CONTENT END -->

## 生命周期方法

| 方法 | 描述 |
|------|------|
| `on_draw_gizmos_selected() → None` | Draw a type-specific gizmo when the light is selected. |

<!-- USER CONTENT START --> lifecycle_methods

<!-- USER CONTENT END -->

## 示例

<!-- USER CONTENT START --> example
```python
# TODO: Add example for Light
```
<!-- USER CONTENT END -->

## 另请参阅

<!-- USER CONTENT START --> see_also

<!-- USER CONTENT END -->
