import os
import re


CSHARP_PROJECT_DIR = "Scripts"
CSHARP_PROJECT_FILE = "Infernux.GameScripts.csproj"
CSHARP_GENERATED_DIR = os.path.join(CSHARP_PROJECT_DIR, "Generated")
CSHARP_STUBS_FILE = os.path.join(CSHARP_GENERATED_DIR, "Infernux.RuntimeStubs.cs")
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

    public sealed class GameObject
    {
        internal GameObject(long instanceId)
        {
            InstanceId = instanceId;
        }

        public long InstanceId { get; }
        public string name
        {
            get => Managed.NativeApi.GetGameObjectName(InstanceId);
            set => Managed.NativeApi.SetGameObjectName(InstanceId, value);
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
            long parentId = parent?.gameObject.InstanceId ?? 0;
            long instanceId = Managed.NativeApi.InstantiateGameObject(original.InstanceId, parentId);
            return instanceId != 0 ? new GameObject(instanceId) : null;
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

    public sealed class Transform
    {
        private readonly GameObject _gameObject;

        internal Transform(GameObject gameObject)
        {
            _gameObject = gameObject;
        }

        public GameObject gameObject => _gameObject;

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

        public Transform? parent => Managed.NativeApi.GetParent(_gameObject.InstanceId);
        public int childCount => Managed.NativeApi.GetChildCount(_gameObject.InstanceId);

        public void Translate(Vector3 delta)
        {
            Managed.NativeApi.Translate(_gameObject.InstanceId, delta);
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

    public abstract class InxComponent
    {
        public long GameObjectId { get; private set; }
        public long ComponentId { get; private set; }
        public bool Enabled { get; private set; } = true;
        public int ExecutionOrder { get; private set; }
        public string ScriptGuid { get; private set; } = string.Empty;
        public GameObject? gameObject => GameObjectId != 0 ? new GameObject(GameObjectId) : null;
        public Transform? transform => gameObject?.transform;

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
        private delegate int TranslateDelegate(long gameObjectId, float x, float y, float z);

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        private delegate int GetLocalScaleDelegate(long gameObjectId, out float x, out float y, out float z);

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        private delegate int SetLocalScaleDelegate(long gameObjectId, float x, float y, float z);

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

        private static NativeLogDelegate? _log;
        private static FindGameObjectByNameDelegate? _findGameObjectByName;
        private static CreateGameObjectDelegate? _createGameObject;
        private static CreatePrimitiveDelegate? _createPrimitive;
        private static DestroyGameObjectDelegate? _destroyGameObject;
        private static InstantiateGameObjectDelegate? _instantiateGameObject;
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
        private static TranslateDelegate? _translate;
        private static GetLocalScaleDelegate? _getLocalScale;
        private static SetLocalScaleDelegate? _setLocalScale;
        private static GetParentDelegate? _getParent;
        private static SetParentDelegate? _setParent;
        private static GetChildCountDelegate? _getChildCount;
        private static GetChildDelegate? _getChild;
        private static FindChildDelegate? _findChild;

        public static void Register(
            IntPtr logFn,
            IntPtr findGameObjectFn,
            IntPtr createGameObjectFn,
            IntPtr createPrimitiveFn,
            IntPtr destroyGameObjectFn,
            IntPtr instantiateGameObjectFn,
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
            IntPtr translateFn,
            IntPtr getLocalScaleFn,
            IntPtr setLocalScaleFn,
            IntPtr getParentFn,
            IntPtr setParentFn,
            IntPtr getChildCountFn,
            IntPtr getChildFn,
            IntPtr findChildFn)
        {
            if (logFn == IntPtr.Zero || findGameObjectFn == IntPtr.Zero || createGameObjectFn == IntPtr.Zero ||
                createPrimitiveFn == IntPtr.Zero || destroyGameObjectFn == IntPtr.Zero ||
                instantiateGameObjectFn == IntPtr.Zero ||
                getWorldPositionFn == IntPtr.Zero ||
                setWorldPositionFn == IntPtr.Zero || getGameObjectNameFn == IntPtr.Zero ||
                setGameObjectNameFn == IntPtr.Zero || setGameObjectActiveFn == IntPtr.Zero ||
                getGameObjectActiveSelfFn == IntPtr.Zero || getGameObjectActiveInHierarchyFn == IntPtr.Zero ||
                getGameObjectTagFn == IntPtr.Zero || setGameObjectTagFn == IntPtr.Zero ||
                compareGameObjectTagFn == IntPtr.Zero || getGameObjectLayerFn == IntPtr.Zero ||
                setGameObjectLayerFn == IntPtr.Zero || getLocalPositionFn == IntPtr.Zero ||
                setLocalPositionFn == IntPtr.Zero || translateFn == IntPtr.Zero ||
                getLocalScaleFn == IntPtr.Zero || setLocalScaleFn == IntPtr.Zero ||
                getParentFn == IntPtr.Zero || setParentFn == IntPtr.Zero || getChildCountFn == IntPtr.Zero ||
                getChildFn == IntPtr.Zero || findChildFn == IntPtr.Zero)
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
            _translate = Marshal.GetDelegateForFunctionPointer<TranslateDelegate>(translateFn);
            _getLocalScale = Marshal.GetDelegateForFunctionPointer<GetLocalScaleDelegate>(getLocalScaleFn);
            _setLocalScale = Marshal.GetDelegateForFunctionPointer<SetLocalScaleDelegate>(setLocalScaleFn);
            _getParent = Marshal.GetDelegateForFunctionPointer<GetParentDelegate>(getParentFn);
            _setParent = Marshal.GetDelegateForFunctionPointer<SetParentDelegate>(setParentFn);
            _getChildCount = Marshal.GetDelegateForFunctionPointer<GetChildCountDelegate>(getChildCountFn);
            _getChild = Marshal.GetDelegateForFunctionPointer<GetChildDelegate>(getChildFn);
            _findChild = Marshal.GetDelegateForFunctionPointer<FindChildDelegate>(findChildFn);
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

        public static void Translate(long gameObjectId, Vector3 delta)
        {
            TranslateDelegate callback =
                _translate ?? throw new InvalidOperationException("Native transform.Translate is not registered.");
            if (callback(gameObjectId, delta.X, delta.Y, delta.Z) != 0)
            {
                throw new InvalidOperationException($"Failed to translate GameObject {gameObjectId}.");
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
        private static readonly Dictionary<long, InxComponent> Components = new();
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
                if (!typeof(InxComponent).IsAssignableFrom(type) || type.IsAbstract)
                {
                    throw new InvalidOperationException($"Type '{typeName}' is not a concrete InxComponent.");
                }

                if (Activator.CreateInstance(type) is not InxComponent component)
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
                InxComponent component = GetComponent(handle);
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
            IntPtr translateFn,
            IntPtr getLocalScaleFn,
            IntPtr setLocalScaleFn,
            IntPtr getParentFn,
            IntPtr setParentFn,
            IntPtr getChildCountFn,
            IntPtr getChildFn,
            IntPtr findChildFn,
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
                    translateFn,
                    getLocalScaleFn,
                    setLocalScaleFn,
                    getParentFn,
                    setParentFn,
                    getChildCountFn,
                    getChildFn,
                    findChildFn);
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
                InxComponent component = GetComponent(handle);
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

        private static InxComponent GetComponent(long handle)
        {
            if (!Components.TryGetValue(handle, out InxComponent? component) || component is null)
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

public sealed class {script_class_name} : InxComponent
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
