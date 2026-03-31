# Component

<div class="class-info">
class in <b>Infernux</b>
</div>

## Description

Base class for all components attached to GameObjects.

<!-- USER CONTENT START --> description

<!-- USER CONTENT END -->

## Properties

| Name | Type | Description |
|------|------|------|
| type_name | `str` |  *(read-only)* |
| component_id | `int` |  *(read-only)* |
| enabled | `bool` |  |
| execution_order | `int` |  |
| game_object | `GameObject` |  *(read-only)* |
| required_component_types | `List[str]` |  *(read-only)* |

<!-- USER CONTENT START --> properties

<!-- USER CONTENT END -->

## Public Methods

| Method | Description |
|------|------|
| `is_component_type(type_name: str) → bool` |  |
| `serialize() → str` |  |
| `deserialize(json_str: str) → None` |  |

<!-- USER CONTENT START --> public_methods

<!-- USER CONTENT END -->

## Example

<!-- USER CONTENT START --> example
```python
# TODO: Add example for Component
```
<!-- USER CONTENT END -->

## See Also

<!-- USER CONTENT START --> see_also

<!-- USER CONTENT END -->
