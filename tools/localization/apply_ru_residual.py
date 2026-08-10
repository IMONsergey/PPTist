#!/usr/bin/env python3
"""Apply the reviewed second-pass Russian PPTist UI translation map safely.

Only exact complete string literals, exact Vue text nodes, and exact visible
attribute values are translated. No substring replacement is allowed.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

HAN = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")
LITERAL_RX = re.compile(r'''(?P<q>["'`])(?P<value>[^"'`\n]*)(?P=q)''')
TEXT_NODE_RX = re.compile(r">(?P<value>[^<>\n]+)<")
VISIBLE_ATTR_RX = re.compile(
    r"(?P<name>\b(?:title|placeholder|aria-label|alt|label|tip))"
    r"(?P<sep>\s*=\s*)(?P<q>[\"'])(?P<value>[^\"']*)(?P=q)",
    re.I,
)
SOURCE_EXTS = {".vue", ".ts", ".tsx", ".js", ".jsx", ".html"}

# These are complete Vue text nodes that contain Chinese inside an expression.
# Generic translation must not rewrite code within {{...}}, so they are explicit.
DYNAMIC_OVERRIDES = {
    "{{ fullscreenState ? 'Выйти из полноэкранного режима' : '全屏' }}":
        "{{ fullscreenState ? 'Выйти из полноэкранного режима' : 'Полный экран' }}",
    "{{playbackRate === 1 ? '倍速' : (playbackRate + 'x')}}":
        "{{playbackRate === 1 ? 'Скорость' : (playbackRate + 'x')}}",
    "循环{{loop ? '开' : '关'}}":
        "Повтор: {{loop ? 'Вкл.' : 'Выкл.'}}",
}

# Correct a few first-pass donor translations that were technically valid but
# semantically wrong/awkward in the current PPTist context.
FIRST_PASS_CORRECTIONS = {
    "Уместить": "Масштабирование",
    "Средняя": "По центру",
}

KNOWN_CORRUPTION = (
    "正在加载Средняя",
    "Применить注销",
    "Крупная部分",
    "边框Линия",
    "Уместить点",
    "Диаграмма数据",
    "Редактироватьor",
)


def source_files(root: Path) -> list[Path]:
    files = [p for p in (root / "src").rglob("*") if p.is_file() and p.suffix in SOURCE_EXTS]
    index = root / "index.html"
    if index.exists():
        files.append(index)
    return sorted(set(files))


def normalize_file(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    final_newline = text.endswith("\n")
    normalized = "\n".join(line.rstrip(" \t") for line in text.splitlines())
    if final_newline:
        normalized += "\n"
    path.write_text(normalized, encoding="utf-8")


def replace_exact_literals(text: str, mapping: dict[str, str]) -> tuple[str, int]:
    hits = 0

    def repl(match: re.Match[str]) -> str:
        nonlocal hits
        raw = match.group("value")
        core = raw.strip()
        target = mapping.get(core)
        if target is None:
            return match.group(0)
        quote = match.group("q")
        if quote in target:
            # A quote-sensitive string is deliberately left for residual audit.
            return match.group(0)
        leading = raw[: len(raw) - len(raw.lstrip())]
        trailing = raw[len(raw.rstrip()) :]
        hits += 1
        return f"{quote}{leading}{target}{trailing}{quote}"

    return LITERAL_RX.sub(repl, text), hits


def replace_vue_template(template: str, mapping: dict[str, str]) -> tuple[str, int, int]:
    text_hits = 0
    attr_hits = 0

    def text_repl(match: re.Match[str]) -> str:
        nonlocal text_hits
        raw = match.group("value")
        core = re.sub(r"\s+", " ", raw).strip()
        target = mapping.get(core)
        if target is None:
            return match.group(0)
        leading = raw[: len(raw) - len(raw.lstrip())]
        trailing = raw[len(raw.rstrip()) :]
        text_hits += 1
        return f">{leading}{target}{trailing}<"

    template = TEXT_NODE_RX.sub(text_repl, template)

    def attr_repl(match: re.Match[str]) -> str:
        nonlocal attr_hits
        raw = match.group("value")
        target = mapping.get(raw.strip())
        if target is None:
            return match.group(0)
        quote = match.group("q")
        if quote in target:
            return match.group(0)
        attr_hits += 1
        return f"{match.group('name')}{match.group('sep')}{quote}{target}{quote}"

    return VISIBLE_ATTR_RX.sub(attr_repl, template), text_hits, attr_hits


def apply_corrections(text: str) -> tuple[str, int]:
    """Only correct full quoted literal values produced by the first donor pass."""
    return replace_exact_literals(text, FIRST_PASS_CORRECTIONS)


def audit(root: Path) -> dict[str, Any]:
    literal_rx = re.compile(
        r'''(?P<q>["'`])(?P<value>[^"'`\n]*[\u3400-\u4dbf\u4e00-\u9fff][^"'`\n]*)(?P=q)'''
    )
    text_rx = re.compile(
        r">(?P<value>[^<>\n]*[\u3400-\u4dbf\u4e00-\u9fff][^<>\n]*)<"
    )
    visible_attr_rx = re.compile(
        r'''(?:title|placeholder|aria-label|alt|label|tip)\s*=\s*["'](?P<value>[^"']+)["']''',
        re.I,
    )
    english_text_rx = re.compile(r">\s*(?P<value>[A-Za-z][A-Za-z0-9 /+&()_.:,!?#-]{2,})\s*<")

    chinese_literals: list[dict[str, Any]] = []
    chinese_template: list[dict[str, Any]] = []
    chinese_noncomment: list[dict[str, Any]] = []
    english_visible: list[dict[str, Any]] = []

    for path in source_files(root):
        content = path.read_text(encoding="utf-8")
        rel = str(path.relative_to(root))
        in_template = False
        in_block_comment = False
        for lineno, line in enumerate(content.splitlines(), 1):
            stripped = line.strip()
            if "/*" in stripped and "*/" not in stripped:
                in_block_comment = True
            comment = (
                in_block_comment
                or stripped.startswith("//")
                or stripped.startswith("*")
                or stripped.startswith("<!--")
            )
            if "<template" in line:
                in_template = True

            if HAN.search(line) and not comment:
                chinese_noncomment.append({"file": rel, "line": lineno, "text": stripped})
                for match in literal_rx.finditer(line):
                    value = match.group("value").strip()
                    if value:
                        chinese_literals.append({"file": rel, "line": lineno, "text": value})
                if in_template:
                    for match in text_rx.finditer(line):
                        value = re.sub(r"\s+", " ", match.group("value")).strip()
                        if value:
                            chinese_template.append({"file": rel, "line": lineno, "text": value})

            if in_template:
                for match in visible_attr_rx.finditer(line):
                    value = match.group("value").strip()
                    if re.search(r"[A-Za-z]", value):
                        english_visible.append({"file": rel, "line": lineno, "kind": "attr", "text": value})
                for match in english_text_rx.finditer(line):
                    english_visible.append(
                        {"file": rel, "line": lineno, "kind": "text", "text": match.group("value").strip()}
                    )

            if "</template>" in line:
                in_template = False
            if "*/" in stripped:
                in_block_comment = False

    def dedupe(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        out = []
        seen = set()
        for item in items:
            key = (item["file"], item["line"], item["text"], item.get("kind"))
            if key not in seen:
                seen.add(key)
                out.append(item)
        return out

    chinese_literals = dedupe(chinese_literals)
    chinese_template = dedupe(chinese_template)
    chinese_noncomment = dedupe(chinese_noncomment)
    english_visible = dedupe(english_visible)

    return {
        "stats": {
            "chinese_noncomment_lines": len(chinese_noncomment),
            "chinese_string_literals": len(chinese_literals),
            "chinese_template_text_nodes": len(chinese_template),
            "english_visible_candidates": len(english_visible),
        },
        "chinese_string_literals": chinese_literals,
        "chinese_template_text_nodes": chinese_template,
        "english_visible_candidates": english_visible,
        "chinese_noncomment_lines": chinese_noncomment,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--map", required=True)
    args = parser.parse_args()

    root = Path(args.root).resolve()
    map_path = Path(args.map).resolve()
    payload = json.loads(map_path.read_text(encoding="utf-8"))
    mapping: dict[str, str] = dict(payload["translations"])
    mapping.update(DYNAMIC_OVERRIDES)

    changed: set[Path] = set()
    literal_hits = template_hits = attr_hits = correction_hits = 0

    for path in source_files(root):
        text = path.read_text(encoding="utf-8")
        original = text

        text, hits = replace_exact_literals(text, mapping)
        literal_hits += hits
        text, hits = apply_corrections(text)
        correction_hits += hits

        if path.suffix == ".vue":
            match = re.search(r"(<template\b[^>]*>)(.*?)(</template>)", text, flags=re.S)
            if match:
                body, th, ah = replace_vue_template(match.group(2), mapping)
                template_hits += th
                attr_hits += ah
                text = text[: match.start(2)] + body + text[match.end(2) :]

        if text != original:
            path.write_text(text, encoding="utf-8")
            normalize_file(path)
            changed.add(path)

    # Explicitly reject every known failure mode before build/type-check.
    offenders = []
    for path in source_files(root):
        text = path.read_text(encoding="utf-8")
        for token in KNOWN_CORRUPTION:
            if token in text:
                offenders.append(f"{path.relative_to(root)}: {token}")
    if offenders:
        raise SystemExit("Known localization corruption detected:\n" + "\n".join(offenders))

    residual = audit(root)
    out = root / ".localization"
    out.mkdir(exist_ok=True)
    report = {
        "map_entries": len(mapping),
        "literal_hits": literal_hits,
        "template_hits": template_hits,
        "visible_attr_hits": attr_hits,
        "first_pass_corrections": correction_hits,
        "files_changed": len(changed),
        "changed_files": [str(p.relative_to(root)) for p in sorted(changed)],
    }
    (out / "pass-2-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (out / "residual-after-pass-2.json").write_text(
        json.dumps(residual, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"pass": report, "residual": residual["stats"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
