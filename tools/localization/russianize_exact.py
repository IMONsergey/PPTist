#!/usr/bin/env python3
"""Controlled PPTist Russian UI localization pass.

Uses the maintained PPTist-i18n Russian locale as a translation donor, but only
replaces complete string literal values / complete Vue text nodes. It never
performs arbitrary substring replacement, because short Chinese/English terms
can be valid parts of identifiers or longer phrases.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

HAN = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")
CYR = re.compile(r"[А-Яа-яЁё]")
LITERAL_RX = re.compile(r'''(?P<q>["'`])(?P<value>[^"'`\n]*)(?P=q)''')
TEXT_NODE_RX = re.compile(r">(?P<value>[^<>\n]+)<")
VISIBLE_ATTR_RX = re.compile(
    r"(?P<name>\b(?:title|placeholder|aria-label|alt|label|tip))"
    r"(?P<sep>\s*=\s*)(?P<q>[\"'])(?P<value>[^\"']*)(?P=q)",
    re.I,
)
RESIDUAL_LITERAL_RX = re.compile(
    r'''(?P<q>["'`])(?P<value>[^"'`\n]*[\u3400-\u4dbf\u4e00-\u9fff][^"'`\n]*)(?P=q)'''
)
RESIDUAL_TEXT_NODE_RX = re.compile(
    r">(?P<value>[^<>\n]*[\u3400-\u4dbf\u4e00-\u9fff][^<>\n]*)<"
)
ENGLISH_TEXT_RX = re.compile(r">\s*(?P<value>[A-Za-z][A-Za-z0-9 /+&()_.:,!?#-]{2,})\s*<")

SOURCE_EXTS = {".vue", ".ts", ".tsx", ".js", ".jsx", ".html"}


def flatten(obj: Any, prefix: str = "") -> dict[str, str]:
    out: dict[str, str] = {}
    if isinstance(obj, dict):
        for key, value in obj.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            out.update(flatten(value, path))
    elif isinstance(obj, str):
        out[prefix] = obj
    return out


def load_maps(donor_locales: Path) -> tuple[dict[str, str], dict[str, str]]:
    zh = json.loads((donor_locales / "zh-CN.json").read_text(encoding="utf-8"))
    en = json.loads((donor_locales / "en-US.json").read_text(encoding="utf-8"))
    ru = json.loads((donor_locales / "ru-RU.json").read_text(encoding="utf-8"))
    zhf, enf, ruf = flatten(zh), flatten(en), flatten(ru)

    zh_map: dict[str, str] = {}
    en_map: dict[str, str] = {}
    for key, target in ruf.items():
        target = target.strip()
        if not target:
            continue
        source_zh = zhf.get(key)
        if isinstance(source_zh, str):
            source_zh = source_zh.strip()
            if source_zh and source_zh != target and HAN.search(source_zh):
                zh_map[source_zh] = target
        source_en = enf.get(key)
        if isinstance(source_en, str):
            source_en = source_en.strip()
            if source_en and source_en != target and CYR.search(target):
                en_map[source_en] = target
    return zh_map, en_map


def translate_exact_literals(text: str, mapping: dict[str, str]) -> tuple[str, int]:
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
            return match.group(0)
        leading = raw[: len(raw) - len(raw.lstrip())]
        trailing = raw[len(raw.rstrip()) :]
        hits += 1
        return f"{quote}{leading}{target}{trailing}{quote}"

    return LITERAL_RX.sub(repl, text), hits


def translate_vue_template(template: str, zh_map: dict[str, str], en_map: dict[str, str]) -> tuple[str, int, int]:
    zh_hits = 0
    en_hits = 0

    def text_repl(match: re.Match[str]) -> str:
        nonlocal zh_hits, en_hits
        raw = match.group("value")
        core = re.sub(r"\s+", " ", raw).strip()
        target = zh_map.get(core)
        if target is not None:
            zh_hits += 1
        else:
            target = en_map.get(core)
            if target is not None:
                en_hits += 1
        if target is None:
            return match.group(0)
        leading = raw[: len(raw) - len(raw.lstrip())]
        trailing = raw[len(raw.rstrip()) :]
        return f">{leading}{target}{trailing}<"

    template = TEXT_NODE_RX.sub(text_repl, template)

    def attr_repl(match: re.Match[str]) -> str:
        nonlocal en_hits
        raw = match.group("value")
        target = en_map.get(raw.strip())
        if target is None:
            return match.group(0)
        quote = match.group("q")
        if quote in target:
            return match.group(0)
        en_hits += 1
        return f"{match.group('name')}{match.group('sep')}{quote}{target}{quote}"

    return VISIBLE_ATTR_RX.sub(attr_repl, template), zh_hits, en_hits


def source_files(root: Path) -> list[Path]:
    files = [p for p in (root / "src").rglob("*") if p.is_file() and p.suffix in SOURCE_EXTS]
    index = root / "index.html"
    if index.exists():
        files.append(index)
    return sorted(set(files))


def normalize_changed_file(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    had_final_newline = text.endswith("\n")
    lines = [line.rstrip(" \t") for line in text.splitlines()]
    normalized = "\n".join(lines)
    if had_final_newline:
        normalized += "\n"
    path.write_text(normalized, encoding="utf-8")


def apply_pass(root: Path, donor_locales: Path) -> dict[str, Any]:
    zh_map, en_map = load_maps(donor_locales)
    changed: set[Path] = set()
    literal_hits = 0
    template_zh_hits = 0
    template_en_hits = 0

    for path in source_files(root):
        text = path.read_text(encoding="utf-8")
        original = text

        text, hits = translate_exact_literals(text, zh_map)
        literal_hits += hits

        if path.suffix == ".vue":
            match = re.search(r"(<template\b[^>]*>)(.*?)(</template>)", text, flags=re.S)
            if match:
                body, zh_hits, en_hits = translate_vue_template(match.group(2), zh_map, en_map)
                template_zh_hits += zh_hits
                template_en_hits += en_hits
                text = text[: match.start(2)] + body + text[match.end(2) :]

        if text != original:
            path.write_text(text, encoding="utf-8")
            changed.add(path)

    index = root / "index.html"
    if index.exists():
        original = index.read_text(encoding="utf-8")
        text = original
        if re.search(r"<html[^>]*\blang=", text):
            text = re.sub(r"(<html[^>]*\blang=)[\"'][^\"']*[\"']", r'\1"ru"', text, count=1)
        else:
            text = text.replace("<html", '<html lang="ru"', 1)
        text = re.sub(r"<title>.*?</title>", "<title>PPTist — редактор презентаций</title>", text, flags=re.S)
        text = re.sub(
            r'<meta name="description" content="[^"]*"\s*/?>',
            '<meta name="description" content="PPTist — браузерный редактор презентаций: создание, импорт, редактирование, показ и экспорт PPT." />',
            text,
            count=1,
        )
        text = re.sub(
            r'<meta name="keywords" content="[^"]*"\s*/?>',
            '<meta name="keywords" content="pptist,ppt,powerpoint,презентации,редактор презентаций,создание презентаций,онлайн ppt,ai презентации" />',
            text,
            count=1,
        )
        text = text.replace("正在加载中，请稍等 ...", "Загрузка, пожалуйста, подождите ...")
        if text != original:
            index.write_text(text, encoding="utf-8")
            changed.add(index)

    for path in sorted(changed):
        normalize_changed_file(path)

    report = {
        "strategy": "whole literal / whole Vue text node / visible English attr only",
        "donor": "robbin2012/PPTist-i18n",
        "zh_dictionary_entries": len(zh_map),
        "en_dictionary_entries": len(en_map),
        "exact_chinese_literal_hits": literal_hits,
        "vue_chinese_text_hits": template_zh_hits,
        "vue_english_visible_hits": template_en_hits,
        "files_changed": len(changed),
        "changed_files": [str(p.relative_to(root)) for p in sorted(changed)],
    }
    return report


def is_comment_line(stripped: str, in_block_comment: bool) -> bool:
    return in_block_comment or stripped.startswith("//") or stripped.startswith("*") or stripped.startswith("<!--")


def dedupe(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    seen = set()
    for item in items:
        key = (item.get("file"), item.get("line"), item.get("text"), item.get("kind"))
        if key not in seen:
            seen.add(key)
            out.append(item)
    return out


def audit(root: Path) -> dict[str, Any]:
    chinese_literals: list[dict[str, Any]] = []
    chinese_template: list[dict[str, Any]] = []
    chinese_noncomment: list[dict[str, Any]] = []
    english_visible: list[dict[str, Any]] = []

    for path in source_files(root):
        content = path.read_text(encoding="utf-8")
        in_template = False
        in_block_comment = False
        rel = str(path.relative_to(root))

        for lineno, line in enumerate(content.splitlines(), 1):
            stripped = line.strip()
            begins_block = "/*" in stripped and "*/" not in stripped
            if begins_block:
                in_block_comment = True
            comment = is_comment_line(stripped, in_block_comment)
            if "<template" in line:
                in_template = True

            if HAN.search(line) and not comment:
                chinese_noncomment.append({"file": rel, "line": lineno, "text": stripped})
                for match in RESIDUAL_LITERAL_RX.finditer(line):
                    value = match.group("value").strip()
                    if value:
                        chinese_literals.append({"file": rel, "line": lineno, "text": value})
                if in_template:
                    for match in RESIDUAL_TEXT_NODE_RX.finditer(line):
                        value = re.sub(r"\s+", " ", match.group("value")).strip()
                        if value:
                            chinese_template.append({"file": rel, "line": lineno, "text": value})

            if in_template:
                for match in VISIBLE_ATTR_RX.finditer(line):
                    value = match.group("value").strip()
                    if re.search(r"[A-Za-z]", value):
                        english_visible.append({"file": rel, "line": lineno, "kind": "attr", "text": value})
                for match in ENGLISH_TEXT_RX.finditer(line):
                    english_visible.append({
                        "file": rel,
                        "line": lineno,
                        "kind": "text",
                        "text": match.group("value").strip(),
                    })

            if "</template>" in line:
                in_template = False
            if "*/" in stripped:
                in_block_comment = False

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


def reject_known_corruption(root: Path) -> None:
    bad = [
        "正在加载Средняя",
        "Применить注销",
        "Крупная部分",
        "边框Линия",
        "Уместить点",
        "Диаграмма数据",
    ]
    offenders = []
    for path in source_files(root):
        text = path.read_text(encoding="utf-8")
        for token in bad:
            if token in text:
                offenders.append(f"{path.relative_to(root)}: {token}")
    if offenders:
        raise SystemExit("Detected substring-corruption artifacts:\n" + "\n".join(offenders))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--donor-locales", required=True)
    args = parser.parse_args()

    root = Path(args.root).resolve()
    donor_locales = Path(args.donor_locales).resolve()
    out = root / ".localization"
    out.mkdir(exist_ok=True)

    pass_report = apply_pass(root, donor_locales)
    reject_known_corruption(root)
    residual = audit(root)

    (out / "pass-1-report.json").write_text(
        json.dumps(pass_report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (out / "residual-ui.json").write_text(
        json.dumps(residual, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    print(json.dumps({"pass": pass_report, "residual_stats": residual["stats"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
