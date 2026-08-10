#!/usr/bin/env python3
"""Translate shipped PPTist demo/mock JSON content from Chinese to Russian."""
from __future__ import annotations

import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from deep_translator import GoogleTranslator

HAN = re.compile(r'[\u3400-\u4dbf\u4e00-\u9fff]')
PROTECT = re.compile(
    r'(\$\{[^{}]*\}|\{\{.*?\}\}|<[^>]+>|https?://[^\s"<>]+|'
    r'\b(?:PPTX?|PPTIST|JSON|SVG|LaTeX|AIGC|AI|API|HTML|CSS|JavaScript|Web|Ctrl|Shift|ESC|Space)\b)',
    re.I,
)

OVERRIDES = {
    '未命名演示文稿': 'Презентация без названия',
    '基于 Web 的开源演示文稿（幻灯片）应用，可以在浏览器中编辑/演示幻灯片。':
        'Открытое веб-приложение для презентаций (слайдов), в котором можно редактировать и показывать презентации прямо в браузере.',
    '犯罪心理学研究': 'Исследование криминальной психологии',
    '犯罪心理学概述': 'Обзор криминальной психологии',
    '犯罪心理的形成': 'Формирование криминального поведения',
    '犯罪类型与心理特征': 'Типы преступлений и психологические особенности',
    '犯罪心理评估与干预': 'Оценка криминальной психологии и вмешательство',
    '犯罪心理学的应用': 'Применение криминальной психологии',
    '未来发展趋势': 'Будущие направления развития',
    '感谢观看': 'Спасибо за внимание',
    '目录': 'Содержание',
    '谢谢': 'Спасибо',
}


def protect(text: str) -> tuple[str, list[tuple[str, str]]]:
    tokens: list[tuple[str, str]] = []
    def repl(match: re.Match[str]) -> str:
        token = f'ZXQMOCK{len(tokens):03d}QXZ'
        tokens.append((token, match.group(0)))
        return token
    return PROTECT.sub(repl, text), tokens


def restore(text: str, tokens: list[tuple[str, str]]) -> str:
    for token, original in tokens:
        for variant in (token, token.lower(), token.upper(), token.capitalize()):
            text = text.replace(variant, original)
    return text


def collect(value: Any, out: set[str]) -> None:
    if isinstance(value, str):
        if HAN.search(value): out.add(value)
    elif isinstance(value, list):
        for item in value: collect(item, out)
    elif isinstance(value, dict):
        for item in value.values(): collect(item, out)


def translate_one(source: str) -> tuple[str, str | None]:
    if source in OVERRIDES:
        return OVERRIDES[source], None
    protected, tokens = protect(source)
    last = None
    for attempt in range(4):
        try:
            translated = GoogleTranslator(source='zh-CN', target='ru').translate(protected)
            translated = restore(translated, tokens).strip()
            if translated and not HAN.search(translated):
                return translated, None
            last = f'invalid translation: {translated!r}'
        except Exception as exc:
            last = repr(exc)
        time.sleep(0.8 * (attempt + 1))
    return source, last or 'translation failed'


def replace(value: Any, mapping: dict[str, str]) -> Any:
    if isinstance(value, str):
        return mapping.get(value, value)
    if isinstance(value, list):
        return [replace(item, mapping) for item in value]
    if isinstance(value, dict):
        return {key: replace(item, mapping) for key, item in value.items()}
    return value


def main() -> None:
    root = Path('public/mocks')
    paths = sorted(root.rglob('*.json'))
    docs: dict[Path, Any] = {}
    original_text: dict[Path, str] = {}
    strings: set[str] = set()

    for path in paths:
        text = path.read_text(encoding='utf-8')
        original_text[path] = text
        doc = json.loads(text)
        docs[path] = doc
        collect(doc, strings)

    mapping: dict[str, str] = {}
    errors: dict[str, str] = {}
    sources = sorted(strings, key=lambda x: (len(x), x))
    print(f'Unique Chinese mock strings: {len(sources)}')

    # Network-bound translations are independent; moderate concurrency keeps the workflow
    # fast while avoiding excessive request bursts.
    with ThreadPoolExecutor(max_workers=6) as pool:
        future_map = {pool.submit(translate_one, source): source for source in sources}
        for index, future in enumerate(as_completed(future_map), 1):
            source = future_map[future]
            try:
                translated, error = future.result()
            except Exception as exc:
                translated, error = source, repr(exc)
            if error:
                errors[source] = error
            else:
                mapping[source] = translated
            if index % 50 == 0:
                print(f'Translated {index}/{len(sources)}')

    # Sequential recovery is friendlier to rate limits for any failed parallel calls.
    if errors:
        retry_sources = list(errors)
        errors = {}
        for index, source in enumerate(retry_sources, 1):
            translated, error = translate_one(source)
            if error: errors[source] = error
            else: mapping[source] = translated
            if index % 20 == 0: print(f'Retried {index}/{len(retry_sources)}')

    missing = [source for source in sources if source not in mapping]
    if missing:
        Path('.localization/mock-translation-errors.json').write_text(
            json.dumps({'missing': missing, 'errors': errors}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8'
        )
        raise SystemExit(f'Failed to translate {len(missing)} mock strings')

    changed_files = []
    for path, doc in docs.items():
        translated_doc = replace(doc, mapping)
        original = original_text[path]
        # Preserve minified vs pretty formatting style.
        if original.count('\n') <= 2:
            output = json.dumps(translated_doc, ensure_ascii=False, separators=(',', ':')) + '\n'
        else:
            output = json.dumps(translated_doc, ensure_ascii=False, indent=2) + '\n'
        if output != original:
            path.write_text(output, encoding='utf-8')
            changed_files.append(str(path))

    residual = []
    for path in paths:
        text = path.read_text(encoding='utf-8')
        match = HAN.search(text)
        if match:
            residual.append({'file': str(path), 'sample': text[max(0, match.start()-80):match.start()+240]})

    report = {
        'json_files_scanned': len(paths),
        'unique_chinese_strings': len(sources),
        'translated_strings': len(mapping),
        'changed_files': changed_files,
        'remaining_han_files': residual,
    }
    Path('.localization/mock-translation-report.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8'
    )
    print(json.dumps({k:v for k,v in report.items() if k != 'changed_files'}, ensure_ascii=False, indent=2))
    if residual:
        raise SystemExit(f'Chinese text remains in {len(residual)} mock JSON files')


if __name__ == '__main__':
    main()
