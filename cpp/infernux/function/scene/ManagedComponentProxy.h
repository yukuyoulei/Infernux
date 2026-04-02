#pragma once

#include "Component.h"
#include <cstdint>
#include <string>

namespace infernux
{

enum class ManagedLifecycleEvent : int32_t;

class ManagedComponentProxy : public Component
{
  public:
    ManagedComponentProxy(std::string typeName, std::string scriptGuid = {});
    ~ManagedComponentProxy() override;

    ManagedComponentProxy(const ManagedComponentProxy &) = delete;
    ManagedComponentProxy &operator=(const ManagedComponentProxy &) = delete;

    ManagedComponentProxy(ManagedComponentProxy &&other) noexcept;
    ManagedComponentProxy &operator=(ManagedComponentProxy &&other) noexcept;

    void Awake() override;
    void OnEnable() override;
    void Start() override;
    void Update(float deltaTime) override;
    void FixedUpdate(float fixedDeltaTime) override;
    void LateUpdate(float deltaTime) override;
    void OnDisable() override;
    void OnDestroy() override;
    void OnValidate() override;
    void Reset() override;

    [[nodiscard]] const char *GetTypeName() const override;
    [[nodiscard]] bool WantsPhysicsCallbacks() const override
    {
        return false;
    }

    [[nodiscard]] std::string Serialize() const override;
    bool Deserialize(const std::string &jsonStr) override;
    [[nodiscard]] std::unique_ptr<Component> Clone() const override;

    [[nodiscard]] const std::string &GetManagedTypeName() const
    {
        return m_typeName;
    }

    [[nodiscard]] const std::string &GetScriptGuid() const
    {
        return m_scriptGuid;
    }

    void SetScriptGuid(const std::string &guid)
    {
        m_scriptGuid = guid;
    }

    [[nodiscard]] bool IsValid() const
    {
        return m_handle != 0;
    }

  private:
    bool EnsureCreated();
    bool SyncManagedContext();
    void InvokeLifecycle(ManagedLifecycleEvent eventId, float value = 0.0f);

    int64_t m_handle = 0;
    std::string m_typeName;
    std::string m_scriptGuid;
};

} // namespace infernux
