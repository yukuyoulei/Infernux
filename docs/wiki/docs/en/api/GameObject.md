# GameObject

<div class="class-info">
class in <b>Infernux</b>
</div>

## Description

Game object in the scene hierarchy.

<!-- USER CONTENT START --> description

<!-- USER CONTENT END -->

## Properties

| Name | Type | Description |
|------|------|------|
| name | `str` |  |
| active | `bool` |  |
| tag | `str` |  |
| layer | `int` |  |
| is_static | `bool` |  |
| prefab_guid | `str` |  |
| prefab_root | `bool` |  |
| active_self | `bool` |  *(read-only)* |
| active_in_hierarchy | `bool` |  *(read-only)* |
| id | `int` |  *(read-only)* |
| is_prefab_instance | `bool` |  *(read-only)* |
| game_object | `Optional[GameObject]` |  *(read-only)* |
| transform | `Transform` |  *(read-only)* |
| scene | `Scene` |  *(read-only)* |

<!-- USER CONTENT START --> properties

<!-- USER CONTENT END -->

## Public Methods

| Method | Description |
|------|------|
| `compare_tag(tag: str) → bool` |  |
| `get_transform() → Transform` |  |
| `add_component(component_type: Any) → Optional[Any]` |  |
| `remove_component(component: Any) → bool` |  |
| `can_remove_component(component: Any) → bool` |  |
| `get_remove_component_blockers(component: Any) → List[str]` |  |
| `get_components(component_type: Any = ...) → List[Any]` |  |
| `get_component(component_type: Any) → Optional[Any]` |  |
| `get_cpp_component(type_name: str) → Optional[Component]` |  |
| `get_cpp_components(type_name: str) → List[Component]` |  |
| `add_py_component(component_instance: Any) → Any` |  |
| `get_py_component(component_type: Any) → Any` |  |
| `get_py_components() → List[Any]` |  |
| `remove_py_component(component: Any) → bool` |  |
| `get_parent() → Optional[GameObject]` |  |
| `set_parent(parent: Optional[GameObject], world_position_stays: bool = True) → None` |  |
| `get_children() → List[GameObject]` |  |
| `get_child_count() → int` |  |
| `get_child(index: int) → GameObject` |  |
| `find_child(name: str) → Optional[GameObject]` |  |
| `find_descendant(name: str) → Optional[GameObject]` |  |
| `is_active_in_hierarchy() → bool` |  |
| `get_component_in_children(component_type: Any, include_inactive: bool = False) → Any` |  |
| `get_component_in_parent(component_type: Any, include_inactive: bool = False) → Any` |  |
| `serialize() → str` |  |
| `deserialize(json_str: str) → None` |  |

<!-- USER CONTENT START --> public_methods

<!-- USER CONTENT END -->

## Static Methods

| Method | Description |
|------|------|
| `static GameObject.find(name: str) → Optional[GameObject]` |  |
| `static GameObject.find_with_tag(tag: str) → Optional[GameObject]` |  |
| `static GameObject.find_game_objects_with_tag(tag: str) → List[GameObject]` |  |
| `static GameObject.instantiate(original: Any) → Optional[GameObject]` |  |
| `static GameObject.destroy(game_object: GameObject) → None` |  |

<!-- USER CONTENT START --> static_methods

<!-- USER CONTENT END -->

## Example

<!-- USER CONTENT START --> example
```python
# TODO: Add example for GameObject
```
<!-- USER CONTENT END -->

## See Also

<!-- USER CONTENT START --> see_also

<!-- USER CONTENT END -->
