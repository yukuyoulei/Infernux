from __future__ import annotations

from pathlib import Path

from Infernux.engine.csharp_tooling import CSHARP_STUBS_FILE, ensure_csharp_tooling


def test_generated_runtime_stubs_include_extended_transform_bridge(tmp_path: Path):
    ensure_csharp_tooling(str(tmp_path), project_name="BridgeTest")

    stubs_path = tmp_path / CSHARP_STUBS_FILE
    content = stubs_path.read_text(encoding="utf-8")

    assert "public readonly struct Quaternion" in content
    assert "public abstract class Object" in content
    assert "public abstract class Component : Object" in content
    assert "public abstract class Behaviour : Component" in content
    assert "public sealed class Transform : Component" in content
    assert "public abstract class MonoBehaviour : Behaviour" in content
    assert "public abstract class InxComponent : MonoBehaviour" not in content
    assert "public abstract long GetInstanceID();" in content
    assert "public static T? Instantiate<T>(T original) where T : Object" in content
    assert "public static void Destroy(Object? obj)" in content
    assert "public Quaternion rotation" in content
    assert "public Quaternion localRotation" in content
    assert "public Vector3 eulerAngles" in content
    assert "public Vector3 localEulerAngles" in content
    assert "public Vector3 lossyScale => Managed.NativeApi.GetWorldScale(_gameObject.InstanceId);" in content
    assert "public Transform root" in content
    assert "public Vector3 forward => rotation * ForwardAxis;" in content
    assert "public void TranslateLocal(Vector3 delta)" in content
    assert "public void Rotate(Vector3 eulerAngles)" in content
    assert "public void Rotate(Vector3 axis, float angle)" in content
    assert "public void RotateAround(Vector3 point, Vector3 axis, float angle)" in content
    assert "public void LookAt(Vector3 target)" in content
    assert "public Vector3 TransformPoint(Vector3 point)" in content
    assert "public Vector3 InverseTransformDirection(Vector3 direction)" in content
    assert "public bool IsChildOf(Transform? parent)" in content
    assert "public void DetachChildren()" in content
    assert "public int GetSiblingIndex()" in content
    assert "public void SetAsLastSibling()" in content
    assert "private delegate int GetWorldRotationDelegate" in content
    assert "private delegate int GetWorldEulerAnglesDelegate" in content
    assert "private delegate int TranslateLocalDelegate" in content
    assert "private delegate int RotateAroundDelegate" in content
    assert "private delegate int TransformVectorDelegate" in content
    assert "private delegate int SetSiblingIndexDelegate" in content
    assert "private delegate int DetachChildrenDelegate" in content
    assert "public T? AddComponent<T>() where T : MonoBehaviour" in content
    assert "public Component? AddComponent(Type type)" in content
    assert "public T? GetComponent<T>() where T : Component" in content
    assert "public Component? GetComponent(Type type)" in content
    assert "public bool TryGetComponent<T>(out T? component) where T : Component" in content
    assert "public bool TryGetComponent(Type type, out Component? component)" in content
    assert "public T[] GetComponents<T>() where T : Component" in content
    assert "public void GetComponents<T>(List<T> results) where T : Component" in content
    assert "public Component[] GetComponents(Type type)" in content
    assert "public T? GetComponentInChildren<T>() where T : Component" in content
    assert "public T? GetComponentInChildren<T>(bool includeInactive) where T : Component" in content
    assert "public Component? GetComponentInChildren(Type type)" in content
    assert "public Component? GetComponentInChildren(Type type, bool includeInactive)" in content
    assert "public T[] GetComponentsInChildren<T>() where T : Component" in content
    assert "public T[] GetComponentsInChildren<T>(bool includeInactive) where T : Component" in content
    assert "public void GetComponentsInChildren<T>(List<T> results) where T : Component" in content
    assert "public void GetComponentsInChildren<T>(bool includeInactive, List<T> results) where T : Component" in content
    assert "public Component[] GetComponentsInChildren(Type type)" in content
    assert "public Component[] GetComponentsInChildren(Type type, bool includeInactive)" in content
    assert "public T? GetComponentInParent<T>() where T : Component" in content
    assert "public T? GetComponentInParent<T>(bool includeInactive) where T : Component" in content
    assert "public Component? GetComponentInParent(Type type)" in content
    assert "public Component? GetComponentInParent(Type type, bool includeInactive)" in content
    assert "public T[] GetComponentsInParent<T>() where T : Component" in content
    assert "public T[] GetComponentsInParent<T>(bool includeInactive) where T : Component" in content
    assert "public void GetComponentsInParent<T>(List<T> results) where T : Component" in content
    assert "public void GetComponentsInParent<T>(bool includeInactive, List<T> results) where T : Component" in content
    assert "public Component[] GetComponentsInParent(Type type)" in content
    assert "public Component[] GetComponentsInParent(Type type, bool includeInactive)" in content
    assert "public override string name" in content
    assert "public bool CompareTag(string tag)" in content
    assert "public abstract bool enabled { get; set; }" in content
    assert "public bool isActiveAndEnabled => enabled && (gameObject?.activeInHierarchy ?? false);" in content
    assert "public override long GetInstanceID()" in content
    assert "return Managed.NativeApi.GetTransformComponentId(_gameObject.InstanceId);" in content
    assert "Managed.NativeApi.SetComponentEnabled(ComponentId, value);" in content
    assert "private delegate long AddManagedComponentDelegate" in content
    assert "private delegate long GetManagedComponentDelegate" in content
    assert "private delegate long GetManagedComponentInChildrenDelegate" in content
    assert "private delegate long GetManagedComponentInParentDelegate" in content
    assert "private delegate long GetTransformComponentIdDelegate(long gameObjectId);" in content
    assert "private delegate int SetComponentEnabledDelegate(long componentId, int enabled);" in content
    assert "private delegate int DestroyComponentByIdDelegate(long componentId);" in content
    assert "internal static string GetManagedTypeName<T>() where T : MonoBehaviour" in content
    assert "internal static T? GetManagedComponent<T>(long handle) where T : MonoBehaviour" in content
    assert "private static readonly Dictionary<long, MonoBehaviour> Components = new();" in content
    assert "internal static T? InstantiateObject<T>(T original, Transform? parent) where T : Object" in content
    assert "internal static Component? AddGameObjectComponent(GameObject gameObject, Type type)" in content
    assert "internal static T? GetGameObjectComponent<T>(GameObject gameObject) where T : Component" in content
    assert "internal static T[] GetGameObjectComponents<T>(GameObject gameObject) where T : Component" in content
    assert "internal static Component[] GetGameObjectComponents(GameObject gameObject, Type type)" in content
    assert "internal static T[] GetGameObjectComponentsInChildren<T>(GameObject gameObject) where T : Component" in content
    assert "internal static T[] GetGameObjectComponentsInChildren<T>(GameObject gameObject, bool includeInactive) where T : Component" in content
    assert "internal static void GetGameObjectComponentsInChildren<T>(GameObject gameObject, List<T> results) where T : Component" in content
    assert "internal static void GetGameObjectComponentsInChildren<T>(GameObject gameObject, bool includeInactive, List<T> results) where T : Component" in content
    assert "internal static Component[] GetGameObjectComponentsInChildren(GameObject gameObject, Type type)" in content
    assert "internal static Component[] GetGameObjectComponentsInChildren(GameObject gameObject, Type type, bool includeInactive)" in content
    assert "internal static T[] GetGameObjectComponentsInParent<T>(GameObject gameObject) where T : Component" in content
    assert "internal static T[] GetGameObjectComponentsInParent<T>(GameObject gameObject, bool includeInactive) where T : Component" in content
    assert "internal static Component[] GetGameObjectComponentsInParent(GameObject gameObject, Type type)" in content
    assert "internal static Component[] GetGameObjectComponentsInParent(GameObject gameObject, Type type, bool includeInactive)" in content
    assert "if (typeof(T).IsAssignableFrom(typeof(Transform)))" in content
    assert "private static bool CanMatchManagedComponentType(Type type)" in content
    assert "if (!expectedType.IsInstanceOfType(candidate))" in content
    assert "private static void CollectComponentsOnGameObject(GameObject gameObject, Type expectedType, List<Component> results)" in content
    assert "private static void CollectComponentsInChildren(GameObject gameObject, Type expectedType, bool includeInactive, bool includeSelf, List<Component> results)" in content
    assert "private static void CollectComponentsInParent(GameObject gameObject, Type expectedType, bool includeInactive, bool includeSelf, List<Component> results)" in content

