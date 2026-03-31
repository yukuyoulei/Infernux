# Shader

<div class="class-info">
类位于 <b>Infernux.core</b>
</div>

## 描述

着色器程序资源。

<!-- USER CONTENT START --> description

<!-- USER CONTENT END -->

## 静态方法

| 方法 | 描述 |
|------|------|
| `Shader.is_loaded(name: str, shader_type: str = ...) → bool` | Check if a shader is loaded in the cache. |
| `Shader.invalidate(shader_id: str) → None` | Invalidate the shader program cache for hot-reload. |
| `Shader.reload(shader_id: str) → bool` | Invalidate cache and refresh all materials using this shader. |
| `Shader.refresh_materials(shader_id: str, engine: Optional[object] = ...) → bool` | Refresh all material pipelines that use a given shader. |
| `Shader.load_spirv(name: str, spirv_code: bytes, shader_type: str = ...) → None` | Load a SPIR-V shader module into the engine. |

<!-- USER CONTENT START --> static_methods

<!-- USER CONTENT END -->

## 示例

<!-- USER CONTENT START --> example
```python
# TODO: Add example for Shader
```
<!-- USER CONTENT END -->

## 另请参阅

<!-- USER CONTENT START --> see_also

<!-- USER CONTENT END -->
