from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from fnmatch import fnmatch
from pathlib import Path
import re


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = Path(__file__).with_name("render_audit_rules.json")

NUMBER_RE = re.compile(
    r"(?<![\w.])(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?(?:[uUlLfF]+)?)(?![\w.])"
)
STRING_RE = re.compile(r'"([^"\\]*(?:\\.[^"\\]*)*)"|\'([^\'\\]*(?:\\.[^\'\\]*)*)\'')
PY_RESOURCE_CALL_RE = re.compile(
    r"\b(?P<api>create_texture|get_texture|set_texture|write_color|write_depth|read|set_output|"
    r"injection_point|bus\.get|bus\.set)\(\s*[\"\'](?P<value>[^\"\']+)[\"\']"
)

COMMENT_PREFIXES = ("//", "/*", "*", "#", '"""', "'''")
DESCRIPTOR_MARKERS = (
    "VkWriteDescriptorSet",
    "VkDescriptorSetLayoutBinding",
    "vkUpdateDescriptorSets",
)
PIPELINE_MARKERS = (
    "VkGraphicsPipelineCreateInfo",
    "VkPipelineLayoutCreateInfo",
    "vkCreateGraphicsPipelines",
)


@dataclass(frozen=True)
class LineHit:
    path: str
    line: int
    text: str


@dataclass(frozen=True)
class WindowOccurrence:
    path: str
    line: int
    snippet: tuple[str, ...]


@dataclass
class FileMetrics:
    descriptor_markers: int = 0
    pipeline_markers: int = 0
    resource_literals: list[LineHit] = field(default_factory=list)
    numeric_hits: dict[str, list[LineHit]] = field(default_factory=lambda: defaultdict(list))
    duplicate_groups: int = 0

    @property
    def unique_numeric_literals(self) -> list[str]:
        return sorted(self.numeric_hits)

    def hotspot_score(self, watch_literals: set[str]) -> int:
        watched = sum(1 for literal in self.numeric_hits if literal in watch_literals)
        resource_count = len(self.resource_literals)
        unique_numbers = len(self.numeric_hits)
        return (
            self.descriptor_markers * 3
            + self.pipeline_markers * 3
            + watched * 4
            + resource_count * 2
            + self.duplicate_groups * 5
            + min(unique_numbers, 12)
        )


@dataclass(frozen=True)
class DuplicateGroup:
    normalized_window: tuple[str, ...]
    occurrences: tuple[WindowOccurrence, ...]

    @property
    def score(self) -> tuple[int, int]:
        return (len(self.occurrences), len(self.normalized_window))


@dataclass
class AuditConfig:
    report_title: str
    roots: list[str]
    extensions: set[str]
    include_globs: list[str]
    exclude_globs: list[str]
    duplicate_exclude_globs: list[str]
    owned_string_literal_paths: set[str]
    monitored_string_literals: set[str]
    watch_numeric_literals: set[str]
    ignore_numeric_literals: set[str]
    duplicate_window_size: int
    duplicate_min_occurrences: int
    numeric_min_occurrences: int
    top_duplicates: int
    top_hotspots: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Audit renderer-focused code for hardcoded literals, duplicated boilerplate, "
            "and maintainability hotspots."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="Path to the render audit configuration JSON.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit the report as JSON instead of Markdown.",
    )
    parser.add_argument(
        "--write-report",
        type=Path,
        help="Optional output path for the rendered report.",
    )
    parser.add_argument(
        "--fail-on-findings",
        action="store_true",
        help="Return exit code 1 when the audit finds any issue.",
    )
    parser.add_argument(
        "--top-duplicates",
        type=int,
        help="Override the number of duplicate groups shown.",
    )
    parser.add_argument(
        "--top-hotspots",
        type=int,
        help="Override the number of hotspot files shown.",
    )
    return parser.parse_args()


def load_config(path: Path, args: argparse.Namespace) -> AuditConfig:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return AuditConfig(
        report_title=payload.get("report_title", "Render Audit Report"),
        roots=payload["roots"],
        extensions=set(payload["extensions"]),
        include_globs=payload.get("include_globs", []),
        exclude_globs=payload.get("exclude_globs", []),
        duplicate_exclude_globs=payload.get("duplicate_exclude_globs", []),
        owned_string_literal_paths=set(payload.get("owned_string_literal_paths", [])),
        monitored_string_literals=set(payload.get("monitored_string_literals", [])),
        watch_numeric_literals=set(payload.get("watch_numeric_literals", [])),
        ignore_numeric_literals={literal.lower() for literal in payload.get("ignore_numeric_literals", [])},
        duplicate_window_size=payload.get("duplicate_window_size", 6),
        duplicate_min_occurrences=payload.get("duplicate_min_occurrences", 2),
        numeric_min_occurrences=payload.get("numeric_min_occurrences", 3),
        top_duplicates=args.top_duplicates or payload.get("top_duplicates", 10),
        top_hotspots=args.top_hotspots or payload.get("top_hotspots", 10),
    )


def is_comment_or_blank(stripped: str) -> bool:
    return not stripped or stripped.startswith(COMMENT_PREFIXES)


def matches_any(path: str, patterns: list[str]) -> bool:
    return any(fnmatch(path, pattern) for pattern in patterns)


def iter_source_files(config: AuditConfig) -> list[tuple[str, Path]]:
    files: list[tuple[str, Path]] = []
    for root_rel in config.roots:
        root = REPO_ROOT / root_rel
        if not root.is_dir():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in config.extensions:
                continue
            rel_path = path.relative_to(REPO_ROOT).as_posix()
            if config.include_globs and not matches_any(rel_path, config.include_globs):
                continue
            if matches_any(rel_path, config.exclude_globs):
                continue
            files.append((rel_path, path))
    files.sort(key=lambda item: item[0])
    return files


def read_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8", errors="replace").splitlines()


def normalize_number(literal: str) -> str:
    return literal.lower()


def normalize_line_for_duplicate(line: str) -> str | None:
    stripped = line.strip()
    if is_comment_or_blank(stripped) or stripped in {"{", "}", "};"}:
        return None
    if stripped.startswith(("from ", "import ", "__all__")):
        return None
    if stripped.startswith(('"', "'")):
        return None

    text = re.sub(r"//.*$", "", stripped)
    text = STRING_RE.sub('"STR"', text)
    text = NUMBER_RE.sub("NUM", text)
    text = re.sub(r"\[[^\]]+\]", "[IDX]", text)
    text = re.sub(r"\s+", " ", text).strip()
    if not text or text in {"{", "}", ";"}:
        return None
    return text


def collect_file_metrics(rel_path: str, lines: list[str], config: AuditConfig) -> FileMetrics:
    metrics = FileMetrics()
    metrics.descriptor_markers = sum(line.count(marker) for line in lines for marker in DESCRIPTOR_MARKERS)
    metrics.pipeline_markers = sum(line.count(marker) for line in lines for marker in PIPELINE_MARKERS)

    is_owned_literal_file = rel_path in config.owned_string_literal_paths

    for line_no, line in enumerate(lines, start=1):
        stripped = line.strip()
        if is_comment_or_blank(stripped):
            continue

        if rel_path.endswith((".py", ".pyi")) and not is_owned_literal_file:
            for match in PY_RESOURCE_CALL_RE.finditer(line):
                literal = match.group("value")
                if literal in config.monitored_string_literals:
                    metrics.resource_literals.append(LineHit(rel_path, line_no, stripped))

        numeric_scan_line = STRING_RE.sub('"STR"', line)
        for match in NUMBER_RE.finditer(numeric_scan_line):
            literal = normalize_number(match.group(1))
            if literal in config.ignore_numeric_literals:
                continue
            metrics.numeric_hits[literal].append(LineHit(rel_path, line_no, stripped))

    return metrics


def collect_duplicate_groups(file_contents: dict[str, list[str]], config: AuditConfig) -> list[DuplicateGroup]:
    occurrences: dict[tuple[str, ...], list[WindowOccurrence]] = defaultdict(list)
    window = config.duplicate_window_size

    for rel_path, lines in file_contents.items():
        if matches_any(rel_path, config.duplicate_exclude_globs):
            continue
        normalized_lines: list[tuple[int, str, str]] = []
        for line_no, line in enumerate(lines, start=1):
            normalized = normalize_line_for_duplicate(line)
            if normalized is None:
                continue
            normalized_lines.append((line_no, normalized, line.rstrip()))

        for start in range(0, len(normalized_lines) - window + 1):
            chunk = normalized_lines[start : start + window]
            normalized_window = tuple(item[1] for item in chunk)
            original_window = tuple(item[2] for item in chunk)
            occurrences[normalized_window].append(
                WindowOccurrence(rel_path, chunk[0][0], original_window)
            )

    groups: list[DuplicateGroup] = []
    for normalized_window, hits in occurrences.items():
        unique_hits = list({(hit.path, hit.line): hit for hit in hits}.values())
        unique_hits.sort(key=lambda hit: (hit.path, hit.line))

        collapsed_hits: list[WindowOccurrence] = []
        last_end_by_file: dict[str, int] = {}
        for hit in unique_hits:
            last_end = last_end_by_file.get(hit.path, -10_000)
            if hit.line <= last_end:
                continue
            collapsed_hits.append(hit)
            last_end_by_file[hit.path] = hit.line + window - 1

        same_file_counts = Counter(hit.path for hit in collapsed_hits)
        distinct_files = len(same_file_counts)
        if len(collapsed_hits) < config.duplicate_min_occurrences:
            continue
        if distinct_files < 2 and max(same_file_counts.values(), default=0) < 2:
            continue
        groups.append(DuplicateGroup(normalized_window, tuple(collapsed_hits)))

    groups.sort(key=lambda group: (group.score[0], group.score[1]), reverse=True)
    return groups


def summarize_numeric_hits(
    file_metrics: dict[str, FileMetrics], config: AuditConfig
) -> tuple[dict[str, list[LineHit]], dict[str, list[LineHit]]]:
    watched: dict[str, list[LineHit]] = defaultdict(list)
    repeated: dict[str, list[LineHit]] = defaultdict(list)

    for metrics in file_metrics.values():
        for literal, hits in metrics.numeric_hits.items():
            if literal in config.watch_numeric_literals:
                watched[literal].extend(hits)
            elif len(hits) >= config.numeric_min_occurrences:
                repeated[literal].extend(hits)

    return watched, repeated


def count_findings(
    watched_numeric: dict[str, list[LineHit]],
    repeated_numeric: dict[str, list[LineHit]],
    resource_hits: list[LineHit],
    duplicate_groups: list[DuplicateGroup],
) -> int:
    return len(watched_numeric) + len(repeated_numeric) + len(resource_hits) + len(duplicate_groups)


def render_markdown_report(
    file_metrics: dict[str, FileMetrics],
    watched_numeric: dict[str, list[LineHit]],
    repeated_numeric: dict[str, list[LineHit]],
    duplicate_groups: list[DuplicateGroup],
    config: AuditConfig,
) -> str:
    resource_hits = sorted(
        (hit for metrics in file_metrics.values() for hit in metrics.resource_literals),
        key=lambda hit: (hit.path, hit.line),
    )
    hotspots = sorted(
        (
            (path, metrics.hotspot_score(config.watch_numeric_literals), metrics)
            for path, metrics in file_metrics.items()
        ),
        key=lambda item: (item[1], item[0]),
        reverse=True,
    )[: config.top_hotspots]

    lines: list[str] = []
    lines.append(f"# {config.report_title}")
    lines.append("")
    lines.append(f"Scanned {len(file_metrics)} files under the configured renderer roots.")
    lines.append("")

    lines.append("## Hotspot Files")
    if hotspots:
        for path, score, metrics in hotspots:
            samples = ", ".join(metrics.unique_numeric_literals[:6]) or "none"
            lines.append(
                f"- {path}: score={score}, duplicate_groups={metrics.duplicate_groups}, "
                f"descriptor_markers={metrics.descriptor_markers}, pipeline_markers={metrics.pipeline_markers}, "
                f"resource_literals={len(metrics.resource_literals)}, sample_numbers={samples}"
            )
    else:
        lines.append("- None")
    lines.append("")

    lines.append("## Watched Numeric Literals")
    if watched_numeric:
        for literal, hits in sorted(watched_numeric.items(), key=lambda item: (len(item[1]), item[0]), reverse=True):
            preview = "; ".join(f"{hit.path}:{hit.line}" for hit in hits[:4])
            lines.append(f"- {literal}: {len(hits)} hits, e.g. {preview}")
    else:
        lines.append("- None")
    lines.append("")

    lines.append("## Repeated Numeric Literals")
    if repeated_numeric:
        for literal, hits in sorted(repeated_numeric.items(), key=lambda item: (len(item[1]), item[0]), reverse=True):
            preview = "; ".join(f"{hit.path}:{hit.line}" for hit in hits[:4])
            lines.append(f"- {literal}: {len(hits)} hits in one file, e.g. {preview}")
    else:
        lines.append("- None")
    lines.append("")

    lines.append("## Hardcoded Render-Graph Literals")
    if resource_hits:
        for hit in resource_hits[:40]:
            lines.append(f"- {hit.path}:{hit.line}: {hit.text}")
        if len(resource_hits) > 40:
            lines.append(f"- ... {len(resource_hits) - 40} more")
    else:
        lines.append("- None")
    lines.append("")

    lines.append("## Duplicate Boilerplate Windows")
    if duplicate_groups:
        for index, group in enumerate(duplicate_groups[: config.top_duplicates], start=1):
            first = group.occurrences[0]
            locations = ", ".join(f"{hit.path}:{hit.line}" for hit in group.occurrences[:4])
            lines.append(f"### Duplicate Group {index}")
            lines.append(f"Occurrences: {len(group.occurrences)}")
            lines.append(f"Locations: {locations}")
            lines.append("")
            lines.append("```text")
            lines.extend(first.snippet)
            lines.append("```")
            lines.append("")
    else:
        lines.append("- None")
        lines.append("")

    return "\n".join(lines)


def render_json_report(
    file_metrics: dict[str, FileMetrics],
    watched_numeric: dict[str, list[LineHit]],
    repeated_numeric: dict[str, list[LineHit]],
    duplicate_groups: list[DuplicateGroup],
    config: AuditConfig,
) -> str:
    payload = {
        "scanned_files": len(file_metrics),
        "hotspots": [
            {
                "path": path,
                "score": metrics.hotspot_score(config.watch_numeric_literals),
                "descriptor_markers": metrics.descriptor_markers,
                "pipeline_markers": metrics.pipeline_markers,
                "resource_literal_hits": len(metrics.resource_literals),
                "duplicate_groups": metrics.duplicate_groups,
                "sample_numbers": metrics.unique_numeric_literals[:8],
            }
            for path, metrics in sorted(
                file_metrics.items(),
                key=lambda item: (item[1].hotspot_score(config.watch_numeric_literals), item[0]),
                reverse=True,
            )[: config.top_hotspots]
        ],
        "watched_numeric_literals": {
            literal: [hit.__dict__ for hit in hits]
            for literal, hits in watched_numeric.items()
        },
        "repeated_numeric_literals": {
            literal: [hit.__dict__ for hit in hits]
            for literal, hits in repeated_numeric.items()
        },
        "resource_literal_hits": [
            hit.__dict__
            for metrics in file_metrics.values()
            for hit in metrics.resource_literals
        ],
        "duplicate_groups": [
            {
                "occurrences": [hit.__dict__ for hit in group.occurrences],
                "snippet": list(group.occurrences[0].snippet),
            }
            for group in duplicate_groups[: config.top_duplicates]
        ],
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


def main() -> int:
    args = parse_args()
    config = load_config(args.config.resolve(), args)

    file_contents: dict[str, list[str]] = {}
    file_metrics: dict[str, FileMetrics] = {}
    for rel_path, path in iter_source_files(config):
        lines = read_lines(path)
        file_contents[rel_path] = lines
        file_metrics[rel_path] = collect_file_metrics(rel_path, lines, config)

    duplicate_groups = collect_duplicate_groups(file_contents, config)
    for group in duplicate_groups:
        for occurrence in group.occurrences:
            file_metrics[occurrence.path].duplicate_groups += 1

    watched_numeric, repeated_numeric = summarize_numeric_hits(file_metrics, config)

    if args.json:
        report_text = render_json_report(
            file_metrics,
            watched_numeric,
            repeated_numeric,
            duplicate_groups,
            config,
        )
    else:
        report_text = render_markdown_report(
            file_metrics,
            watched_numeric,
            repeated_numeric,
            duplicate_groups,
            config,
        )

    print(report_text)

    if args.write_report is not None:
        output_path = args.write_report.resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report_text + "\n", encoding="utf-8")

    total_findings = count_findings(
        watched_numeric,
        repeated_numeric,
        [hit for metrics in file_metrics.values() for hit in metrics.resource_literals],
        duplicate_groups,
    )
    if args.fail_on_findings and total_findings > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())