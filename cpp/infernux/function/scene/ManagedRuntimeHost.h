#pragma once

#include <cstdint>
#include <string>

namespace infernux
{

enum class ManagedLifecycleEvent : int32_t
{
    Awake = 1,
    OnEnable = 2,
    Start = 3,
    Update = 4,
    FixedUpdate = 5,
    LateUpdate = 6,
    OnDisable = 7,
    OnDestroy = 8,
    OnValidate = 9,
    Reset = 10,
};

class ManagedRuntimeHost
{
  public:
    static ManagedRuntimeHost &Instance();

    void ConfigureProject(const std::string &projectPath);
    void Shutdown();

    [[nodiscard]] bool IsSupportedPlatform() const;
    [[nodiscard]] bool IsConfigured() const;
    [[nodiscard]] bool IsRuntimeAvailable();
    [[nodiscard]] bool ReloadScriptsIfChanged();
    [[nodiscard]] const std::string &GetLastError() const;

    bool CreateComponent(const std::string &typeName, int64_t &handle);
    bool DestroyComponent(int64_t handle);
    bool UpdateComponentContext(int64_t handle, uint64_t gameObjectId, uint64_t componentId, bool enabled,
                                int executionOrder, const std::string &scriptGuid);
    bool InvokeLifecycle(int64_t handle, ManagedLifecycleEvent eventId, float value = 0.0f);

  private:
    ManagedRuntimeHost() = default;
    ~ManagedRuntimeHost() = default;

    ManagedRuntimeHost(const ManagedRuntimeHost &) = delete;
    ManagedRuntimeHost &operator=(const ManagedRuntimeHost &) = delete;

    bool EnsureInitialized();
    bool ResolveManagedArtifacts();
    bool LoadHostFxrLibrary();
    bool LoadBridgeDelegates();
    bool BindBridgeDelegates();
    void SetError(const std::string &message);

    std::string m_projectPath;
    std::string m_assemblyPath;
    std::string m_runtimeConfigPath;
    std::string m_lastError;
    bool m_runtimeInitialized = false;
    bool m_hostFxrLoaded = false;
    bool m_delegateLoadAttempted = false;
    void *m_hostFxrModule = nullptr;
    void *m_loadAssemblyAndGetFunctionPointer = nullptr;
    void *m_createComponentFn = nullptr;
    void *m_destroyComponentFn = nullptr;
    void *m_updateContextFn = nullptr;
    void *m_invokeLifecycleFn = nullptr;
    void *m_registerNativeApiFn = nullptr;
};

} // namespace infernux
