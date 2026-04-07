import os
import re


CSHARP_PROJECT_DIR = "Scripts"
CSHARP_PROJECT_FILE = "Infernux.GameScripts.csproj"
CSHARP_GENERATED_DIR = os.path.join(CSHARP_PROJECT_DIR, "Generated")
CSHARP_STUBS_FILE = os.path.join(CSHARP_GENERATED_DIR, "Infernux.RuntimeStubs.cs")
CSHARP_AUTOBUILD_ROOT = os.path.join(CSHARP_PROJECT_DIR, "obj", "InfernuxAutoBuild")
CSHARP_AUTOBUILD_POINTER = os.path.join(CSHARP_AUTOBUILD_ROOT, "current.txt")
DEFAULT_CSHARP_SCRIPT = os.path.join("Assets", "Scripts", "Main.cs")


def sanitize_csharp_identifier(name: str) -> str:
    cleaned = re.sub(r"[^0-9A-Za-z_]", "", name or "")
    if not cleaned:
        return "GameScript"
    if cleaned[0].isdigit():
        cleaned = f"Script{cleaned}"
    return cleaned


def infer_project_name(project_dir: str, project_name: str = "") -> str:
    explicit = (project_name or "").strip()
    if explicit:
        return explicit
    return os.path.basename(os.path.abspath(project_dir)) or "GameScript"


def _build_csproj_content() -> str:
    return """<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>enable</Nullable>
    <LangVersion>latest</LangVersion>
    <GenerateRuntimeConfigurationFiles>true</GenerateRuntimeConfigurationFiles>
    <EnableDefaultCompileItems>false</EnableDefaultCompileItems>
    <RootNamespace>InfernuxGame</RootNamespace>
    <AssemblyName>Infernux.GameScripts</AssemblyName>
  </PropertyGroup>

  <ItemGroup>
    <Compile Include="..\\Assets\\**\\*.cs" />
    <Compile Include="Generated\\**\\*.cs" />
  </ItemGroup>
</Project>
"""


def _build_stubs_content() -> str:
    return """using System;
using System.Collections.Generic;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Runtime.CompilerServices;
using System.Text;
using System.Threading;

namespace Infernux
{
    public enum PrimitiveType
    {
        Cube = 0,
        Sphere = 1,
        Capsule = 2,
        Cylinder = 3,
        Plane = 4,
    }

    public readonly struct Vector3
    {
        public float X { get; }
        public float Y { get; }
        public float Z { get; }

        public Vector3(float x, float y, float z)
        {
            X = x;
            Y = y;
            Z = z;
        }

        public override string ToString()
        {
            return $"({X}, {Y}, {Z})";
        }
    }

    public readonly struct Quaternion
    {
        public float X { get; }
        public float Y { get; }
        public float Z { get; }
        public float W { get; }

        public Quaternion(float x, float y, float z, float w)
        {
            X = x;
            Y = y;
            Z = z;
            W = w;
        }

        public static Quaternion identity => new(0f, 0f, 0f, 1f);

        public static Vector3 operator *(Quaternion rotation, Vector3 point)
        {
            float x2 = rotation.X + rotation.X;
            float y2 = rotation.Y + rotation.Y;
            float z2 = rotation.Z + rotation.Z;
            float xx2 = rotation.X * x2;
            float yy2 = rotation.Y * y2;
            float zz2 = rotation.Z * z2;
            float xy2 = rotation.X * y2;
            float xz2 = rotation.X * z2;
            float yz2 = rotation.Y * z2;
            float wx2 = rotation.W * x2;
            float wy2 = rotation.W * y2;
            float wz2 = rotation.W * z2;

            return new Vector3(
                (1f - (yy2 + zz2)) * point.X + (xy2 - wz2) * point.Y + (xz2 + wy2) * point.Z,
                (xy2 + wz2) * point.X + (1f - (xx2 + zz2)) * point.Y + (yz2 - wx2) * point.Z,
                (xz2 - wy2) * point.X + (yz2 + wx2) * point.Y + (1f - (xx2 + yy2)) * point.Z
            );
        }

        public override string ToString()
        {
            return $"({X}, {Y}, {Z}, {W})";
        }
    }

    public abstract class Object
    {
        public abstract string name { get; set; }
        public abstract long GetInstanceID();

        public static T? Instantiate<T>(T original) where T : Object
        {
            return Instantiate(original, null);
        }

        public static T? Instantiate<T>(T original, Transform? parent) where T : Object
        {
            ArgumentNullException.ThrowIfNull(original);
            return Managed.ManagedComponentBridge.InstantiateObject(original, parent);
        }

        public static void Destroy(Object? obj)
        {
            if (obj is null)
            {
                return;
            }

            switch (obj)
            {
                case GameObject gameObject:
                    GameObject.Destroy(gameObject);
                    return;
                case Transform:
                    throw new InvalidOperationException("Transform cannot be destroyed independently.");
                case Component component:
                    Managed.NativeApi.DestroyComponentById(component.GetInstanceID());
                    return;
                default:
                    throw new NotSupportedException($"Destroy does not support '{obj.GetType().FullName}'.");
            }
        }

        public override string ToString()
        {
            return name;
        }
    }

    public abstract class Component : Object
    {
        public abstract GameObject? gameObject { get; }
        public virtual Transform? transform => gameObject?.transform;
        public override string name
        {
            get => gameObject?.name ?? string.Empty;
            set
            {
                if (gameObject is GameObject owner)
                {
                    owner.name = value;
                }
            }
        }

        public bool CompareTag(string tag)
        {
            return gameObject?.CompareTag(tag) ?? false;
        }
    }

    public abstract class Behaviour : Component
    {
        public abstract bool enabled { get; set; }
        public bool isActiveAndEnabled => enabled && (gameObject?.activeInHierarchy ?? false);
    }

    public sealed class GameObject : Object
    {
        internal GameObject(long instanceId)
        {
            InstanceId = instanceId;
        }

        public long InstanceId { get; }
        public override string name
        {
            get => Managed.NativeApi.GetGameObjectName(InstanceId);
            set => Managed.NativeApi.SetGameObjectName(InstanceId, value);
        }

        public override long GetInstanceID()
        {
            return InstanceId;
        }

        public bool activeSelf => Managed.NativeApi.GetGameObjectActiveSelf(InstanceId);
        public bool activeInHierarchy => Managed.NativeApi.GetGameObjectActiveInHierarchy(InstanceId);
        public string tag
        {
            get => Managed.NativeApi.GetGameObjectTag(InstanceId);
            set => Managed.NativeApi.SetGameObjectTag(InstanceId, value);
        }

        public int layer
        {
            get => Managed.NativeApi.GetGameObjectLayer(InstanceId);
            set => Managed.NativeApi.SetGameObjectLayer(InstanceId, value);
        }

        public Transform transform => new(this);

        public static GameObject? Find(string name)
        {
            long instanceId = Managed.NativeApi.FindGameObjectByName(name);
            return instanceId != 0 ? new GameObject(instanceId) : null;
        }

        public static GameObject? Create(string? name = null)
        {
            long instanceId = Managed.NativeApi.CreateGameObject(name);
            return instanceId != 0 ? new GameObject(instanceId) : null;
        }

        public static GameObject? CreatePrimitive(PrimitiveType type, string? name = null)
        {
            long instanceId = Managed.NativeApi.CreatePrimitive(type, name);
            return instanceId != 0 ? new GameObject(instanceId) : null;
        }

        public static GameObject? Instantiate(GameObject original, Transform? parent = null)
        {
            ArgumentNullException.ThrowIfNull(original);
            long parentId = parent?.gameObject?.InstanceId ?? 0;
            long instanceId = Managed.NativeApi.InstantiateGameObject(original.InstanceId, parentId);
            return instanceId != 0 ? new GameObject(instanceId) : null;
        }

        public T? AddComponent<T>() where T : MonoBehaviour
        {
            long handle = Managed.NativeApi.AddManagedComponent(
                InstanceId,
                Managed.ManagedComponentBridge.GetManagedTypeName<T>());
            return Managed.ManagedComponentBridge.GetManagedComponent<T>(handle);
        }

        public Component? AddComponent(Type type)
        {
            ArgumentNullException.ThrowIfNull(type);
            return Managed.ManagedComponentBridge.AddGameObjectComponent(this, type);
        }

        public T? GetComponent<T>() where T : Component
        {
            return Managed.ManagedComponentBridge.GetGameObjectComponent<T>(this);
        }

        public Component? GetComponent(Type type)
        {
            ArgumentNullException.ThrowIfNull(type);
            return Managed.ManagedComponentBridge.GetGameObjectComponent(this, type);
        }

        public bool TryGetComponent<T>(out T? component) where T : Component
        {
            component = GetComponent<T>();
            return component is not null;
        }

        public bool TryGetComponent(Type type, out Component? component)
        {
            component = GetComponent(type);
            return component is not null;
        }

        public T? GetComponentInChildren<T>() where T : Component
        {
            return Managed.ManagedComponentBridge.GetGameObjectComponentInChildren<T>(this);
        }

        public Component? GetComponentInChildren(Type type)
        {
            ArgumentNullException.ThrowIfNull(type);
            return Managed.ManagedComponentBridge.GetGameObjectComponentInChildren(this, type);
        }

        public T? GetComponentInParent<T>() where T : Component
        {
            return Managed.ManagedComponentBridge.GetGameObjectComponentInParent<T>(this);
        }

        public Component? GetComponentInParent(Type type)
        {
            ArgumentNullException.ThrowIfNull(type);
            return Managed.ManagedComponentBridge.GetGameObjectComponentInParent(this, type);
        }

        public static void Destroy(GameObject? target)
        {
            if (target is null)
            {
                return;
            }

            Managed.NativeApi.DestroyGameObject(target.InstanceId);
        }

        public void SetActive(bool active)
        {
            Managed.NativeApi.SetGameObjectActive(InstanceId, active);
        }

        public void Destroy()
        {
            Managed.NativeApi.DestroyGameObject(InstanceId);
        }

        public bool CompareTag(string tag)
        {
            return Managed.NativeApi.CompareGameObjectTag(InstanceId, tag);
        }
    }

    public sealed class Transform : Component
    {
        private readonly GameObject _gameObject;
        private static readonly Vector3 ForwardAxis = new(0f, 0f, 1f);
        private static readonly Vector3 RightAxis = new(1f, 0f, 0f);
        private static readonly Vector3 UpAxis = new(0f, 1f, 0f);

        internal Transform(GameObject gameObject)
        {
            _gameObject = gameObject;
        }

        public override GameObject gameObject => _gameObject;
        public override Transform transform => this;

        public override long GetInstanceID()
        {
            return Managed.NativeApi.GetTransformComponentId(_gameObject.InstanceId);
        }

        public Vector3 position
        {
            get => Managed.NativeApi.GetWorldPosition(_gameObject.InstanceId);
            set => Managed.NativeApi.SetWorldPosition(_gameObject.InstanceId, value);
        }

        public Vector3 localPosition
        {
            get => Managed.NativeApi.GetLocalPosition(_gameObject.InstanceId);
            set => Managed.NativeApi.SetLocalPosition(_gameObject.InstanceId, value);
        }

        public Vector3 localScale
        {
            get => Managed.NativeApi.GetLocalScale(_gameObject.InstanceId);
            set => Managed.NativeApi.SetLocalScale(_gameObject.InstanceId, value);
        }

        public Quaternion rotation
        {
            get => Managed.NativeApi.GetWorldRotation(_gameObject.InstanceId);
            set => Managed.NativeApi.SetWorldRotation(_gameObject.InstanceId, value);
        }

        public Quaternion localRotation
        {
            get => Managed.NativeApi.GetLocalRotation(_gameObject.InstanceId);
            set => Managed.NativeApi.SetLocalRotation(_gameObject.InstanceId, value);
        }

        public Vector3 eulerAngles
        {
            get => Managed.NativeApi.GetWorldEulerAngles(_gameObject.InstanceId);
            set => Managed.NativeApi.SetWorldEulerAngles(_gameObject.InstanceId, value);
        }

        public Vector3 localEulerAngles
        {
            get => Managed.NativeApi.GetLocalEulerAngles(_gameObject.InstanceId);
            set => Managed.NativeApi.SetLocalEulerAngles(_gameObject.InstanceId, value);
        }

        public Transform? parent => Managed.NativeApi.GetParent(_gameObject.InstanceId);
        public int childCount => Managed.NativeApi.GetChildCount(_gameObject.InstanceId);
        public Vector3 lossyScale => Managed.NativeApi.GetWorldScale(_gameObject.InstanceId);
        public Transform root
        {
            get
            {
                Transform current = this;
                while (current.parent is Transform next)
                {
                    current = next;
                }

                return current;
            }
        }
        public Vector3 forward => rotation * ForwardAxis;
        public Vector3 right => rotation * RightAxis;
        public Vector3 up => rotation * UpAxis;
        public Vector3 localForward => localRotation * ForwardAxis;
        public Vector3 localRight => localRotation * RightAxis;
        public Vector3 localUp => localRotation * UpAxis;

        public void Translate(Vector3 delta)
        {
            Managed.NativeApi.Translate(_gameObject.InstanceId, delta);
        }

        public void TranslateLocal(Vector3 delta)
        {
            Managed.NativeApi.TranslateLocal(_gameObject.InstanceId, delta);
        }

        public void Rotate(Vector3 eulerAngles)
        {
            Managed.NativeApi.Rotate(_gameObject.InstanceId, eulerAngles);
        }

        public void Rotate(Vector3 axis, float angle)
        {
            Managed.NativeApi.Rotate(_gameObject.InstanceId, axis, angle);
        }

        public void RotateAround(Vector3 point, Vector3 axis, float angle)
        {
            Managed.NativeApi.RotateAround(_gameObject.InstanceId, point, axis, angle);
        }

        public void LookAt(Vector3 target)
        {
            LookAt(target, UpAxis);
        }

        public void LookAt(Vector3 target, Vector3 up)
        {
            Managed.NativeApi.LookAt(_gameObject.InstanceId, target, up);
        }

        public Vector3 TransformPoint(Vector3 point)
        {
            return Managed.NativeApi.TransformPoint(_gameObject.InstanceId, point);
        }

        public Vector3 InverseTransformPoint(Vector3 point)
        {
            return Managed.NativeApi.InverseTransformPoint(_gameObject.InstanceId, point);
        }

        public Vector3 TransformDirection(Vector3 direction)
        {
            return Managed.NativeApi.TransformDirection(_gameObject.InstanceId, direction);
        }

        public Vector3 InverseTransformDirection(Vector3 direction)
        {
            return Managed.NativeApi.InverseTransformDirection(_gameObject.InstanceId, direction);
        }

        public Vector3 TransformVector(Vector3 vector)
        {
            return Managed.NativeApi.TransformVector(_gameObject.InstanceId, vector);
        }

        public Vector3 InverseTransformVector(Vector3 vector)
        {
            return Managed.NativeApi.InverseTransformVector(_gameObject.InstanceId, vector);
        }

        public void SetParent(Transform? parent, bool worldPositionStays = true)
        {
            long parentId = parent?._gameObject.InstanceId ?? 0;
            Managed.NativeApi.SetParent(_gameObject.InstanceId, parentId, worldPositionStays);
        }

        public Transform? GetChild(int index)
        {
            return Managed.NativeApi.GetChild(_gameObject.InstanceId, index);
        }

        public Transform? Find(string name)
        {
            return Managed.NativeApi.FindChild(_gameObject.InstanceId, name);
        }

        public void DetachChildren()
        {
            Managed.NativeApi.DetachChildren(_gameObject.InstanceId);
        }

        public bool IsChildOf(Transform? parent)
        {
            if (parent is null)
            {
                return false;
            }

            Transform? current = this.parent;
            while (current is not null)
            {
                if (current._gameObject.InstanceId == parent._gameObject.InstanceId)
                {
                    return true;
                }

                current = current.parent;
            }

            return false;
        }

        public int GetSiblingIndex()
        {
            return Managed.NativeApi.GetSiblingIndex(_gameObject.InstanceId);
        }

        public void SetSiblingIndex(int index)
        {
            Managed.NativeApi.SetSiblingIndex(_gameObject.InstanceId, index);
        }

        public void SetAsFirstSibling()
        {
            SetSiblingIndex(0);
        }

        public void SetAsLastSibling()
        {
            SetSiblingIndex(int.MaxValue);
        }
    }

    public static class Debug
    {
        public static void Log(object? message)
        {
            Managed.NativeApi.Log(1, message);
        }

        public static void LogWarning(object? message)
        {
            Managed.NativeApi.Log(2, message);
        }

        public static void LogError(object? message)
        {
            Managed.NativeApi.Log(3, message);
        }
    }

    public abstract class MonoBehaviour : Behaviour
    {
        public long GameObjectId { get; private set; }
        public long ComponentId { get; private set; }
        public bool Enabled { get; private set; } = true;
        public int ExecutionOrder { get; private set; }
        public string ScriptGuid { get; private set; } = string.Empty;
        public override GameObject? gameObject => GameObjectId != 0 ? new GameObject(GameObjectId) : null;
        public override bool enabled
        {
            get => Enabled;
            set
            {
                if (ComponentId != 0)
                {
                    Managed.NativeApi.SetComponentEnabled(ComponentId, value);
                }

                Enabled = value;
            }
        }

        public override long GetInstanceID()
        {
            return ComponentId;
        }

        internal void __UpdateContext(long gameObjectId, long componentId, bool enabled, int executionOrder, string? scriptGuid)
        {
            GameObjectId = gameObjectId;
            ComponentId = componentId;
            Enabled = enabled;
            ExecutionOrder = executionOrder;
            ScriptGuid = scriptGuid ?? string.Empty;
        }

        public virtual void Awake()
        {
        }

        public virtual void OnEnable()
        {
        }

        public virtual void Start()
        {
        }

        public virtual void Update(float deltaTime)
        {
        }

        public virtual void FixedUpdate(float fixedDeltaTime)
        {
        }

        public virtual void LateUpdate(float deltaTime)
        {
        }

        public virtual void OnDisable()
        {
        }

        public virtual void OnDestroy()
        {
        }

        public virtual void OnValidate()
        {
        }

        public virtual void Reset()
        {
        }
    }

}

namespace Infernux.Managed
{
    internal static class NativeApi
    {
        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        private delegate void NativeLogDelegate(int level, IntPtr messageUtf8);

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        private delegate long FindGameObjectByNameDelegate(IntPtr nameUtf8);

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        private delegate long CreateGameObjectDelegate(IntPtr nameUtf8);

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        private delegate long CreatePrimitiveDelegate(int primitiveType, IntPtr nameUtf8);

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        private delegate int DestroyGameObjectDelegate(long gameObjectId);

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        private delegate long InstantiateGameObjectDelegate(long sourceGameObjectId, long parentGameObjectId);

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        private delegate long AddManagedComponentDelegate(long gameObjectId, IntPtr typeNameUtf8);

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        private delegate long GetManagedComponentDelegate(long gameObjectId, IntPtr typeNameUtf8);

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        private delegate long GetManagedComponentInChildrenDelegate(long gameObjectId, IntPtr typeNameUtf8);

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        private delegate long GetManagedComponentInParentDelegate(long gameObjectId, IntPtr typeNameUtf8);

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        private delegate long GetTransformComponentIdDelegate(long gameObjectId);

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        private delegate int SetComponentEnabledDelegate(long componentId, int enabled);

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        private delegate int DestroyComponentByIdDelegate(long componentId);

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        private delegate int GetWorldPositionDelegate(long gameObjectId, out float x, out float y, out float z);

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        private delegate int SetWorldPositionDelegate(long gameObjectId, float x, float y, float z);

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        private delegate int GetGameObjectNameDelegate(long gameObjectId, IntPtr nameUtf8, int nameUtf8Capacity);

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        private delegate int SetGameObjectNameDelegate(long gameObjectId, IntPtr nameUtf8);

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        private delegate int SetGameObjectActiveDelegate(long gameObjectId, int active);

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        private delegate int GetGameObjectActiveSelfDelegate(long gameObjectId, out int active);

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        private delegate int GetGameObjectActiveInHierarchyDelegate(long gameObjectId, out int active);

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        private delegate int GetGameObjectTagDelegate(long gameObjectId, IntPtr tagUtf8, int tagUtf8Capacity);

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        private delegate int SetGameObjectTagDelegate(long gameObjectId, IntPtr tagUtf8);

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        private delegate int CompareGameObjectTagDelegate(long gameObjectId, IntPtr tagUtf8, out int matches);

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        private delegate int GetGameObjectLayerDelegate(long gameObjectId, out int layer);

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        private delegate int SetGameObjectLayerDelegate(long gameObjectId, int layer);

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        private delegate int GetLocalPositionDelegate(long gameObjectId, out float x, out float y, out float z);

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        private delegate int SetLocalPositionDelegate(long gameObjectId, float x, float y, float z);

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        private delegate int GetWorldRotationDelegate(long gameObjectId, out float x, out float y, out float z, out float w);

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        private delegate int SetWorldRotationDelegate(long gameObjectId, float x, float y, float z, float w);

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        private delegate int GetLocalRotationDelegate(long gameObjectId, out float x, out float y, out float z, out float w);

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        private delegate int SetLocalRotationDelegate(long gameObjectId, float x, float y, float z, float w);

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        private delegate int GetWorldEulerAnglesDelegate(long gameObjectId, out float x, out float y, out float z);

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        private delegate int SetWorldEulerAnglesDelegate(long gameObjectId, float x, float y, float z);

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        private delegate int GetLocalEulerAnglesDelegate(long gameObjectId, out float x, out float y, out float z);

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        private delegate int SetLocalEulerAnglesDelegate(long gameObjectId, float x, float y, float z);

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        private delegate int TranslateDelegate(long gameObjectId, float x, float y, float z);

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        private delegate int TranslateLocalDelegate(long gameObjectId, float x, float y, float z);

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        private delegate int GetLocalScaleDelegate(long gameObjectId, out float x, out float y, out float z);

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        private delegate int SetLocalScaleDelegate(long gameObjectId, float x, float y, float z);

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        private delegate int GetWorldScaleDelegate(long gameObjectId, out float x, out float y, out float z);

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        private delegate int RotateEulerDelegate(long gameObjectId, float x, float y, float z);

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        private delegate int RotateAxisAngleDelegate(long gameObjectId, float axisX, float axisY, float axisZ, float angle);

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        private delegate int RotateAroundDelegate(
            long gameObjectId,
            float pointX,
            float pointY,
            float pointZ,
            float axisX,
            float axisY,
            float axisZ,
            float angle);

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        private delegate int LookAtDelegate(
            long gameObjectId,
            float targetX,
            float targetY,
            float targetZ,
            float upX,
            float upY,
            float upZ);

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        private delegate int TransformPointDelegate(
            long gameObjectId,
            float x,
            float y,
            float z,
            out float outX,
            out float outY,
            out float outZ);

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        private delegate int InverseTransformPointDelegate(
            long gameObjectId,
            float x,
            float y,
            float z,
            out float outX,
            out float outY,
            out float outZ);

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        private delegate int TransformDirectionDelegate(
            long gameObjectId,
            float x,
            float y,
            float z,
            out float outX,
            out float outY,
            out float outZ);

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        private delegate int InverseTransformDirectionDelegate(
            long gameObjectId,
            float x,
            float y,
            float z,
            out float outX,
            out float outY,
            out float outZ);

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        private delegate int TransformVectorDelegate(
            long gameObjectId,
            float x,
            float y,
            float z,
            out float outX,
            out float outY,
            out float outZ);

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        private delegate int InverseTransformVectorDelegate(
            long gameObjectId,
            float x,
            float y,
            float z,
            out float outX,
            out float outY,
            out float outZ);

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        private delegate long GetParentDelegate(long gameObjectId);

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        private delegate int SetParentDelegate(long gameObjectId, long parentGameObjectId, int worldPositionStays);

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        private delegate int GetChildCountDelegate(long gameObjectId, out int childCount);

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        private delegate long GetChildDelegate(long gameObjectId, int index);

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        private delegate long FindChildDelegate(long gameObjectId, IntPtr nameUtf8);

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        private delegate int GetSiblingIndexDelegate(long gameObjectId, out int siblingIndex);

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        private delegate int SetSiblingIndexDelegate(long gameObjectId, int siblingIndex);

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        private delegate int DetachChildrenDelegate(long gameObjectId);

        private static NativeLogDelegate? _log;
        private static FindGameObjectByNameDelegate? _findGameObjectByName;
        private static CreateGameObjectDelegate? _createGameObject;
        private static CreatePrimitiveDelegate? _createPrimitive;
        private static DestroyGameObjectDelegate? _destroyGameObject;
        private static InstantiateGameObjectDelegate? _instantiateGameObject;
        private static AddManagedComponentDelegate? _addManagedComponent;
        private static GetManagedComponentDelegate? _getManagedComponent;
        private static GetManagedComponentInChildrenDelegate? _getManagedComponentInChildren;
        private static GetManagedComponentInParentDelegate? _getManagedComponentInParent;
        private static GetTransformComponentIdDelegate? _getTransformComponentId;
        private static SetComponentEnabledDelegate? _setComponentEnabled;
        private static DestroyComponentByIdDelegate? _destroyComponentById;
        private static GetWorldPositionDelegate? _getWorldPosition;
        private static SetWorldPositionDelegate? _setWorldPosition;
        private static GetGameObjectNameDelegate? _getGameObjectName;
        private static SetGameObjectNameDelegate? _setGameObjectName;
        private static SetGameObjectActiveDelegate? _setGameObjectActive;
        private static GetGameObjectActiveSelfDelegate? _getGameObjectActiveSelf;
        private static GetGameObjectActiveInHierarchyDelegate? _getGameObjectActiveInHierarchy;
        private static GetGameObjectTagDelegate? _getGameObjectTag;
        private static SetGameObjectTagDelegate? _setGameObjectTag;
        private static CompareGameObjectTagDelegate? _compareGameObjectTag;
        private static GetGameObjectLayerDelegate? _getGameObjectLayer;
        private static SetGameObjectLayerDelegate? _setGameObjectLayer;
        private static GetLocalPositionDelegate? _getLocalPosition;
        private static SetLocalPositionDelegate? _setLocalPosition;
        private static GetWorldRotationDelegate? _getWorldRotation;
        private static SetWorldRotationDelegate? _setWorldRotation;
        private static GetLocalRotationDelegate? _getLocalRotation;
        private static SetLocalRotationDelegate? _setLocalRotation;
        private static GetWorldEulerAnglesDelegate? _getWorldEulerAngles;
        private static SetWorldEulerAnglesDelegate? _setWorldEulerAngles;
        private static GetLocalEulerAnglesDelegate? _getLocalEulerAngles;
        private static SetLocalEulerAnglesDelegate? _setLocalEulerAngles;
        private static TranslateDelegate? _translate;
        private static TranslateLocalDelegate? _translateLocal;
        private static GetLocalScaleDelegate? _getLocalScale;
        private static SetLocalScaleDelegate? _setLocalScale;
        private static GetWorldScaleDelegate? _getWorldScale;
        private static RotateEulerDelegate? _rotateEuler;
        private static RotateAxisAngleDelegate? _rotateAxisAngle;
        private static RotateAroundDelegate? _rotateAround;
        private static LookAtDelegate? _lookAt;
        private static TransformPointDelegate? _transformPoint;
        private static InverseTransformPointDelegate? _inverseTransformPoint;
        private static TransformDirectionDelegate? _transformDirection;
        private static InverseTransformDirectionDelegate? _inverseTransformDirection;
        private static TransformVectorDelegate? _transformVector;
        private static InverseTransformVectorDelegate? _inverseTransformVector;
        private static GetParentDelegate? _getParent;
        private static SetParentDelegate? _setParent;
        private static GetChildCountDelegate? _getChildCount;
        private static GetChildDelegate? _getChild;
        private static FindChildDelegate? _findChild;
        private static GetSiblingIndexDelegate? _getSiblingIndex;
        private static SetSiblingIndexDelegate? _setSiblingIndex;
        private static DetachChildrenDelegate? _detachChildren;

        public static void Register(
            IntPtr logFn,
            IntPtr findGameObjectFn,
            IntPtr createGameObjectFn,
            IntPtr createPrimitiveFn,
            IntPtr destroyGameObjectFn,
            IntPtr instantiateGameObjectFn,
            IntPtr addManagedComponentFn,
            IntPtr getManagedComponentFn,
            IntPtr getManagedComponentInChildrenFn,
            IntPtr getManagedComponentInParentFn,
            IntPtr getTransformComponentIdFn,
            IntPtr setComponentEnabledFn,
            IntPtr destroyComponentByIdFn,
            IntPtr getWorldPositionFn,
            IntPtr setWorldPositionFn,
            IntPtr getGameObjectNameFn,
            IntPtr setGameObjectNameFn,
            IntPtr setGameObjectActiveFn,
            IntPtr getGameObjectActiveSelfFn,
            IntPtr getGameObjectActiveInHierarchyFn,
            IntPtr getGameObjectTagFn,
            IntPtr setGameObjectTagFn,
            IntPtr compareGameObjectTagFn,
            IntPtr getGameObjectLayerFn,
            IntPtr setGameObjectLayerFn,
            IntPtr getLocalPositionFn,
            IntPtr setLocalPositionFn,
            IntPtr getWorldRotationFn,
            IntPtr setWorldRotationFn,
            IntPtr getLocalRotationFn,
            IntPtr setLocalRotationFn,
            IntPtr getWorldEulerAnglesFn,
            IntPtr setWorldEulerAnglesFn,
            IntPtr getLocalEulerAnglesFn,
            IntPtr setLocalEulerAnglesFn,
            IntPtr translateFn,
            IntPtr translateLocalFn,
            IntPtr getLocalScaleFn,
            IntPtr setLocalScaleFn,
            IntPtr getWorldScaleFn,
            IntPtr rotateEulerFn,
            IntPtr rotateAxisAngleFn,
            IntPtr rotateAroundFn,
            IntPtr lookAtFn,
            IntPtr transformPointFn,
            IntPtr inverseTransformPointFn,
            IntPtr transformDirectionFn,
            IntPtr inverseTransformDirectionFn,
            IntPtr transformVectorFn,
            IntPtr inverseTransformVectorFn,
            IntPtr getParentFn,
            IntPtr setParentFn,
            IntPtr getChildCountFn,
            IntPtr getChildFn,
            IntPtr findChildFn,
            IntPtr getSiblingIndexFn,
            IntPtr setSiblingIndexFn,
            IntPtr detachChildrenFn)
        {
            if (logFn == IntPtr.Zero || findGameObjectFn == IntPtr.Zero || createGameObjectFn == IntPtr.Zero ||
                createPrimitiveFn == IntPtr.Zero || destroyGameObjectFn == IntPtr.Zero ||
                instantiateGameObjectFn == IntPtr.Zero || addManagedComponentFn == IntPtr.Zero ||
                getManagedComponentFn == IntPtr.Zero || getManagedComponentInChildrenFn == IntPtr.Zero ||
                getManagedComponentInParentFn == IntPtr.Zero || getTransformComponentIdFn == IntPtr.Zero ||
                setComponentEnabledFn == IntPtr.Zero || destroyComponentByIdFn == IntPtr.Zero ||
                getWorldPositionFn == IntPtr.Zero ||
                setWorldPositionFn == IntPtr.Zero || getGameObjectNameFn == IntPtr.Zero ||
                setGameObjectNameFn == IntPtr.Zero || setGameObjectActiveFn == IntPtr.Zero ||
                getGameObjectActiveSelfFn == IntPtr.Zero || getGameObjectActiveInHierarchyFn == IntPtr.Zero ||
                getGameObjectTagFn == IntPtr.Zero || setGameObjectTagFn == IntPtr.Zero ||
                compareGameObjectTagFn == IntPtr.Zero || getGameObjectLayerFn == IntPtr.Zero ||
                setGameObjectLayerFn == IntPtr.Zero || getLocalPositionFn == IntPtr.Zero ||
                setLocalPositionFn == IntPtr.Zero || getWorldRotationFn == IntPtr.Zero ||
                setWorldRotationFn == IntPtr.Zero || getLocalRotationFn == IntPtr.Zero ||
                setLocalRotationFn == IntPtr.Zero || getWorldEulerAnglesFn == IntPtr.Zero ||
                setWorldEulerAnglesFn == IntPtr.Zero || getLocalEulerAnglesFn == IntPtr.Zero ||
                setLocalEulerAnglesFn == IntPtr.Zero || translateFn == IntPtr.Zero ||
                translateLocalFn == IntPtr.Zero || getLocalScaleFn == IntPtr.Zero || setLocalScaleFn == IntPtr.Zero ||
                getWorldScaleFn == IntPtr.Zero || rotateEulerFn == IntPtr.Zero || rotateAxisAngleFn == IntPtr.Zero ||
                rotateAroundFn == IntPtr.Zero || lookAtFn == IntPtr.Zero || transformPointFn == IntPtr.Zero ||
                inverseTransformPointFn == IntPtr.Zero || transformDirectionFn == IntPtr.Zero ||
                inverseTransformDirectionFn == IntPtr.Zero || transformVectorFn == IntPtr.Zero ||
                inverseTransformVectorFn == IntPtr.Zero ||
                getParentFn == IntPtr.Zero || setParentFn == IntPtr.Zero || getChildCountFn == IntPtr.Zero ||
                getChildFn == IntPtr.Zero || findChildFn == IntPtr.Zero || getSiblingIndexFn == IntPtr.Zero ||
                setSiblingIndexFn == IntPtr.Zero || detachChildrenFn == IntPtr.Zero)
            {
                throw new InvalidOperationException("Managed native API registration received a null callback pointer.");
            }

            _log = Marshal.GetDelegateForFunctionPointer<NativeLogDelegate>(logFn);
            _findGameObjectByName = Marshal.GetDelegateForFunctionPointer<FindGameObjectByNameDelegate>(findGameObjectFn);
            _createGameObject = Marshal.GetDelegateForFunctionPointer<CreateGameObjectDelegate>(createGameObjectFn);
            _createPrimitive = Marshal.GetDelegateForFunctionPointer<CreatePrimitiveDelegate>(createPrimitiveFn);
            _destroyGameObject = Marshal.GetDelegateForFunctionPointer<DestroyGameObjectDelegate>(destroyGameObjectFn);
            _instantiateGameObject =
                Marshal.GetDelegateForFunctionPointer<InstantiateGameObjectDelegate>(instantiateGameObjectFn);
            _addManagedComponent =
                Marshal.GetDelegateForFunctionPointer<AddManagedComponentDelegate>(addManagedComponentFn);
            _getManagedComponent =
                Marshal.GetDelegateForFunctionPointer<GetManagedComponentDelegate>(getManagedComponentFn);
            _getManagedComponentInChildren =
                Marshal.GetDelegateForFunctionPointer<GetManagedComponentInChildrenDelegate>(getManagedComponentInChildrenFn);
            _getManagedComponentInParent =
                Marshal.GetDelegateForFunctionPointer<GetManagedComponentInParentDelegate>(getManagedComponentInParentFn);
            _getTransformComponentId =
                Marshal.GetDelegateForFunctionPointer<GetTransformComponentIdDelegate>(getTransformComponentIdFn);
            _setComponentEnabled =
                Marshal.GetDelegateForFunctionPointer<SetComponentEnabledDelegate>(setComponentEnabledFn);
            _destroyComponentById =
                Marshal.GetDelegateForFunctionPointer<DestroyComponentByIdDelegate>(destroyComponentByIdFn);
            _getWorldPosition = Marshal.GetDelegateForFunctionPointer<GetWorldPositionDelegate>(getWorldPositionFn);
            _setWorldPosition = Marshal.GetDelegateForFunctionPointer<SetWorldPositionDelegate>(setWorldPositionFn);
            _getGameObjectName = Marshal.GetDelegateForFunctionPointer<GetGameObjectNameDelegate>(getGameObjectNameFn);
            _setGameObjectName = Marshal.GetDelegateForFunctionPointer<SetGameObjectNameDelegate>(setGameObjectNameFn);
            _setGameObjectActive = Marshal.GetDelegateForFunctionPointer<SetGameObjectActiveDelegate>(setGameObjectActiveFn);
            _getGameObjectActiveSelf =
                Marshal.GetDelegateForFunctionPointer<GetGameObjectActiveSelfDelegate>(getGameObjectActiveSelfFn);
            _getGameObjectActiveInHierarchy =
                Marshal.GetDelegateForFunctionPointer<GetGameObjectActiveInHierarchyDelegate>(getGameObjectActiveInHierarchyFn);
            _getGameObjectTag = Marshal.GetDelegateForFunctionPointer<GetGameObjectTagDelegate>(getGameObjectTagFn);
            _setGameObjectTag = Marshal.GetDelegateForFunctionPointer<SetGameObjectTagDelegate>(setGameObjectTagFn);
            _compareGameObjectTag =
                Marshal.GetDelegateForFunctionPointer<CompareGameObjectTagDelegate>(compareGameObjectTagFn);
            _getGameObjectLayer = Marshal.GetDelegateForFunctionPointer<GetGameObjectLayerDelegate>(getGameObjectLayerFn);
            _setGameObjectLayer = Marshal.GetDelegateForFunctionPointer<SetGameObjectLayerDelegate>(setGameObjectLayerFn);
            _getLocalPosition = Marshal.GetDelegateForFunctionPointer<GetLocalPositionDelegate>(getLocalPositionFn);
            _setLocalPosition = Marshal.GetDelegateForFunctionPointer<SetLocalPositionDelegate>(setLocalPositionFn);
            _getWorldRotation = Marshal.GetDelegateForFunctionPointer<GetWorldRotationDelegate>(getWorldRotationFn);
            _setWorldRotation = Marshal.GetDelegateForFunctionPointer<SetWorldRotationDelegate>(setWorldRotationFn);
            _getLocalRotation = Marshal.GetDelegateForFunctionPointer<GetLocalRotationDelegate>(getLocalRotationFn);
            _setLocalRotation = Marshal.GetDelegateForFunctionPointer<SetLocalRotationDelegate>(setLocalRotationFn);
            _getWorldEulerAngles =
                Marshal.GetDelegateForFunctionPointer<GetWorldEulerAnglesDelegate>(getWorldEulerAnglesFn);
            _setWorldEulerAngles =
                Marshal.GetDelegateForFunctionPointer<SetWorldEulerAnglesDelegate>(setWorldEulerAnglesFn);
            _getLocalEulerAngles =
                Marshal.GetDelegateForFunctionPointer<GetLocalEulerAnglesDelegate>(getLocalEulerAnglesFn);
            _setLocalEulerAngles =
                Marshal.GetDelegateForFunctionPointer<SetLocalEulerAnglesDelegate>(setLocalEulerAnglesFn);
            _translate = Marshal.GetDelegateForFunctionPointer<TranslateDelegate>(translateFn);
            _translateLocal = Marshal.GetDelegateForFunctionPointer<TranslateLocalDelegate>(translateLocalFn);
            _getLocalScale = Marshal.GetDelegateForFunctionPointer<GetLocalScaleDelegate>(getLocalScaleFn);
            _setLocalScale = Marshal.GetDelegateForFunctionPointer<SetLocalScaleDelegate>(setLocalScaleFn);
            _getWorldScale = Marshal.GetDelegateForFunctionPointer<GetWorldScaleDelegate>(getWorldScaleFn);
            _rotateEuler = Marshal.GetDelegateForFunctionPointer<RotateEulerDelegate>(rotateEulerFn);
            _rotateAxisAngle = Marshal.GetDelegateForFunctionPointer<RotateAxisAngleDelegate>(rotateAxisAngleFn);
            _rotateAround = Marshal.GetDelegateForFunctionPointer<RotateAroundDelegate>(rotateAroundFn);
            _lookAt = Marshal.GetDelegateForFunctionPointer<LookAtDelegate>(lookAtFn);
            _transformPoint = Marshal.GetDelegateForFunctionPointer<TransformPointDelegate>(transformPointFn);
            _inverseTransformPoint =
                Marshal.GetDelegateForFunctionPointer<InverseTransformPointDelegate>(inverseTransformPointFn);
            _transformDirection =
                Marshal.GetDelegateForFunctionPointer<TransformDirectionDelegate>(transformDirectionFn);
            _inverseTransformDirection =
                Marshal.GetDelegateForFunctionPointer<InverseTransformDirectionDelegate>(inverseTransformDirectionFn);
            _transformVector = Marshal.GetDelegateForFunctionPointer<TransformVectorDelegate>(transformVectorFn);
            _inverseTransformVector =
                Marshal.GetDelegateForFunctionPointer<InverseTransformVectorDelegate>(inverseTransformVectorFn);
            _getParent = Marshal.GetDelegateForFunctionPointer<GetParentDelegate>(getParentFn);
            _setParent = Marshal.GetDelegateForFunctionPointer<SetParentDelegate>(setParentFn);
            _getChildCount = Marshal.GetDelegateForFunctionPointer<GetChildCountDelegate>(getChildCountFn);
            _getChild = Marshal.GetDelegateForFunctionPointer<GetChildDelegate>(getChildFn);
            _findChild = Marshal.GetDelegateForFunctionPointer<FindChildDelegate>(findChildFn);
            _getSiblingIndex = Marshal.GetDelegateForFunctionPointer<GetSiblingIndexDelegate>(getSiblingIndexFn);
            _setSiblingIndex = Marshal.GetDelegateForFunctionPointer<SetSiblingIndexDelegate>(setSiblingIndexFn);
            _detachChildren = Marshal.GetDelegateForFunctionPointer<DetachChildrenDelegate>(detachChildrenFn);
        }

        public static void Log(int level, object? message)
        {
            NativeLogDelegate callback = _log ?? throw new InvalidOperationException("Native log API is not registered.");
            string text = message?.ToString() ?? "null";
            IntPtr messagePtr = IntPtr.Zero;
            try
            {
                messagePtr = Marshal.StringToCoTaskMemUTF8(text);
                callback(level, messagePtr);
            }
            finally
            {
                if (messagePtr != IntPtr.Zero)
                {
                    Marshal.FreeCoTaskMem(messagePtr);
                }
            }
        }

        public static long FindGameObjectByName(string name)
        {
            FindGameObjectByNameDelegate callback =
                _findGameObjectByName ?? throw new InvalidOperationException("Native GameObject.Find API is not registered.");
            IntPtr namePtr = IntPtr.Zero;
            try
            {
                namePtr = Marshal.StringToCoTaskMemUTF8(name ?? string.Empty);
                return callback(namePtr);
            }
            finally
            {
                if (namePtr != IntPtr.Zero)
                {
                    Marshal.FreeCoTaskMem(namePtr);
                }
            }
        }

        public static long CreatePrimitive(PrimitiveType type, string? name)
        {
            CreatePrimitiveDelegate callback =
                _createPrimitive ?? throw new InvalidOperationException("Native GameObject.CreatePrimitive API is not registered.");
            IntPtr namePtr = IntPtr.Zero;
            try
            {
                namePtr = Marshal.StringToCoTaskMemUTF8(name ?? string.Empty);
                return callback((int)type, namePtr);
            }
            finally
            {
                if (namePtr != IntPtr.Zero)
                {
                    Marshal.FreeCoTaskMem(namePtr);
                }
            }
        }

        public static long CreateGameObject(string? name)
        {
            CreateGameObjectDelegate callback =
                _createGameObject ?? throw new InvalidOperationException("Native GameObject.Create API is not registered.");
            IntPtr namePtr = IntPtr.Zero;
            try
            {
                namePtr = Marshal.StringToCoTaskMemUTF8(name ?? string.Empty);
                return callback(namePtr);
            }
            finally
            {
                if (namePtr != IntPtr.Zero)
                {
                    Marshal.FreeCoTaskMem(namePtr);
                }
            }
        }

        public static void DestroyGameObject(long gameObjectId)
        {
            DestroyGameObjectDelegate callback =
                _destroyGameObject ?? throw new InvalidOperationException("Native GameObject.Destroy API is not registered.");
            if (callback(gameObjectId) != 0)
            {
                throw new InvalidOperationException($"Failed to destroy GameObject {gameObjectId}.");
            }
        }

        public static long InstantiateGameObject(long sourceGameObjectId, long parentGameObjectId)
        {
            InstantiateGameObjectDelegate callback =
                _instantiateGameObject ??
                throw new InvalidOperationException("Native GameObject.Instantiate API is not registered.");
            return callback(sourceGameObjectId, parentGameObjectId);
        }

        public static long AddManagedComponent(long gameObjectId, string typeName)
        {
            AddManagedComponentDelegate callback =
                _addManagedComponent ?? throw new InvalidOperationException("Native GameObject.AddComponent is not registered.");
            IntPtr typeNamePtr = IntPtr.Zero;
            try
            {
                typeNamePtr = Marshal.StringToCoTaskMemUTF8(typeName ?? string.Empty);
                return callback(gameObjectId, typeNamePtr);
            }
            finally
            {
                if (typeNamePtr != IntPtr.Zero)
                {
                    Marshal.FreeCoTaskMem(typeNamePtr);
                }
            }
        }

        public static long GetManagedComponent(long gameObjectId, string typeName)
        {
            GetManagedComponentDelegate callback =
                _getManagedComponent ?? throw new InvalidOperationException("Native GameObject.GetComponent is not registered.");
            IntPtr typeNamePtr = IntPtr.Zero;
            try
            {
                typeNamePtr = Marshal.StringToCoTaskMemUTF8(typeName ?? string.Empty);
                return callback(gameObjectId, typeNamePtr);
            }
            finally
            {
                if (typeNamePtr != IntPtr.Zero)
                {
                    Marshal.FreeCoTaskMem(typeNamePtr);
                }
            }
        }

        public static long GetManagedComponentInChildren(long gameObjectId, string typeName)
        {
            GetManagedComponentInChildrenDelegate callback =
                _getManagedComponentInChildren ??
                throw new InvalidOperationException("Native GameObject.GetComponentInChildren is not registered.");
            IntPtr typeNamePtr = IntPtr.Zero;
            try
            {
                typeNamePtr = Marshal.StringToCoTaskMemUTF8(typeName ?? string.Empty);
                return callback(gameObjectId, typeNamePtr);
            }
            finally
            {
                if (typeNamePtr != IntPtr.Zero)
                {
                    Marshal.FreeCoTaskMem(typeNamePtr);
                }
            }
        }

        public static long GetManagedComponentInParent(long gameObjectId, string typeName)
        {
            GetManagedComponentInParentDelegate callback =
                _getManagedComponentInParent ??
                throw new InvalidOperationException("Native GameObject.GetComponentInParent is not registered.");
            IntPtr typeNamePtr = IntPtr.Zero;
            try
            {
                typeNamePtr = Marshal.StringToCoTaskMemUTF8(typeName ?? string.Empty);
                return callback(gameObjectId, typeNamePtr);
            }
            finally
            {
                if (typeNamePtr != IntPtr.Zero)
                {
                    Marshal.FreeCoTaskMem(typeNamePtr);
                }
            }
        }

        public static long GetTransformComponentId(long gameObjectId)
        {
            GetTransformComponentIdDelegate callback =
                _getTransformComponentId ?? throw new InvalidOperationException("Native Transform.GetInstanceID is not registered.");
            return callback(gameObjectId);
        }

        public static void SetComponentEnabled(long componentId, bool enabled)
        {
            SetComponentEnabledDelegate callback =
                _setComponentEnabled ?? throw new InvalidOperationException("Native Component.enabled is not registered.");
            if (callback(componentId, enabled ? 1 : 0) != 0)
            {
                throw new InvalidOperationException($"Failed to set enabled state for Component {componentId}.");
            }
        }

        public static void DestroyComponentById(long componentId)
        {
            DestroyComponentByIdDelegate callback =
                _destroyComponentById ?? throw new InvalidOperationException("Native Component.Destroy is not registered.");
            if (callback(componentId) != 0)
            {
                throw new InvalidOperationException($"Failed to destroy Component {componentId}.");
            }
        }

        public static Vector3 GetWorldPosition(long gameObjectId)
        {
            GetWorldPositionDelegate callback =
                _getWorldPosition ?? throw new InvalidOperationException("Native transform.position getter is not registered.");
            if (callback(gameObjectId, out float x, out float y, out float z) != 0)
            {
                throw new InvalidOperationException($"Failed to read world position for GameObject {gameObjectId}.");
            }

            return new Vector3(x, y, z);
        }

        public static void SetWorldPosition(long gameObjectId, Vector3 position)
        {
            SetWorldPositionDelegate callback =
                _setWorldPosition ?? throw new InvalidOperationException("Native transform.position setter is not registered.");
            if (callback(gameObjectId, position.X, position.Y, position.Z) != 0)
            {
                throw new InvalidOperationException($"Failed to write world position for GameObject {gameObjectId}.");
            }
        }

        public static string GetGameObjectName(long gameObjectId)
        {
            GetGameObjectNameDelegate callback =
                _getGameObjectName ?? throw new InvalidOperationException("Native GameObject.name getter is not registered.");
            IntPtr namePtr = IntPtr.Zero;
            try
            {
                const int bufferSize = 2048;
                namePtr = Marshal.AllocCoTaskMem(bufferSize);
                Marshal.WriteByte(namePtr, 0, 0);
                if (callback(gameObjectId, namePtr, bufferSize) != 0)
                {
                    throw new InvalidOperationException($"Failed to read GameObject name for {gameObjectId}.");
                }

                return Marshal.PtrToStringUTF8(namePtr) ?? string.Empty;
            }
            finally
            {
                if (namePtr != IntPtr.Zero)
                {
                    Marshal.FreeCoTaskMem(namePtr);
                }
            }
        }

        public static void SetGameObjectName(long gameObjectId, string? name)
        {
            SetGameObjectNameDelegate callback =
                _setGameObjectName ?? throw new InvalidOperationException("Native GameObject.name setter is not registered.");
            IntPtr namePtr = IntPtr.Zero;
            try
            {
                namePtr = Marshal.StringToCoTaskMemUTF8(name ?? string.Empty);
                if (callback(gameObjectId, namePtr) != 0)
                {
                    throw new InvalidOperationException($"Failed to set GameObject name for {gameObjectId}.");
                }
            }
            finally
            {
                if (namePtr != IntPtr.Zero)
                {
                    Marshal.FreeCoTaskMem(namePtr);
                }
            }
        }

        public static void SetGameObjectActive(long gameObjectId, bool active)
        {
            SetGameObjectActiveDelegate callback =
                _setGameObjectActive ?? throw new InvalidOperationException("Native GameObject.SetActive is not registered.");
            if (callback(gameObjectId, active ? 1 : 0) != 0)
            {
                throw new InvalidOperationException($"Failed to set active state for GameObject {gameObjectId}.");
            }
        }

        public static bool GetGameObjectActiveSelf(long gameObjectId)
        {
            GetGameObjectActiveSelfDelegate callback =
                _getGameObjectActiveSelf ?? throw new InvalidOperationException("Native GameObject.activeSelf is not registered.");
            if (callback(gameObjectId, out int active) != 0)
            {
                throw new InvalidOperationException($"Failed to read activeSelf for GameObject {gameObjectId}.");
            }

            return active != 0;
        }

        public static bool GetGameObjectActiveInHierarchy(long gameObjectId)
        {
            GetGameObjectActiveInHierarchyDelegate callback =
                _getGameObjectActiveInHierarchy ??
                throw new InvalidOperationException("Native GameObject.activeInHierarchy is not registered.");
            if (callback(gameObjectId, out int active) != 0)
            {
                throw new InvalidOperationException($"Failed to read activeInHierarchy for GameObject {gameObjectId}.");
            }

            return active != 0;
        }

        public static string GetGameObjectTag(long gameObjectId)
        {
            GetGameObjectTagDelegate callback =
                _getGameObjectTag ?? throw new InvalidOperationException("Native GameObject.tag getter is not registered.");
            IntPtr tagPtr = IntPtr.Zero;
            try
            {
                const int bufferSize = 2048;
                tagPtr = Marshal.AllocCoTaskMem(bufferSize);
                Marshal.WriteByte(tagPtr, 0, 0);
                if (callback(gameObjectId, tagPtr, bufferSize) != 0)
                {
                    throw new InvalidOperationException($"Failed to read GameObject tag for {gameObjectId}.");
                }

                return Marshal.PtrToStringUTF8(tagPtr) ?? string.Empty;
            }
            finally
            {
                if (tagPtr != IntPtr.Zero)
                {
                    Marshal.FreeCoTaskMem(tagPtr);
                }
            }
        }

        public static void SetGameObjectTag(long gameObjectId, string? tag)
        {
            SetGameObjectTagDelegate callback =
                _setGameObjectTag ?? throw new InvalidOperationException("Native GameObject.tag setter is not registered.");
            IntPtr tagPtr = IntPtr.Zero;
            try
            {
                tagPtr = Marshal.StringToCoTaskMemUTF8(tag ?? string.Empty);
                if (callback(gameObjectId, tagPtr) != 0)
                {
                    throw new InvalidOperationException($"Failed to set GameObject tag for {gameObjectId}.");
                }
            }
            finally
            {
                if (tagPtr != IntPtr.Zero)
                {
                    Marshal.FreeCoTaskMem(tagPtr);
                }
            }
        }

        public static bool CompareGameObjectTag(long gameObjectId, string? tag)
        {
            CompareGameObjectTagDelegate callback =
                _compareGameObjectTag ??
                throw new InvalidOperationException("Native GameObject.CompareTag is not registered.");
            IntPtr tagPtr = IntPtr.Zero;
            try
            {
                tagPtr = Marshal.StringToCoTaskMemUTF8(tag ?? string.Empty);
                if (callback(gameObjectId, tagPtr, out int matches) != 0)
                {
                    throw new InvalidOperationException($"Failed to compare GameObject tag for {gameObjectId}.");
                }

                return matches != 0;
            }
            finally
            {
                if (tagPtr != IntPtr.Zero)
                {
                    Marshal.FreeCoTaskMem(tagPtr);
                }
            }
        }

        public static int GetGameObjectLayer(long gameObjectId)
        {
            GetGameObjectLayerDelegate callback =
                _getGameObjectLayer ?? throw new InvalidOperationException("Native GameObject.layer getter is not registered.");
            if (callback(gameObjectId, out int layer) != 0)
            {
                throw new InvalidOperationException($"Failed to read GameObject layer for {gameObjectId}.");
            }

            return layer;
        }

        public static void SetGameObjectLayer(long gameObjectId, int layer)
        {
            SetGameObjectLayerDelegate callback =
                _setGameObjectLayer ?? throw new InvalidOperationException("Native GameObject.layer setter is not registered.");
            if (callback(gameObjectId, layer) != 0)
            {
                throw new InvalidOperationException($"Failed to set GameObject layer for {gameObjectId}.");
            }
        }

        public static Vector3 GetLocalPosition(long gameObjectId)
        {
            GetLocalPositionDelegate callback =
                _getLocalPosition ?? throw new InvalidOperationException("Native transform.localPosition getter is not registered.");
            if (callback(gameObjectId, out float x, out float y, out float z) != 0)
            {
                throw new InvalidOperationException($"Failed to read local position for GameObject {gameObjectId}.");
            }

            return new Vector3(x, y, z);
        }

        public static void SetLocalPosition(long gameObjectId, Vector3 position)
        {
            SetLocalPositionDelegate callback =
                _setLocalPosition ?? throw new InvalidOperationException("Native transform.localPosition setter is not registered.");
            if (callback(gameObjectId, position.X, position.Y, position.Z) != 0)
            {
                throw new InvalidOperationException($"Failed to write local position for GameObject {gameObjectId}.");
            }
        }

        public static Quaternion GetWorldRotation(long gameObjectId)
        {
            GetWorldRotationDelegate callback =
                _getWorldRotation ?? throw new InvalidOperationException("Native transform.rotation getter is not registered.");
            if (callback(gameObjectId, out float x, out float y, out float z, out float w) != 0)
            {
                throw new InvalidOperationException($"Failed to read world rotation for GameObject {gameObjectId}.");
            }

            return new Quaternion(x, y, z, w);
        }

        public static void SetWorldRotation(long gameObjectId, Quaternion rotation)
        {
            SetWorldRotationDelegate callback =
                _setWorldRotation ?? throw new InvalidOperationException("Native transform.rotation setter is not registered.");
            if (callback(gameObjectId, rotation.X, rotation.Y, rotation.Z, rotation.W) != 0)
            {
                throw new InvalidOperationException($"Failed to write world rotation for GameObject {gameObjectId}.");
            }
        }

        public static Quaternion GetLocalRotation(long gameObjectId)
        {
            GetLocalRotationDelegate callback =
                _getLocalRotation ?? throw new InvalidOperationException("Native transform.localRotation getter is not registered.");
            if (callback(gameObjectId, out float x, out float y, out float z, out float w) != 0)
            {
                throw new InvalidOperationException($"Failed to read local rotation for GameObject {gameObjectId}.");
            }

            return new Quaternion(x, y, z, w);
        }

        public static void SetLocalRotation(long gameObjectId, Quaternion rotation)
        {
            SetLocalRotationDelegate callback =
                _setLocalRotation ?? throw new InvalidOperationException("Native transform.localRotation setter is not registered.");
            if (callback(gameObjectId, rotation.X, rotation.Y, rotation.Z, rotation.W) != 0)
            {
                throw new InvalidOperationException($"Failed to write local rotation for GameObject {gameObjectId}.");
            }
        }

        public static Vector3 GetWorldEulerAngles(long gameObjectId)
        {
            GetWorldEulerAnglesDelegate callback =
                _getWorldEulerAngles ?? throw new InvalidOperationException("Native transform.eulerAngles getter is not registered.");
            if (callback(gameObjectId, out float x, out float y, out float z) != 0)
            {
                throw new InvalidOperationException($"Failed to read world euler angles for GameObject {gameObjectId}.");
            }

            return new Vector3(x, y, z);
        }

        public static void SetWorldEulerAngles(long gameObjectId, Vector3 eulerAngles)
        {
            SetWorldEulerAnglesDelegate callback =
                _setWorldEulerAngles ?? throw new InvalidOperationException("Native transform.eulerAngles setter is not registered.");
            if (callback(gameObjectId, eulerAngles.X, eulerAngles.Y, eulerAngles.Z) != 0)
            {
                throw new InvalidOperationException($"Failed to write world euler angles for GameObject {gameObjectId}.");
            }
        }

        public static Vector3 GetLocalEulerAngles(long gameObjectId)
        {
            GetLocalEulerAnglesDelegate callback =
                _getLocalEulerAngles ?? throw new InvalidOperationException("Native transform.localEulerAngles getter is not registered.");
            if (callback(gameObjectId, out float x, out float y, out float z) != 0)
            {
                throw new InvalidOperationException($"Failed to read local euler angles for GameObject {gameObjectId}.");
            }

            return new Vector3(x, y, z);
        }

        public static void SetLocalEulerAngles(long gameObjectId, Vector3 eulerAngles)
        {
            SetLocalEulerAnglesDelegate callback =
                _setLocalEulerAngles ?? throw new InvalidOperationException("Native transform.localEulerAngles setter is not registered.");
            if (callback(gameObjectId, eulerAngles.X, eulerAngles.Y, eulerAngles.Z) != 0)
            {
                throw new InvalidOperationException($"Failed to write local euler angles for GameObject {gameObjectId}.");
            }
        }

        public static void Translate(long gameObjectId, Vector3 delta)
        {
            TranslateDelegate callback =
                _translate ?? throw new InvalidOperationException("Native transform.Translate is not registered.");
            if (callback(gameObjectId, delta.X, delta.Y, delta.Z) != 0)
            {
                throw new InvalidOperationException($"Failed to translate GameObject {gameObjectId}.");
            }
        }

        public static void TranslateLocal(long gameObjectId, Vector3 delta)
        {
            TranslateLocalDelegate callback =
                _translateLocal ?? throw new InvalidOperationException("Native transform.TranslateLocal is not registered.");
            if (callback(gameObjectId, delta.X, delta.Y, delta.Z) != 0)
            {
                throw new InvalidOperationException($"Failed to local-translate GameObject {gameObjectId}.");
            }
        }

        public static Vector3 GetLocalScale(long gameObjectId)
        {
            GetLocalScaleDelegate callback =
                _getLocalScale ?? throw new InvalidOperationException("Native transform.localScale getter is not registered.");
            if (callback(gameObjectId, out float x, out float y, out float z) != 0)
            {
                throw new InvalidOperationException($"Failed to read local scale for GameObject {gameObjectId}.");
            }

            return new Vector3(x, y, z);
        }

        public static void SetLocalScale(long gameObjectId, Vector3 scale)
        {
            SetLocalScaleDelegate callback =
                _setLocalScale ?? throw new InvalidOperationException("Native transform.localScale setter is not registered.");
            if (callback(gameObjectId, scale.X, scale.Y, scale.Z) != 0)
            {
                throw new InvalidOperationException($"Failed to write local scale for GameObject {gameObjectId}.");
            }
        }

        public static Vector3 GetWorldScale(long gameObjectId)
        {
            GetWorldScaleDelegate callback =
                _getWorldScale ?? throw new InvalidOperationException("Native transform.lossyScale getter is not registered.");
            if (callback(gameObjectId, out float x, out float y, out float z) != 0)
            {
                throw new InvalidOperationException($"Failed to read world scale for GameObject {gameObjectId}.");
            }

            return new Vector3(x, y, z);
        }

        public static void Rotate(long gameObjectId, Vector3 eulerAngles)
        {
            RotateEulerDelegate callback =
                _rotateEuler ?? throw new InvalidOperationException("Native transform.Rotate(euler) is not registered.");
            if (callback(gameObjectId, eulerAngles.X, eulerAngles.Y, eulerAngles.Z) != 0)
            {
                throw new InvalidOperationException($"Failed to rotate GameObject {gameObjectId} by euler angles.");
            }
        }

        public static void Rotate(long gameObjectId, Vector3 axis, float angle)
        {
            RotateAxisAngleDelegate callback =
                _rotateAxisAngle ?? throw new InvalidOperationException("Native transform.Rotate(axis, angle) is not registered.");
            if (callback(gameObjectId, axis.X, axis.Y, axis.Z, angle) != 0)
            {
                throw new InvalidOperationException($"Failed to rotate GameObject {gameObjectId} around an axis.");
            }
        }

        public static void RotateAround(long gameObjectId, Vector3 point, Vector3 axis, float angle)
        {
            RotateAroundDelegate callback =
                _rotateAround ?? throw new InvalidOperationException("Native transform.RotateAround is not registered.");
            if (callback(gameObjectId, point.X, point.Y, point.Z, axis.X, axis.Y, axis.Z, angle) != 0)
            {
                throw new InvalidOperationException($"Failed to rotate GameObject {gameObjectId} around a point.");
            }
        }

        public static void LookAt(long gameObjectId, Vector3 target, Vector3 up)
        {
            LookAtDelegate callback =
                _lookAt ?? throw new InvalidOperationException("Native transform.LookAt is not registered.");
            if (callback(gameObjectId, target.X, target.Y, target.Z, up.X, up.Y, up.Z) != 0)
            {
                throw new InvalidOperationException($"Failed to make GameObject {gameObjectId} look at a target.");
            }
        }

        public static Vector3 TransformPoint(long gameObjectId, Vector3 point)
        {
            TransformPointDelegate callback =
                _transformPoint ?? throw new InvalidOperationException("Native transform.TransformPoint is not registered.");
            if (callback(gameObjectId, point.X, point.Y, point.Z, out float x, out float y, out float z) != 0)
            {
                throw new InvalidOperationException($"Failed to transform point for GameObject {gameObjectId}.");
            }

            return new Vector3(x, y, z);
        }

        public static Vector3 InverseTransformPoint(long gameObjectId, Vector3 point)
        {
            InverseTransformPointDelegate callback =
                _inverseTransformPoint ?? throw new InvalidOperationException("Native transform.InverseTransformPoint is not registered.");
            if (callback(gameObjectId, point.X, point.Y, point.Z, out float x, out float y, out float z) != 0)
            {
                throw new InvalidOperationException($"Failed to inverse-transform point for GameObject {gameObjectId}.");
            }

            return new Vector3(x, y, z);
        }

        public static Vector3 TransformDirection(long gameObjectId, Vector3 direction)
        {
            TransformDirectionDelegate callback =
                _transformDirection ?? throw new InvalidOperationException("Native transform.TransformDirection is not registered.");
            if (callback(gameObjectId, direction.X, direction.Y, direction.Z, out float x, out float y, out float z) != 0)
            {
                throw new InvalidOperationException($"Failed to transform direction for GameObject {gameObjectId}.");
            }

            return new Vector3(x, y, z);
        }

        public static Vector3 InverseTransformDirection(long gameObjectId, Vector3 direction)
        {
            InverseTransformDirectionDelegate callback =
                _inverseTransformDirection ?? throw new InvalidOperationException("Native transform.InverseTransformDirection is not registered.");
            if (callback(gameObjectId, direction.X, direction.Y, direction.Z, out float x, out float y, out float z) != 0)
            {
                throw new InvalidOperationException($"Failed to inverse-transform direction for GameObject {gameObjectId}.");
            }

            return new Vector3(x, y, z);
        }

        public static Vector3 TransformVector(long gameObjectId, Vector3 vector)
        {
            TransformVectorDelegate callback =
                _transformVector ?? throw new InvalidOperationException("Native transform.TransformVector is not registered.");
            if (callback(gameObjectId, vector.X, vector.Y, vector.Z, out float x, out float y, out float z) != 0)
            {
                throw new InvalidOperationException($"Failed to transform vector for GameObject {gameObjectId}.");
            }

            return new Vector3(x, y, z);
        }

        public static Vector3 InverseTransformVector(long gameObjectId, Vector3 vector)
        {
            InverseTransformVectorDelegate callback =
                _inverseTransformVector ?? throw new InvalidOperationException("Native transform.InverseTransformVector is not registered.");
            if (callback(gameObjectId, vector.X, vector.Y, vector.Z, out float x, out float y, out float z) != 0)
            {
                throw new InvalidOperationException($"Failed to inverse-transform vector for GameObject {gameObjectId}.");
            }

            return new Vector3(x, y, z);
        }

        public static Transform? GetParent(long gameObjectId)
        {
            GetParentDelegate callback =
                _getParent ?? throw new InvalidOperationException("Native transform.parent getter is not registered.");
            long parentId = callback(gameObjectId);
            return parentId != 0 ? new GameObject(parentId).transform : null;
        }

        public static void SetParent(long gameObjectId, long parentGameObjectId, bool worldPositionStays)
        {
            SetParentDelegate callback =
                _setParent ?? throw new InvalidOperationException("Native transform.SetParent is not registered.");
            if (callback(gameObjectId, parentGameObjectId, worldPositionStays ? 1 : 0) != 0)
            {
                throw new InvalidOperationException($"Failed to set parent for GameObject {gameObjectId}.");
            }
        }

        public static int GetChildCount(long gameObjectId)
        {
            GetChildCountDelegate callback =
                _getChildCount ?? throw new InvalidOperationException("Native transform.childCount is not registered.");
            if (callback(gameObjectId, out int childCount) != 0)
            {
                throw new InvalidOperationException($"Failed to read childCount for GameObject {gameObjectId}.");
            }

            return childCount;
        }

        public static Transform? GetChild(long gameObjectId, int index)
        {
            GetChildDelegate callback =
                _getChild ?? throw new InvalidOperationException("Native transform.GetChild is not registered.");
            long childId = callback(gameObjectId, index);
            return childId != 0 ? new GameObject(childId).transform : null;
        }

        public static Transform? FindChild(long gameObjectId, string name)
        {
            FindChildDelegate callback =
                _findChild ?? throw new InvalidOperationException("Native transform.Find is not registered.");
            IntPtr namePtr = IntPtr.Zero;
            try
            {
                namePtr = Marshal.StringToCoTaskMemUTF8(name ?? string.Empty);
                long childId = callback(gameObjectId, namePtr);
                return childId != 0 ? new GameObject(childId).transform : null;
            }
            finally
            {
                if (namePtr != IntPtr.Zero)
                {
                    Marshal.FreeCoTaskMem(namePtr);
                }
            }
        }

        public static int GetSiblingIndex(long gameObjectId)
        {
            GetSiblingIndexDelegate callback =
                _getSiblingIndex ?? throw new InvalidOperationException("Native transform.GetSiblingIndex is not registered.");
            if (callback(gameObjectId, out int siblingIndex) != 0)
            {
                throw new InvalidOperationException($"Failed to read sibling index for GameObject {gameObjectId}.");
            }

            return siblingIndex;
        }

        public static void SetSiblingIndex(long gameObjectId, int siblingIndex)
        {
            SetSiblingIndexDelegate callback =
                _setSiblingIndex ?? throw new InvalidOperationException("Native transform.SetSiblingIndex is not registered.");
            if (callback(gameObjectId, siblingIndex) != 0)
            {
                throw new InvalidOperationException($"Failed to set sibling index for GameObject {gameObjectId}.");
            }
        }

        public static void DetachChildren(long gameObjectId)
        {
            DetachChildrenDelegate callback =
                _detachChildren ?? throw new InvalidOperationException("Native transform.DetachChildren is not registered.");
            if (callback(gameObjectId) != 0)
            {
                throw new InvalidOperationException($"Failed to detach children for GameObject {gameObjectId}.");
            }
        }
    }

    internal enum ManagedLifecycleEvent
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
    }

    public static class ManagedComponentBridge
    {
        private static readonly Dictionary<long, MonoBehaviour> Components = new();
        private static readonly Dictionary<string, Type> TypeCache = new(StringComparer.Ordinal);
        private static long _nextHandle;

        [UnmanagedCallersOnly(CallConvs = new[] { typeof(CallConvCdecl) })]
        public static int CreateComponent(IntPtr typeNameUtf8, IntPtr handleOut, IntPtr errorUtf8, int errorUtf8Capacity)
        {
            try
            {
                string typeName = ReadUtf8(typeNameUtf8);
                if (string.IsNullOrWhiteSpace(typeName))
                {
                    throw new InvalidOperationException("Managed component type name was empty.");
                }

                Type type = ResolveComponentType(typeName);
                if (!typeof(MonoBehaviour).IsAssignableFrom(type) || type.IsAbstract)
                {
                    throw new InvalidOperationException($"Type '{typeName}' is not a concrete MonoBehaviour.");
                }

                if (Activator.CreateInstance(type) is not MonoBehaviour component)
                {
                    throw new InvalidOperationException($"Failed to construct managed component '{typeName}'.");
                }

                long handle = Interlocked.Increment(ref _nextHandle);
                Components[handle] = component;
                Marshal.WriteInt64(handleOut, handle);
                return 0;
            }
            catch (Exception ex)
            {
                WriteError(errorUtf8, errorUtf8Capacity, ex.Message);
                return 1;
            }
        }

        [UnmanagedCallersOnly(CallConvs = new[] { typeof(CallConvCdecl) })]
        public static int DestroyComponent(long handle, IntPtr errorUtf8, int errorUtf8Capacity)
        {
            try
            {
                Components.Remove(handle);
                return 0;
            }
            catch (Exception ex)
            {
                WriteError(errorUtf8, errorUtf8Capacity, ex.Message);
                return 1;
            }
        }

        [UnmanagedCallersOnly(CallConvs = new[] { typeof(CallConvCdecl) })]
        public static int UpdateComponentContext(
            long handle,
            long gameObjectId,
            long componentId,
            int enabled,
            int executionOrder,
            IntPtr scriptGuidUtf8,
            IntPtr errorUtf8,
            int errorUtf8Capacity)
        {
            try
            {
                MonoBehaviour component = GetComponentByHandle(handle);
                component.__UpdateContext(
                    gameObjectId,
                    componentId,
                    enabled != 0,
                    executionOrder,
                    ReadUtf8(scriptGuidUtf8));
                return 0;
            }
            catch (Exception ex)
            {
                WriteError(errorUtf8, errorUtf8Capacity, ex.Message);
                return 1;
            }
        }

        [UnmanagedCallersOnly(CallConvs = new[] { typeof(CallConvCdecl) })]
        public static int RegisterNativeApi(
            IntPtr logFn,
            IntPtr findGameObjectFn,
            IntPtr createGameObjectFn,
            IntPtr createPrimitiveFn,
            IntPtr destroyGameObjectFn,
            IntPtr instantiateGameObjectFn,
            IntPtr addManagedComponentFn,
            IntPtr getManagedComponentFn,
            IntPtr getManagedComponentInChildrenFn,
            IntPtr getManagedComponentInParentFn,
            IntPtr getTransformComponentIdFn,
            IntPtr setComponentEnabledFn,
            IntPtr destroyComponentByIdFn,
            IntPtr getWorldPositionFn,
            IntPtr setWorldPositionFn,
            IntPtr getGameObjectNameFn,
            IntPtr setGameObjectNameFn,
            IntPtr setGameObjectActiveFn,
            IntPtr getGameObjectActiveSelfFn,
            IntPtr getGameObjectActiveInHierarchyFn,
            IntPtr getGameObjectTagFn,
            IntPtr setGameObjectTagFn,
            IntPtr compareGameObjectTagFn,
            IntPtr getGameObjectLayerFn,
            IntPtr setGameObjectLayerFn,
            IntPtr getLocalPositionFn,
            IntPtr setLocalPositionFn,
            IntPtr getWorldRotationFn,
            IntPtr setWorldRotationFn,
            IntPtr getLocalRotationFn,
            IntPtr setLocalRotationFn,
            IntPtr getWorldEulerAnglesFn,
            IntPtr setWorldEulerAnglesFn,
            IntPtr getLocalEulerAnglesFn,
            IntPtr setLocalEulerAnglesFn,
            IntPtr translateFn,
            IntPtr translateLocalFn,
            IntPtr getLocalScaleFn,
            IntPtr setLocalScaleFn,
            IntPtr getWorldScaleFn,
            IntPtr rotateEulerFn,
            IntPtr rotateAxisAngleFn,
            IntPtr rotateAroundFn,
            IntPtr lookAtFn,
            IntPtr transformPointFn,
            IntPtr inverseTransformPointFn,
            IntPtr transformDirectionFn,
            IntPtr inverseTransformDirectionFn,
            IntPtr transformVectorFn,
            IntPtr inverseTransformVectorFn,
            IntPtr getParentFn,
            IntPtr setParentFn,
            IntPtr getChildCountFn,
            IntPtr getChildFn,
            IntPtr findChildFn,
            IntPtr getSiblingIndexFn,
            IntPtr setSiblingIndexFn,
            IntPtr detachChildrenFn,
            IntPtr errorUtf8,
            int errorUtf8Capacity)
        {
            try
            {
                NativeApi.Register(
                    logFn,
                    findGameObjectFn,
                    createGameObjectFn,
                    createPrimitiveFn,
                    destroyGameObjectFn,
                    instantiateGameObjectFn,
                    addManagedComponentFn,
                    getManagedComponentFn,
                    getManagedComponentInChildrenFn,
                    getManagedComponentInParentFn,
                    getTransformComponentIdFn,
                    setComponentEnabledFn,
                    destroyComponentByIdFn,
                    getWorldPositionFn,
                    setWorldPositionFn,
                    getGameObjectNameFn,
                    setGameObjectNameFn,
                    setGameObjectActiveFn,
                    getGameObjectActiveSelfFn,
                    getGameObjectActiveInHierarchyFn,
                    getGameObjectTagFn,
                    setGameObjectTagFn,
                    compareGameObjectTagFn,
                    getGameObjectLayerFn,
                    setGameObjectLayerFn,
                    getLocalPositionFn,
                    setLocalPositionFn,
                    getWorldRotationFn,
                    setWorldRotationFn,
                    getLocalRotationFn,
                    setLocalRotationFn,
                    getWorldEulerAnglesFn,
                    setWorldEulerAnglesFn,
                    getLocalEulerAnglesFn,
                    setLocalEulerAnglesFn,
                    translateFn,
                    translateLocalFn,
                    getLocalScaleFn,
                    setLocalScaleFn,
                    getWorldScaleFn,
                    rotateEulerFn,
                    rotateAxisAngleFn,
                    rotateAroundFn,
                    lookAtFn,
                    transformPointFn,
                    inverseTransformPointFn,
                    transformDirectionFn,
                    inverseTransformDirectionFn,
                    transformVectorFn,
                    inverseTransformVectorFn,
                    getParentFn,
                    setParentFn,
                    getChildCountFn,
                    getChildFn,
                    findChildFn,
                    getSiblingIndexFn,
                    setSiblingIndexFn,
                    detachChildrenFn);
                return 0;
            }
            catch (Exception ex)
            {
                WriteError(errorUtf8, errorUtf8Capacity, ex.Message);
                return 1;
            }
        }

        [UnmanagedCallersOnly(CallConvs = new[] { typeof(CallConvCdecl) })]
        public static int InvokeLifecycle(long handle, int eventId, float value, IntPtr errorUtf8, int errorUtf8Capacity)
        {
            try
            {
                MonoBehaviour component = GetComponentByHandle(handle);
                switch ((ManagedLifecycleEvent)eventId)
                {
                    case ManagedLifecycleEvent.Awake:
                        component.Awake();
                        break;
                    case ManagedLifecycleEvent.OnEnable:
                        component.OnEnable();
                        break;
                    case ManagedLifecycleEvent.Start:
                        component.Start();
                        break;
                    case ManagedLifecycleEvent.Update:
                        component.Update(value);
                        break;
                    case ManagedLifecycleEvent.FixedUpdate:
                        component.FixedUpdate(value);
                        break;
                    case ManagedLifecycleEvent.LateUpdate:
                        component.LateUpdate(value);
                        break;
                    case ManagedLifecycleEvent.OnDisable:
                        component.OnDisable();
                        break;
                    case ManagedLifecycleEvent.OnDestroy:
                        component.OnDestroy();
                        break;
                    case ManagedLifecycleEvent.OnValidate:
                        component.OnValidate();
                        break;
                    case ManagedLifecycleEvent.Reset:
                        component.Reset();
                        break;
                    default:
                        throw new InvalidOperationException($"Unsupported lifecycle event id: {eventId}");
                }

                return 0;
            }
            catch (Exception ex)
            {
                WriteError(errorUtf8, errorUtf8Capacity, ex.Message);
                return 1;
            }
        }

        internal static string GetManagedTypeName<T>() where T : MonoBehaviour
        {
            Type type = typeof(T);
            return type.FullName ?? type.Name;
        }

        internal static T? GetManagedComponent<T>(long handle) where T : MonoBehaviour
        {
            if (handle == 0)
            {
                return null;
            }

            MonoBehaviour component = GetComponentByHandle(handle);
            if (component is T typedComponent)
            {
                return typedComponent;
            }

            throw new InvalidCastException(
                $"Managed component handle {handle} is '{component.GetType().FullName}', not '{typeof(T).FullName}'.");
        }

        internal static T? InstantiateObject<T>(T original, Transform? parent) where T : Object
        {
            return original switch
            {
                GameObject gameObject => (T?)(Object?)GameObject.Instantiate(gameObject, parent),
                Transform transform => (T?)(Object?)InstantiateTransform(transform, parent),
                MonoBehaviour behaviour => InstantiateMonoBehaviour(original, behaviour, parent),
                _ => throw new NotSupportedException(
                    $"Instantiate does not support '{original.GetType().FullName}'."),
            };
        }

        internal static Component? AddGameObjectComponent(GameObject gameObject, Type type)
        {
            ArgumentNullException.ThrowIfNull(gameObject);
            ArgumentNullException.ThrowIfNull(type);

            if (!typeof(MonoBehaviour).IsAssignableFrom(type) || type.IsAbstract)
            {
                throw new ArgumentException(
                    $"AddComponent(Type) requires a concrete MonoBehaviour type, got '{type.FullName}'.", nameof(type));
            }

            long handle = NativeApi.AddManagedComponent(gameObject.InstanceId, GetManagedTypeNameForLookup(type));
            return handle != 0 ? GetManagedComponent(handle, type) : null;
        }

        internal static T? GetGameObjectComponent<T>(GameObject gameObject) where T : Component
        {
            ArgumentNullException.ThrowIfNull(gameObject);

            if (typeof(T) == typeof(Transform))
            {
                return gameObject.transform as T;
            }

            return GetManagedGameObjectComponent<T>(gameObject.InstanceId);
        }

        internal static Component? GetGameObjectComponent(GameObject gameObject, Type type)
        {
            ArgumentNullException.ThrowIfNull(gameObject);
            ArgumentNullException.ThrowIfNull(type);

            if (type.IsAssignableFrom(typeof(Transform)))
            {
                return gameObject.transform;
            }

            return GetManagedGameObjectComponent(gameObject.InstanceId, type);
        }

        internal static T? GetGameObjectComponentInChildren<T>(GameObject gameObject) where T : Component
        {
            ArgumentNullException.ThrowIfNull(gameObject);

            if (typeof(T) == typeof(Transform))
            {
                return gameObject.transform as T;
            }

            return GetManagedGameObjectComponentInChildren<T>(gameObject.InstanceId);
        }

        internal static Component? GetGameObjectComponentInChildren(GameObject gameObject, Type type)
        {
            ArgumentNullException.ThrowIfNull(gameObject);
            ArgumentNullException.ThrowIfNull(type);

            if (type.IsAssignableFrom(typeof(Transform)))
            {
                return gameObject.transform;
            }

            return GetManagedGameObjectComponentInChildren(gameObject.InstanceId, type);
        }

        internal static T? GetGameObjectComponentInParent<T>(GameObject gameObject) where T : Component
        {
            ArgumentNullException.ThrowIfNull(gameObject);

            if (typeof(T) == typeof(Transform))
            {
                return gameObject.transform as T;
            }

            return GetManagedGameObjectComponentInParent<T>(gameObject.InstanceId);
        }

        internal static Component? GetGameObjectComponentInParent(GameObject gameObject, Type type)
        {
            ArgumentNullException.ThrowIfNull(gameObject);
            ArgumentNullException.ThrowIfNull(type);

            if (type.IsAssignableFrom(typeof(Transform)))
            {
                return gameObject.transform;
            }

            return GetManagedGameObjectComponentInParent(gameObject.InstanceId, type);
        }

        private static T? GetManagedGameObjectComponent<T>(long gameObjectId) where T : Component
        {
            if (!typeof(MonoBehaviour).IsAssignableFrom(typeof(T)))
            {
                throw new NotSupportedException(
                    $"GetComponent<{typeof(T).Name}> currently supports Transform or managed MonoBehaviour-derived types only.");
            }

            long handle = NativeApi.GetManagedComponent(gameObjectId, GetManagedTypeNameForLookup(typeof(T)));
            return handle != 0 ? (T?)(object)GetManagedComponent(handle, typeof(T)) : null;
        }

        private static Component? GetManagedGameObjectComponent(long gameObjectId, Type type)
        {
            ValidateManagedLookupType(type, nameof(type), "GetComponent(Type)");
            long handle = NativeApi.GetManagedComponent(gameObjectId, GetManagedTypeNameForLookup(type));
            return handle != 0 ? GetManagedComponent(handle, type) : null;
        }

        private static T? GetManagedGameObjectComponentInChildren<T>(long gameObjectId) where T : Component
        {
            if (!typeof(MonoBehaviour).IsAssignableFrom(typeof(T)))
            {
                throw new NotSupportedException(
                    $"GetComponentInChildren<{typeof(T).Name}> currently supports Transform or managed MonoBehaviour-derived types only.");
            }

            long handle = NativeApi.GetManagedComponentInChildren(gameObjectId, GetManagedTypeNameForLookup(typeof(T)));
            return handle != 0 ? (T?)(object)GetManagedComponent(handle, typeof(T)) : null;
        }

        private static Component? GetManagedGameObjectComponentInChildren(long gameObjectId, Type type)
        {
            ValidateManagedLookupType(type, nameof(type), "GetComponentInChildren(Type)");
            long handle = NativeApi.GetManagedComponentInChildren(gameObjectId, GetManagedTypeNameForLookup(type));
            return handle != 0 ? GetManagedComponent(handle, type) : null;
        }

        private static T? GetManagedGameObjectComponentInParent<T>(long gameObjectId) where T : Component
        {
            if (!typeof(MonoBehaviour).IsAssignableFrom(typeof(T)))
            {
                throw new NotSupportedException(
                    $"GetComponentInParent<{typeof(T).Name}> currently supports Transform or managed MonoBehaviour-derived types only.");
            }

            long handle = NativeApi.GetManagedComponentInParent(gameObjectId, GetManagedTypeNameForLookup(typeof(T)));
            return handle != 0 ? (T?)(object)GetManagedComponent(handle, typeof(T)) : null;
        }

        private static Component? GetManagedGameObjectComponentInParent(long gameObjectId, Type type)
        {
            ValidateManagedLookupType(type, nameof(type), "GetComponentInParent(Type)");
            long handle = NativeApi.GetManagedComponentInParent(gameObjectId, GetManagedTypeNameForLookup(type));
            return handle != 0 ? GetManagedComponent(handle, type) : null;
        }

        private static string GetManagedTypeNameForLookup(Type type)
        {
            return type.FullName ?? type.Name;
        }

        private static void ValidateManagedLookupType(Type type, string paramName, string apiName)
        {
            if (!typeof(MonoBehaviour).IsAssignableFrom(type))
            {
                throw new ArgumentException(
                    $"{apiName} currently supports Transform or MonoBehaviour-derived types only.", paramName);
            }
        }

        private static Transform InstantiateTransform(Transform transform, Transform? parent)
        {
            GameObject owner = transform.gameObject ??
                throw new InvalidOperationException("Transform has no owning GameObject.");
            GameObject? clone = GameObject.Instantiate(owner, parent);
            return clone?.transform ??
                throw new InvalidOperationException("Failed to instantiate Transform owner GameObject.");
        }

        private static T? InstantiateMonoBehaviour<T>(T original, MonoBehaviour behaviour, Transform? parent) where T : Object
        {
            GameObject owner = behaviour.gameObject ??
                throw new InvalidOperationException("MonoBehaviour has no owning GameObject.");
            GameObject? clone = GameObject.Instantiate(owner, parent);
            if (clone is null)
            {
                return null;
            }

            Component? cloneComponent = clone.GetComponent(behaviour.GetType());
            return cloneComponent is T typedComponent ? typedComponent : null;
        }

        private static MonoBehaviour GetManagedComponent(long handle, Type expectedType)
        {
            if (!typeof(MonoBehaviour).IsAssignableFrom(expectedType))
            {
                throw new ArgumentException("Expected managed component type must derive from MonoBehaviour.", nameof(expectedType));
            }

            MonoBehaviour component = GetComponentByHandle(handle);
            if (expectedType.IsInstanceOfType(component))
            {
                return component;
            }

            throw new InvalidCastException(
                $"Managed component handle {handle} is '{component.GetType().FullName}', not '{expectedType.FullName}'.");
        }

        private static MonoBehaviour GetComponentByHandle(long handle)
        {
            if (!Components.TryGetValue(handle, out MonoBehaviour? component) || component is null)
            {
                throw new KeyNotFoundException($"Managed component handle {handle} was not found.");
            }

            return component;
        }

        private static Type ResolveComponentType(string typeName)
        {
            if (TypeCache.TryGetValue(typeName, out Type? cached))
            {
                return cached;
            }

            Assembly assembly = Assembly.GetExecutingAssembly();
            foreach (Type type in assembly.GetTypes())
            {
                if (type.FullName == typeName || type.Name == typeName)
                {
                    TypeCache[typeName] = type;
                    return type;
                }
            }

            throw new TypeLoadException($"Managed component type '{typeName}' was not found in {assembly.GetName().Name}.");
        }

        private static string ReadUtf8(IntPtr ptr)
        {
            return ptr == IntPtr.Zero ? string.Empty : Marshal.PtrToStringUTF8(ptr) ?? string.Empty;
        }

        private static void WriteError(IntPtr destination, int capacity, string message)
        {
            if (destination == IntPtr.Zero || capacity <= 0)
            {
                return;
            }

            byte[] bytes = Encoding.UTF8.GetBytes(message ?? string.Empty);
            int count = Math.Min(bytes.Length, capacity - 1);
            if (count > 0)
            {
                Marshal.Copy(bytes, 0, destination, count);
            }
            Marshal.WriteByte(destination, count, 0);
        }
    }
}
"""


def _build_default_script_content(project_name: str) -> str:
    script_class_name = sanitize_csharp_identifier(project_name)
    return f"""using Infernux;

public sealed class {script_class_name} : MonoBehaviour
{{
    public override void Start()
    {{
    }}

    public override void Update(float deltaTime)
    {{
    }}
}}
"""


def ensure_csharp_tooling(project_dir: str, project_name: str = "") -> None:
    project_dir = os.path.abspath(project_dir)
    project_name = infer_project_name(project_dir, project_name)

    csproj_path = os.path.join(project_dir, CSHARP_PROJECT_DIR, CSHARP_PROJECT_FILE)
    stubs_path = os.path.join(project_dir, CSHARP_STUBS_FILE)
    default_script_path = os.path.join(project_dir, DEFAULT_CSHARP_SCRIPT)
    gitignore_path = os.path.join(project_dir, ".gitignore")

    for subdir in (
        os.path.join(project_dir, "Assets"),
        os.path.join(project_dir, "Assets", "Scripts"),
        os.path.join(project_dir, CSHARP_PROJECT_DIR),
        os.path.join(project_dir, CSHARP_GENERATED_DIR),
    ):
        os.makedirs(subdir, exist_ok=True)

    with open(csproj_path, "w", encoding="utf-8") as f:
        f.write(_build_csproj_content())

    with open(stubs_path, "w", encoding="utf-8") as f:
        f.write(_build_stubs_content())

    if not os.path.isfile(default_script_path):
        with open(default_script_path, "w", encoding="utf-8") as f:
            f.write(_build_default_script_content(project_name))

    gitignore_lines = [
        "/.vs/",
        "/bin/",
        "/obj/",
        f"/{CSHARP_PROJECT_DIR}/bin/",
        f"/{CSHARP_PROJECT_DIR}/obj/",
    ]
    existing_lines: list[str] = []
    if os.path.isfile(gitignore_path):
        with open(gitignore_path, "r", encoding="utf-8", errors="replace") as f:
            existing_lines = [line.rstrip("\n") for line in f]
    for line in gitignore_lines:
        if line not in existing_lines:
            existing_lines.append(line)
    with open(gitignore_path, "w", encoding="utf-8") as f:
        for line in existing_lines:
            f.write(f"{line}\n")
