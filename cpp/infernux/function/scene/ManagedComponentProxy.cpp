#include "ManagedComponentProxy.h"

#include "GameObject.h"
#include "ManagedRuntimeHost.h"
#include <core/log/InxLog.h>
#include <nlohmann/json.hpp>

using json = nlohmann::json;

namespace infernux
{

ManagedComponentProxy::ManagedComponentProxy(std::string typeName, std::string scriptGuid)
    : m_typeName(std::move(typeName)), m_scriptGuid(std::move(scriptGuid))
{
}

ManagedComponentProxy::~ManagedComponentProxy()
{
    if (m_handle != 0) {
        ManagedRuntimeHost::Instance().DestroyComponent(m_handle);
        m_handle = 0;
    }
}

ManagedComponentProxy::ManagedComponentProxy(ManagedComponentProxy &&other) noexcept
    : Component(std::move(other)), m_handle(other.m_handle), m_typeName(std::move(other.m_typeName)),
      m_scriptGuid(std::move(other.m_scriptGuid))
{
    other.m_handle = 0;
}

ManagedComponentProxy &ManagedComponentProxy::operator=(ManagedComponentProxy &&other) noexcept
{
    if (this != &other) {
        if (m_handle != 0) {
            ManagedRuntimeHost::Instance().DestroyComponent(m_handle);
        }
        Component::operator=(std::move(other));
        m_handle = other.m_handle;
        m_typeName = std::move(other.m_typeName);
        m_scriptGuid = std::move(other.m_scriptGuid);
        other.m_handle = 0;
    }
    return *this;
}

void ManagedComponentProxy::Awake()
{
    InvokeLifecycle(ManagedLifecycleEvent::Awake);
}

void ManagedComponentProxy::OnEnable()
{
    InvokeLifecycle(ManagedLifecycleEvent::OnEnable);
}

void ManagedComponentProxy::Start()
{
    InvokeLifecycle(ManagedLifecycleEvent::Start);
}

void ManagedComponentProxy::Update(float deltaTime)
{
    InvokeLifecycle(ManagedLifecycleEvent::Update, deltaTime);
}

void ManagedComponentProxy::FixedUpdate(float fixedDeltaTime)
{
    InvokeLifecycle(ManagedLifecycleEvent::FixedUpdate, fixedDeltaTime);
}

void ManagedComponentProxy::LateUpdate(float deltaTime)
{
    InvokeLifecycle(ManagedLifecycleEvent::LateUpdate, deltaTime);
}

void ManagedComponentProxy::OnDisable()
{
    InvokeLifecycle(ManagedLifecycleEvent::OnDisable);
}

void ManagedComponentProxy::OnDestroy()
{
    InvokeLifecycle(ManagedLifecycleEvent::OnDestroy);
}

void ManagedComponentProxy::OnValidate()
{
    InvokeLifecycle(ManagedLifecycleEvent::OnValidate);
}

void ManagedComponentProxy::Reset()
{
    InvokeLifecycle(ManagedLifecycleEvent::Reset);
}

const char *ManagedComponentProxy::GetTypeName() const
{
    return m_typeName.c_str();
}

std::string ManagedComponentProxy::Serialize() const
{
    json j = json::parse(Component::Serialize());
    j["type"] = "ManagedComponentProxy";
    j["managed_type_name"] = m_typeName;
    j["script_guid"] = m_scriptGuid;
    j["script_language"] = "csharp";
    return j.dump(2);
}

bool ManagedComponentProxy::Deserialize(const std::string &jsonStr)
{
    try {
        json j = json::parse(jsonStr);
        Component::Deserialize(jsonStr);
        if (j.contains("managed_type_name")) {
            m_typeName = j["managed_type_name"].get<std::string>();
        } else if (j.contains("type_name")) {
            m_typeName = j["type_name"].get<std::string>();
        }
        if (j.contains("script_guid")) {
            m_scriptGuid = j["script_guid"].get<std::string>();
        }
        return true;
    } catch (const std::exception &e) {
        INXLOG_ERROR("[ManagedComponentProxy] Deserialize failed: ", e.what());
        return false;
    }
}

std::unique_ptr<Component> ManagedComponentProxy::Clone() const
{
    return nullptr;
}

bool ManagedComponentProxy::EnsureCreated()
{
    if (m_handle != 0) {
        return true;
    }
    if (m_typeName.empty()) {
        INXLOG_ERROR("[ManagedComponentProxy] Cannot create managed component with empty type name.");
        return false;
    }
    if (!ManagedRuntimeHost::Instance().CreateComponent(m_typeName, m_handle)) {
        return false;
    }
    return true;
}

bool ManagedComponentProxy::SyncManagedContext()
{
    if (!EnsureCreated()) {
        return false;
    }

    const uint64_t gameObjectId = m_gameObject ? m_gameObject->GetID() : 0;
    return ManagedRuntimeHost::Instance().UpdateComponentContext(m_handle, gameObjectId, GetComponentID(), IsEnabled(),
                                                                 GetExecutionOrder(), m_scriptGuid);
}

void ManagedComponentProxy::InvokeLifecycle(ManagedLifecycleEvent eventId, float value)
{
    if (!SyncManagedContext()) {
        const std::string &error = ManagedRuntimeHost::Instance().GetLastError();
        if (!error.empty()) {
            INXLOG_ERROR("[ManagedComponentProxy] Failed to sync managed context for '", m_typeName, "': ", error);
        }
        return;
    }

    if (!ManagedRuntimeHost::Instance().InvokeLifecycle(m_handle, eventId, value)) {
        const std::string &error = ManagedRuntimeHost::Instance().GetLastError();
        if (!error.empty()) {
            INXLOG_ERROR("[ManagedComponentProxy] Managed lifecycle failed for '", m_typeName, "': ", error);
        }
    }
}

} // namespace infernux
