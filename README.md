<p align="center">
  <img src="docs/assets/logo.png" alt="Infernux logo" width="128" />
</p>

<h1 align="center">Infernux With C#</h1>

<p align="center">
  <strong>面向 Windows 的开源游戏引擎，包含 C++17 / Vulkan 原生运行时、Python 编辑器层，以及正在完善中的 C# Gameplay 运行时。</strong>
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="MIT License" /></a>
  <img src="https://img.shields.io/badge/version-0.1.1-orange.svg" alt="Version" />
  <img src="https://img.shields.io/badge/platform-Windows-lightgrey.svg" alt="Platform" />
  <img src="https://img.shields.io/badge/python-3.12%2B-brightgreen.svg" alt="Python" />
  <img src="https://img.shields.io/badge/.NET-8-blue.svg" alt=".NET 8" />
  <img src="https://img.shields.io/badge/C%2B%2B-17-blue.svg" alt="C++ 17" />
  <img src="https://img.shields.io/badge/graphics-Vulkan-red.svg" alt="Vulkan" />
</p>

<p align="center">
  <a href="README-zh.md">English README</a> |
  <a href="https://chenlizheme.github.io/Infernux/">官网</a> |
  <a href="https://chenlizheme.github.io/Infernux/wiki.html">文档</a>
</p>

---

## 项目概览

Infernux 是一个从零开始构建的引擎，目标是让团队真正掌控运行时、工具链和迭代流程，而不是依赖不可修改的黑盒。

目前这个项目可以概括为三层：

- C++17 / Vulkan 原生引擎运行时
- 基于 Python 的编辑器、工具链和资产工作流层
- 仅限 Windows 的原生 CLR Host，用于承载 C# 托管 Gameplay 脚本

性能关键路径保持在原生层，编辑器和工具仍然以 Python 为主，Gameplay 能力则在逐步从 Python 脚本迁移到 C# 组件运行时。

## 当前状态

当前仓库是一个 Windows 技术预览版，已经具备真实可用的引擎/编辑器能力，但还不是一个完成态的跨平台产品。

已经可用的能力：

- Vulkan 前向与延迟渲染、PBR、阴影、后处理、RenderGraph、RenderStack
- Jolt 物理、场景层级、Prefab、基于 GUID 的资产系统与依赖追踪
- 内置编辑器面板，包括 Hierarchy、Inspector、Scene View、Game View、Project、Console 和 UI 工具
- Python 编辑器/工具层，可用于工作流、自动化与内容制作
- 通过 `hostfxr` 实现的 Windows 原生 CLR 托管
- C# 运行时组件生命周期，以及持续扩展中的引擎桥接层

仍在推进中的部分：

- 更完整的 C# Gameplay API 覆盖
- 更多文档和上手材料
- 动画系统和更深入的内容管线能力

## 架构

| 层 | 职责 |
|:---|:-----|
| C++17 / Vulkan | 渲染、场景系统、物理、资源、平台集成 |
| pybind11 bridge | Python / 编辑器层的原生绑定 |
| Python | 编辑器 UI、工具链、工作流、打包、资产自动化 |
| Native CLR host | 在 Windows 上加载并驱动托管 Gameplay 程序集 |
| C# | 运行时 Gameplay 组件与托管引擎 API |

当前边界要点：

- Python 仍然是编辑器与生产工具层。
- C# 当前定位是托管 Gameplay 运行时层。
- 托管运行时宿主目前只支持 Windows。

## C# Gameplay 支持

引擎现在会生成托管 Gameplay 工程：

- `Scripts/Infernux.GameScripts.csproj`

同时生成运行时桩代码：

- `Scripts/Generated/Infernux.RuntimeStubs.cs`

用户自己的 Gameplay 脚本默认从这里编译：

- `Assets/**/*.cs`

生成的工程目标框架是 `net8.0`，原生运行时通过 `hostfxr` 加载对应程序集。

### 当前已桥接的 C# API

用户脚本目前继承自 `InxComponent`。

`Component`

- 公共基类：`Transform` 与 `InxComponent` 都继承自它
- 上下文属性：`gameObject`、`transform`

`InxComponent`

- 上下文属性：`gameObject`、`transform`、`Enabled`、`ExecutionOrder`、`ScriptGuid`
- 生命周期：`Awake`、`OnEnable`、`Start`、`Update(float deltaTime)`、`FixedUpdate(float fixedDeltaTime)`、`LateUpdate(float deltaTime)`、`OnDisable`、`OnDestroy`、`OnValidate`、`Reset`

`GameObject`

- `Find(string)`
- `Create(string? name = null)`
- `CreatePrimitive(PrimitiveType, string? name = null)`
- `Instantiate(GameObject, Transform? parent = null)`
- `AddComponent<T>() where T : InxComponent`
- `GetComponent<T>() where T : Component`
- `TryGetComponent<T>(out T? component) where T : Component`
- `GetComponentInChildren<T>() where T : Component`
- `GetComponentInParent<T>() where T : Component`
- `Destroy(GameObject?)`
- `Destroy()`
- `name`
- `tag`
- `layer`
- `activeSelf`
- `activeInHierarchy`
- `SetActive(bool)`
- `CompareTag(string)`

`Transform`

- `position`
- `localPosition`
- `localScale`
- `lossyScale`
- `rotation`
- `localRotation`
- `eulerAngles`
- `localEulerAngles`
- `parent`
- `root`
- `childCount`
- `forward`
- `right`
- `up`
- `localForward`
- `localRight`
- `localUp`
- `Translate(Vector3)`
- `TranslateLocal(Vector3)`
- `Rotate(Vector3)`
- `Rotate(Vector3, float)`
- `RotateAround(Vector3, Vector3, float)`
- `LookAt(Vector3)`
- `LookAt(Vector3, Vector3)`
- `TransformPoint(Vector3)`
- `InverseTransformPoint(Vector3)`
- `TransformDirection(Vector3)`
- `InverseTransformDirection(Vector3)`
- `TransformVector(Vector3)`
- `InverseTransformVector(Vector3)`
- `SetParent(Transform? parent, bool worldPositionStays = true)`
- `GetChild(int)`
- `Find(string)`
- `DetachChildren()`
- `IsChildOf(Transform?)`
- `GetSiblingIndex()`
- `SetSiblingIndex(int)`
- `SetAsFirstSibling()`
- `SetAsLastSibling()`

`Debug`

- `Log`
- `LogWarning`
- `LogError`

### 示例

```csharp
using Infernux;

public sealed class NewComponent : InxComponent
{
    public override void Start()
    {
        var cube = GameObject.CreatePrimitive(PrimitiveType.Cube, "RuntimeCube");
        if (cube != null)
        {
            cube.transform.position = new Vector3(0, 1, 0);
            cube.transform.localScale = new Vector3(2, 2, 2);

            var clone = GameObject.Instantiate(cube);
            if (clone != null)
            {
                clone.transform.position = new Vector3(2, 1, 0);
            }

            Debug.Log($"Created {cube.name}");
        }
    }
}
```

## 环境要求

| 依赖 | 版本 |
|:-----|:-----|
| Windows | 10 / 11（64 位） |
| Visual Studio | 2022，带 MSVC v143 |
| CMake | 3.22+ |
| Python | 3.12+ x64 |
| Vulkan SDK | 1.3+ |
| .NET | .NET 8 SDK 或 Runtime |
| Git | 最新版 Git for Windows |

说明：

- 原生 CLR Host 会从已安装的 .NET 位置搜索 `hostfxr.dll`。
- Windows 构建脚本默认使用 `PythonSpec 3.12`，如果机器上装了 `3.13` 也可以显式指定。

## 快速开始

### 克隆仓库

```powershell
git clone --recurse-submodules https://github.com/ChenlizheMe/Infernux.git
cd Infernux
```

如果之前没有带子模块：

```powershell
git submodule update --init --recursive
```

### 推荐的 Windows 构建方式

直接使用仓库内置脚本：

```powershell
powershell -ExecutionPolicy Bypass -File .\dev\build_engine_windows.ps1 -PythonSpec 3.12
```

常用参数：

- `-Preset debug`
- `-SkipManagedBuild`
- `-RunLauncher`

这个脚本会做的事情：

- 检查 Python、CMake、Vulkan SDK、Git
- 初始化子模块
- 在 `.venv` 中安装 Python 依赖
- 配置并编译原生引擎
- 打包并把 Python 模块安装到本地环境
- 如果仓库根目录存在托管工程，则顺手构建 C# Gameplay 项目

### 以开发模式启动编辑器

```powershell
.\.venv\Scripts\python.exe .\packaging\launcher.py
```

## 托管工程工作流

对于实际游戏项目，引擎会生成：

- `Scripts/Infernux.GameScripts.csproj`
- `Scripts/Generated/Infernux.RuntimeStubs.cs`

构建托管 Gameplay 程序集：

```powershell
dotnet build 'E:\Path\To\YourProject\Scripts\Infernux.GameScripts.csproj' -c Debug
```

如果因为 `Infernux.GameScripts.dll` 被占用导致构建失败，可以关闭编辑器，或者临时输出到别的目录：

```powershell
dotnet build 'E:\Path\To\YourProject\Scripts\Infernux.GameScripts.csproj' -c Debug -p:OutDir=E:\Path\To\YourProject\Scripts\bin\DebugVerify\
```

原生宿主会按下面这些位置查找程序集：

- `Data/Managed/Infernux.GameScripts.dll`
- `Scripts/bin/Debug/net8.0/Infernux.GameScripts.dll`
- `Scripts/bin/Release/net8.0/Infernux.GameScripts.dll`

并要求对应的 `.runtimeconfig.json` 同时存在。

## 手动构建原生引擎

如果你不想用 PowerShell 脚本，也可以手工执行：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cmake --preset release -DPython3_EXECUTABLE="%CD%\\.venv\\Scripts\\python.exe"
cmake --build --preset release
```

不过在 Windows 上仍然更推荐使用构建脚本，因为它已经处理好了工具探测和打包细节。

## 测试

Python 测试：

```powershell
cd python
python -m pytest test -v
```

目前 C# Gameplay 的 Smoke Test 最直接的验证方式是：

- 构建生成的 `Infernux.GameScripts.csproj`
- 启动编辑器
- 给场景对象挂上 C# 组件并进入 Play Mode

## 打包

便携式 Hub 包：

```powershell
cmake --build --preset packaging
```

Windows 安装器：

```powershell
cmake --build --preset packaging-installer
```

## 文档

- 官网：[https://chenlizheme.github.io/Infernux/](https://chenlizheme.github.io/Infernux/)
- 文档入口：[https://chenlizheme.github.io/Infernux/wiki.html](https://chenlizheme.github.io/Infernux/wiki.html)

本地重新生成文档：

```powershell
python docs/wiki/generate_api_docs.py
python -m mkdocs build --clean -f docs/wiki/mkdocs.yml
```

## 参与贡献

当前最有价值的 Issue 和 PR 方向主要是：

- C# Gameplay 桥接覆盖面
- 编辑器稳定性与工作流打磨
- 文档和上手体验
- 内容管线健壮性

如果是比较大的架构改动，建议先开 Issue 或 Discussion 再推进。

相关社区文件：

- `CONTRIBUTING.md`
- `SECURITY.md`
- `SUPPORT.md`

## 许可证

Infernux 基于 MIT License 发布，详见 [LICENSE](LICENSE)。
