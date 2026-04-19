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


def default_script_class_name(project_name: str) -> str:
    class_name = sanitize_csharp_identifier(project_name)
    reserved = {
        "Infernux",
        "Object",
        "Component",
        "Behaviour",
        "MonoBehaviour",
        "GameObject",
        "Transform",
        "Camera",
        "Debug",
        "Mathf",
        "Random",
        "Color",
        "Color32",
        "Vector2",
        "Vector3",
        "Quaternion",
        "Ray",
        "Matrix4x4",
    }
    if class_name in reserved:
        class_name = f"{class_name}Main"
    return class_name


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

    public enum Space
    {
        World = 0,
        Self = 1,
    }

    public enum CameraProjection
    {
        Perspective = 0,
        Orthographic = 1,
    }

    public enum CameraClearFlags
    {
        Skybox = 0,
        SolidColor = 1,
        DepthOnly = 2,
        DontClear = 3,
    }

    public readonly struct Vector2
    {
        public float X { get; }
        public float Y { get; }

        public Vector2(float x, float y)
        {
            X = x;
            Y = y;
        }

        public static Vector2 zero => new(0f, 0f);
        public static Vector2 one => new(1f, 1f);
        public static Vector2 right => new(1f, 0f);
        public static Vector2 up => new(0f, 1f);

        public float sqrMagnitude => X * X + Y * Y;
        public float magnitude => MathF.Sqrt(sqrMagnitude);
        public Vector2 normalized
        {
            get
            {
                float length = magnitude;
                return length > 1e-6f ? this / length : zero;
            }
        }

        public static Vector2 operator +(Vector2 lhs, Vector2 rhs)
        {
            return new Vector2(lhs.X + rhs.X, lhs.Y + rhs.Y);
        }

        public static Vector2 operator -(Vector2 lhs, Vector2 rhs)
        {
            return new Vector2(lhs.X - rhs.X, lhs.Y - rhs.Y);
        }

        public static Vector2 operator -(Vector2 value)
        {
            return new Vector2(-value.X, -value.Y);
        }

        public static Vector2 operator *(Vector2 value, float scalar)
        {
            return new Vector2(value.X * scalar, value.Y * scalar);
        }

        public static Vector2 operator *(float scalar, Vector2 value)
        {
            return value * scalar;
        }

        public static Vector2 operator /(Vector2 value, float scalar)
        {
            return new Vector2(value.X / scalar, value.Y / scalar);
        }

        public static float Dot(Vector2 lhs, Vector2 rhs)
        {
            return lhs.X * rhs.X + lhs.Y * rhs.Y;
        }

        public static Vector2 Lerp(Vector2 a, Vector2 b, float t)
        {
            return new Vector2(Mathf.Lerp(a.X, b.X, t), Mathf.Lerp(a.Y, b.Y, t));
        }

        public override string ToString()
        {
            return $"({X}, {Y})";
        }
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

        public static Vector3 zero => new(0f, 0f, 0f);
        public static Vector3 right => new(1f, 0f, 0f);
        public static Vector3 up => new(0f, 1f, 0f);
        public static Vector3 forward => new(0f, 0f, 1f);

        public float sqrMagnitude => X * X + Y * Y + Z * Z;
        public float magnitude => MathF.Sqrt(sqrMagnitude);
        public Vector3 normalized
        {
            get
            {
                float length = magnitude;
                return length > 1e-6f ? this / length : zero;
            }
        }

        public static Vector3 operator +(Vector3 lhs, Vector3 rhs)
        {
            return new Vector3(lhs.X + rhs.X, lhs.Y + rhs.Y, lhs.Z + rhs.Z);
        }

        public static Vector3 operator -(Vector3 lhs, Vector3 rhs)
        {
            return new Vector3(lhs.X - rhs.X, lhs.Y - rhs.Y, lhs.Z - rhs.Z);
        }

        public static Vector3 operator -(Vector3 value)
        {
            return new Vector3(-value.X, -value.Y, -value.Z);
        }

        public static Vector3 operator *(Vector3 value, float scalar)
        {
            return new Vector3(value.X * scalar, value.Y * scalar, value.Z * scalar);
        }

        public static Vector3 operator *(float scalar, Vector3 value)
        {
            return value * scalar;
        }

        public static Vector3 operator /(Vector3 value, float scalar)
        {
            return new Vector3(value.X / scalar, value.Y / scalar, value.Z / scalar);
        }

        public static float Dot(Vector3 lhs, Vector3 rhs)
        {
            return lhs.X * rhs.X + lhs.Y * rhs.Y + lhs.Z * rhs.Z;
        }

        public static Vector3 Cross(Vector3 lhs, Vector3 rhs)
        {
            return new Vector3(
                lhs.Y * rhs.Z - lhs.Z * rhs.Y,
                lhs.Z * rhs.X - lhs.X * rhs.Z,
                lhs.X * rhs.Y - lhs.Y * rhs.X);
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

        public static Quaternion Euler(Vector3 euler)
        {
            return Euler(euler.X, euler.Y, euler.Z);
        }

        public static Quaternion Euler(float x, float y, float z)
        {
            float halfX = x * (MathF.PI / 180f) * 0.5f;
            float halfY = y * (MathF.PI / 180f) * 0.5f;
            float halfZ = z * (MathF.PI / 180f) * 0.5f;
            float cx = MathF.Cos(halfX);
            float sx = MathF.Sin(halfX);
            float cy = MathF.Cos(halfY);
            float sy = MathF.Sin(halfY);
            float cz = MathF.Cos(halfZ);
            float sz = MathF.Sin(halfZ);

            return new Quaternion(
                cy * sx * cz + sy * cx * sz,
                sy * cx * cz - cy * sx * sz,
                cy * cx * sz - sy * sx * cz,
                cy * cx * cz + sy * sx * sz);
        }

        public static Quaternion AngleAxis(float angle, Vector3 axis)
        {
            float axisLength = MathF.Sqrt(axis.X * axis.X + axis.Y * axis.Y + axis.Z * axis.Z);
            if (axisLength <= 1e-6f)
            {
                return identity;
            }

            float invLength = 1f / axisLength;
            float halfAngle = angle * (MathF.PI / 180f) * 0.5f;
            float sinHalfAngle = MathF.Sin(halfAngle);
            float cosHalfAngle = MathF.Cos(halfAngle);
            return new Quaternion(
                axis.X * invLength * sinHalfAngle,
                axis.Y * invLength * sinHalfAngle,
                axis.Z * invLength * sinHalfAngle,
                cosHalfAngle);
        }

        public static Quaternion LookRotation(Vector3 forward)
        {
            return LookRotation(forward, Vector3.up);
        }

        public static Quaternion LookRotation(Vector3 forward, Vector3 upwards)
        {
            Vector3 zAxis = forward.normalized;
            if (zAxis.sqrMagnitude <= 1e-12f)
            {
                return identity;
            }

            Vector3 xAxis = Vector3.Cross(upwards, zAxis).normalized;
            if (xAxis.sqrMagnitude <= 1e-12f)
            {
                Vector3 fallbackUp = MathF.Abs(zAxis.Y) < 0.999f ? Vector3.up : Vector3.right;
                xAxis = Vector3.Cross(fallbackUp, zAxis).normalized;
            }

            Vector3 yAxis = Vector3.Cross(zAxis, xAxis);

            float m00 = xAxis.X;
            float m01 = yAxis.X;
            float m02 = zAxis.X;
            float m10 = xAxis.Y;
            float m11 = yAxis.Y;
            float m12 = zAxis.Y;
            float m20 = xAxis.Z;
            float m21 = yAxis.Z;
            float m22 = zAxis.Z;
            float trace = m00 + m11 + m22;

            if (trace > 0f)
            {
                float s = MathF.Sqrt(trace + 1f) * 2f;
                return new Quaternion(
                    (m21 - m12) / s,
                    (m02 - m20) / s,
                    (m10 - m01) / s,
                    0.25f * s);
            }

            if (m00 > m11 && m00 > m22)
            {
                float s = MathF.Sqrt(1f + m00 - m11 - m22) * 2f;
                return new Quaternion(
                    0.25f * s,
                    (m01 + m10) / s,
                    (m02 + m20) / s,
                    (m21 - m12) / s);
            }

            if (m11 > m22)
            {
                float s = MathF.Sqrt(1f + m11 - m00 - m22) * 2f;
                return new Quaternion(
                    (m01 + m10) / s,
                    0.25f * s,
                    (m12 + m21) / s,
                    (m02 - m20) / s);
            }

            float lastS = MathF.Sqrt(1f + m22 - m00 - m11) * 2f;
            return new Quaternion(
                (m02 + m20) / lastS,
                (m12 + m21) / lastS,
                0.25f * lastS,
                (m10 - m01) / lastS);
        }

        public static Quaternion operator *(Quaternion lhs, Quaternion rhs)
        {
            return new Quaternion(
                lhs.W * rhs.X + lhs.X * rhs.W + lhs.Y * rhs.Z - lhs.Z * rhs.Y,
                lhs.W * rhs.Y - lhs.X * rhs.Z + lhs.Y * rhs.W + lhs.Z * rhs.X,
                lhs.W * rhs.Z + lhs.X * rhs.Y - lhs.Y * rhs.X + lhs.Z * rhs.W,
                lhs.W * rhs.W - lhs.X * rhs.X - lhs.Y * rhs.Y - lhs.Z * rhs.Z);
        }

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

    public struct Color
    {
        public float r;
        public float g;
        public float b;
        public float a;

        public Color(float r, float g, float b, float a = 1f)
        {
            this.r = r;
            this.g = g;
            this.b = b;
            this.a = a;
        }

        public static Color white => new(1f, 1f, 1f, 1f);
        public static Color black => new(0f, 0f, 0f, 1f);
        public static Color red => new(1f, 0f, 0f, 1f);
        public static Color green => new(0f, 1f, 0f, 1f);
        public static Color blue => new(0f, 0f, 1f, 1f);
        public static Color yellow => new(1f, 0.92156863f, 0.015686275f, 1f);
        public static Color cyan => new(0f, 1f, 1f, 1f);
        public static Color magenta => new(1f, 0f, 1f, 1f);
        public static Color gray => new(0.5f, 0.5f, 0.5f, 1f);
        public static Color clear => new(0f, 0f, 0f, 0f);

        public float grayscale => 0.299f * r + 0.587f * g + 0.114f * b;

        public static Color Lerp(Color a, Color b, float t)
        {
            t = Mathf.Clamp01(t);
            return new Color(
                Mathf.Lerp(a.r, b.r, t),
                Mathf.Lerp(a.g, b.g, t),
                Mathf.Lerp(a.b, b.b, t),
                Mathf.Lerp(a.a, b.a, t));
        }

        public static Color operator +(Color lhs, Color rhs)
        {
            return new Color(lhs.r + rhs.r, lhs.g + rhs.g, lhs.b + rhs.b, lhs.a + rhs.a);
        }

        public static Color operator -(Color lhs, Color rhs)
        {
            return new Color(lhs.r - rhs.r, lhs.g - rhs.g, lhs.b - rhs.b, lhs.a - rhs.a);
        }

        public static Color operator *(Color lhs, float scalar)
        {
            return new Color(lhs.r * scalar, lhs.g * scalar, lhs.b * scalar, lhs.a * scalar);
        }

        public static Color operator *(float scalar, Color rhs)
        {
            return rhs * scalar;
        }

        public static Color operator *(Color lhs, Color rhs)
        {
            return new Color(lhs.r * rhs.r, lhs.g * rhs.g, lhs.b * rhs.b, lhs.a * rhs.a);
        }

        public override string ToString()
        {
            return $"RGBA({r}, {g}, {b}, {a})";
        }
    }

    public struct Color32
    {
        public byte r;
        public byte g;
        public byte b;
        public byte a;

        public Color32(byte r, byte g, byte b, byte a = 255)
        {
            this.r = r;
            this.g = g;
            this.b = b;
            this.a = a;
        }

        public static implicit operator Color(Color32 value)
        {
            const float kInv = 1f / 255f;
            return new Color(value.r * kInv, value.g * kInv, value.b * kInv, value.a * kInv);
        }

        public static implicit operator Color32(Color value)
        {
            return new Color32(
                (byte)Mathf.Clamp(Mathf.RoundToInt(value.r * 255f), 0, 255),
                (byte)Mathf.Clamp(Mathf.RoundToInt(value.g * 255f), 0, 255),
                (byte)Mathf.Clamp(Mathf.RoundToInt(value.b * 255f), 0, 255),
                (byte)Mathf.Clamp(Mathf.RoundToInt(value.a * 255f), 0, 255));
        }

        public override string ToString()
        {
            return $"RGBA({r}, {g}, {b}, {a})";
        }
    }

    public struct Matrix4x4
    {
        public float m00;
        public float m01;
        public float m02;
        public float m03;
        public float m10;
        public float m11;
        public float m12;
        public float m13;
        public float m20;
        public float m21;
        public float m22;
        public float m23;
        public float m30;
        public float m31;
        public float m32;
        public float m33;

        public Matrix4x4(
            float m00, float m01, float m02, float m03,
            float m10, float m11, float m12, float m13,
            float m20, float m21, float m22, float m23,
            float m30, float m31, float m32, float m33)
        {
            this.m00 = m00;
            this.m01 = m01;
            this.m02 = m02;
            this.m03 = m03;
            this.m10 = m10;
            this.m11 = m11;
            this.m12 = m12;
            this.m13 = m13;
            this.m20 = m20;
            this.m21 = m21;
            this.m22 = m22;
            this.m23 = m23;
            this.m30 = m30;
            this.m31 = m31;
            this.m32 = m32;
            this.m33 = m33;
        }

        public static Matrix4x4 identity => new(
            1f, 0f, 0f, 0f,
            0f, 1f, 0f, 0f,
            0f, 0f, 1f, 0f,
            0f, 0f, 0f, 1f);

        public Matrix4x4 inverse
        {
            get
            {
                float[] m =
                {
                    m00, m01, m02, m03,
                    m10, m11, m12, m13,
                    m20, m21, m22, m23,
                    m30, m31, m32, m33,
                };
                float[] inv = new float[16];

                inv[0] = m[5] * m[10] * m[15] -
                         m[5] * m[11] * m[14] -
                         m[9] * m[6] * m[15] +
                         m[9] * m[7] * m[14] +
                         m[13] * m[6] * m[11] -
                         m[13] * m[7] * m[10];
                inv[4] = -m[4] * m[10] * m[15] +
                          m[4] * m[11] * m[14] +
                          m[8] * m[6] * m[15] -
                          m[8] * m[7] * m[14] -
                          m[12] * m[6] * m[11] +
                          m[12] * m[7] * m[10];
                inv[8] = m[4] * m[9] * m[15] -
                         m[4] * m[11] * m[13] -
                         m[8] * m[5] * m[15] +
                         m[8] * m[7] * m[13] +
                         m[12] * m[5] * m[11] -
                         m[12] * m[7] * m[9];
                inv[12] = -m[4] * m[9] * m[14] +
                           m[4] * m[10] * m[13] +
                           m[8] * m[5] * m[14] -
                           m[8] * m[6] * m[13] -
                           m[12] * m[5] * m[10] +
                           m[12] * m[6] * m[9];
                inv[1] = -m[1] * m[10] * m[15] +
                          m[1] * m[11] * m[14] +
                          m[9] * m[2] * m[15] -
                          m[9] * m[3] * m[14] -
                          m[13] * m[2] * m[11] +
                          m[13] * m[3] * m[10];
                inv[5] = m[0] * m[10] * m[15] -
                         m[0] * m[11] * m[14] -
                         m[8] * m[2] * m[15] +
                         m[8] * m[3] * m[14] +
                         m[12] * m[2] * m[11] -
                         m[12] * m[3] * m[10];
                inv[9] = -m[0] * m[9] * m[15] +
                          m[0] * m[11] * m[13] +
                          m[8] * m[1] * m[15] -
                          m[8] * m[3] * m[13] -
                          m[12] * m[1] * m[11] +
                          m[12] * m[3] * m[9];
                inv[13] = m[0] * m[9] * m[14] -
                          m[0] * m[10] * m[13] -
                          m[8] * m[1] * m[14] +
                          m[8] * m[2] * m[13] +
                          m[12] * m[1] * m[10] -
                          m[12] * m[2] * m[9];
                inv[2] = m[1] * m[6] * m[15] -
                         m[1] * m[7] * m[14] -
                         m[5] * m[2] * m[15] +
                         m[5] * m[3] * m[14] +
                         m[13] * m[2] * m[7] -
                         m[13] * m[3] * m[6];
                inv[6] = -m[0] * m[6] * m[15] +
                          m[0] * m[7] * m[14] +
                          m[4] * m[2] * m[15] -
                          m[4] * m[3] * m[14] -
                          m[12] * m[2] * m[7] +
                          m[12] * m[3] * m[6];
                inv[10] = m[0] * m[5] * m[15] -
                          m[0] * m[7] * m[13] -
                          m[4] * m[1] * m[15] +
                          m[4] * m[3] * m[13] +
                          m[12] * m[1] * m[7] -
                          m[12] * m[3] * m[5];
                inv[14] = -m[0] * m[5] * m[14] +
                           m[0] * m[6] * m[13] +
                           m[4] * m[1] * m[14] -
                           m[4] * m[2] * m[13] -
                           m[12] * m[1] * m[6] +
                           m[12] * m[2] * m[5];
                inv[3] = -m[1] * m[6] * m[11] +
                          m[1] * m[7] * m[10] +
                          m[5] * m[2] * m[11] -
                          m[5] * m[3] * m[10] -
                          m[9] * m[2] * m[7] +
                          m[9] * m[3] * m[6];
                inv[7] = m[0] * m[6] * m[11] -
                         m[0] * m[7] * m[10] -
                         m[4] * m[2] * m[11] +
                         m[4] * m[3] * m[10] +
                         m[8] * m[2] * m[7] -
                         m[8] * m[3] * m[6];
                inv[11] = -m[0] * m[5] * m[11] +
                           m[0] * m[7] * m[9] +
                           m[4] * m[1] * m[11] -
                           m[4] * m[3] * m[9] -
                           m[8] * m[1] * m[7] +
                           m[8] * m[3] * m[5];
                inv[15] = m[0] * m[5] * m[10] -
                          m[0] * m[6] * m[9] -
                          m[4] * m[1] * m[10] +
                          m[4] * m[2] * m[9] +
                          m[8] * m[1] * m[6] -
                          m[8] * m[2] * m[5];

                float det = m[0] * inv[0] + m[1] * inv[4] + m[2] * inv[8] + m[3] * inv[12];
                if (Mathf.Abs(det) <= Mathf.Epsilon)
                {
                    return identity;
                }

                det = 1f / det;
                return new Matrix4x4(
                    inv[0] * det, inv[1] * det, inv[2] * det, inv[3] * det,
                    inv[4] * det, inv[5] * det, inv[6] * det, inv[7] * det,
                    inv[8] * det, inv[9] * det, inv[10] * det, inv[11] * det,
                    inv[12] * det, inv[13] * det, inv[14] * det, inv[15] * det);
            }
        }

        public static Matrix4x4 TRS(Vector3 position, Quaternion rotation, Vector3 scale)
        {
            float x = rotation.X;
            float y = rotation.Y;
            float z = rotation.Z;
            float w = rotation.W;
            float x2 = x + x;
            float y2 = y + y;
            float z2 = z + z;
            float xx = x * x2;
            float yy = y * y2;
            float zz = z * z2;
            float xy = x * y2;
            float xz = x * z2;
            float yz = y * z2;
            float wx = w * x2;
            float wy = w * y2;
            float wz = w * z2;

            return new Matrix4x4(
                (1f - (yy + zz)) * scale.X, (xy - wz) * scale.Y, (xz + wy) * scale.Z, position.X,
                (xy + wz) * scale.X, (1f - (xx + zz)) * scale.Y, (yz - wx) * scale.Z, position.Y,
                (xz - wy) * scale.X, (yz + wx) * scale.Y, (1f - (xx + yy)) * scale.Z, position.Z,
                0f, 0f, 0f, 1f);
        }

        public Vector3 MultiplyPoint(Vector3 point)
        {
            float x = m00 * point.X + m01 * point.Y + m02 * point.Z + m03;
            float y = m10 * point.X + m11 * point.Y + m12 * point.Z + m13;
            float z = m20 * point.X + m21 * point.Y + m22 * point.Z + m23;
            float w = m30 * point.X + m31 * point.Y + m32 * point.Z + m33;
            if (Mathf.Abs(w) > Mathf.Epsilon)
            {
                float invW = 1f / w;
                return new Vector3(x * invW, y * invW, z * invW);
            }

            return new Vector3(x, y, z);
        }

        public Vector3 MultiplyVector(Vector3 vector)
        {
            return new Vector3(
                m00 * vector.X + m01 * vector.Y + m02 * vector.Z,
                m10 * vector.X + m11 * vector.Y + m12 * vector.Z,
                m20 * vector.X + m21 * vector.Y + m22 * vector.Z);
        }

        public static Matrix4x4 operator *(Matrix4x4 lhs, Matrix4x4 rhs)
        {
            return new Matrix4x4(
                lhs.m00 * rhs.m00 + lhs.m01 * rhs.m10 + lhs.m02 * rhs.m20 + lhs.m03 * rhs.m30,
                lhs.m00 * rhs.m01 + lhs.m01 * rhs.m11 + lhs.m02 * rhs.m21 + lhs.m03 * rhs.m31,
                lhs.m00 * rhs.m02 + lhs.m01 * rhs.m12 + lhs.m02 * rhs.m22 + lhs.m03 * rhs.m32,
                lhs.m00 * rhs.m03 + lhs.m01 * rhs.m13 + lhs.m02 * rhs.m23 + lhs.m03 * rhs.m33,
                lhs.m10 * rhs.m00 + lhs.m11 * rhs.m10 + lhs.m12 * rhs.m20 + lhs.m13 * rhs.m30,
                lhs.m10 * rhs.m01 + lhs.m11 * rhs.m11 + lhs.m12 * rhs.m21 + lhs.m13 * rhs.m31,
                lhs.m10 * rhs.m02 + lhs.m11 * rhs.m12 + lhs.m12 * rhs.m22 + lhs.m13 * rhs.m32,
                lhs.m10 * rhs.m03 + lhs.m11 * rhs.m13 + lhs.m12 * rhs.m23 + lhs.m13 * rhs.m33,
                lhs.m20 * rhs.m00 + lhs.m21 * rhs.m10 + lhs.m22 * rhs.m20 + lhs.m23 * rhs.m30,
                lhs.m20 * rhs.m01 + lhs.m21 * rhs.m11 + lhs.m22 * rhs.m21 + lhs.m23 * rhs.m31,
                lhs.m20 * rhs.m02 + lhs.m21 * rhs.m12 + lhs.m22 * rhs.m22 + lhs.m23 * rhs.m32,
                lhs.m20 * rhs.m03 + lhs.m21 * rhs.m13 + lhs.m22 * rhs.m23 + lhs.m23 * rhs.m33,
                lhs.m30 * rhs.m00 + lhs.m31 * rhs.m10 + lhs.m32 * rhs.m20 + lhs.m33 * rhs.m30,
                lhs.m30 * rhs.m01 + lhs.m31 * rhs.m11 + lhs.m32 * rhs.m21 + lhs.m33 * rhs.m31,
                lhs.m30 * rhs.m02 + lhs.m31 * rhs.m12 + lhs.m32 * rhs.m22 + lhs.m33 * rhs.m32,
                lhs.m30 * rhs.m03 + lhs.m31 * rhs.m13 + lhs.m32 * rhs.m23 + lhs.m33 * rhs.m33);
        }

        public override string ToString()
        {
            return $"[{m00}, {m01}, {m02}, {m03}; {m10}, {m11}, {m12}, {m13}; {m20}, {m21}, {m22}, {m23}; {m30}, {m31}, {m32}, {m33}]";
        }
    }

    public struct Ray
    {
        public Vector3 origin;
        public Vector3 direction;

        public Ray(Vector3 origin, Vector3 direction)
        {
            this.origin = origin;
            this.direction = direction.normalized;
        }

        public Vector3 GetPoint(float distance)
        {
            return origin + direction * distance;
        }

        public override string ToString()
        {
            return $"Origin: {origin}, Dir: {direction}";
        }
    }

    public static class Mathf
    {
        public const float PI = MathF.PI;
        public const float Deg2Rad = PI / 180f;
        public const float Rad2Deg = 180f / PI;
        public const float Epsilon = 1e-6f;

        public static float Abs(float value) => MathF.Abs(value);
        public static int Abs(int value) => Math.Abs(value);
        public static float Min(float a, float b) => MathF.Min(a, b);
        public static int Min(int a, int b) => Math.Min(a, b);
        public static float Max(float a, float b) => MathF.Max(a, b);
        public static int Max(int a, int b) => Math.Max(a, b);
        public static float Sign(float value) => value >= 0f ? 1f : -1f;
        public static float Sqrt(float value) => MathF.Sqrt(value);
        public static float Sin(float value) => MathF.Sin(value);
        public static float Cos(float value) => MathF.Cos(value);
        public static float Tan(float value) => MathF.Tan(value);
        public static float Asin(float value) => MathF.Asin(value);
        public static float Acos(float value) => MathF.Acos(value);
        public static float Atan(float value) => MathF.Atan(value);
        public static float Atan2(float y, float x) => MathF.Atan2(y, x);
        public static float Floor(float value) => MathF.Floor(value);
        public static float Ceil(float value) => MathF.Ceiling(value);
        public static float Round(float value) => MathF.Round(value);
        public static int FloorToInt(float value) => (int)MathF.Floor(value);
        public static int CeilToInt(float value) => (int)MathF.Ceiling(value);
        public static int RoundToInt(float value) => (int)MathF.Round(value);

        public static float Clamp(float value, float min, float max)
        {
            if (value < min)
            {
                return min;
            }

            if (value > max)
            {
                return max;
            }

            return value;
        }

        public static int Clamp(int value, int min, int max)
        {
            if (value < min)
            {
                return min;
            }

            if (value > max)
            {
                return max;
            }

            return value;
        }

        public static float Clamp01(float value)
        {
            return Clamp(value, 0f, 1f);
        }

        public static float Lerp(float a, float b, float t)
        {
            return a + (b - a) * Clamp01(t);
        }

        public static float LerpUnclamped(float a, float b, float t)
        {
            return a + (b - a) * t;
        }

        public static float InverseLerp(float a, float b, float value)
        {
            if (Abs(b - a) <= Epsilon)
            {
                return 0f;
            }

            return Clamp01((value - a) / (b - a));
        }

        public static float Repeat(float t, float length)
        {
            if (length <= 0f)
            {
                return 0f;
            }

            return Clamp(t - Floor(t / length) * length, 0f, length);
        }

        public static float PingPong(float t, float length)
        {
            t = Repeat(t, length * 2f);
            return length - Abs(t - length);
        }

        public static float DeltaAngle(float current, float target)
        {
            float delta = Repeat(target - current, 360f);
            if (delta > 180f)
            {
                delta -= 360f;
            }

            return delta;
        }

        public static float LerpAngle(float a, float b, float t)
        {
            return a + DeltaAngle(a, b) * Clamp01(t);
        }

        public static float MoveTowards(float current, float target, float maxDelta)
        {
            if (Abs(target - current) <= maxDelta)
            {
                return target;
            }

            return current + Sign(target - current) * maxDelta;
        }

        public static float MoveTowardsAngle(float current, float target, float maxDelta)
        {
            float delta = DeltaAngle(current, target);
            if (-maxDelta < delta && delta < maxDelta)
            {
                return target;
            }

            target = current + delta;
            return MoveTowards(current, target, maxDelta);
        }

        public static bool Approximately(float a, float b)
        {
            return Abs(b - a) < Max(1e-6f * Max(Abs(a), Abs(b)), Epsilon * 8f);
        }
    }

    public static class Random
    {
        private static global::System.Random _random = new();

        public static float value => (float)_random.NextDouble();

        public static void InitState(int seed)
        {
            _random = new global::System.Random(seed);
        }

        public static int Range(int minInclusive, int maxExclusive)
        {
            return _random.Next(minInclusive, maxExclusive);
        }

        public static float Range(float minInclusive, float maxInclusive)
        {
            return minInclusive + ((float)_random.NextDouble() * (maxInclusive - minInclusive));
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

        public T? GetComponent<T>() where T : Component
        {
            return gameObject?.GetComponent<T>();
        }

        public Component? GetComponent(Type type)
        {
            ArgumentNullException.ThrowIfNull(type);
            return gameObject?.GetComponent(type);
        }

        public bool TryGetComponent<T>(out T? component) where T : Component
        {
            if (gameObject is GameObject owner)
            {
                return owner.TryGetComponent(out component);
            }

            component = null;
            return false;
        }

        public bool TryGetComponent(Type type, out Component? component)
        {
            ArgumentNullException.ThrowIfNull(type);
            if (gameObject is GameObject owner)
            {
                return owner.TryGetComponent(type, out component);
            }

            component = null;
            return false;
        }

        public T[] GetComponents<T>() where T : Component
        {
            return gameObject?.GetComponents<T>() ?? Array.Empty<T>();
        }

        public void GetComponents<T>(List<T> results) where T : Component
        {
            ArgumentNullException.ThrowIfNull(results);
            if (gameObject is GameObject owner)
            {
                owner.GetComponents(results);
                return;
            }

            results.Clear();
        }

        public Component[] GetComponents(Type type)
        {
            ArgumentNullException.ThrowIfNull(type);
            return gameObject?.GetComponents(type) ?? Array.Empty<Component>();
        }

        public void GetComponents(Type type, List<Component> results)
        {
            ArgumentNullException.ThrowIfNull(type);
            ArgumentNullException.ThrowIfNull(results);
            if (gameObject is GameObject owner)
            {
                owner.GetComponents(type, results);
                return;
            }

            results.Clear();
        }

        public T? GetComponentInChildren<T>() where T : Component
        {
            return GetComponentInChildren<T>(false);
        }

        public T? GetComponentInChildren<T>(bool includeInactive) where T : Component
        {
            return gameObject?.GetComponentInChildren<T>(includeInactive);
        }

        public bool TryGetComponentInChildren<T>(out T? component) where T : Component
        {
            return TryGetComponentInChildren(false, out component);
        }

        public bool TryGetComponentInChildren<T>(bool includeInactive, out T? component) where T : Component
        {
            if (gameObject is GameObject owner)
            {
                return owner.TryGetComponentInChildren(includeInactive, out component);
            }

            component = null;
            return false;
        }

        public Component? GetComponentInChildren(Type type)
        {
            ArgumentNullException.ThrowIfNull(type);
            return GetComponentInChildren(type, false);
        }

        public Component? GetComponentInChildren(Type type, bool includeInactive)
        {
            ArgumentNullException.ThrowIfNull(type);
            return gameObject?.GetComponentInChildren(type, includeInactive);
        }

        public bool TryGetComponentInChildren(Type type, out Component? component)
        {
            ArgumentNullException.ThrowIfNull(type);
            return TryGetComponentInChildren(type, false, out component);
        }

        public bool TryGetComponentInChildren(Type type, bool includeInactive, out Component? component)
        {
            ArgumentNullException.ThrowIfNull(type);
            if (gameObject is GameObject owner)
            {
                return owner.TryGetComponentInChildren(type, includeInactive, out component);
            }

            component = null;
            return false;
        }

        public T[] GetComponentsInChildren<T>() where T : Component
        {
            return GetComponentsInChildren<T>(false);
        }

        public T[] GetComponentsInChildren<T>(bool includeInactive) where T : Component
        {
            return gameObject?.GetComponentsInChildren<T>(includeInactive) ?? Array.Empty<T>();
        }

        public void GetComponentsInChildren<T>(List<T> results) where T : Component
        {
            GetComponentsInChildren(false, results);
        }

        public void GetComponentsInChildren<T>(bool includeInactive, List<T> results) where T : Component
        {
            ArgumentNullException.ThrowIfNull(results);
            if (gameObject is GameObject owner)
            {
                owner.GetComponentsInChildren(includeInactive, results);
                return;
            }

            results.Clear();
        }

        public Component[] GetComponentsInChildren(Type type)
        {
            ArgumentNullException.ThrowIfNull(type);
            return GetComponentsInChildren(type, false);
        }

        public Component[] GetComponentsInChildren(Type type, bool includeInactive)
        {
            ArgumentNullException.ThrowIfNull(type);
            return gameObject?.GetComponentsInChildren(type, includeInactive) ?? Array.Empty<Component>();
        }

        public void GetComponentsInChildren(Type type, List<Component> results)
        {
            GetComponentsInChildren(type, false, results);
        }

        public void GetComponentsInChildren(Type type, bool includeInactive, List<Component> results)
        {
            ArgumentNullException.ThrowIfNull(type);
            ArgumentNullException.ThrowIfNull(results);
            if (gameObject is GameObject owner)
            {
                owner.GetComponentsInChildren(type, includeInactive, results);
                return;
            }

            results.Clear();
        }

        public T? GetComponentInParent<T>() where T : Component
        {
            return GetComponentInParent<T>(false);
        }

        public T? GetComponentInParent<T>(bool includeInactive) where T : Component
        {
            return gameObject?.GetComponentInParent<T>(includeInactive);
        }

        public bool TryGetComponentInParent<T>(out T? component) where T : Component
        {
            return TryGetComponentInParent(false, out component);
        }

        public bool TryGetComponentInParent<T>(bool includeInactive, out T? component) where T : Component
        {
            if (gameObject is GameObject owner)
            {
                return owner.TryGetComponentInParent(includeInactive, out component);
            }

            component = null;
            return false;
        }

        public Component? GetComponentInParent(Type type)
        {
            ArgumentNullException.ThrowIfNull(type);
            return GetComponentInParent(type, false);
        }

        public Component? GetComponentInParent(Type type, bool includeInactive)
        {
            ArgumentNullException.ThrowIfNull(type);
            return gameObject?.GetComponentInParent(type, includeInactive);
        }

        public bool TryGetComponentInParent(Type type, out Component? component)
        {
            ArgumentNullException.ThrowIfNull(type);
            return TryGetComponentInParent(type, false, out component);
        }

        public bool TryGetComponentInParent(Type type, bool includeInactive, out Component? component)
        {
            ArgumentNullException.ThrowIfNull(type);
            if (gameObject is GameObject owner)
            {
                return owner.TryGetComponentInParent(type, includeInactive, out component);
            }

            component = null;
            return false;
        }

        public T[] GetComponentsInParent<T>() where T : Component
        {
            return GetComponentsInParent<T>(false);
        }

        public T[] GetComponentsInParent<T>(bool includeInactive) where T : Component
        {
            return gameObject?.GetComponentsInParent<T>(includeInactive) ?? Array.Empty<T>();
        }

        public void GetComponentsInParent<T>(List<T> results) where T : Component
        {
            GetComponentsInParent(false, results);
        }

        public void GetComponentsInParent<T>(bool includeInactive, List<T> results) where T : Component
        {
            ArgumentNullException.ThrowIfNull(results);
            if (gameObject is GameObject owner)
            {
                owner.GetComponentsInParent(includeInactive, results);
                return;
            }

            results.Clear();
        }

        public Component[] GetComponentsInParent(Type type)
        {
            ArgumentNullException.ThrowIfNull(type);
            return GetComponentsInParent(type, false);
        }

        public Component[] GetComponentsInParent(Type type, bool includeInactive)
        {
            ArgumentNullException.ThrowIfNull(type);
            return gameObject?.GetComponentsInParent(type, includeInactive) ?? Array.Empty<Component>();
        }

        public void GetComponentsInParent(Type type, List<Component> results)
        {
            GetComponentsInParent(type, false, results);
        }

        public void GetComponentsInParent(Type type, bool includeInactive, List<Component> results)
        {
            ArgumentNullException.ThrowIfNull(type);
            ArgumentNullException.ThrowIfNull(results);
            if (gameObject is GameObject owner)
            {
                owner.GetComponentsInParent(type, includeInactive, results);
                return;
            }

            results.Clear();
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
            return Managed.ManagedComponentBridge.TryGetGameObjectComponent(this, out component);
        }

        public bool TryGetComponent(Type type, out Component? component)
        {
            ArgumentNullException.ThrowIfNull(type);
            return Managed.ManagedComponentBridge.TryGetGameObjectComponent(this, type, out component);
        }

        public T[] GetComponents<T>() where T : Component
        {
            return Managed.ManagedComponentBridge.GetGameObjectComponents<T>(this);
        }

        public void GetComponents<T>(List<T> results) where T : Component
        {
            ArgumentNullException.ThrowIfNull(results);
            Managed.ManagedComponentBridge.GetGameObjectComponents(this, results);
        }

        public Component[] GetComponents(Type type)
        {
            ArgumentNullException.ThrowIfNull(type);
            return Managed.ManagedComponentBridge.GetGameObjectComponents(this, type);
        }

        public void GetComponents(Type type, List<Component> results)
        {
            ArgumentNullException.ThrowIfNull(type);
            ArgumentNullException.ThrowIfNull(results);
            Managed.ManagedComponentBridge.GetGameObjectComponents(this, type, results);
        }

        public T? GetComponentInChildren<T>() where T : Component
        {
            return GetComponentInChildren<T>(false);
        }

        public T? GetComponentInChildren<T>(bool includeInactive) where T : Component
        {
            return Managed.ManagedComponentBridge.GetGameObjectComponentInChildren<T>(this, includeInactive);
        }

        public bool TryGetComponentInChildren<T>(out T? component) where T : Component
        {
            return TryGetComponentInChildren(false, out component);
        }

        public bool TryGetComponentInChildren<T>(bool includeInactive, out T? component) where T : Component
        {
            return Managed.ManagedComponentBridge.TryGetGameObjectComponentInChildren(this, includeInactive, out component);
        }

        public Component? GetComponentInChildren(Type type)
        {
            ArgumentNullException.ThrowIfNull(type);
            return GetComponentInChildren(type, false);
        }

        public Component? GetComponentInChildren(Type type, bool includeInactive)
        {
            ArgumentNullException.ThrowIfNull(type);
            return Managed.ManagedComponentBridge.GetGameObjectComponentInChildren(this, type, includeInactive);
        }

        public bool TryGetComponentInChildren(Type type, out Component? component)
        {
            ArgumentNullException.ThrowIfNull(type);
            return TryGetComponentInChildren(type, false, out component);
        }

        public bool TryGetComponentInChildren(Type type, bool includeInactive, out Component? component)
        {
            ArgumentNullException.ThrowIfNull(type);
            return Managed.ManagedComponentBridge.TryGetGameObjectComponentInChildren(this, type, includeInactive, out component);
        }

        public T[] GetComponentsInChildren<T>() where T : Component
        {
            return GetComponentsInChildren<T>(false);
        }

        public T[] GetComponentsInChildren<T>(bool includeInactive) where T : Component
        {
            return Managed.ManagedComponentBridge.GetGameObjectComponentsInChildren<T>(this, includeInactive);
        }

        public void GetComponentsInChildren<T>(List<T> results) where T : Component
        {
            GetComponentsInChildren(false, results);
        }

        public void GetComponentsInChildren<T>(bool includeInactive, List<T> results) where T : Component
        {
            ArgumentNullException.ThrowIfNull(results);
            Managed.ManagedComponentBridge.GetGameObjectComponentsInChildren(this, includeInactive, results);
        }

        public Component[] GetComponentsInChildren(Type type)
        {
            ArgumentNullException.ThrowIfNull(type);
            return GetComponentsInChildren(type, false);
        }

        public Component[] GetComponentsInChildren(Type type, bool includeInactive)
        {
            ArgumentNullException.ThrowIfNull(type);
            return Managed.ManagedComponentBridge.GetGameObjectComponentsInChildren(this, type, includeInactive);
        }

        public void GetComponentsInChildren(Type type, List<Component> results)
        {
            GetComponentsInChildren(type, false, results);
        }

        public void GetComponentsInChildren(Type type, bool includeInactive, List<Component> results)
        {
            ArgumentNullException.ThrowIfNull(type);
            ArgumentNullException.ThrowIfNull(results);
            Managed.ManagedComponentBridge.GetGameObjectComponentsInChildren(this, type, includeInactive, results);
        }

        public T? GetComponentInParent<T>() where T : Component
        {
            return GetComponentInParent<T>(false);
        }

        public T? GetComponentInParent<T>(bool includeInactive) where T : Component
        {
            return Managed.ManagedComponentBridge.GetGameObjectComponentInParent<T>(this, includeInactive);
        }

        public bool TryGetComponentInParent<T>(out T? component) where T : Component
        {
            return TryGetComponentInParent(false, out component);
        }

        public bool TryGetComponentInParent<T>(bool includeInactive, out T? component) where T : Component
        {
            return Managed.ManagedComponentBridge.TryGetGameObjectComponentInParent(this, includeInactive, out component);
        }

        public Component? GetComponentInParent(Type type)
        {
            ArgumentNullException.ThrowIfNull(type);
            return GetComponentInParent(type, false);
        }

        public Component? GetComponentInParent(Type type, bool includeInactive)
        {
            ArgumentNullException.ThrowIfNull(type);
            return Managed.ManagedComponentBridge.GetGameObjectComponentInParent(this, type, includeInactive);
        }

        public bool TryGetComponentInParent(Type type, out Component? component)
        {
            ArgumentNullException.ThrowIfNull(type);
            return TryGetComponentInParent(type, false, out component);
        }

        public bool TryGetComponentInParent(Type type, bool includeInactive, out Component? component)
        {
            ArgumentNullException.ThrowIfNull(type);
            return Managed.ManagedComponentBridge.TryGetGameObjectComponentInParent(this, type, includeInactive, out component);
        }

        public T[] GetComponentsInParent<T>() where T : Component
        {
            return GetComponentsInParent<T>(false);
        }

        public T[] GetComponentsInParent<T>(bool includeInactive) where T : Component
        {
            return Managed.ManagedComponentBridge.GetGameObjectComponentsInParent<T>(this, includeInactive);
        }

        public void GetComponentsInParent<T>(List<T> results) where T : Component
        {
            GetComponentsInParent(false, results);
        }

        public void GetComponentsInParent<T>(bool includeInactive, List<T> results) where T : Component
        {
            ArgumentNullException.ThrowIfNull(results);
            Managed.ManagedComponentBridge.GetGameObjectComponentsInParent(this, includeInactive, results);
        }

        public Component[] GetComponentsInParent(Type type)
        {
            ArgumentNullException.ThrowIfNull(type);
            return GetComponentsInParent(type, false);
        }

        public Component[] GetComponentsInParent(Type type, bool includeInactive)
        {
            ArgumentNullException.ThrowIfNull(type);
            return Managed.ManagedComponentBridge.GetGameObjectComponentsInParent(this, type, includeInactive);
        }

        public void GetComponentsInParent(Type type, List<Component> results)
        {
            GetComponentsInParent(type, false, results);
        }

        public void GetComponentsInParent(Type type, bool includeInactive, List<Component> results)
        {
            ArgumentNullException.ThrowIfNull(type);
            ArgumentNullException.ThrowIfNull(results);
            Managed.ManagedComponentBridge.GetGameObjectComponentsInParent(this, type, includeInactive, results);
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
        public Matrix4x4 localToWorldMatrix => Matrix4x4.TRS(position, rotation, lossyScale);
        public Matrix4x4 worldToLocalMatrix => localToWorldMatrix.inverse;
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
        public bool hasChanged
        {
            get => Managed.NativeApi.GetTransformHasChanged(_gameObject.InstanceId);
            set => Managed.NativeApi.SetTransformHasChanged(_gameObject.InstanceId, value);
        }

        public Vector3 forward
        {
            get => rotation * ForwardAxis;
            set
            {
                if (value.sqrMagnitude <= 1e-12f)
                {
                    return;
                }

                rotation = Quaternion.LookRotation(value, up);
            }
        }

        public Vector3 right
        {
            get => rotation * RightAxis;
            set
            {
                if (value.sqrMagnitude <= 1e-12f)
                {
                    return;
                }

                Vector3 targetUp = up;
                Vector3 targetForward = Vector3.Cross(value.normalized, targetUp).normalized;
                if (targetForward.sqrMagnitude <= 1e-12f)
                {
                    return;
                }

                rotation = Quaternion.LookRotation(targetForward, targetUp);
            }
        }

        public Vector3 up
        {
            get => rotation * UpAxis;
            set
            {
                if (value.sqrMagnitude <= 1e-12f)
                {
                    return;
                }

                rotation = Quaternion.LookRotation(forward, value);
            }
        }

        public Vector3 localForward => localRotation * ForwardAxis;
        public Vector3 localRight => localRotation * RightAxis;
        public Vector3 localUp => localRotation * UpAxis;

        public void Translate(Vector3 translation)
        {
            Translate(translation, Space.Self);
        }

        public void Translate(Vector3 translation, Space relativeTo = Space.Self)
        {
            if (relativeTo == Space.Self)
            {
                Managed.NativeApi.TranslateLocal(_gameObject.InstanceId, translation);
                return;
            }

            Managed.NativeApi.Translate(_gameObject.InstanceId, translation);
        }

        public void Translate(float x, float y, float z)
        {
            Translate(new Vector3(x, y, z));
        }

        public void Translate(float x, float y, float z, Space relativeTo = Space.Self)
        {
            Translate(new Vector3(x, y, z), relativeTo);
        }

        public void Translate(Vector3 translation, Transform? relativeTo)
        {
            if (relativeTo is null)
            {
                Managed.NativeApi.Translate(_gameObject.InstanceId, translation);
                return;
            }

            Managed.NativeApi.Translate(_gameObject.InstanceId, relativeTo.TransformDirection(translation));
        }

        public void Translate(float x, float y, float z, Transform? relativeTo)
        {
            Translate(new Vector3(x, y, z), relativeTo);
        }

        public void SetPositionAndRotation(Vector3 position, Quaternion rotation)
        {
            this.position = position;
            this.rotation = rotation;
        }

        public void GetPositionAndRotation(out Vector3 position, out Quaternion rotation)
        {
            position = this.position;
            rotation = this.rotation;
        }

        public void SetLocalPositionAndRotation(Vector3 localPosition, Quaternion localRotation)
        {
            this.localPosition = localPosition;
            this.localRotation = localRotation;
        }

        public void GetLocalPositionAndRotation(out Vector3 localPosition, out Quaternion localRotation)
        {
            localPosition = this.localPosition;
            localRotation = this.localRotation;
        }

        public void TranslateLocal(Vector3 delta)
        {
            Managed.NativeApi.TranslateLocal(_gameObject.InstanceId, delta);
        }

        public void Rotate(Vector3 eulerAngles)
        {
            Rotate(eulerAngles, Space.Self);
        }

        public void Rotate(Vector3 eulerAngles, Space relativeTo = Space.Self)
        {
            if (relativeTo == Space.Self)
            {
                Managed.NativeApi.Rotate(_gameObject.InstanceId, eulerAngles);
                return;
            }

            rotation = Quaternion.Euler(eulerAngles) * rotation;
        }

        public void Rotate(float xAngle, float yAngle, float zAngle)
        {
            Rotate(new Vector3(xAngle, yAngle, zAngle));
        }

        public void Rotate(float xAngle, float yAngle, float zAngle, Space relativeTo = Space.Self)
        {
            Rotate(new Vector3(xAngle, yAngle, zAngle), relativeTo);
        }

        public void Rotate(Vector3 axis, float angle)
        {
            Rotate(axis, angle, Space.Self);
        }

        public void Rotate(Vector3 axis, float angle, Space relativeTo)
        {
            if (relativeTo == Space.Self)
            {
                Managed.NativeApi.Rotate(_gameObject.InstanceId, axis, angle);
                return;
            }

            rotation = Quaternion.AngleAxis(angle, axis) * rotation;
        }

        public void RotateAround(Vector3 point, Vector3 axis, float angle)
        {
            Managed.NativeApi.RotateAround(_gameObject.InstanceId, point, axis, angle);
        }

        public void LookAt(Vector3 target)
        {
            LookAt(target, UpAxis);
        }

        public void LookAt(Transform target)
        {
            ArgumentNullException.ThrowIfNull(target);
            LookAt(target.position, UpAxis);
        }

        public void LookAt(Transform target, Vector3 worldUp)
        {
            ArgumentNullException.ThrowIfNull(target);
            LookAt(target.position, worldUp);
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

    public sealed class Camera : Behaviour
    {
        private readonly GameObject _gameObject;
        private readonly long _componentId;

        internal Camera(GameObject gameObject, long componentId)
        {
            _gameObject = gameObject;
            _componentId = componentId;
        }

        public static Camera? main => Managed.ManagedComponentBridge.GetMainCamera();
        public override GameObject gameObject => _gameObject;

        public override bool enabled
        {
            get => Managed.NativeApi.GetComponentEnabled(_componentId);
            set => Managed.NativeApi.SetComponentEnabled(_componentId, value);
        }

        public override long GetInstanceID()
        {
            return _componentId;
        }

        public CameraProjection projectionMode
        {
            get => Managed.NativeApi.GetCameraProjectionMode(_componentId);
            set => Managed.NativeApi.SetCameraProjectionMode(_componentId, value);
        }

        public bool orthographic
        {
            get => projectionMode == CameraProjection.Orthographic;
            set => projectionMode = value ? CameraProjection.Orthographic : CameraProjection.Perspective;
        }

        public float fieldOfView
        {
            get => Managed.NativeApi.GetCameraFieldOfView(_componentId);
            set => Managed.NativeApi.SetCameraFieldOfView(_componentId, value);
        }

        public float aspect
        {
            get => Managed.NativeApi.GetCameraAspect(_componentId);
            set => Managed.NativeApi.SetCameraAspect(_componentId, value);
        }

        public float orthographicSize
        {
            get => Managed.NativeApi.GetCameraOrthographicSize(_componentId);
            set => Managed.NativeApi.SetCameraOrthographicSize(_componentId, value);
        }

        public float nearClipPlane
        {
            get => Managed.NativeApi.GetCameraNearClipPlane(_componentId);
            set => Managed.NativeApi.SetCameraNearClipPlane(_componentId, value);
        }

        public float farClipPlane
        {
            get => Managed.NativeApi.GetCameraFarClipPlane(_componentId);
            set => Managed.NativeApi.SetCameraFarClipPlane(_componentId, value);
        }

        public float depth
        {
            get => Managed.NativeApi.GetCameraDepth(_componentId);
            set => Managed.NativeApi.SetCameraDepth(_componentId, value);
        }

        public int cullingMask
        {
            get => Managed.NativeApi.GetCameraCullingMask(_componentId);
            set => Managed.NativeApi.SetCameraCullingMask(_componentId, value);
        }

        public CameraClearFlags clearFlags
        {
            get => Managed.NativeApi.GetCameraClearFlags(_componentId);
            set => Managed.NativeApi.SetCameraClearFlags(_componentId, value);
        }

        public Color backgroundColor
        {
            get => Managed.NativeApi.GetCameraBackgroundColor(_componentId);
            set => Managed.NativeApi.SetCameraBackgroundColor(_componentId, value);
        }

        public int pixelWidth => Managed.NativeApi.GetCameraPixelWidth(_componentId);
        public int pixelHeight => Managed.NativeApi.GetCameraPixelHeight(_componentId);

        public Vector3 ScreenToWorldPoint(Vector3 position)
        {
            return Managed.NativeApi.CameraScreenToWorldPoint(_componentId, position);
        }

        public Vector3 WorldToScreenPoint(Vector3 position)
        {
            return Managed.NativeApi.CameraWorldToScreenPoint(_componentId, position);
        }

        public Ray ScreenPointToRay(Vector3 position)
        {
            return ScreenPointToRay(new Vector2(position.X, position.Y));
        }

        public Ray ScreenPointToRay(Vector2 position)
        {
            return Managed.NativeApi.CameraScreenPointToRay(_componentId, position);
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

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        private delegate int GetTransformHasChangedDelegate(long gameObjectId, out int hasChanged);

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        private delegate int SetTransformHasChangedDelegate(long gameObjectId, int hasChanged);

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        private delegate int GetComponentEnabledDelegate(long componentId, out int enabled);

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        private delegate long AddCameraComponentDelegate(long gameObjectId);

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        private delegate long GetCameraComponentIdDelegate(long gameObjectId);

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        private delegate long GetMainCameraGameObjectIdDelegate();

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        private delegate int GetCameraProjectionModeDelegate(long componentId, out int mode);

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        private delegate int SetCameraProjectionModeDelegate(long componentId, int mode);

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        private delegate int GetCameraFloatDelegate(long componentId, out float value);

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        private delegate int SetCameraFloatDelegate(long componentId, float value);

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        private delegate int GetCameraIntDelegate(long componentId, out int value);

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        private delegate int SetCameraIntDelegate(long componentId, int value);

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        private delegate int GetCameraColorDelegate(long componentId, out float r, out float g, out float b, out float a);

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        private delegate int SetCameraColorDelegate(long componentId, float r, float g, float b, float a);

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        private delegate int CameraScreenToWorldPointDelegate(
            long componentId,
            float x,
            float y,
            float z,
            out float outX,
            out float outY,
            out float outZ);

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        private delegate int CameraWorldToScreenPointDelegate(
            long componentId,
            float x,
            float y,
            float z,
            out float outX,
            out float outY,
            out float outZ);

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        private delegate int CameraScreenPointToRayDelegate(
            long componentId,
            float x,
            float y,
            out float originX,
            out float originY,
            out float originZ,
            out float directionX,
            out float directionY,
            out float directionZ);

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
        private static GetTransformHasChangedDelegate? _getTransformHasChanged;
        private static SetTransformHasChangedDelegate? _setTransformHasChanged;
        private static GetComponentEnabledDelegate? _getComponentEnabled;
        private static AddCameraComponentDelegate? _addCameraComponent;
        private static GetCameraComponentIdDelegate? _getCameraComponentId;
        private static GetMainCameraGameObjectIdDelegate? _getMainCameraGameObjectId;
        private static GetCameraProjectionModeDelegate? _getCameraProjectionMode;
        private static SetCameraProjectionModeDelegate? _setCameraProjectionMode;
        private static GetCameraFloatDelegate? _getCameraFieldOfView;
        private static SetCameraFloatDelegate? _setCameraFieldOfView;
        private static GetCameraFloatDelegate? _getCameraAspect;
        private static SetCameraFloatDelegate? _setCameraAspect;
        private static GetCameraFloatDelegate? _getCameraOrthographicSize;
        private static SetCameraFloatDelegate? _setCameraOrthographicSize;
        private static GetCameraFloatDelegate? _getCameraNearClipPlane;
        private static SetCameraFloatDelegate? _setCameraNearClipPlane;
        private static GetCameraFloatDelegate? _getCameraFarClipPlane;
        private static SetCameraFloatDelegate? _setCameraFarClipPlane;
        private static GetCameraFloatDelegate? _getCameraDepth;
        private static SetCameraFloatDelegate? _setCameraDepth;
        private static GetCameraIntDelegate? _getCameraCullingMask;
        private static SetCameraIntDelegate? _setCameraCullingMask;
        private static GetCameraIntDelegate? _getCameraClearFlags;
        private static SetCameraIntDelegate? _setCameraClearFlags;
        private static GetCameraColorDelegate? _getCameraBackgroundColor;
        private static SetCameraColorDelegate? _setCameraBackgroundColor;
        private static GetCameraIntDelegate? _getCameraPixelWidth;
        private static GetCameraIntDelegate? _getCameraPixelHeight;
        private static CameraScreenToWorldPointDelegate? _cameraScreenToWorldPoint;
        private static CameraWorldToScreenPointDelegate? _cameraWorldToScreenPoint;
        private static CameraScreenPointToRayDelegate? _cameraScreenPointToRay;

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
            IntPtr detachChildrenFn,
            IntPtr getTransformHasChangedFn,
            IntPtr setTransformHasChangedFn,
            IntPtr getComponentEnabledFn,
            IntPtr addCameraComponentFn,
            IntPtr getCameraComponentIdFn,
            IntPtr getMainCameraGameObjectIdFn,
            IntPtr getCameraProjectionModeFn,
            IntPtr setCameraProjectionModeFn,
            IntPtr getCameraFieldOfViewFn,
            IntPtr setCameraFieldOfViewFn,
            IntPtr getCameraAspectFn,
            IntPtr setCameraAspectFn,
            IntPtr getCameraOrthographicSizeFn,
            IntPtr setCameraOrthographicSizeFn,
            IntPtr getCameraNearClipPlaneFn,
            IntPtr setCameraNearClipPlaneFn,
            IntPtr getCameraFarClipPlaneFn,
            IntPtr setCameraFarClipPlaneFn,
            IntPtr getCameraDepthFn,
            IntPtr setCameraDepthFn,
            IntPtr getCameraCullingMaskFn,
            IntPtr setCameraCullingMaskFn,
            IntPtr getCameraClearFlagsFn,
            IntPtr setCameraClearFlagsFn,
            IntPtr getCameraBackgroundColorFn,
            IntPtr setCameraBackgroundColorFn,
            IntPtr getCameraPixelWidthFn,
            IntPtr getCameraPixelHeightFn,
            IntPtr cameraScreenToWorldPointFn,
            IntPtr cameraWorldToScreenPointFn,
            IntPtr cameraScreenPointToRayFn)
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
                setSiblingIndexFn == IntPtr.Zero || detachChildrenFn == IntPtr.Zero ||
                getTransformHasChangedFn == IntPtr.Zero || setTransformHasChangedFn == IntPtr.Zero ||
                getComponentEnabledFn == IntPtr.Zero || addCameraComponentFn == IntPtr.Zero ||
                getCameraComponentIdFn == IntPtr.Zero || getMainCameraGameObjectIdFn == IntPtr.Zero ||
                getCameraProjectionModeFn == IntPtr.Zero || setCameraProjectionModeFn == IntPtr.Zero ||
                getCameraFieldOfViewFn == IntPtr.Zero || setCameraFieldOfViewFn == IntPtr.Zero ||
                getCameraAspectFn == IntPtr.Zero || setCameraAspectFn == IntPtr.Zero ||
                getCameraOrthographicSizeFn == IntPtr.Zero || setCameraOrthographicSizeFn == IntPtr.Zero ||
                getCameraNearClipPlaneFn == IntPtr.Zero || setCameraNearClipPlaneFn == IntPtr.Zero ||
                getCameraFarClipPlaneFn == IntPtr.Zero || setCameraFarClipPlaneFn == IntPtr.Zero ||
                getCameraDepthFn == IntPtr.Zero || setCameraDepthFn == IntPtr.Zero ||
                getCameraCullingMaskFn == IntPtr.Zero || setCameraCullingMaskFn == IntPtr.Zero ||
                getCameraClearFlagsFn == IntPtr.Zero || setCameraClearFlagsFn == IntPtr.Zero ||
                getCameraBackgroundColorFn == IntPtr.Zero || setCameraBackgroundColorFn == IntPtr.Zero ||
                getCameraPixelWidthFn == IntPtr.Zero || getCameraPixelHeightFn == IntPtr.Zero ||
                cameraScreenToWorldPointFn == IntPtr.Zero || cameraWorldToScreenPointFn == IntPtr.Zero ||
                cameraScreenPointToRayFn == IntPtr.Zero)
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
            _getTransformHasChanged =
                Marshal.GetDelegateForFunctionPointer<GetTransformHasChangedDelegate>(getTransformHasChangedFn);
            _setTransformHasChanged =
                Marshal.GetDelegateForFunctionPointer<SetTransformHasChangedDelegate>(setTransformHasChangedFn);
            _getComponentEnabled =
                Marshal.GetDelegateForFunctionPointer<GetComponentEnabledDelegate>(getComponentEnabledFn);
            _addCameraComponent =
                Marshal.GetDelegateForFunctionPointer<AddCameraComponentDelegate>(addCameraComponentFn);
            _getCameraComponentId =
                Marshal.GetDelegateForFunctionPointer<GetCameraComponentIdDelegate>(getCameraComponentIdFn);
            _getMainCameraGameObjectId =
                Marshal.GetDelegateForFunctionPointer<GetMainCameraGameObjectIdDelegate>(getMainCameraGameObjectIdFn);
            _getCameraProjectionMode =
                Marshal.GetDelegateForFunctionPointer<GetCameraProjectionModeDelegate>(getCameraProjectionModeFn);
            _setCameraProjectionMode =
                Marshal.GetDelegateForFunctionPointer<SetCameraProjectionModeDelegate>(setCameraProjectionModeFn);
            _getCameraFieldOfView =
                Marshal.GetDelegateForFunctionPointer<GetCameraFloatDelegate>(getCameraFieldOfViewFn);
            _setCameraFieldOfView =
                Marshal.GetDelegateForFunctionPointer<SetCameraFloatDelegate>(setCameraFieldOfViewFn);
            _getCameraAspect =
                Marshal.GetDelegateForFunctionPointer<GetCameraFloatDelegate>(getCameraAspectFn);
            _setCameraAspect =
                Marshal.GetDelegateForFunctionPointer<SetCameraFloatDelegate>(setCameraAspectFn);
            _getCameraOrthographicSize =
                Marshal.GetDelegateForFunctionPointer<GetCameraFloatDelegate>(getCameraOrthographicSizeFn);
            _setCameraOrthographicSize =
                Marshal.GetDelegateForFunctionPointer<SetCameraFloatDelegate>(setCameraOrthographicSizeFn);
            _getCameraNearClipPlane =
                Marshal.GetDelegateForFunctionPointer<GetCameraFloatDelegate>(getCameraNearClipPlaneFn);
            _setCameraNearClipPlane =
                Marshal.GetDelegateForFunctionPointer<SetCameraFloatDelegate>(setCameraNearClipPlaneFn);
            _getCameraFarClipPlane =
                Marshal.GetDelegateForFunctionPointer<GetCameraFloatDelegate>(getCameraFarClipPlaneFn);
            _setCameraFarClipPlane =
                Marshal.GetDelegateForFunctionPointer<SetCameraFloatDelegate>(setCameraFarClipPlaneFn);
            _getCameraDepth =
                Marshal.GetDelegateForFunctionPointer<GetCameraFloatDelegate>(getCameraDepthFn);
            _setCameraDepth =
                Marshal.GetDelegateForFunctionPointer<SetCameraFloatDelegate>(setCameraDepthFn);
            _getCameraCullingMask =
                Marshal.GetDelegateForFunctionPointer<GetCameraIntDelegate>(getCameraCullingMaskFn);
            _setCameraCullingMask =
                Marshal.GetDelegateForFunctionPointer<SetCameraIntDelegate>(setCameraCullingMaskFn);
            _getCameraClearFlags =
                Marshal.GetDelegateForFunctionPointer<GetCameraIntDelegate>(getCameraClearFlagsFn);
            _setCameraClearFlags =
                Marshal.GetDelegateForFunctionPointer<SetCameraIntDelegate>(setCameraClearFlagsFn);
            _getCameraBackgroundColor =
                Marshal.GetDelegateForFunctionPointer<GetCameraColorDelegate>(getCameraBackgroundColorFn);
            _setCameraBackgroundColor =
                Marshal.GetDelegateForFunctionPointer<SetCameraColorDelegate>(setCameraBackgroundColorFn);
            _getCameraPixelWidth =
                Marshal.GetDelegateForFunctionPointer<GetCameraIntDelegate>(getCameraPixelWidthFn);
            _getCameraPixelHeight =
                Marshal.GetDelegateForFunctionPointer<GetCameraIntDelegate>(getCameraPixelHeightFn);
            _cameraScreenToWorldPoint =
                Marshal.GetDelegateForFunctionPointer<CameraScreenToWorldPointDelegate>(cameraScreenToWorldPointFn);
            _cameraWorldToScreenPoint =
                Marshal.GetDelegateForFunctionPointer<CameraWorldToScreenPointDelegate>(cameraWorldToScreenPointFn);
            _cameraScreenPointToRay =
                Marshal.GetDelegateForFunctionPointer<CameraScreenPointToRayDelegate>(cameraScreenPointToRayFn);
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

        public static bool GetComponentEnabled(long componentId)
        {
            GetComponentEnabledDelegate callback =
                _getComponentEnabled ?? throw new InvalidOperationException("Native Component.enabled getter is not registered.");
            if (callback(componentId, out int enabled) != 0)
            {
                throw new InvalidOperationException($"Failed to read enabled state for Component {componentId}.");
            }

            return enabled != 0;
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

        public static long AddCameraComponent(long gameObjectId)
        {
            AddCameraComponentDelegate callback =
                _addCameraComponent ?? throw new InvalidOperationException("Native GameObject.AddComponent(Camera) is not registered.");
            return callback(gameObjectId);
        }

        public static long GetCameraComponentId(long gameObjectId)
        {
            GetCameraComponentIdDelegate callback =
                _getCameraComponentId ?? throw new InvalidOperationException("Native GameObject.GetComponent(Camera) is not registered.");
            return callback(gameObjectId);
        }

        public static long GetMainCameraGameObjectId()
        {
            GetMainCameraGameObjectIdDelegate callback =
                _getMainCameraGameObjectId ?? throw new InvalidOperationException("Native Camera.main is not registered.");
            return callback();
        }

        public static CameraProjection GetCameraProjectionMode(long componentId)
        {
            GetCameraProjectionModeDelegate callback =
                _getCameraProjectionMode ?? throw new InvalidOperationException("Native Camera.projectionMode getter is not registered.");
            if (callback(componentId, out int mode) != 0)
            {
                throw new InvalidOperationException($"Failed to read projection mode for Camera {componentId}.");
            }

            return (CameraProjection)mode;
        }

        public static void SetCameraProjectionMode(long componentId, CameraProjection mode)
        {
            SetCameraProjectionModeDelegate callback =
                _setCameraProjectionMode ?? throw new InvalidOperationException("Native Camera.projectionMode setter is not registered.");
            if (callback(componentId, (int)mode) != 0)
            {
                throw new InvalidOperationException($"Failed to set projection mode for Camera {componentId}.");
            }
        }

        public static float GetCameraFieldOfView(long componentId)
        {
            GetCameraFloatDelegate callback =
                _getCameraFieldOfView ?? throw new InvalidOperationException("Native Camera.fieldOfView getter is not registered.");
            if (callback(componentId, out float value) != 0)
            {
                throw new InvalidOperationException($"Failed to read fieldOfView for Camera {componentId}.");
            }

            return value;
        }

        public static void SetCameraFieldOfView(long componentId, float value)
        {
            SetCameraFloatDelegate callback =
                _setCameraFieldOfView ?? throw new InvalidOperationException("Native Camera.fieldOfView setter is not registered.");
            if (callback(componentId, value) != 0)
            {
                throw new InvalidOperationException($"Failed to set fieldOfView for Camera {componentId}.");
            }
        }

        public static float GetCameraAspect(long componentId)
        {
            GetCameraFloatDelegate callback =
                _getCameraAspect ?? throw new InvalidOperationException("Native Camera.aspect getter is not registered.");
            if (callback(componentId, out float value) != 0)
            {
                throw new InvalidOperationException($"Failed to read aspect for Camera {componentId}.");
            }

            return value;
        }

        public static void SetCameraAspect(long componentId, float value)
        {
            SetCameraFloatDelegate callback =
                _setCameraAspect ?? throw new InvalidOperationException("Native Camera.aspect setter is not registered.");
            if (callback(componentId, value) != 0)
            {
                throw new InvalidOperationException($"Failed to set aspect for Camera {componentId}.");
            }
        }

        public static float GetCameraOrthographicSize(long componentId)
        {
            GetCameraFloatDelegate callback =
                _getCameraOrthographicSize ?? throw new InvalidOperationException("Native Camera.orthographicSize getter is not registered.");
            if (callback(componentId, out float value) != 0)
            {
                throw new InvalidOperationException($"Failed to read orthographicSize for Camera {componentId}.");
            }

            return value;
        }

        public static void SetCameraOrthographicSize(long componentId, float value)
        {
            SetCameraFloatDelegate callback =
                _setCameraOrthographicSize ?? throw new InvalidOperationException("Native Camera.orthographicSize setter is not registered.");
            if (callback(componentId, value) != 0)
            {
                throw new InvalidOperationException($"Failed to set orthographicSize for Camera {componentId}.");
            }
        }

        public static float GetCameraNearClipPlane(long componentId)
        {
            GetCameraFloatDelegate callback =
                _getCameraNearClipPlane ?? throw new InvalidOperationException("Native Camera.nearClipPlane getter is not registered.");
            if (callback(componentId, out float value) != 0)
            {
                throw new InvalidOperationException($"Failed to read nearClipPlane for Camera {componentId}.");
            }

            return value;
        }

        public static void SetCameraNearClipPlane(long componentId, float value)
        {
            SetCameraFloatDelegate callback =
                _setCameraNearClipPlane ?? throw new InvalidOperationException("Native Camera.nearClipPlane setter is not registered.");
            if (callback(componentId, value) != 0)
            {
                throw new InvalidOperationException($"Failed to set nearClipPlane for Camera {componentId}.");
            }
        }

        public static float GetCameraFarClipPlane(long componentId)
        {
            GetCameraFloatDelegate callback =
                _getCameraFarClipPlane ?? throw new InvalidOperationException("Native Camera.farClipPlane getter is not registered.");
            if (callback(componentId, out float value) != 0)
            {
                throw new InvalidOperationException($"Failed to read farClipPlane for Camera {componentId}.");
            }

            return value;
        }

        public static void SetCameraFarClipPlane(long componentId, float value)
        {
            SetCameraFloatDelegate callback =
                _setCameraFarClipPlane ?? throw new InvalidOperationException("Native Camera.farClipPlane setter is not registered.");
            if (callback(componentId, value) != 0)
            {
                throw new InvalidOperationException($"Failed to set farClipPlane for Camera {componentId}.");
            }
        }

        public static float GetCameraDepth(long componentId)
        {
            GetCameraFloatDelegate callback =
                _getCameraDepth ?? throw new InvalidOperationException("Native Camera.depth getter is not registered.");
            if (callback(componentId, out float value) != 0)
            {
                throw new InvalidOperationException($"Failed to read depth for Camera {componentId}.");
            }

            return value;
        }

        public static void SetCameraDepth(long componentId, float value)
        {
            SetCameraFloatDelegate callback =
                _setCameraDepth ?? throw new InvalidOperationException("Native Camera.depth setter is not registered.");
            if (callback(componentId, value) != 0)
            {
                throw new InvalidOperationException($"Failed to set depth for Camera {componentId}.");
            }
        }

        public static int GetCameraCullingMask(long componentId)
        {
            GetCameraIntDelegate callback =
                _getCameraCullingMask ?? throw new InvalidOperationException("Native Camera.cullingMask getter is not registered.");
            if (callback(componentId, out int value) != 0)
            {
                throw new InvalidOperationException($"Failed to read cullingMask for Camera {componentId}.");
            }

            return value;
        }

        public static void SetCameraCullingMask(long componentId, int value)
        {
            SetCameraIntDelegate callback =
                _setCameraCullingMask ?? throw new InvalidOperationException("Native Camera.cullingMask setter is not registered.");
            if (callback(componentId, value) != 0)
            {
                throw new InvalidOperationException($"Failed to set cullingMask for Camera {componentId}.");
            }
        }

        public static CameraClearFlags GetCameraClearFlags(long componentId)
        {
            GetCameraIntDelegate callback =
                _getCameraClearFlags ?? throw new InvalidOperationException("Native Camera.clearFlags getter is not registered.");
            if (callback(componentId, out int value) != 0)
            {
                throw new InvalidOperationException($"Failed to read clearFlags for Camera {componentId}.");
            }

            return (CameraClearFlags)value;
        }

        public static void SetCameraClearFlags(long componentId, CameraClearFlags value)
        {
            SetCameraIntDelegate callback =
                _setCameraClearFlags ?? throw new InvalidOperationException("Native Camera.clearFlags setter is not registered.");
            if (callback(componentId, (int)value) != 0)
            {
                throw new InvalidOperationException($"Failed to set clearFlags for Camera {componentId}.");
            }
        }

        public static Color GetCameraBackgroundColor(long componentId)
        {
            GetCameraColorDelegate callback =
                _getCameraBackgroundColor ?? throw new InvalidOperationException("Native Camera.backgroundColor getter is not registered.");
            if (callback(componentId, out float r, out float g, out float b, out float a) != 0)
            {
                throw new InvalidOperationException($"Failed to read backgroundColor for Camera {componentId}.");
            }

            return new Color(r, g, b, a);
        }

        public static void SetCameraBackgroundColor(long componentId, Color value)
        {
            SetCameraColorDelegate callback =
                _setCameraBackgroundColor ?? throw new InvalidOperationException("Native Camera.backgroundColor setter is not registered.");
            if (callback(componentId, value.r, value.g, value.b, value.a) != 0)
            {
                throw new InvalidOperationException($"Failed to set backgroundColor for Camera {componentId}.");
            }
        }

        public static int GetCameraPixelWidth(long componentId)
        {
            GetCameraIntDelegate callback =
                _getCameraPixelWidth ?? throw new InvalidOperationException("Native Camera.pixelWidth getter is not registered.");
            if (callback(componentId, out int value) != 0)
            {
                throw new InvalidOperationException($"Failed to read pixelWidth for Camera {componentId}.");
            }

            return value;
        }

        public static int GetCameraPixelHeight(long componentId)
        {
            GetCameraIntDelegate callback =
                _getCameraPixelHeight ?? throw new InvalidOperationException("Native Camera.pixelHeight getter is not registered.");
            if (callback(componentId, out int value) != 0)
            {
                throw new InvalidOperationException($"Failed to read pixelHeight for Camera {componentId}.");
            }

            return value;
        }

        public static Vector3 CameraScreenToWorldPoint(long componentId, Vector3 position)
        {
            CameraScreenToWorldPointDelegate callback =
                _cameraScreenToWorldPoint ?? throw new InvalidOperationException("Native Camera.ScreenToWorldPoint is not registered.");
            if (callback(componentId, position.X, position.Y, position.Z, out float x, out float y, out float z) != 0)
            {
                throw new InvalidOperationException($"Failed to convert screen point to world point for Camera {componentId}.");
            }

            return new Vector3(x, y, z);
        }

        public static Vector3 CameraWorldToScreenPoint(long componentId, Vector3 position)
        {
            CameraWorldToScreenPointDelegate callback =
                _cameraWorldToScreenPoint ?? throw new InvalidOperationException("Native Camera.WorldToScreenPoint is not registered.");
            if (callback(componentId, position.X, position.Y, position.Z, out float x, out float y, out float z) != 0)
            {
                throw new InvalidOperationException($"Failed to convert world point to screen point for Camera {componentId}.");
            }

            return new Vector3(x, y, z);
        }

        public static Ray CameraScreenPointToRay(long componentId, Vector2 position)
        {
            CameraScreenPointToRayDelegate callback =
                _cameraScreenPointToRay ?? throw new InvalidOperationException("Native Camera.ScreenPointToRay is not registered.");
            if (callback(
                    componentId,
                    position.X,
                    position.Y,
                    out float originX,
                    out float originY,
                    out float originZ,
                    out float directionX,
                    out float directionY,
                    out float directionZ) != 0)
            {
                throw new InvalidOperationException($"Failed to build screen ray for Camera {componentId}.");
            }

            return new Ray(
                new Vector3(originX, originY, originZ),
                new Vector3(directionX, directionY, directionZ));
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

        public static bool GetTransformHasChanged(long gameObjectId)
        {
            GetTransformHasChangedDelegate callback =
                _getTransformHasChanged ?? throw new InvalidOperationException("Native transform.hasChanged getter is not registered.");
            if (callback(gameObjectId, out int hasChanged) != 0)
            {
                throw new InvalidOperationException($"Failed to read hasChanged for GameObject {gameObjectId}.");
            }

            return hasChanged != 0;
        }

        public static void SetTransformHasChanged(long gameObjectId, bool hasChanged)
        {
            SetTransformHasChangedDelegate callback =
                _setTransformHasChanged ?? throw new InvalidOperationException("Native transform.hasChanged setter is not registered.");
            if (callback(gameObjectId, hasChanged ? 1 : 0) != 0)
            {
                throw new InvalidOperationException($"Failed to write hasChanged for GameObject {gameObjectId}.");
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
        private static readonly Dictionary<long, Camera> NativeCameras = new();
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
            IntPtr getTransformHasChangedFn,
            IntPtr setTransformHasChangedFn,
            IntPtr getComponentEnabledFn,
            IntPtr addCameraComponentFn,
            IntPtr getCameraComponentIdFn,
            IntPtr getMainCameraGameObjectIdFn,
            IntPtr getCameraProjectionModeFn,
            IntPtr setCameraProjectionModeFn,
            IntPtr getCameraFieldOfViewFn,
            IntPtr setCameraFieldOfViewFn,
            IntPtr getCameraAspectFn,
            IntPtr setCameraAspectFn,
            IntPtr getCameraOrthographicSizeFn,
            IntPtr setCameraOrthographicSizeFn,
            IntPtr getCameraNearClipPlaneFn,
            IntPtr setCameraNearClipPlaneFn,
            IntPtr getCameraFarClipPlaneFn,
            IntPtr setCameraFarClipPlaneFn,
            IntPtr getCameraDepthFn,
            IntPtr setCameraDepthFn,
            IntPtr getCameraCullingMaskFn,
            IntPtr setCameraCullingMaskFn,
            IntPtr getCameraClearFlagsFn,
            IntPtr setCameraClearFlagsFn,
            IntPtr getCameraBackgroundColorFn,
            IntPtr setCameraBackgroundColorFn,
            IntPtr getCameraPixelWidthFn,
            IntPtr getCameraPixelHeightFn,
            IntPtr cameraScreenToWorldPointFn,
            IntPtr cameraWorldToScreenPointFn,
            IntPtr cameraScreenPointToRayFn,
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
                    detachChildrenFn,
                    getTransformHasChangedFn,
                    setTransformHasChangedFn,
                    getComponentEnabledFn,
                    addCameraComponentFn,
                    getCameraComponentIdFn,
                    getMainCameraGameObjectIdFn,
                    getCameraProjectionModeFn,
                    setCameraProjectionModeFn,
                    getCameraFieldOfViewFn,
                    setCameraFieldOfViewFn,
                    getCameraAspectFn,
                    setCameraAspectFn,
                    getCameraOrthographicSizeFn,
                    setCameraOrthographicSizeFn,
                    getCameraNearClipPlaneFn,
                    setCameraNearClipPlaneFn,
                    getCameraFarClipPlaneFn,
                    setCameraFarClipPlaneFn,
                    getCameraDepthFn,
                    setCameraDepthFn,
                    getCameraCullingMaskFn,
                    setCameraCullingMaskFn,
                    getCameraClearFlagsFn,
                    setCameraClearFlagsFn,
                    getCameraBackgroundColorFn,
                    setCameraBackgroundColorFn,
                    getCameraPixelWidthFn,
                    getCameraPixelHeightFn,
                    cameraScreenToWorldPointFn,
                    cameraWorldToScreenPointFn,
                    cameraScreenPointToRayFn);
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
                Camera camera => (T?)(Object?)InstantiateCamera(camera, parent),
                MonoBehaviour behaviour => InstantiateMonoBehaviour(original, behaviour, parent),
                _ => throw new NotSupportedException(
                    $"Instantiate does not support '{original.GetType().FullName}'."),
            };
        }

        internal static Component? AddGameObjectComponent(GameObject gameObject, Type type)
        {
            ArgumentNullException.ThrowIfNull(gameObject);
            ArgumentNullException.ThrowIfNull(type);

            if (type == typeof(Camera))
            {
                long componentId = NativeApi.AddCameraComponent(gameObject.InstanceId);
                return componentId != 0 ? GetOrCreateCamera(gameObject, componentId) : null;
            }

            if (!typeof(MonoBehaviour).IsAssignableFrom(type) || type.IsAbstract)
            {
                throw new ArgumentException(
                    $"AddComponent(Type) requires a supported concrete component type, got '{type.FullName}'.", nameof(type));
            }

            long handle = NativeApi.AddManagedComponent(gameObject.InstanceId, GetManagedTypeNameForLookup(type));
            return handle != 0 ? GetManagedComponent(handle, type) : null;
        }

        internal static T? GetGameObjectComponent<T>(GameObject gameObject) where T : Component
        {
            ArgumentNullException.ThrowIfNull(gameObject);
            return GetGameObjectComponent(gameObject, typeof(T)) as T;
        }

        internal static bool TryGetGameObjectComponent<T>(GameObject gameObject, out T? component) where T : Component
        {
            component = GetGameObjectComponent<T>(gameObject);
            return component is not null;
        }

        internal static T[] GetGameObjectComponents<T>(GameObject gameObject) where T : Component
        {
            ArgumentNullException.ThrowIfNull(gameObject);
            Component[] components = GetGameObjectComponents(gameObject, typeof(T));
            T[] typed = new T[components.Length];
            for (int i = 0; i < components.Length; i++)
            {
                typed[i] = (T)components[i];
            }
            return typed;
        }

        internal static void GetGameObjectComponents<T>(GameObject gameObject, List<T> results) where T : Component
        {
            ArgumentNullException.ThrowIfNull(gameObject);
            ArgumentNullException.ThrowIfNull(results);

            results.Clear();
            Component[] components = GetGameObjectComponents(gameObject, typeof(T));
            for (int i = 0; i < components.Length; i++)
            {
                results.Add((T)components[i]);
            }
        }

        internal static Component? GetGameObjectComponent(GameObject gameObject, Type type)
        {
            ArgumentNullException.ThrowIfNull(gameObject);
            ArgumentNullException.ThrowIfNull(type);

            if (!typeof(Component).IsAssignableFrom(type))
            {
                throw new ArgumentException(
                    $"GetComponent(Type) requires a Component-derived type, got '{type.FullName}'.", nameof(type));
            }

            List<Component> results = new();
            CollectComponentsOnGameObject(gameObject, type, results);
            return results.Count > 0 ? results[0] : null;
        }

        internal static bool TryGetGameObjectComponent(GameObject gameObject, Type type, out Component? component)
        {
            component = GetGameObjectComponent(gameObject, type);
            return component is not null;
        }

        internal static Component[] GetGameObjectComponents(GameObject gameObject, Type type)
        {
            ArgumentNullException.ThrowIfNull(gameObject);
            ArgumentNullException.ThrowIfNull(type);

            if (!typeof(Component).IsAssignableFrom(type))
            {
                throw new ArgumentException(
                    $"GetComponents(Type) requires a Component-derived type, got '{type.FullName}'.", nameof(type));
            }

            List<Component> results = new();
            CollectComponentsOnGameObject(gameObject, type, results);
            return results.ToArray();
        }

        internal static void GetGameObjectComponents(GameObject gameObject, Type type, List<Component> results)
        {
            ArgumentNullException.ThrowIfNull(gameObject);
            ArgumentNullException.ThrowIfNull(type);
            ArgumentNullException.ThrowIfNull(results);

            if (!typeof(Component).IsAssignableFrom(type))
            {
                throw new ArgumentException(
                    $"GetComponents(Type) requires a Component-derived type, got '{type.FullName}'.", nameof(type));
            }

            results.Clear();
            CollectComponentsOnGameObject(gameObject, type, results);
        }

        internal static T? GetGameObjectComponentInChildren<T>(GameObject gameObject) where T : Component
        {
            return GetGameObjectComponentInChildren<T>(gameObject, false);
        }

        internal static bool TryGetGameObjectComponentInChildren<T>(GameObject gameObject, out T? component) where T : Component
        {
            return TryGetGameObjectComponentInChildren(gameObject, false, out component);
        }

        internal static T? GetGameObjectComponentInChildren<T>(GameObject gameObject, bool includeInactive) where T : Component
        {
            ArgumentNullException.ThrowIfNull(gameObject);
            return GetGameObjectComponentInChildren(gameObject, typeof(T), includeInactive) as T;
        }

        internal static bool TryGetGameObjectComponentInChildren<T>(GameObject gameObject, bool includeInactive, out T? component) where T : Component
        {
            component = GetGameObjectComponentInChildren<T>(gameObject, includeInactive);
            return component is not null;
        }

        internal static T[] GetGameObjectComponentsInChildren<T>(GameObject gameObject) where T : Component
        {
            return GetGameObjectComponentsInChildren<T>(gameObject, false);
        }

        internal static void GetGameObjectComponentsInChildren<T>(GameObject gameObject, List<T> results) where T : Component
        {
            GetGameObjectComponentsInChildren(gameObject, false, results);
        }

        internal static void GetGameObjectComponentsInChildren<T>(GameObject gameObject, bool includeInactive, List<T> results) where T : Component
        {
            ArgumentNullException.ThrowIfNull(gameObject);
            ArgumentNullException.ThrowIfNull(results);

            results.Clear();
            Component[] components = GetGameObjectComponentsInChildren(gameObject, typeof(T), includeInactive);
            for (int i = 0; i < components.Length; i++)
            {
                results.Add((T)components[i]);
            }
        }

        internal static T[] GetGameObjectComponentsInChildren<T>(GameObject gameObject, bool includeInactive) where T : Component
        {
            ArgumentNullException.ThrowIfNull(gameObject);
            Component[] components = GetGameObjectComponentsInChildren(gameObject, typeof(T), includeInactive);
            T[] typed = new T[components.Length];
            for (int i = 0; i < components.Length; i++)
            {
                typed[i] = (T)components[i];
            }
            return typed;
        }

        internal static Component? GetGameObjectComponentInChildren(GameObject gameObject, Type type)
        {
            return GetGameObjectComponentInChildren(gameObject, type, false);
        }

        internal static bool TryGetGameObjectComponentInChildren(GameObject gameObject, Type type, out Component? component)
        {
            return TryGetGameObjectComponentInChildren(gameObject, type, false, out component);
        }

        internal static Component? GetGameObjectComponentInChildren(GameObject gameObject, Type type, bool includeInactive)
        {
            ArgumentNullException.ThrowIfNull(gameObject);
            ArgumentNullException.ThrowIfNull(type);

            if (!typeof(Component).IsAssignableFrom(type))
            {
                throw new ArgumentException(
                    $"GetComponentInChildren(Type) requires a Component-derived type, got '{type.FullName}'.", nameof(type));
            }

            List<Component> results = new();
            CollectComponentsInChildren(gameObject, type, includeInactive, true, results);
            return results.Count > 0 ? results[0] : null;
        }

        internal static bool TryGetGameObjectComponentInChildren(GameObject gameObject, Type type, bool includeInactive, out Component? component)
        {
            component = GetGameObjectComponentInChildren(gameObject, type, includeInactive);
            return component is not null;
        }

        internal static Component[] GetGameObjectComponentsInChildren(GameObject gameObject, Type type)
        {
            return GetGameObjectComponentsInChildren(gameObject, type, false);
        }

        internal static void GetGameObjectComponentsInChildren(GameObject gameObject, Type type, List<Component> results)
        {
            GetGameObjectComponentsInChildren(gameObject, type, false, results);
        }

        internal static void GetGameObjectComponentsInChildren(GameObject gameObject, Type type, bool includeInactive, List<Component> results)
        {
            ArgumentNullException.ThrowIfNull(gameObject);
            ArgumentNullException.ThrowIfNull(type);
            ArgumentNullException.ThrowIfNull(results);

            if (!typeof(Component).IsAssignableFrom(type))
            {
                throw new ArgumentException(
                    $"GetComponentsInChildren(Type) requires a Component-derived type, got '{type.FullName}'.", nameof(type));
            }

            results.Clear();
            CollectComponentsInChildren(gameObject, type, includeInactive, true, results);
        }

        internal static Component[] GetGameObjectComponentsInChildren(GameObject gameObject, Type type, bool includeInactive)
        {
            ArgumentNullException.ThrowIfNull(gameObject);
            ArgumentNullException.ThrowIfNull(type);

            if (!typeof(Component).IsAssignableFrom(type))
            {
                throw new ArgumentException(
                    $"GetComponentsInChildren(Type) requires a Component-derived type, got '{type.FullName}'.", nameof(type));
            }

            List<Component> results = new();
            CollectComponentsInChildren(gameObject, type, includeInactive, true, results);
            return results.ToArray();
        }

        internal static T? GetGameObjectComponentInParent<T>(GameObject gameObject) where T : Component
        {
            return GetGameObjectComponentInParent<T>(gameObject, false);
        }

        internal static bool TryGetGameObjectComponentInParent<T>(GameObject gameObject, out T? component) where T : Component
        {
            return TryGetGameObjectComponentInParent(gameObject, false, out component);
        }

        internal static T? GetGameObjectComponentInParent<T>(GameObject gameObject, bool includeInactive) where T : Component
        {
            ArgumentNullException.ThrowIfNull(gameObject);
            return GetGameObjectComponentInParent(gameObject, typeof(T), includeInactive) as T;
        }

        internal static bool TryGetGameObjectComponentInParent<T>(GameObject gameObject, bool includeInactive, out T? component) where T : Component
        {
            component = GetGameObjectComponentInParent<T>(gameObject, includeInactive);
            return component is not null;
        }

        internal static T[] GetGameObjectComponentsInParent<T>(GameObject gameObject) where T : Component
        {
            return GetGameObjectComponentsInParent<T>(gameObject, false);
        }

        internal static void GetGameObjectComponentsInParent<T>(GameObject gameObject, List<T> results) where T : Component
        {
            GetGameObjectComponentsInParent(gameObject, false, results);
        }

        internal static void GetGameObjectComponentsInParent<T>(GameObject gameObject, bool includeInactive, List<T> results) where T : Component
        {
            ArgumentNullException.ThrowIfNull(gameObject);
            ArgumentNullException.ThrowIfNull(results);

            results.Clear();
            Component[] components = GetGameObjectComponentsInParent(gameObject, typeof(T), includeInactive);
            for (int i = 0; i < components.Length; i++)
            {
                results.Add((T)components[i]);
            }
        }

        internal static T[] GetGameObjectComponentsInParent<T>(GameObject gameObject, bool includeInactive) where T : Component
        {
            ArgumentNullException.ThrowIfNull(gameObject);
            Component[] components = GetGameObjectComponentsInParent(gameObject, typeof(T), includeInactive);
            T[] typed = new T[components.Length];
            for (int i = 0; i < components.Length; i++)
            {
                typed[i] = (T)components[i];
            }
            return typed;
        }

        internal static Component? GetGameObjectComponentInParent(GameObject gameObject, Type type)
        {
            return GetGameObjectComponentInParent(gameObject, type, false);
        }

        internal static bool TryGetGameObjectComponentInParent(GameObject gameObject, Type type, out Component? component)
        {
            return TryGetGameObjectComponentInParent(gameObject, type, false, out component);
        }

        internal static Component? GetGameObjectComponentInParent(GameObject gameObject, Type type, bool includeInactive)
        {
            ArgumentNullException.ThrowIfNull(gameObject);
            ArgumentNullException.ThrowIfNull(type);

            if (!typeof(Component).IsAssignableFrom(type))
            {
                throw new ArgumentException(
                    $"GetComponentInParent(Type) requires a Component-derived type, got '{type.FullName}'.", nameof(type));
            }

            List<Component> results = new();
            CollectComponentsInParent(gameObject, type, includeInactive, true, results);
            return results.Count > 0 ? results[0] : null;
        }

        internal static bool TryGetGameObjectComponentInParent(GameObject gameObject, Type type, bool includeInactive, out Component? component)
        {
            component = GetGameObjectComponentInParent(gameObject, type, includeInactive);
            return component is not null;
        }

        internal static Component[] GetGameObjectComponentsInParent(GameObject gameObject, Type type)
        {
            return GetGameObjectComponentsInParent(gameObject, type, false);
        }

        internal static void GetGameObjectComponentsInParent(GameObject gameObject, Type type, List<Component> results)
        {
            GetGameObjectComponentsInParent(gameObject, type, false, results);
        }

        internal static void GetGameObjectComponentsInParent(GameObject gameObject, Type type, bool includeInactive, List<Component> results)
        {
            ArgumentNullException.ThrowIfNull(gameObject);
            ArgumentNullException.ThrowIfNull(type);
            ArgumentNullException.ThrowIfNull(results);

            if (!typeof(Component).IsAssignableFrom(type))
            {
                throw new ArgumentException(
                    $"GetComponentsInParent(Type) requires a Component-derived type, got '{type.FullName}'.", nameof(type));
            }

            results.Clear();
            CollectComponentsInParent(gameObject, type, includeInactive, true, results);
        }

        internal static Component[] GetGameObjectComponentsInParent(GameObject gameObject, Type type, bool includeInactive)
        {
            ArgumentNullException.ThrowIfNull(gameObject);
            ArgumentNullException.ThrowIfNull(type);

            if (!typeof(Component).IsAssignableFrom(type))
            {
                throw new ArgumentException(
                    $"GetComponentsInParent(Type) requires a Component-derived type, got '{type.FullName}'.", nameof(type));
            }

            List<Component> results = new();
            CollectComponentsInParent(gameObject, type, includeInactive, true, results);
            return results.ToArray();
        }

        private static T? GetManagedGameObjectComponent<T>(GameObject gameObject) where T : Component
        {
            if (!CanMatchManagedComponentType(typeof(T)))
            {
                throw new NotSupportedException(
                    $"GetComponent<{typeof(T).Name}> currently supports Transform or managed MonoBehaviour-derived types only.");
            }

            MonoBehaviour? component = FindManagedComponentOnGameObject(gameObject.InstanceId, typeof(T));
            return component is T typedComponent ? typedComponent : null;
        }

        private static Component? GetManagedGameObjectComponent(GameObject gameObject, Type type)
        {
            ValidateManagedLookupType(type, nameof(type), "GetComponent(Type)");
            return FindManagedComponentOnGameObject(gameObject.InstanceId, type);
        }

        private static T? GetManagedGameObjectComponentInChildren<T>(GameObject gameObject, bool includeInactive) where T : Component
        {
            if (!CanMatchManagedComponentType(typeof(T)))
            {
                throw new NotSupportedException(
                    $"GetComponentInChildren<{typeof(T).Name}> currently supports Transform or managed MonoBehaviour-derived types only.");
            }

            MonoBehaviour? component = FindManagedComponentInChildren(gameObject, typeof(T), includeInactive, true);
            return component is T typedComponent ? typedComponent : null;
        }

        private static Component? GetManagedGameObjectComponentInChildren(GameObject gameObject, Type type, bool includeInactive)
        {
            ValidateManagedLookupType(type, nameof(type), "GetComponentInChildren(Type)");
            return FindManagedComponentInChildren(gameObject, type, includeInactive, true);
        }

        private static T? GetManagedGameObjectComponentInParent<T>(GameObject gameObject, bool includeInactive) where T : Component
        {
            if (!CanMatchManagedComponentType(typeof(T)))
            {
                throw new NotSupportedException(
                    $"GetComponentInParent<{typeof(T).Name}> currently supports Transform or managed MonoBehaviour-derived types only.");
            }

            MonoBehaviour? component = FindManagedComponentInParent(gameObject, typeof(T), includeInactive, true);
            return component is T typedComponent ? typedComponent : null;
        }

        private static Component? GetManagedGameObjectComponentInParent(GameObject gameObject, Type type, bool includeInactive)
        {
            ValidateManagedLookupType(type, nameof(type), "GetComponentInParent(Type)");
            return FindManagedComponentInParent(gameObject, type, includeInactive, true);
        }

        private static string GetManagedTypeNameForLookup(Type type)
        {
            return type.FullName ?? type.Name;
        }

        private static void ValidateManagedLookupType(Type type, string paramName, string apiName)
        {
            if (!CanMatchManagedComponentType(type))
            {
                throw new ArgumentException(
                    $"{apiName} currently supports Transform or MonoBehaviour-derived types only.", paramName);
            }
        }

        private static bool CanMatchManagedComponentType(Type type)
        {
            return typeof(MonoBehaviour).IsAssignableFrom(type) || type.IsAssignableFrom(typeof(MonoBehaviour));
        }

        private static Transform InstantiateTransform(Transform transform, Transform? parent)
        {
            GameObject owner = transform.gameObject ??
                throw new InvalidOperationException("Transform has no owning GameObject.");
            GameObject? clone = GameObject.Instantiate(owner, parent);
            return clone?.transform ??
                throw new InvalidOperationException("Failed to instantiate Transform owner GameObject.");
        }

        private static Camera? InstantiateCamera(Camera camera, Transform? parent)
        {
            GameObject owner = camera.gameObject ??
                throw new InvalidOperationException("Camera has no owning GameObject.");
            GameObject? clone = GameObject.Instantiate(owner, parent);
            return clone?.GetComponent<Camera>();
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

        private static void CollectComponentsOnGameObject(GameObject gameObject, Type expectedType, List<Component> results)
        {
            if (expectedType.IsAssignableFrom(typeof(Transform)))
            {
                results.Add(gameObject.transform);
            }

            Camera? camera = GetNativeCameraOnGameObject(gameObject);
            if (camera is not null && expectedType.IsInstanceOfType(camera))
            {
                results.Add(camera);
            }

            foreach (MonoBehaviour candidate in EnumerateManagedComponentsOnGameObject(gameObject.InstanceId))
            {
                if (expectedType.IsInstanceOfType(candidate))
                {
                    results.Add(candidate);
                }
            }
        }

        private static void CollectComponentsInChildren(GameObject gameObject, Type expectedType, bool includeInactive, bool includeSelf, List<Component> results)
        {
            if (includeSelf || includeInactive || gameObject.activeInHierarchy)
            {
                CollectComponentsOnGameObject(gameObject, expectedType, results);
            }

            Transform root = gameObject.transform;
            for (int i = 0; i < root.childCount; i++)
            {
                Transform? child = root.GetChild(i);
                GameObject? childObject = child?.gameObject;
                if (childObject is not null)
                {
                    CollectComponentsInChildren(childObject, expectedType, includeInactive, false, results);
                }
            }
        }

        private static void CollectComponentsInParent(GameObject gameObject, Type expectedType, bool includeInactive, bool includeSelf, List<Component> results)
        {
            bool isSelf = includeSelf;
            for (GameObject? current = gameObject; current is not null; current = current.transform.parent?.gameObject)
            {
                if (isSelf || includeInactive || current.activeInHierarchy)
                {
                    CollectComponentsOnGameObject(current, expectedType, results);
                }
                isSelf = false;
            }
        }

        private static IEnumerable<MonoBehaviour> EnumerateManagedComponentsOnGameObject(long gameObjectId)
        {
            List<MonoBehaviour> matches = new();
            foreach (MonoBehaviour candidate in Components.Values)
            {
                if (candidate.GameObjectId == gameObjectId)
                {
                    matches.Add(candidate);
                }
            }

            matches.Sort(static (left, right) =>
            {
                long leftId = left.ComponentId != 0 ? left.ComponentId : long.MaxValue;
                long rightId = right.ComponentId != 0 ? right.ComponentId : long.MaxValue;
                return leftId.CompareTo(rightId);
            });
            return matches;
        }

        internal static Camera? GetMainCamera()
        {
            long gameObjectId = NativeApi.GetMainCameraGameObjectId();
            if (gameObjectId == 0)
            {
                return null;
            }

            GameObject gameObject = new(gameObjectId);
            long componentId = NativeApi.GetCameraComponentId(gameObjectId);
            return componentId != 0 ? GetOrCreateCamera(gameObject, componentId) : null;
        }

        private static Camera? GetNativeCameraOnGameObject(GameObject gameObject)
        {
            long componentId = NativeApi.GetCameraComponentId(gameObject.InstanceId);
            return componentId != 0 ? GetOrCreateCamera(gameObject, componentId) : null;
        }

        private static Camera GetOrCreateCamera(GameObject gameObject, long componentId)
        {
            if (NativeCameras.TryGetValue(componentId, out Camera? camera))
            {
                return camera;
            }

            camera = new Camera(gameObject, componentId);
            NativeCameras[componentId] = camera;
            return camera;
        }

        private static MonoBehaviour? FindManagedComponentOnGameObject(long gameObjectId, Type expectedType)
        {
            foreach (MonoBehaviour candidate in EnumerateManagedComponentsOnGameObject(gameObjectId))
            {
                if (expectedType.IsInstanceOfType(candidate))
                {
                    return candidate;
                }
            }
            return null;
        }

        private static MonoBehaviour? FindManagedComponentInChildren(GameObject gameObject, Type expectedType, bool includeInactive, bool includeSelf)
        {
            if (includeSelf || includeInactive || gameObject.activeInHierarchy)
            {
                MonoBehaviour? self = FindManagedComponentOnGameObject(gameObject.InstanceId, expectedType);
                if (self is not null)
                {
                    return self;
                }
            }

            Transform root = gameObject.transform;
            for (int i = 0; i < root.childCount; i++)
            {
                Transform? child = root.GetChild(i);
                GameObject? childObject = child?.gameObject;
                if (childObject is null)
                {
                    continue;
                }

                MonoBehaviour? nested = FindManagedComponentInChildren(childObject, expectedType, includeInactive, false);
                if (nested is not null)
                {
                    return nested;
                }
            }

            return null;
        }

        private static MonoBehaviour? FindManagedComponentInParent(GameObject gameObject, Type expectedType, bool includeInactive, bool includeSelf)
        {
            bool isSelf = includeSelf;
            for (GameObject? current = gameObject; current is not null; current = current.transform.parent?.gameObject)
            {
                if (isSelf || includeInactive || current.activeInHierarchy)
                {
                    MonoBehaviour? match = FindManagedComponentOnGameObject(current.InstanceId, expectedType);
                    if (match is not null)
                    {
                        return match;
                    }
                }
                isSelf = false;
            }

            return null;
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
    script_class_name = default_script_class_name(project_name)
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

