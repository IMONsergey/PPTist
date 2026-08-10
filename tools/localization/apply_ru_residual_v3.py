#!/usr/bin/env python3
"""Third controlled PPTist Russianization pass.

Fixes nested Vue <template> handling from v2. Translations are still exact-only:
complete string literals, complete Vue text nodes, and complete visible attrs.
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
    r"(?P<sep>\s*=\s*)(?P<q>[\"'])(?P<value>[^\"']*)(?P=q)", re.I,
)
SOURCE_EXTS = {'.vue', '.ts', '.tsx', '.js', '.jsx', '.html'}

DYNAMIC_OVERRIDES = {
    "{{ fullscreenState ? 'Выйти из полноэкранного режима' : '全屏' }}":
        "{{ fullscreenState ? 'Выйти из полноэкранного режима' : 'Полный экран' }}",
    "{{playbackRate === 1 ? '倍速' : (playbackRate + 'x')}}":
        "{{playbackRate === 1 ? 'Скорость' : (playbackRate + 'x')}}",
    "循环{{loop ? '开' : '关'}}": "Повтор: {{loop ? 'Вкл.' : 'Выкл.'}}",
}

KNOWN_CORRUPTION = (
    '正在加载Средняя', 'Применить注销', 'Крупная部分', '边框Линия',
    'Уместить点', 'Диаграмма数据', 'Редактироватьor',
)


def source_files(root: Path) -> list[Path]:
    files = [p for p in (root / 'src').rglob('*') if p.is_file() and p.suffix in SOURCE_EXTS]
    index = root / 'index.html'
    if index.exists(): files.append(index)
    return sorted(set(files))


def normalize(path: Path) -> None:
    text = path.read_text(encoding='utf-8')
    final = text.endswith('\n')
    text = '\n'.join(line.rstrip(' \t') for line in text.splitlines())
    if final: text += '\n'
    path.write_text(text, encoding='utf-8')


def replace_literals(text: str, mapping: dict[str, str]) -> tuple[str, int]:
    hits = 0
    def repl(m: re.Match[str]) -> str:
        nonlocal hits
        raw = m.group('value'); key = raw.strip(); target = mapping.get(key)
        if target is None: return m.group(0)
        q = m.group('q')
        if q in target: return m.group(0)
        lead = raw[:len(raw)-len(raw.lstrip())]
        trail = raw[len(raw.rstrip()):]
        hits += 1
        return f'{q}{lead}{target}{trail}{q}'
    return LITERAL_RX.sub(repl, text), hits


def replace_vue_visible(text: str, mapping: dict[str, str]) -> tuple[str, int, int]:
    """Apply exact UI translations across the SFC; mapping membership keeps this safe."""
    text_hits = 0; attr_hits = 0
    def text_repl(m: re.Match[str]) -> str:
        nonlocal text_hits
        raw = m.group('value'); key = re.sub(r'\s+', ' ', raw).strip(); target = mapping.get(key)
        if target is None: return m.group(0)
        lead = raw[:len(raw)-len(raw.lstrip())]
        trail = raw[len(raw.rstrip()):]
        text_hits += 1
        return f'>{lead}{target}{trail}<'
    text = TEXT_NODE_RX.sub(text_repl, text)
    def attr_repl(m: re.Match[str]) -> str:
        nonlocal attr_hits
        target = mapping.get(m.group('value').strip())
        if target is None: return m.group(0)
        q = m.group('q')
        if q in target: return m.group(0)
        attr_hits += 1
        return f"{m.group('name')}{m.group('sep')}{q}{target}{q}"
    return VISIBLE_ATTR_RX.sub(attr_repl, text), text_hits, attr_hits


def is_comment(stripped: str, block: bool) -> bool:
    return block or stripped.startswith('//') or stripped.startswith('*') or stripped.startswith('<!--')


def dedupe(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out=[]; seen=set()
    for item in items:
        key=(item.get('file'), item.get('line'), item.get('text'), item.get('kind'))
        if key not in seen: seen.add(key); out.append(item)
    return out


def audit(root: Path) -> dict[str, Any]:
    literal_han = re.compile(r'''(?P<q>["'`])(?P<value>[^"'`\n]*[\u3400-\u4dbf\u4e00-\u9fff][^"'`\n]*)(?P=q)''')
    node_han = re.compile(r">(?P<value>[^<>\n]*[\u3400-\u4dbf\u4e00-\u9fff][^<>\n]*)<")
    english_text = re.compile(r">\s*(?P<value>[A-Za-z][A-Za-z0-9 /+&()_.:,!?#-]{2,})\s*<")
    chinese_literals=[]; chinese_nodes=[]; chinese_lines=[]; english_visible=[]

    for path in source_files(root):
        content=path.read_text(encoding='utf-8'); rel=str(path.relative_to(root))
        depth=0; block=False
        for lineno,line in enumerate(content.splitlines(),1):
            stripped=line.strip()
            opens=len(re.findall(r'<template\b', line)); closes=line.count('</template>')
            depth += opens
            in_template = depth > 0
            if '/*' in stripped and '*/' not in stripped: block=True
            comment=is_comment(stripped, block)
            if HAN.search(line) and not comment:
                chinese_lines.append({'file':rel,'line':lineno,'text':stripped})
                for m in literal_han.finditer(line):
                    value=m.group('value').strip()
                    if value: chinese_literals.append({'file':rel,'line':lineno,'text':value})
                if in_template:
                    for m in node_han.finditer(line):
                        value=re.sub(r'\s+',' ',m.group('value')).strip()
                        if value: chinese_nodes.append({'file':rel,'line':lineno,'text':value})
            if in_template:
                for m in VISIBLE_ATTR_RX.finditer(line):
                    value=m.group('value').strip()
                    if re.search(r'[A-Za-z]', value): english_visible.append({'file':rel,'line':lineno,'kind':'attr','text':value})
                for m in english_text.finditer(line):
                    english_visible.append({'file':rel,'line':lineno,'kind':'text','text':m.group('value').strip()})
            if '*/' in stripped: block=False
            depth=max(0, depth-closes)

    chinese_literals=dedupe(chinese_literals); chinese_nodes=dedupe(chinese_nodes)
    chinese_lines=dedupe(chinese_lines); english_visible=dedupe(english_visible)
    return {
        'stats': {
            'chinese_noncomment_lines':len(chinese_lines),
            'chinese_string_literals':len(chinese_literals),
            'chinese_template_text_nodes':len(chinese_nodes),
            'english_visible_candidates':len(english_visible),
        },
        'chinese_string_literals':chinese_literals,
        'chinese_template_text_nodes':chinese_nodes,
        'english_visible_candidates':english_visible,
        'chinese_noncomment_lines':chinese_lines,
    }


def main() -> None:
    ap=argparse.ArgumentParser(); ap.add_argument('--root',default='.'); ap.add_argument('--map',required=True); args=ap.parse_args()
    root=Path(args.root).resolve(); payload=json.loads(Path(args.map).resolve().read_text(encoding='utf-8'))
    mapping=dict(payload['translations']); mapping.update(DYNAMIC_OVERRIDES)
    changed=set(); literal_hits=text_hits=attr_hits=0

    for path in source_files(root):
        text=path.read_text(encoding='utf-8'); original=text
        text,h=replace_literals(text,mapping); literal_hits+=h
        if path.suffix=='.vue':
            text,th,ah=replace_vue_visible(text,mapping); text_hits+=th; attr_hits+=ah
        if text!=original:
            path.write_text(text,encoding='utf-8'); normalize(path); changed.add(path)

    offenders=[]
    for path in source_files(root):
        text=path.read_text(encoding='utf-8')
        for token in KNOWN_CORRUPTION:
            if token in text: offenders.append(f'{path.relative_to(root)}: {token}')
    if offenders: raise SystemExit('Known localization corruption detected:\n'+'\n'.join(offenders))

    residual=audit(root); out=root/'.localization'; out.mkdir(exist_ok=True)
    report={'map_entries':len(mapping),'literal_hits':literal_hits,'template_hits':text_hits,'visible_attr_hits':attr_hits,
            'files_changed':len(changed),'changed_files':[str(p.relative_to(root)) for p in sorted(changed)]}
    (out/'pass-3-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (out/'residual-after-pass-3.json').write_text(json.dumps(residual,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'pass':report,'residual':residual['stats']},ensure_ascii=False,indent=2))

if __name__=='__main__': main()
