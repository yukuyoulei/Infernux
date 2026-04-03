<p align="center">
  <img src="docs/assets/logo.png" alt="Infernux logo" width="128" />
</p>

<h1 align="center">Infernux</h1>

<p align="center">
  <strong>Windows-first open-source game engine with a C++17 / Vulkan runtime, a Python editor layer, and an in-progress C# gameplay runtime.</strong>
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
  <a href="README-zh.md">Chinese README</a> |
  <a href="https://chenlizheme.github.io/Infernux/">Website</a> |
  <a href="https://chenlizheme.github.io/Infernux/wiki.html">Docs</a>
</p>

---

## Overview

Infernux is a from-scratch engine for teams that want to own the runtime, the tools, and the iteration loop.

Today the project is best described as:

- a native C++17 / Vulkan engine runtime
- a Python-based editor, tooling, and asset workflow layer
- a Windows-only native CLR host for managed C# gameplay scripts

The hot path stays native, the editor stays scriptable, and the gameplay surface is gradually moving from Python gameplay scripts toward C# runtime components.

## Current State

The repository is a Windows technical preview with real engine/editor functionality, not a finished multi-platform product.

What is already working:

- Vulkan forward and deferred rendering, PBR, shadows, post-processing, RenderGraph, and RenderStack
- Jolt physics, scene hierarchy, prefabs, GUID-based assets, and dependency tracking
- Built-in editor panels including Hierarchy, Inspector, Scene View, Game View, Project, Console, and UI tooling
- Python editor/tooling layer for workflows, automation, and authoring
- Native CLR hosting on Windows through `hostfxr`
- C# runtime component lifecycle and a growing engine bridge

What is still in progress:

- broader C# gameplay API coverage
- more docs and onboarding material
- animation and deeper content-pipeline work

## Architecture

| Layer | Responsibility |
|:------|:---------------|
| C++17 / Vulkan | Renderer, scene systems, physics, resources, platform integration |
| pybind11 bridge | Native bindings for the Python/editor layer |
| Python | Editor UI, tooling, workflows, packaging, asset automation |
| Native CLR host | Loads and drives managed gameplay assemblies on Windows |
| C# | Runtime gameplay components and managed engine-facing APIs |

Important boundary:

- Python is still the production/editor layer.
- C# is currently the managed gameplay runtime layer.
- Managed runtime hosting is Windows-only right now.

## C# Gameplay Support

The engine now generates a managed gameplay project at:

- `Scripts/Infernux.GameScripts.csproj`

and runtime stubs at:

- `Scripts/Generated/Infernux.RuntimeStubs.cs`

User gameplay scripts are compiled from:

- `Assets/**/*.cs`

The generated project targets `net8.0`, and the native runtime loads the resulting assembly through `hostfxr`.

### C# API currently bridged

User gameplay scripts currently inherit from `InxComponent`.

`InxComponent`

- context properties: `gameObject`, `transform`, `Enabled`, `ExecutionOrder`, `ScriptGuid`
- lifecycle methods: `Awake`, `OnEnable`, `Start`, `Update(float deltaTime)`, `FixedUpdate(float fixedDeltaTime)`, `LateUpdate(float deltaTime)`, `OnDisable`, `OnDestroy`, `OnValidate`, `Reset`

`GameObject`

- `Find(string)`
- `Create(string? name = null)`
- `CreatePrimitive(PrimitiveType, string? name = null)`
- `Instantiate(GameObject, Transform? parent = null)`
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
- `parent`
- `childCount`
- `Translate(Vector3)`
- `SetParent(Transform? parent, bool worldPositionStays = true)`
- `GetChild(int)`
- `Find(string)`

`Debug`

- `Log`
- `LogWarning`
- `LogError`

### Example

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

## Requirements

| Dependency | Version |
|:-----------|:--------|
| Windows | 10 / 11 (64-bit) |
| Visual Studio | 2022 with MSVC v143 |
| CMake | 3.22+ |
| Python | 3.12+ x64 |
| Vulkan SDK | 1.3+ |
| .NET | .NET 8 SDK or runtime |
| Git | Latest Git for Windows |

Notes:

- The native CLR host searches for `hostfxr.dll` from installed .NET locations.
- The Windows build helper defaults to `PythonSpec 3.12`, but `3.13` also works if installed and selected explicitly.

## Quick Start

### Clone

```powershell
git clone --recurse-submodules https://github.com/ChenlizheMe/Infernux.git
cd Infernux
```

If you already cloned without submodules:

```powershell
git submodule update --init --recursive
```

### Recommended Windows build

Use the repository helper:

```powershell
powershell -ExecutionPolicy Bypass -File .\dev\build_engine_windows.ps1 -PythonSpec 3.12
```

Useful options:

- `-Preset debug`
- `-SkipManagedBuild`
- `-RunLauncher`

What this script does:

- validates Python, CMake, Vulkan SDK, and Git
- initializes submodules
- installs Python requirements into `.venv`
- configures and builds the native engine
- packages and installs the Python module into the local environment
- optionally builds a managed gameplay project if one exists in the repo root

### Launch the editor in development mode

```powershell
.\.venv\Scripts\python.exe .\packaging\launcher.py
```

## Managed Project Workflow

For an actual game project, the engine generates:

- `Scripts/Infernux.GameScripts.csproj`
- `Scripts/Generated/Infernux.RuntimeStubs.cs`

Build the managed gameplay assembly with:

```powershell
dotnet build 'E:\Path\To\YourProject\Scripts\Infernux.GameScripts.csproj' -c Debug
```

If the build fails because `Infernux.GameScripts.dll` is locked, close the running editor or build to a temporary output directory:

```powershell
dotnet build 'E:\Path\To\YourProject\Scripts\Infernux.GameScripts.csproj' -c Debug -p:OutDir=E:\Path\To\YourProject\Scripts\bin\DebugVerify\
```

The native host looks for:

- `Data/Managed/Infernux.GameScripts.dll`
- `Scripts/bin/Debug/net8.0/Infernux.GameScripts.dll`
- `Scripts/bin/Release/net8.0/Infernux.GameScripts.dll`

with the matching `.runtimeconfig.json`.

## Manual Native Build

If you prefer not to use the PowerShell helper:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cmake --preset release -DPython3_EXECUTABLE="%CD%\\.venv\\Scripts\\python.exe"
cmake --build --preset release
```

The helper script is still the recommended path on Windows because it handles tool detection and packaging details for you.

## Tests

Python tests:

```powershell
cd python
python -m pytest test -v
```

Managed gameplay smoke tests are currently best validated by:

- building the generated `Infernux.GameScripts.csproj`
- launching the editor
- entering Play Mode with a C# component attached

## Packaging

Portable Hub bundle:

```powershell
cmake --build --preset packaging
```

Windows installer:

```powershell
cmake --build --preset packaging-installer
```

## Documentation

- Website: [https://chenlizheme.github.io/Infernux/](https://chenlizheme.github.io/Infernux/)
- Docs hub: [https://chenlizheme.github.io/Infernux/wiki.html](https://chenlizheme.github.io/Infernux/wiki.html)

Regenerate docs locally:

```powershell
python docs/wiki/generate_api_docs.py
python -m mkdocs build --clean -f docs/wiki/mkdocs.yml
```

## Contributing

Useful issues and PRs right now are the ones that improve:

- C# gameplay bridge coverage
- editor stability and workflow polish
- docs and onboarding
- content pipeline robustness

Before sending broad architectural changes, open an issue or discussion first.

Related community files:

- `CONTRIBUTING.md`
- `SECURITY.md`
- `SUPPORT.md`

## License

Infernux is released under the MIT License. See [LICENSE](LICENSE) for details.
