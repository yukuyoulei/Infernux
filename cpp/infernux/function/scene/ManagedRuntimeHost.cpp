#include "ManagedRuntimeHost.h"

#include <algorithm>
#include <array>
#include <cctype>
#include <cstring>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <sstream>
#include <string_view>
#include <vector>

#include <core/config/InxPlatform.h>
#include <core/log/InxLog.h>
#include <function/scene/GameObject.h>
#include <function/scene/MeshRenderer.h>
#include <function/scene/PrimitiveMeshes.h>
#include <function/scene/SceneManager.h>
#include <function/scene/Transform.h>
#include <platform/filesystem/InxPath.h>
#include <pybind11/pybind11.h>

#ifdef INX_PLATFORM_WINDOWS
#include <Windows.h>
#endif

namespace infernux
{

namespace
{
namespace py = pybind11;

#ifdef INX_PLATFORM_WINDOWS
using char_t = wchar_t;
using hostfxr_handle = void *;
using load_assembly_and_get_function_pointer_fn =
    int(__cdecl *)(const char_t *assembly_path, const char_t *type_name, const char_t *method_name,
                   const char_t *delegate_type_name, void *reserved, void **delegate);
using hostfxr_initialize_for_runtime_config_fn =
    int(__cdecl *)(const char_t *runtime_config_path, const void *parameters, hostfxr_handle *host_context_handle);
using hostfxr_get_runtime_delegate_fn = int(__cdecl *)(const hostfxr_handle host_context_handle, int32_t type,
                                                       void **delegate);
using hostfxr_close_fn = int(__cdecl *)(const hostfxr_handle host_context_handle);

using create_component_fn = int(__cdecl *)(const char *type_name_utf8, int64_t *handle_out, char *error_utf8,
                                           int32_t error_utf8_capacity);
using destroy_component_fn = int(__cdecl *)(int64_t handle, char *error_utf8, int32_t error_utf8_capacity);
using update_component_context_fn =
    int(__cdecl *)(int64_t handle, int64_t game_object_id, int64_t component_id, int32_t enabled, int32_t execution_order,
                   const char *script_guid_utf8, char *error_utf8, int32_t error_utf8_capacity);
using invoke_lifecycle_fn = int(__cdecl *)(int64_t handle, int32_t event_id, float value, char *error_utf8,
                                           int32_t error_utf8_capacity);
using native_log_fn = void(__cdecl *)(int32_t level, const char *message_utf8);
using find_game_object_by_name_fn = int64_t(__cdecl *)(const char *name_utf8);
using create_game_object_fn = int64_t(__cdecl *)(const char *name_utf8);
using create_primitive_fn = int64_t(__cdecl *)(int32_t primitive_type, const char *name_utf8);
using destroy_game_object_fn = int32_t(__cdecl *)(int64_t game_object_id);
using instantiate_game_object_fn = int64_t(__cdecl *)(int64_t source_game_object_id, int64_t parent_game_object_id);
using get_game_object_world_position_fn =
    int32_t(__cdecl *)(int64_t game_object_id, float *x, float *y, float *z);
using set_game_object_world_position_fn = int32_t(__cdecl *)(int64_t game_object_id, float x, float y, float z);
using get_game_object_name_fn = int32_t(__cdecl *)(int64_t game_object_id, char *name_utf8, int32_t name_utf8_capacity);
using set_game_object_name_fn = int32_t(__cdecl *)(int64_t game_object_id, const char *name_utf8);
using set_game_object_active_fn = int32_t(__cdecl *)(int64_t game_object_id, int32_t active);
using get_game_object_active_self_fn = int32_t(__cdecl *)(int64_t game_object_id, int32_t *active_out);
using get_game_object_active_in_hierarchy_fn = int32_t(__cdecl *)(int64_t game_object_id, int32_t *active_out);
using get_game_object_tag_fn = int32_t(__cdecl *)(int64_t game_object_id, char *tag_utf8, int32_t tag_utf8_capacity);
using set_game_object_tag_fn = int32_t(__cdecl *)(int64_t game_object_id, const char *tag_utf8);
using compare_game_object_tag_fn = int32_t(__cdecl *)(int64_t game_object_id, const char *tag_utf8, int32_t *matches_out);
using get_game_object_layer_fn = int32_t(__cdecl *)(int64_t game_object_id, int32_t *layer_out);
using set_game_object_layer_fn = int32_t(__cdecl *)(int64_t game_object_id, int32_t layer);
using get_game_object_local_position_fn =
    int32_t(__cdecl *)(int64_t game_object_id, float *x, float *y, float *z);
using set_game_object_local_position_fn = int32_t(__cdecl *)(int64_t game_object_id, float x, float y, float z);
using translate_game_object_fn = int32_t(__cdecl *)(int64_t game_object_id, float x, float y, float z);
using get_game_object_local_scale_fn = int32_t(__cdecl *)(int64_t game_object_id, float *x, float *y, float *z);
using set_game_object_local_scale_fn = int32_t(__cdecl *)(int64_t game_object_id, float x, float y, float z);
using get_transform_parent_fn = int64_t(__cdecl *)(int64_t game_object_id);
using set_transform_parent_fn = int32_t(__cdecl *)(int64_t game_object_id, int64_t parent_game_object_id,
                                                   int32_t world_position_stays);
using get_transform_child_count_fn = int32_t(__cdecl *)(int64_t game_object_id, int32_t *count_out);
using get_transform_child_fn = int64_t(__cdecl *)(int64_t game_object_id, int32_t index);
using find_transform_child_fn = int64_t(__cdecl *)(int64_t game_object_id, const char *name_utf8);
using register_native_api_fn =
    int(__cdecl *)(native_log_fn log_fn, find_game_object_by_name_fn find_game_object_fn,
                   create_game_object_fn create_game_object_fn, create_primitive_fn create_primitive_fn,
                   destroy_game_object_fn destroy_game_object_fn,
                   instantiate_game_object_fn instantiate_game_object_fn,
                   get_game_object_world_position_fn get_world_position_fn,
                   set_game_object_world_position_fn set_world_position_fn, get_game_object_name_fn get_name_fn,
                   set_game_object_name_fn set_name_fn, set_game_object_active_fn set_active_fn,
                   get_game_object_active_self_fn get_active_self_fn,
                   get_game_object_active_in_hierarchy_fn get_active_in_hierarchy_fn, get_game_object_tag_fn get_tag_fn,
                   set_game_object_tag_fn set_tag_fn, compare_game_object_tag_fn compare_tag_fn,
                   get_game_object_layer_fn get_layer_fn, set_game_object_layer_fn set_layer_fn,
                   get_game_object_local_position_fn get_local_position_fn,
                   set_game_object_local_position_fn set_local_position_fn, translate_game_object_fn translate_fn,
                   get_game_object_local_scale_fn get_local_scale_fn,
                   set_game_object_local_scale_fn set_local_scale_fn, get_transform_parent_fn get_parent_fn,
                   set_transform_parent_fn set_parent_fn, get_transform_child_count_fn get_child_count_fn,
                   get_transform_child_fn get_child_fn, find_transform_child_fn find_child_fn, char *error_utf8,
                   int32_t error_utf8_capacity);

constexpr int32_t kHostFxrDelegateLoadAssemblyAndGetFunctionPointer = 5;
const wchar_t *const kUnmanagedCallersOnlyMethod = reinterpret_cast<const wchar_t *>(static_cast<intptr_t>(-1));

std::wstring ToWide(const std::string &utf8)
{
    return ToFsPath(utf8).wstring();
}

std::string TrimAscii(std::string value)
{
    auto notSpace = [](unsigned char ch) { return !std::isspace(ch); };
    value.erase(value.begin(), std::find_if(value.begin(), value.end(), notSpace));
    value.erase(std::find_if(value.rbegin(), value.rend(), notSpace).base(), value.end());
    return value;
}

std::string ReadUtf8Buffer(const std::array<char, 2048> &buffer)
{
    auto end = std::find(buffer.begin(), buffer.end(), '\0');
    return std::string(buffer.begin(), end);
}

std::string NarrowAscii(const wchar_t *value)
{
    if (!value) {
        return {};
    }
    std::string narrowed;
    for (wchar_t ch : std::wstring_view(value)) {
        narrowed.push_back(ch >= 0 && ch <= 0x7F ? static_cast<char>(ch) : '?');
    }
    return narrowed;
}

int32_t WriteUtf8ToBuffer(const std::string &value, char *destinationUtf8, int32_t destinationCapacity)
{
    if (!destinationUtf8 || destinationCapacity <= 0) {
        return 1;
    }

    const int32_t copyCount =
        std::min(static_cast<int32_t>(value.size()), static_cast<int32_t>(std::max(0, destinationCapacity - 1)));
    if (copyCount > 0) {
        std::memcpy(destinationUtf8, value.data(), static_cast<size_t>(copyCount));
    }
    destinationUtf8[copyCount] = '\0';
    return 0;
}

bool TrySetManagedArtifactsFromRoot(const std::filesystem::path &root, std::string &assemblyPathOut,
                                    std::string &runtimeConfigPathOut)
{
    const std::filesystem::path assembly = root / "Infernux.GameScripts.dll";
    const std::filesystem::path runtimeConfig = root / "Infernux.GameScripts.runtimeconfig.json";
    if (std::filesystem::is_regular_file(assembly) && std::filesystem::is_regular_file(runtimeConfig)) {
        assemblyPathOut = FromFsPath(assembly);
        runtimeConfigPathOut = FromFsPath(runtimeConfig);
        return true;
    }

    std::vector<std::filesystem::path> runtimeConfigs;
    if (!std::filesystem::is_directory(root)) {
        return false;
    }

    for (const auto &entry : std::filesystem::directory_iterator(root)) {
        if (!entry.is_regular_file()) {
            continue;
        }

        const std::filesystem::path candidate = entry.path();
        const std::string filename = candidate.filename().string();
        if (filename.size() <= std::strlen(".runtimeconfig.json") ||
            filename.substr(filename.size() - std::strlen(".runtimeconfig.json")) != ".runtimeconfig.json") {
            continue;
        }

        const std::string assemblyStem = filename.substr(0, filename.size() - std::strlen(".runtimeconfig.json"));
        if (std::filesystem::is_regular_file(root / (assemblyStem + ".dll"))) {
            runtimeConfigs.push_back(candidate);
        }
    }

    if (runtimeConfigs.empty()) {
        return false;
    }

    std::sort(runtimeConfigs.begin(), runtimeConfigs.end(),
              [](const std::filesystem::path &lhs, const std::filesystem::path &rhs) {
                  std::error_code leftEc;
                  std::error_code rightEc;
                  const auto leftTime = std::filesystem::last_write_time(lhs, leftEc);
                  const auto rightTime = std::filesystem::last_write_time(rhs, rightEc);
                  if (!leftEc && !rightEc && leftTime != rightTime) {
                      return leftTime > rightTime;
                  }
                  return lhs.filename().native() > rhs.filename().native();
              });

    const std::filesystem::path selectedRuntimeConfig = runtimeConfigs.front();
    const std::string runtimeFilename = selectedRuntimeConfig.filename().string();
    const std::string assemblyStem =
        runtimeFilename.substr(0, runtimeFilename.size() - std::strlen(".runtimeconfig.json"));
    const std::filesystem::path selectedAssembly = root / (assemblyStem + ".dll");
    assemblyPathOut = FromFsPath(selectedAssembly);
    runtimeConfigPathOut = FromFsPath(selectedRuntimeConfig);
    return true;
}

std::wstring BuildBridgeTypeName(const std::string &assemblyPath)
{
    const std::filesystem::path assemblyFsPath = ToFsPath(assemblyPath);
    const std::wstring assemblyName = assemblyFsPath.stem().wstring();
    return L"Infernux.Managed.ManagedComponentBridge, " + assemblyName;
}

bool InvokeManaged(create_component_fn fn, const std::string &typeName, int64_t &handle, std::string &error)
{
    std::array<char, 2048> errorBuffer{};
    handle = 0;
    const int rc = fn(typeName.c_str(), &handle, errorBuffer.data(), static_cast<int32_t>(errorBuffer.size()));
    if (rc == 0) {
        return true;
    }
    error = ReadUtf8Buffer(errorBuffer);
    if (error.empty()) {
        error = "Managed CreateComponent call failed.";
    }
    return false;
}

std::vector<int> ParseVersionParts(const std::wstring &version)
{
    std::vector<int> parts;
    std::wstringstream stream(version);
    std::wstring token;
    while (std::getline(stream, token, L'.')) {
        try {
            parts.push_back(std::stoi(token));
        } catch (...) {
            parts.push_back(0);
        }
    }
    return parts;
}

bool IsVersionGreater(const std::wstring &lhs, const std::wstring &rhs)
{
    const std::vector<int> leftParts = ParseVersionParts(lhs);
    const std::vector<int> rightParts = ParseVersionParts(rhs);
    const size_t count = std::max(leftParts.size(), rightParts.size());
    for (size_t i = 0; i < count; ++i) {
        const int left = i < leftParts.size() ? leftParts[i] : 0;
        const int right = i < rightParts.size() ? rightParts[i] : 0;
        if (left != right) {
            return left > right;
        }
    }
    return false;
}

template <typename Fn, typename... Args> bool InvokeManagedWithError(Fn fn, std::string &error, Args... args)
{
    std::array<char, 2048> errorBuffer{};
    const int rc = fn(args..., errorBuffer.data(), static_cast<int32_t>(errorBuffer.size()));
    if (rc == 0) {
        return true;
    }
    error = ReadUtf8Buffer(errorBuffer);
    if (error.empty()) {
        error = "Managed runtime call failed.";
    }
    return false;
}

void ForwardManagedLogToDebugConsole(int level, const char *messageUtf8)
{
    try {
        py::gil_scoped_acquire gil;
        py::module_ debugModule = py::module_::import("Infernux.debug");
        py::object debugClass = debugModule.attr("Debug");
        const char *message = messageUtf8 ? messageUtf8 : "";

        switch (level) {
        case LOG_WARN:
            debugClass.attr("log_warning")(message);
            break;
        case LOG_ERROR:
        case LOG_FATAL:
            debugClass.attr("log_error")(message);
            break;
        case LOG_DEBUG:
        case LOG_INFO:
        default:
            debugClass.attr("log")(message);
            break;
        }
    } catch (const std::exception &e) {
        INXLOG_WARN("[ManagedRuntimeHost] Failed to forward managed log to DebugConsole: ", e.what());
    } catch (...) {
        INXLOG_WARN("[ManagedRuntimeHost] Failed to forward managed log to DebugConsole.");
    }
}

void __cdecl NativeLog(int level, const char *messageUtf8)
{
    const char *message = messageUtf8 ? messageUtf8 : "";
    switch (level) {
    case LOG_DEBUG:
        INXLOG_DEBUG("[Managed] ", message);
        break;
    case LOG_WARN:
        INXLOG_WARN("[Managed] ", message);
        break;
    case LOG_ERROR:
    case LOG_FATAL:
        INXLOG_ERROR("[Managed] ", message);
        break;
    case LOG_INFO:
    default:
        INXLOG_INFO("[Managed] ", message);
        break;
    }

    ForwardManagedLogToDebugConsole(level, messageUtf8);
}

int64_t __cdecl FindGameObjectByName(const char *nameUtf8)
{
    if (!nameUtf8 || !*nameUtf8) {
        return 0;
    }

    Scene *scene = SceneManager::Instance().GetActiveScene();
    if (!scene) {
        return 0;
    }

    GameObject *gameObject = scene->Find(nameUtf8);
    return gameObject ? static_cast<int64_t>(gameObject->GetID()) : 0;
}

int64_t __cdecl CreateGameObject(const char *nameUtf8)
{
    Scene *scene = SceneManager::Instance().GetActiveScene();
    if (!scene) {
        return 0;
    }

    GameObject *gameObject = scene->CreateGameObject((nameUtf8 && *nameUtf8) ? nameUtf8 : "GameObject");
    return gameObject ? static_cast<int64_t>(gameObject->GetID()) : 0;
}

int64_t __cdecl CreatePrimitiveObject(int32_t primitiveType, const char *nameUtf8)
{
    Scene *scene = SceneManager::Instance().GetActiveScene();
    if (!scene) {
        return 0;
    }

    std::string objectName;
    std::vector<Vertex> vertices;
    std::vector<uint32_t> indices;
    const std::string requestedName = nameUtf8 ? nameUtf8 : "";

    switch (primitiveType) {
    case 0:
        objectName = requestedName.empty() ? "Cube" : requestedName;
        vertices =
            std::vector<Vertex>(PrimitiveMeshes::GetCubeVertices().begin(), PrimitiveMeshes::GetCubeVertices().end());
        indices =
            std::vector<uint32_t>(PrimitiveMeshes::GetCubeIndices().begin(), PrimitiveMeshes::GetCubeIndices().end());
        break;
    case 1:
        objectName = requestedName.empty() ? "Sphere" : requestedName;
        vertices = PrimitiveMeshes::GetSphereVertices();
        indices = PrimitiveMeshes::GetSphereIndices();
        break;
    case 2:
        objectName = requestedName.empty() ? "Capsule" : requestedName;
        vertices = PrimitiveMeshes::GetCapsuleVertices();
        indices = PrimitiveMeshes::GetCapsuleIndices();
        break;
    case 3:
        objectName = requestedName.empty() ? "Cylinder" : requestedName;
        vertices = PrimitiveMeshes::GetCylinderVertices();
        indices = PrimitiveMeshes::GetCylinderIndices();
        break;
    case 4:
        objectName = requestedName.empty() ? "Plane" : requestedName;
        vertices = PrimitiveMeshes::GetPlaneVertices();
        indices = PrimitiveMeshes::GetPlaneIndices();
        break;
    default:
        return 0;
    }

    GameObject *gameObject = scene->CreateGameObject(objectName);
    if (!gameObject) {
        return 0;
    }

    MeshRenderer *renderer = gameObject->AddComponent<MeshRenderer>();
    if (!renderer) {
        return static_cast<int64_t>(gameObject->GetID());
    }

    renderer->SetMesh(std::move(vertices), std::move(indices));
    renderer->SetInlineMeshName(objectName);
    return static_cast<int64_t>(gameObject->GetID());
}

int32_t __cdecl DestroyGameObject(int64_t gameObjectId)
{
    if (gameObjectId <= 0) {
        return 1;
    }

    Scene *scene = SceneManager::Instance().GetActiveScene();
    if (!scene) {
        return 1;
    }

    GameObject *gameObject = scene->FindByID(static_cast<uint64_t>(gameObjectId));
    if (!gameObject) {
        return 1;
    }

    scene->DestroyGameObject(gameObject);
    return 0;
}

int64_t __cdecl InstantiateGameObject(int64_t sourceGameObjectId, int64_t parentGameObjectId)
{
    if (sourceGameObjectId <= 0) {
        return 0;
    }

    Scene *scene = SceneManager::Instance().GetActiveScene();
    if (!scene) {
        return 0;
    }

    GameObject *source = scene->FindByID(static_cast<uint64_t>(sourceGameObjectId));
    if (!source) {
        return 0;
    }

    GameObject *parent = nullptr;
    if (parentGameObjectId > 0) {
        parent = scene->FindByID(static_cast<uint64_t>(parentGameObjectId));
        if (!parent) {
            return 0;
        }
    }

    GameObject *clone = scene->InstantiateGameObject(source, parent);
    return clone ? static_cast<int64_t>(clone->GetID()) : 0;
}

int32_t __cdecl GetGameObjectWorldPosition(int64_t gameObjectId, float *x, float *y, float *z)
{
    if (gameObjectId <= 0 || !x || !y || !z) {
        return 1;
    }

    Scene *scene = SceneManager::Instance().GetActiveScene();
    if (!scene) {
        return 1;
    }

    GameObject *gameObject = scene->FindByID(static_cast<uint64_t>(gameObjectId));
    if (!gameObject || !gameObject->GetTransform()) {
        return 1;
    }

    const glm::vec3 worldPosition = gameObject->GetTransform()->GetWorldPosition();
    *x = worldPosition.x;
    *y = worldPosition.y;
    *z = worldPosition.z;
    return 0;
}

int32_t __cdecl SetGameObjectWorldPosition(int64_t gameObjectId, float x, float y, float z)
{
    if (gameObjectId <= 0) {
        return 1;
    }

    Scene *scene = SceneManager::Instance().GetActiveScene();
    if (!scene) {
        return 1;
    }

    GameObject *gameObject = scene->FindByID(static_cast<uint64_t>(gameObjectId));
    if (!gameObject || !gameObject->GetTransform()) {
        return 1;
    }

    gameObject->GetTransform()->SetWorldPosition(x, y, z);
    return 0;
}

int32_t __cdecl GetGameObjectName(int64_t gameObjectId, char *nameUtf8, int32_t nameUtf8Capacity)
{
    if (gameObjectId <= 0 || !nameUtf8 || nameUtf8Capacity <= 0) {
        return 1;
    }

    Scene *scene = SceneManager::Instance().GetActiveScene();
    if (!scene) {
        return 1;
    }

    GameObject *gameObject = scene->FindByID(static_cast<uint64_t>(gameObjectId));
    if (!gameObject) {
        return 1;
    }

    return WriteUtf8ToBuffer(gameObject->GetName(), nameUtf8, nameUtf8Capacity);
}

int32_t __cdecl SetGameObjectName(int64_t gameObjectId, const char *nameUtf8)
{
    if (gameObjectId <= 0) {
        return 1;
    }

    Scene *scene = SceneManager::Instance().GetActiveScene();
    if (!scene) {
        return 1;
    }

    GameObject *gameObject = scene->FindByID(static_cast<uint64_t>(gameObjectId));
    if (!gameObject) {
        return 1;
    }

    gameObject->SetName(nameUtf8 ? nameUtf8 : "");
    return 0;
}

int32_t __cdecl SetGameObjectActive(int64_t gameObjectId, int32_t active)
{
    if (gameObjectId <= 0) {
        return 1;
    }

    Scene *scene = SceneManager::Instance().GetActiveScene();
    if (!scene) {
        return 1;
    }

    GameObject *gameObject = scene->FindByID(static_cast<uint64_t>(gameObjectId));
    if (!gameObject) {
        return 1;
    }

    gameObject->SetActive(active != 0);
    return 0;
}

int32_t __cdecl GetGameObjectActiveSelf(int64_t gameObjectId, int32_t *activeOut)
{
    if (gameObjectId <= 0 || !activeOut) {
        return 1;
    }

    Scene *scene = SceneManager::Instance().GetActiveScene();
    if (!scene) {
        return 1;
    }

    GameObject *gameObject = scene->FindByID(static_cast<uint64_t>(gameObjectId));
    if (!gameObject) {
        return 1;
    }

    *activeOut = gameObject->GetActiveSelf() ? 1 : 0;
    return 0;
}

int32_t __cdecl GetGameObjectActiveInHierarchy(int64_t gameObjectId, int32_t *activeOut)
{
    if (gameObjectId <= 0 || !activeOut) {
        return 1;
    }

    Scene *scene = SceneManager::Instance().GetActiveScene();
    if (!scene) {
        return 1;
    }

    GameObject *gameObject = scene->FindByID(static_cast<uint64_t>(gameObjectId));
    if (!gameObject) {
        return 1;
    }

    *activeOut = gameObject->IsActiveInHierarchy() ? 1 : 0;
    return 0;
}

int32_t __cdecl GetGameObjectTag(int64_t gameObjectId, char *tagUtf8, int32_t tagUtf8Capacity)
{
    if (gameObjectId <= 0 || !tagUtf8 || tagUtf8Capacity <= 0) {
        return 1;
    }

    Scene *scene = SceneManager::Instance().GetActiveScene();
    if (!scene) {
        return 1;
    }

    GameObject *gameObject = scene->FindByID(static_cast<uint64_t>(gameObjectId));
    if (!gameObject) {
        return 1;
    }

    return WriteUtf8ToBuffer(gameObject->GetTag(), tagUtf8, tagUtf8Capacity);
}

int32_t __cdecl SetGameObjectTag(int64_t gameObjectId, const char *tagUtf8)
{
    if (gameObjectId <= 0) {
        return 1;
    }

    Scene *scene = SceneManager::Instance().GetActiveScene();
    if (!scene) {
        return 1;
    }

    GameObject *gameObject = scene->FindByID(static_cast<uint64_t>(gameObjectId));
    if (!gameObject) {
        return 1;
    }

    gameObject->SetTag(tagUtf8 ? tagUtf8 : "");
    return 0;
}

int32_t __cdecl CompareGameObjectTag(int64_t gameObjectId, const char *tagUtf8, int32_t *matchesOut)
{
    if (gameObjectId <= 0 || !matchesOut) {
        return 1;
    }

    Scene *scene = SceneManager::Instance().GetActiveScene();
    if (!scene) {
        return 1;
    }

    GameObject *gameObject = scene->FindByID(static_cast<uint64_t>(gameObjectId));
    if (!gameObject) {
        return 1;
    }

    *matchesOut = gameObject->CompareTag(tagUtf8 ? tagUtf8 : "") ? 1 : 0;
    return 0;
}

int32_t __cdecl GetGameObjectLayer(int64_t gameObjectId, int32_t *layerOut)
{
    if (gameObjectId <= 0 || !layerOut) {
        return 1;
    }

    Scene *scene = SceneManager::Instance().GetActiveScene();
    if (!scene) {
        return 1;
    }

    GameObject *gameObject = scene->FindByID(static_cast<uint64_t>(gameObjectId));
    if (!gameObject) {
        return 1;
    }

    *layerOut = gameObject->GetLayer();
    return 0;
}

int32_t __cdecl SetGameObjectLayer(int64_t gameObjectId, int32_t layer)
{
    if (gameObjectId <= 0) {
        return 1;
    }

    Scene *scene = SceneManager::Instance().GetActiveScene();
    if (!scene) {
        return 1;
    }

    GameObject *gameObject = scene->FindByID(static_cast<uint64_t>(gameObjectId));
    if (!gameObject) {
        return 1;
    }

    gameObject->SetLayer(layer);
    return 0;
}

int32_t __cdecl GetGameObjectLocalPosition(int64_t gameObjectId, float *x, float *y, float *z)
{
    if (gameObjectId <= 0 || !x || !y || !z) {
        return 1;
    }

    Scene *scene = SceneManager::Instance().GetActiveScene();
    if (!scene) {
        return 1;
    }

    GameObject *gameObject = scene->FindByID(static_cast<uint64_t>(gameObjectId));
    if (!gameObject || !gameObject->GetTransform()) {
        return 1;
    }

    const glm::vec3 localPosition = gameObject->GetTransform()->GetLocalPosition();
    *x = localPosition.x;
    *y = localPosition.y;
    *z = localPosition.z;
    return 0;
}

int32_t __cdecl SetGameObjectLocalPosition(int64_t gameObjectId, float x, float y, float z)
{
    if (gameObjectId <= 0) {
        return 1;
    }

    Scene *scene = SceneManager::Instance().GetActiveScene();
    if (!scene) {
        return 1;
    }

    GameObject *gameObject = scene->FindByID(static_cast<uint64_t>(gameObjectId));
    if (!gameObject || !gameObject->GetTransform()) {
        return 1;
    }

    gameObject->GetTransform()->SetLocalPosition(x, y, z);
    return 0;
}

int32_t __cdecl TranslateGameObject(int64_t gameObjectId, float x, float y, float z)
{
    if (gameObjectId <= 0) {
        return 1;
    }

    Scene *scene = SceneManager::Instance().GetActiveScene();
    if (!scene) {
        return 1;
    }

    GameObject *gameObject = scene->FindByID(static_cast<uint64_t>(gameObjectId));
    if (!gameObject || !gameObject->GetTransform()) {
        return 1;
    }

    gameObject->GetTransform()->Translate(glm::vec3(x, y, z));
    return 0;
}

int32_t __cdecl GetGameObjectLocalScale(int64_t gameObjectId, float *x, float *y, float *z)
{
    if (gameObjectId <= 0 || !x || !y || !z) {
        return 1;
    }

    Scene *scene = SceneManager::Instance().GetActiveScene();
    if (!scene) {
        return 1;
    }

    GameObject *gameObject = scene->FindByID(static_cast<uint64_t>(gameObjectId));
    if (!gameObject || !gameObject->GetTransform()) {
        return 1;
    }

    const glm::vec3 localScale = gameObject->GetTransform()->GetLocalScale();
    *x = localScale.x;
    *y = localScale.y;
    *z = localScale.z;
    return 0;
}

int32_t __cdecl SetGameObjectLocalScale(int64_t gameObjectId, float x, float y, float z)
{
    if (gameObjectId <= 0) {
        return 1;
    }

    Scene *scene = SceneManager::Instance().GetActiveScene();
    if (!scene) {
        return 1;
    }

    GameObject *gameObject = scene->FindByID(static_cast<uint64_t>(gameObjectId));
    if (!gameObject || !gameObject->GetTransform()) {
        return 1;
    }

    gameObject->GetTransform()->SetLocalScale(x, y, z);
    return 0;
}

int64_t __cdecl GetTransformParent(int64_t gameObjectId)
{
    if (gameObjectId <= 0) {
        return 0;
    }

    Scene *scene = SceneManager::Instance().GetActiveScene();
    if (!scene) {
        return 0;
    }

    GameObject *gameObject = scene->FindByID(static_cast<uint64_t>(gameObjectId));
    if (!gameObject || !gameObject->GetTransform()) {
        return 0;
    }

    Transform *parent = gameObject->GetTransform()->GetParent();
    return parent && parent->GetGameObject() ? static_cast<int64_t>(parent->GetGameObject()->GetID()) : 0;
}

int32_t __cdecl SetTransformParent(int64_t gameObjectId, int64_t parentGameObjectId, int32_t worldPositionStays)
{
    if (gameObjectId <= 0) {
        return 1;
    }

    Scene *scene = SceneManager::Instance().GetActiveScene();
    if (!scene) {
        return 1;
    }

    GameObject *gameObject = scene->FindByID(static_cast<uint64_t>(gameObjectId));
    if (!gameObject || !gameObject->GetTransform()) {
        return 1;
    }

    Transform *parentTransform = nullptr;
    if (parentGameObjectId > 0) {
        GameObject *parentGameObject = scene->FindByID(static_cast<uint64_t>(parentGameObjectId));
        if (!parentGameObject || !parentGameObject->GetTransform()) {
            return 1;
        }
        parentTransform = parentGameObject->GetTransform();
    }

    gameObject->GetTransform()->SetParent(parentTransform, worldPositionStays != 0);
    return 0;
}

int32_t __cdecl GetTransformChildCount(int64_t gameObjectId, int32_t *countOut)
{
    if (gameObjectId <= 0 || !countOut) {
        return 1;
    }

    Scene *scene = SceneManager::Instance().GetActiveScene();
    if (!scene) {
        return 1;
    }

    GameObject *gameObject = scene->FindByID(static_cast<uint64_t>(gameObjectId));
    if (!gameObject || !gameObject->GetTransform()) {
        return 1;
    }

    *countOut = static_cast<int32_t>(gameObject->GetTransform()->GetChildCount());
    return 0;
}

int64_t __cdecl GetTransformChild(int64_t gameObjectId, int32_t index)
{
    if (gameObjectId <= 0 || index < 0) {
        return 0;
    }

    Scene *scene = SceneManager::Instance().GetActiveScene();
    if (!scene) {
        return 0;
    }

    GameObject *gameObject = scene->FindByID(static_cast<uint64_t>(gameObjectId));
    if (!gameObject || !gameObject->GetTransform()) {
        return 0;
    }

    Transform *child = gameObject->GetTransform()->GetChild(static_cast<size_t>(index));
    return child && child->GetGameObject() ? static_cast<int64_t>(child->GetGameObject()->GetID()) : 0;
}

int64_t __cdecl FindTransformChild(int64_t gameObjectId, const char *nameUtf8)
{
    if (gameObjectId <= 0 || !nameUtf8 || !*nameUtf8) {
        return 0;
    }

    Scene *scene = SceneManager::Instance().GetActiveScene();
    if (!scene) {
        return 0;
    }

    GameObject *gameObject = scene->FindByID(static_cast<uint64_t>(gameObjectId));
    if (!gameObject || !gameObject->GetTransform()) {
        return 0;
    }

    Transform *child = gameObject->GetTransform()->Find(nameUtf8);
    return child && child->GetGameObject() ? static_cast<int64_t>(child->GetGameObject()->GetID()) : 0;
}

std::filesystem::path FindBestHostFxr()
{
    std::vector<std::filesystem::path> roots;

    auto addRoot = [&roots](const wchar_t *value) {
        if (!value || !*value) {
            return;
        }
        std::filesystem::path root(value);
        if (std::find(roots.begin(), roots.end(), root) == roots.end()) {
            roots.push_back(root);
        }
    };

    wchar_t buffer[MAX_PATH] = {};
    if (GetEnvironmentVariableW(L"DOTNET_ROOT", buffer, MAX_PATH) > 0) {
        addRoot(buffer);
    }
    if (GetEnvironmentVariableW(L"DOTNET_ROOT(x86)", buffer, MAX_PATH) > 0) {
        addRoot(buffer);
    }

    wchar_t programFiles[MAX_PATH] = {};
    if (GetEnvironmentVariableW(L"ProgramFiles", programFiles, MAX_PATH) > 0) {
        addRoot((std::filesystem::path(programFiles) / "dotnet").c_str());
    }
    wchar_t programFilesX86[MAX_PATH] = {};
    if (GetEnvironmentVariableW(L"ProgramFiles(x86)", programFilesX86, MAX_PATH) > 0) {
        addRoot((std::filesystem::path(programFilesX86) / "dotnet").c_str());
    }

    std::filesystem::path bestPath;
    std::wstring bestVersion;

    for (const auto &root : roots) {
        std::filesystem::path fxrDir = root / "host" / "fxr";
        if (!std::filesystem::is_directory(fxrDir)) {
            continue;
        }
        for (const auto &entry : std::filesystem::directory_iterator(fxrDir)) {
            if (!entry.is_directory()) {
                continue;
            }
            const std::wstring version = entry.path().filename().wstring();
            const std::filesystem::path candidate = entry.path() / "hostfxr.dll";
            if (!std::filesystem::is_regular_file(candidate)) {
                continue;
            }
            if (bestPath.empty() || IsVersionGreater(version, bestVersion)) {
                bestPath = candidate;
                bestVersion = version;
            }
        }
    }

    return bestPath;
}
#endif
} // namespace

ManagedRuntimeHost &ManagedRuntimeHost::Instance()
{
    static ManagedRuntimeHost instance;
    return instance;
}

void ManagedRuntimeHost::ConfigureProject(const std::string &projectPath)
{
    const std::string normalized = FromFsPath(std::filesystem::absolute(ToFsPath(projectPath)));
    if (normalized == m_projectPath) {
        return;
    }

    if (m_runtimeInitialized) {
        SetError("Managed runtime is already initialized for this process. Restart Infernux to switch projects.");
        INXLOG_WARN("[ManagedRuntimeHost] ", m_lastError);
        return;
    }

    m_projectPath = normalized;
    m_assemblyPath.clear();
    m_runtimeConfigPath.clear();
    m_lastError.clear();
}

void ManagedRuntimeHost::Shutdown()
{
    m_lastError.clear();
}

bool ManagedRuntimeHost::IsSupportedPlatform() const
{
#ifdef INX_PLATFORM_WINDOWS
    return true;
#else
    return false;
#endif
}

bool ManagedRuntimeHost::IsConfigured() const
{
    return !m_projectPath.empty();
}

bool ManagedRuntimeHost::IsRuntimeAvailable()
{
    return EnsureInitialized();
}

bool ManagedRuntimeHost::ReloadScriptsIfChanged()
{
    if (!IsSupportedPlatform()) {
        SetError("Managed C# runtime hosting is currently supported only on Windows.");
        return false;
    }
    if (!IsConfigured()) {
        SetError("Managed runtime host is not configured with a project path.");
        return false;
    }

    std::string nextAssemblyPath;
    std::string nextRuntimeConfigPath;
    const std::string currentAssemblyPath = m_assemblyPath;
    const std::string currentRuntimeConfigPath = m_runtimeConfigPath;
    m_assemblyPath.clear();
    m_runtimeConfigPath.clear();
    const bool resolved = ResolveManagedArtifacts();
    nextAssemblyPath = m_assemblyPath;
    nextRuntimeConfigPath = m_runtimeConfigPath;
    m_assemblyPath = currentAssemblyPath;
    m_runtimeConfigPath = currentRuntimeConfigPath;
    if (!resolved) {
        return false;
    }

    if (!m_runtimeInitialized) {
        m_assemblyPath = nextAssemblyPath;
        m_runtimeConfigPath = nextRuntimeConfigPath;
        return EnsureInitialized();
    }

    if (nextAssemblyPath == m_assemblyPath && nextRuntimeConfigPath == m_runtimeConfigPath) {
        return true;
    }

    void *previousCreateComponentFn = m_createComponentFn;
    void *previousDestroyComponentFn = m_destroyComponentFn;
    void *previousUpdateContextFn = m_updateContextFn;
    void *previousInvokeLifecycleFn = m_invokeLifecycleFn;
    void *previousRegisterNativeApiFn = m_registerNativeApiFn;
    const std::string previousError = m_lastError;

    m_assemblyPath = nextAssemblyPath;
    m_runtimeConfigPath = nextRuntimeConfigPath;
    m_createComponentFn = nullptr;
    m_destroyComponentFn = nullptr;
    m_updateContextFn = nullptr;
    m_invokeLifecycleFn = nullptr;
    m_registerNativeApiFn = nullptr;
    m_lastError.clear();

    if (!LoadBridgeDelegates()) {
        m_assemblyPath = currentAssemblyPath;
        m_runtimeConfigPath = currentRuntimeConfigPath;
        m_createComponentFn = previousCreateComponentFn;
        m_destroyComponentFn = previousDestroyComponentFn;
        m_updateContextFn = previousUpdateContextFn;
        m_invokeLifecycleFn = previousInvokeLifecycleFn;
        m_registerNativeApiFn = previousRegisterNativeApiFn;
        if (m_lastError.empty()) {
            m_lastError = previousError;
        }
        return false;
    }

    m_lastError.clear();
    INXLOG_INFO("[ManagedRuntimeHost] Reloaded managed gameplay assembly: ", m_assemblyPath);
    return true;
}

const std::string &ManagedRuntimeHost::GetLastError() const
{
    return m_lastError;
}

bool ManagedRuntimeHost::CreateComponent(const std::string &typeName, int64_t &handle)
{
    if (!EnsureInitialized()) {
        handle = 0;
        return false;
    }

#ifdef INX_PLATFORM_WINDOWS
    std::string error;
    if (!InvokeManaged(reinterpret_cast<create_component_fn>(m_createComponentFn), typeName, handle, error)) {
        SetError(error);
        return false;
    }
    return true;
#else
    (void)typeName;
    handle = 0;
    return false;
#endif
}

bool ManagedRuntimeHost::DestroyComponent(int64_t handle)
{
    if (!EnsureInitialized()) {
        return false;
    }

#ifdef INX_PLATFORM_WINDOWS
    std::string error;
    if (!InvokeManagedWithError(reinterpret_cast<destroy_component_fn>(m_destroyComponentFn), error, handle)) {
        SetError(error);
        return false;
    }
    return true;
#else
    (void)handle;
    return false;
#endif
}

bool ManagedRuntimeHost::UpdateComponentContext(int64_t handle, uint64_t gameObjectId, uint64_t componentId, bool enabled,
                                                int executionOrder, const std::string &scriptGuid)
{
    if (!EnsureInitialized()) {
        return false;
    }

#ifdef INX_PLATFORM_WINDOWS
    std::string error;
    if (!InvokeManagedWithError(reinterpret_cast<update_component_context_fn>(m_updateContextFn), error, handle,
                                static_cast<int64_t>(gameObjectId), static_cast<int64_t>(componentId), enabled ? 1 : 0,
                                executionOrder, scriptGuid.c_str())) {
        SetError(error);
        return false;
    }
    return true;
#else
    (void)handle;
    (void)gameObjectId;
    (void)componentId;
    (void)enabled;
    (void)executionOrder;
    (void)scriptGuid;
    return false;
#endif
}

bool ManagedRuntimeHost::InvokeLifecycle(int64_t handle, ManagedLifecycleEvent eventId, float value)
{
    if (!EnsureInitialized()) {
        return false;
    }

#ifdef INX_PLATFORM_WINDOWS
    std::string error;
    if (!InvokeManagedWithError(reinterpret_cast<invoke_lifecycle_fn>(m_invokeLifecycleFn), error, handle,
                                static_cast<int32_t>(eventId), value)) {
        SetError(error);
        return false;
    }
    return true;
#else
    (void)handle;
    (void)eventId;
    (void)value;
    return false;
#endif
}

bool ManagedRuntimeHost::EnsureInitialized()
{
    if (m_runtimeInitialized) {
        return true;
    }

    if (!IsSupportedPlatform()) {
        SetError("Managed C# runtime hosting is currently supported only on Windows.");
        return false;
    }
    if (!IsConfigured()) {
        SetError("Managed runtime host is not configured with a project path.");
        return false;
    }
    if (!ResolveManagedArtifacts()) {
        return false;
    }
    if (!LoadHostFxrLibrary()) {
        return false;
    }
    if (!LoadBridgeDelegates()) {
        return false;
    }

    m_runtimeInitialized = true;
    m_lastError.clear();
    INXLOG_INFO("[ManagedRuntimeHost] Ready: ", m_assemblyPath);
    return true;
}

bool ManagedRuntimeHost::ResolveManagedArtifacts()
{
    if (!m_assemblyPath.empty() && !m_runtimeConfigPath.empty()) {
        return true;
    }

    const std::filesystem::path autoBuildPointer =
        ToFsPath(JoinPath({m_projectPath, "Scripts", "obj", "InfernuxAutoBuild", "current.txt"}));
    if (std::filesystem::is_regular_file(autoBuildPointer)) {
        std::ifstream stream(autoBuildPointer);
        std::string rootText;
        if (std::getline(stream, rootText)) {
            const std::filesystem::path root = ToFsPath(TrimAscii(rootText));
            if (TrySetManagedArtifactsFromRoot(root, m_assemblyPath, m_runtimeConfigPath)) {
                return true;
            }
        }
    }

    const std::vector<std::filesystem::path> candidateRoots = {
        ToFsPath(JoinPath({m_projectPath, "Data", "Managed"})),
        ToFsPath(JoinPath({m_projectPath, "Scripts", "bin", "Debug", "net8.0"})),
        ToFsPath(JoinPath({m_projectPath, "Scripts", "bin", "Release", "net8.0"})),
    };

    for (const auto &root : candidateRoots) {
        if (TrySetManagedArtifactsFromRoot(root, m_assemblyPath, m_runtimeConfigPath)) {
            return true;
        }
    }

    SetError("Failed to locate managed gameplay build output. Expected Infernux.GameScripts.dll and "
             "Infernux.GameScripts.runtimeconfig.json under Data/Managed or Scripts/bin/<Config>/net8.0.");
    return false;
}

bool ManagedRuntimeHost::LoadHostFxrLibrary()
{
#ifndef INX_PLATFORM_WINDOWS
    SetError("Managed runtime hosting is not implemented on this platform.");
    return false;
#else
    if (m_hostFxrLoaded) {
        return true;
    }

    const std::filesystem::path hostfxrPath = FindBestHostFxr();
    if (hostfxrPath.empty()) {
        SetError("hostfxr.dll was not found. Install the .NET 8 runtime or SDK.");
        return false;
    }

    HMODULE module = LoadLibraryW(hostfxrPath.c_str());
    if (module == nullptr) {
        SetError("Failed to load hostfxr.dll from " + FromFsPath(hostfxrPath));
        return false;
    }

    m_hostFxrModule = module;
    m_hostFxrLoaded = true;
    return true;
#endif
}

bool ManagedRuntimeHost::LoadBridgeDelegates()
{
#ifndef INX_PLATFORM_WINDOWS
    return false;
#else
    if (m_delegateLoadAttempted && !m_loadAssemblyAndGetFunctionPointer) {
        return false;
    }
    if (m_loadAssemblyAndGetFunctionPointer) {
        return BindBridgeDelegates();
    }

    m_delegateLoadAttempted = true;

    auto *initializeForRuntimeConfig = reinterpret_cast<hostfxr_initialize_for_runtime_config_fn>(
        GetProcAddress(static_cast<HMODULE>(m_hostFxrModule), "hostfxr_initialize_for_runtime_config"));
    auto *getRuntimeDelegate = reinterpret_cast<hostfxr_get_runtime_delegate_fn>(
        GetProcAddress(static_cast<HMODULE>(m_hostFxrModule), "hostfxr_get_runtime_delegate"));
    auto *closeRuntime = reinterpret_cast<hostfxr_close_fn>(GetProcAddress(static_cast<HMODULE>(m_hostFxrModule), "hostfxr_close"));

    if (!initializeForRuntimeConfig || !getRuntimeDelegate || !closeRuntime) {
        SetError("Failed to resolve required hostfxr exports.");
        return false;
    }

    hostfxr_handle context = nullptr;
    const std::wstring runtimeConfig = ToWide(m_runtimeConfigPath);
    int rc = initializeForRuntimeConfig(runtimeConfig.c_str(), nullptr, &context);
    if (rc != 0 || context == nullptr) {
        SetError("hostfxr_initialize_for_runtime_config failed (rc=" + std::to_string(rc) + ") for " +
                 m_runtimeConfigPath);
        return false;
    }

    void *loadAssemblyDelegate = nullptr;
    rc = getRuntimeDelegate(context, kHostFxrDelegateLoadAssemblyAndGetFunctionPointer, &loadAssemblyDelegate);
    closeRuntime(context);
    if (rc != 0 || loadAssemblyDelegate == nullptr) {
        SetError("hostfxr_get_runtime_delegate failed to load assembly delegate.");
        return false;
    }

    m_loadAssemblyAndGetFunctionPointer = loadAssemblyDelegate;
    return BindBridgeDelegates();
#endif
}

bool ManagedRuntimeHost::BindBridgeDelegates()
{
#ifndef INX_PLATFORM_WINDOWS
    return false;
#else
    if (!m_loadAssemblyAndGetFunctionPointer) {
        SetError("Managed runtime assembly delegate is not available.");
        return false;
    }

    auto *loadAssemblyAndGetFunctionPointer =
        reinterpret_cast<load_assembly_and_get_function_pointer_fn>(m_loadAssemblyAndGetFunctionPointer);

    const std::wstring assemblyPath = ToWide(m_assemblyPath);
    const std::wstring bridgeTypeName = BuildBridgeTypeName(m_assemblyPath);
    auto loadMethod = [&](const wchar_t *methodName, void **outFn) -> bool {
        const int methodRc = loadAssemblyAndGetFunctionPointer(assemblyPath.c_str(), bridgeTypeName.c_str(), methodName,
                                                               kUnmanagedCallersOnlyMethod, nullptr, outFn);
        if (methodRc != 0 || *outFn == nullptr) {
            SetError("Failed to bind managed bridge method '" + NarrowAscii(methodName) + "' (rc=" +
                     std::to_string(methodRc) + ") from " + m_assemblyPath);
            return false;
        }
        return true;
    };

    if (!loadMethod(L"CreateComponent", &m_createComponentFn) || !loadMethod(L"DestroyComponent", &m_destroyComponentFn) ||
        !loadMethod(L"UpdateComponentContext", &m_updateContextFn) || !loadMethod(L"InvokeLifecycle", &m_invokeLifecycleFn) ||
        !loadMethod(L"RegisterNativeApi", &m_registerNativeApiFn)) {
        return false;
    }

    std::string error;
    if (!InvokeManagedWithError(reinterpret_cast<register_native_api_fn>(m_registerNativeApiFn), error, &NativeLog,
                                &FindGameObjectByName, &CreateGameObject, &CreatePrimitiveObject, &DestroyGameObject,
                                &InstantiateGameObject, &GetGameObjectWorldPosition, &SetGameObjectWorldPosition,
                                &GetGameObjectName, &SetGameObjectName, &SetGameObjectActive,
                                &GetGameObjectActiveSelf, &GetGameObjectActiveInHierarchy, &GetGameObjectTag,
                                &SetGameObjectTag, &CompareGameObjectTag, &GetGameObjectLayer, &SetGameObjectLayer,
                                &GetGameObjectLocalPosition, &SetGameObjectLocalPosition, &TranslateGameObject,
                                &GetGameObjectLocalScale, &SetGameObjectLocalScale, &GetTransformParent,
                                &SetTransformParent, &GetTransformChildCount, &GetTransformChild,
                                &FindTransformChild)) {
        SetError(error.empty() ? "Managed bridge failed to register native API callbacks." : error);
        return false;
    }

    return true;
#endif
}

void ManagedRuntimeHost::SetError(const std::string &message)
{
    m_lastError = message;
    if (!message.empty()) {
        INXLOG_ERROR("[ManagedRuntimeHost] ", message);
    }
}

} // namespace infernux
