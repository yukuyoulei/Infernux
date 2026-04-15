<p align="center">
  <img src="docs/assets/logo.png" alt="Infernux logo" width="128" />
</p>

<h1 align="center">Infernux</h1>

<p align="center">
  <strong>开源游戏引擎，采用 C++17 / Vulkan 原生运行时，并配备面向生产工作流的 Python 层。</strong>
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="MIT License" /></a>
  <img src="https://img.shields.io/badge/version-0.1.3-orange.svg" alt="Version" />
  <img src="https://img.shields.io/badge/platform-Windows-lightgrey.svg" alt="Platform" />
  <img src="https://img.shields.io/badge/python-3.12+-brightgreen.svg" alt="Python" />
  <img src="https://img.shields.io/badge/C%2B%2B-17-blue.svg" alt="C++ 17" />
  <img src="https://img.shields.io/badge/graphics-Vulkan-red.svg" alt="Vulkan" />
</p>

<p align="center">
  <a href="README-zh.md">English</a> ·
  <a href="https://chenlizheme.github.io/Infernux/">官网</a> ·
  <a href="https://chenlizheme.github.io/Infernux/wiki.html">文档</a> ·
  <a href="#快速开始">快速开始</a>
</p>

## 运行画面

<p align="center">
  <img src="docs/assets/demo.png" alt="Infernux 编辑器中运行 10000 个立方体场景的截图" width="100%" />
</p>

<p align="center">
  <em>编辑器保持在 Play 模式运行时，场景仍持续渲染的实时画面。</em>
</p>

## 项目概览

Infernux 是一套从零开始构建的游戏引擎，面向那些希望真正掌控运行时、编辑器工作流和脚本扩展面的开发者，而不是把引擎当作一个无法触及内部机制的黑盒产品。

整个项目由三层组成：

- 原生 C++17 / Vulkan 运行时，负责渲染、场景系统、物理、音频和平台服务。
- 通过 pybind11 搭建的桥接层，将原生运行时能力暴露给 Python。
- Python 层，负责游戏玩法、编辑器工具、内容工作流、构建自动化与渲染编排。

架构目标很直接：性能热点留在原生层，迭代效率留给 Python，同时让整体代码库足够清晰，方便团队继续扩展，而不是被隐藏规则反向绑架。

## 当前范围

Infernux 目前仍是以 Windows 为主的技术预览版。项目已经具备可用的编辑器与运行时核心，但它仍应被视为持续演进中的引擎，而不是已经定型的商业平台。

当前已经具备的核心能力包括：

- Vulkan 前向与延迟渲染、PBR、级联阴影、MSAA、Shader 反射和后处理。
- 由 Python 编写的 RenderGraph 与 RenderStack API。
- 集成 Jolt 物理，包括刚体、碰撞体、场景查询、回调与层级过滤。
- 基于 GUID 的资源系统、依赖追踪、场景序列化、Prefab 工作流和 Play 模式隔离。
- 集成编辑器，包含 Hierarchy、Inspector、Scene View、Game View、Project、Console、UI 编辑和构建设置。
- Python 侧组件生命周期、协程、序列化字段以及脚本热重载支持。
- 基础运行时 UI 原语，包括 Canvas、Text、Image、Button 与指针事件。
- 面向 Hub、独立分发包和 Windows 安装器的打包路径。

## 已实现的 C# 桥接接口

当前仓库已经实现了首批 C# 托管运行时桥接，目标是让 `Infernux.GameScripts.dll` 中的 `MonoBehaviour` 脚本能够直接驱动场景对象。当前这部分能力以 Windows 为主。

- 生命周期桥接：支持 `Awake`、`OnEnable`、`Start`、`Update(float)`、`FixedUpdate(float)`、`LateUpdate(float)`、`OnDisable`、`OnDestroy`、`OnValidate`、`Reset`。
- 组件上下文桥接：已打通 `GameObjectId`、`ComponentId`、`enabled`、`ExecutionOrder`、`ScriptGuid` 等运行时上下文同步。
- `GameObject` 桥接：支持 `Find`、`Create`、`CreatePrimitive`、`Instantiate`、`Destroy`、`SetActive`，以及 `name`、`activeSelf`、`activeInHierarchy`、`tag`、`layer`、`transform`。
- 组件访问桥接：支持 `AddComponent<T>()`、`GetComponent`、`TryGetComponent`、`GetComponents`、`GetComponentInChildren`、`GetComponentsInChildren`、`GetComponentInParent`、`GetComponentsInParent`。
- `Transform` 属性桥接：支持 `position`、`localPosition`、`localScale`、`rotation`、`localRotation`、`eulerAngles`、`localEulerAngles`、`lossyScale`、`parent`、`childCount`、`root`。
- `Transform` 操作桥接：支持 `Translate`、`TranslateLocal`、`Rotate`、`RotateAround`、`LookAt`、`TransformPoint`、`InverseTransformPoint`、`TransformDirection`、`InverseTransformDirection`、`TransformVector`、`InverseTransformVector`。
- 层级操作桥接：支持 `SetParent`、`GetChild`、`Find`、`DetachChildren`、`GetSiblingIndex`、`SetSiblingIndex`、`SetAsFirstSibling`、`SetAsLastSibling`、`IsChildOf`。
- 调试桥接：支持 `Debug.Log`、`Debug.LogWarning`、`Debug.LogError` 将托管侧日志回送到原生日志系统。

当前限制：

- C# 托管运行时宿主目前仅支持 Windows。
- 目前 `GetComponent*` 系列面向 C# 的查询，已确认支持 `Transform` 和托管 `MonoBehaviour` 派生组件；其他原生内建组件的 C# 直连桥接仍在继续补齐。

## 架构

| 层级 | 职责 |
|:-----|:-----|
| C++17 / Vulkan | 渲染、资源所有权、场景系统、物理、音频、平台集成 |
| pybind11 bridge | 将原生能力绑定并暴露给 Python |
| Python | 游戏玩法、编辑器逻辑、工具链、自动化、渲染编排 |

这种分层让性能敏感的系统留在原生代码里，同时把日常生产代码放在更易迭代、也更易对接外部工具和数据管线的语言中。

## 快速开始

### 环境要求

<details>
<summary><b>Windows</b></summary>

| 依赖 | 版本 |
|:-----|:-----|
| Windows | 10 / 11（64 位） |
| Python | 3.12+ |
| Vulkan SDK | 1.3+ |
| CMake | 3.22+ |
| Visual Studio | 2022（MSVC v143） |
| pybind11 | 2.11+ |

</details>

<details>
<summary><b>macOS</b></summary>

| 依赖 | 版本 |
|:-----|:-----|
| macOS | 12+ |
| Python | 3.12+ |
| Vulkan SDK | 1.3+（LunarG SDK，含 MoltenVK） |
| CMake | 3.22+ |
| Ninja | 1.10+ |
| Xcode Command Line Tools | 最新版 |
| pybind11 | 2.11+ |

安装 Vulkan SDK 后，执行环境脚本：

```bash
source ~/VulkanSDK/<version>/setup-env.sh
brew install cmake ninja
```

</details>

只要是 Python 3.12 环境即可。下面的命令使用 Conda，因为它是当前仓库里最常见的工作流。

### 克隆

```bash
git clone --recurse-submodules https://github.com/ChenlizheMe/Infernux.git
cd Infernux
```

如果仓库最初没有连同子模块一起克隆：

```bash
git submodule update --init --recursive
```

### 构建

```bash
conda create -n infengine python=3.12 -y
conda activate infengine
pip install -r requirements.txt
cmake --preset release
cmake --build --preset release
```

在 macOS 上，请将 `release` 替换为 `release-macos`。

构建过程会把原生模块和运行时依赖复制到 Python 包中，因此你可以直接在当前环境里 `import Infernux`。

### 以开发模式启动 Hub

```bash
conda activate infengine
python packaging/launcher.py
```

开发模式会使用当前 Python 环境和本地构建产物，不会安装 Hub 自己管理的运行时。

### 运行测试

```bash
conda activate infengine
cd python
python -m pytest test/ -v
```

## 文档

- 官网：<https://chenlizheme.github.io/Infernux/>
- 文档入口：<https://chenlizheme.github.io/Infernux/wiki.html>
- API 参考：从 Python 包自动生成，并发布到 `docs/wiki/site/`

如果你想在本地重新生成 API Markdown 和静态站点：

```bash
conda activate infengine
python docs/wiki/generate_api_docs.py
python -m mkdocs build --clean -f docs/wiki/mkdocs.yml
```

对应的 CMake 目标分别是 `generate_api_docs` 和 `build_wiki_html`。

## 打包

Hub 当前支持两条分发路径。

### 独立目录包

```bash
cmake --build --preset packaging
```

该命令会在 `dist/Infernux Hub/` 下生成可携带的 PyInstaller 输出。

### Windows 安装器

```bash
cmake --build --preset packaging-installer
```

该命令会生成图形化 Windows 安装器。安装流程会为当前主机准备匹配架构的 Python 3.12 运行时，并在此托管基础上为项目创建独立运行环境。

## 引用

如果你在论文、技术文章或公开发表的材料中使用了 Infernux，可以按软件条目引用：

```bibtex
@software{chen2026infernux,
  author  = {Chen, Lizhe},
  title   = {Infernux},
  year    = {2026},
  version = {0.1.3},
  url     = {https://github.com/ChenlizheMe/Infernux},
  note    = {Open-source game engine with a C++17/Vulkan runtime and a Python production layer}
}
```

## 参与贡献

在当前阶段，Bug 报告、功能建议和工作流反馈都非常有帮助。提交 issue 时，建议包含引擎版本、环境信息、复现步骤，以及问题位于原生运行时、Python 层还是打包链路。

贡献与支持相关说明见：

- `CONTRIBUTING.md`
- `SECURITY.md`
- `SUPPORT.md`

## 许可证

Infernux 基于 MIT 协议发布，详见 `LICENSE`。
