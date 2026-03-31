from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


DEV_DIR = Path(__file__).resolve().parent
REPO_ROOT = DEV_DIR.parent
BASE_CONFIG_PATH = DEV_DIR / "render_audit_rules.json"
AUDIT_SCRIPT_PATH = DEV_DIR / "render_audit.py"


PRESETS: dict[str, dict[str, object]] = {
    "editor": {
        "report_title": "Editor Render Audit Report",
        "include_globs": [
            "cpp/infernux/function/renderer/OutlineRenderer.cpp",
            "cpp/infernux/function/renderer/SceneRenderGraph.cpp",
            "cpp/infernux/function/renderer/gui/**",
            "cpp/infernux/function/renderer/VkCoreDraw.cpp",
            "cpp/infernux/function/renderer/VkCoreGlobals.cpp",
            "cpp/infernux/function/renderer/VkCoreMaterial.cpp",
        ],
        "monitored_string_literals": [
            "_ComponentGizmos",
            "_EditorGizmos",
            "_EditorTools",
            "outline_mask",
            "outline_composite",
            "color",
            "depth",
            "shadow_map",
        ],
        "watch_numeric_literals": [
            "14",
            "16",
            "32",
            "64",
            "128",
            "256",
            "1024",
            "2500",
            "2999",
            "5000",
            "32500",
            "32700",
        ],
        "top_duplicates": 15,
        "top_hotspots": 12,
    },
    "renderstack": {
        "report_title": "RenderStack Audit Report",
        "include_globs": [
            "python/Infernux/renderstack/**",
        ],
        "top_duplicates": 15,
        "top_hotspots": 12,
    },
    "core": {
        "report_title": "Renderer Core Audit Report",
        "include_globs": [
            "cpp/infernux/function/renderer/*.cpp",
            "cpp/infernux/function/renderer/*.h",
            "cpp/infernux/function/renderer/vk/**",
        ],
        "exclude_globs": [
            "external/**",
            "**/__pycache__/**",
            "cpp/infernux/function/renderer/gui/**",
        ],
        "top_duplicates": 15,
        "top_hotspots": 12,
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate scoped render-audit config stubs and optionally run the audit.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("preset", choices=sorted(PRESETS), help="Audit preset to materialize.")
    parser.add_argument(
        "--output-config",
        type=Path,
        help="Path to write the generated config JSON.",
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="Run render_audit.py immediately after writing the config.",
    )
    parser.add_argument(
        "--report",
        type=Path,
        help="Optional report output path when --run is used.",
    )
    parser.add_argument(
        "--json-report",
        action="store_true",
        help="Emit the audit report as JSON when --run is used.",
    )
    return parser.parse_args()


def merge_unique(base: list[str], extra: list[str]) -> list[str]:
    merged = list(base)
    for item in extra:
        if item not in merged:
            merged.append(item)
    return merged


def build_config(preset_name: str) -> dict[str, object]:
    base = json.loads(BASE_CONFIG_PATH.read_text(encoding="utf-8"))
    preset = PRESETS[preset_name]

    config = dict(base)
    for key, value in preset.items():
        if key in {"monitored_string_literals", "watch_numeric_literals", "exclude_globs", "duplicate_exclude_globs"}:
            config[key] = merge_unique(config.get(key, []), value)
        else:
            config[key] = value
    return config


def resolve_output_config(args: argparse.Namespace) -> Path:
    if args.output_config is not None:
        return args.output_config.resolve()
    return (DEV_DIR / f"render_audit_{args.preset}.json").resolve()


def run_audit(config_path: Path, args: argparse.Namespace) -> int:
    command = [sys.executable, str(AUDIT_SCRIPT_PATH), "--config", str(config_path)]
    if args.json_report:
        command.append("--json")
    if args.report is not None:
        command.extend(["--write-report", str(args.report.resolve())])

    completed = subprocess.run(command, cwd=REPO_ROOT, check=False)
    return completed.returncode


def main() -> int:
    args = parse_args()
    config = build_config(args.preset)
    output_config = resolve_output_config(args)
    output_config.parent.mkdir(parents=True, exist_ok=True)
    output_config.write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote audit config: {output_config}")

    if not args.run:
        return 0

    return run_audit(output_config, args)


if __name__ == "__main__":
    raise SystemExit(main())