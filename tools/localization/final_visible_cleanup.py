#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

HAN = re.compile(r'[\u3400-\u4dbf\u4e00-\u9fff]')
SOURCE_EXTS = {'.vue', '.ts', '.tsx', '.js', '.jsx', '.html'}

REPLACEMENTS = {
    'src/components/ChartDataEditor.vue': [
        ('图表类型：{{ CHART_TYPE_MAP[chartType] }}', 'Тип диаграммы: {{ CHART_TYPE_MAP[chartType] }}'),
    ],
    'src/views/Editor/Canvas/index.vue': [
        ("message.success(`元素气泡菜单已${showBubbleMenu.value ? 'Включить' : 'Отключить'}`)",
         "message.success(`Плавающее меню элементов: ${showBubbleMenu.value ? 'включено' : 'отключено'}`)"),
    ],
    'src/views/Editor/ExportDialog/ExportPDF.vue': [
        ('建议：请在弹出的打印窗口中勾选「背景图形」选项，边距选择「默认」。',
         'Совет: в окне печати включите «Фоновая графика» и выберите поля «По умолчанию».'),
    ],
    'src/views/Editor/ExportDialog/ExportPPTX.vue': [
        ('提示：1. 支持导出格式：avi、mp4、mov、wmv、mp3、wav；2. 跨域资源无法导出。',
         'Примечание: 1. Поддерживаются форматы avi, mp4, mov, wmv, mp3, wav. 2. Ресурсы с других доменов экспортировать нельзя.'),
    ],
    'src/views/Editor/ExportDialog/ExportSpecificFile.vue': [
        ('提示：.pptist 是本应用的特有文件后缀，支持将该类型的文件导入回应用中。',
         'Примечание: .pptist — собственный формат приложения; такой файл можно импортировать обратно.'),
    ],
    'src/views/Editor/NotesPanel.vue': [
        ("`输入批注（为${handleElementId ? 'Выбранный элемент' : 'Текущий слайд' }）`",
         "`Введите комментарий (${handleElementId ? 'выбранный элемент' : 'текущий слайд'})`"),
    ],
    'src/views/Editor/Toolbar/ElementAnimationPanel.vue': [
        ('<i-icon-park-outline:effects /> 添加动画', '<i-icon-park-outline:effects /> Добавить анимацию'),
    ],
    'src/views/Editor/Toolbar/ElementPositionPanel.vue': [
        ('水平：', 'По горизонтали:'), ('垂直：', 'По вертикали:'),
        ('宽度：', 'Ширина:'), ('高度：', 'Высота:'), ('旋转：', 'Поворот:'),
    ],
    'src/views/Editor/Toolbar/ElementStylePanel/ChartStylePanel/ThemeColorsSetting.vue': [
        ('<i-icon-park-outline:plus /> 添加主题色', '<i-icon-park-outline:plus /> Добавить цвет темы'),
    ],
    'src/views/Editor/Toolbar/ElementStylePanel/ChartStylePanel/index.vue': [
        ('<i-icon-park-outline:edit /> 编辑图表', '<i-icon-park-outline:edit /> Редактировать диаграмму'),
    ],
    'src/views/Mobile/MobileEditor/SlideToolbar.vue': [
        ('<i-icon-park-outline:picture class="icon" /> 图片', '<i-icon-park-outline:picture class="icon" /> Изображение'),
    ],
}


def source_files() -> list[Path]:
    return sorted(p for p in Path('src').rglob('*') if p.is_file() and p.suffix in SOURCE_EXTS)


def normalize(path: Path) -> None:
    text = path.read_text(encoding='utf-8')
    final = text.endswith('\n')
    text = '\n'.join(line.rstrip(' \t') for line in text.splitlines())
    if final:
        text += '\n'
    path.write_text(text, encoding='utf-8')


def apply_fixes() -> list[dict[str, object]]:
    report: list[dict[str, object]] = []
    for path_str, pairs in REPLACEMENTS.items():
        path = Path(path_str)
        text = path.read_text(encoding='utf-8')
        original = text
        for old, new in pairs:
            count = text.count(old)
            # Idempotent reruns are allowed: if the source is gone but translated text exists,
            # treat it as already fixed rather than failing.
            if count == 0:
                if new in text:
                    report.append({'file': path_str, 'from': old, 'to': new, 'count': 0, 'already_fixed': True})
                    continue
                raise SystemExit(f'Expected visible fragment not found: {path_str}: {old}')
            text = text.replace(old, new)
            report.append({'file': path_str, 'from': old, 'to': new, 'count': count})
        if text != original:
            path.write_text(text, encoding='utf-8')
            normalize(path)
    return report


def strip_comments(line: str, block: bool, html: bool) -> tuple[str, bool, bool]:
    """Return code/markup outside comments while preserving multiline comment state."""
    out: list[str] = []
    i = 0
    n = len(line)
    while i < n:
        if block:
            end = line.find('*/', i)
            if end == -1:
                return ''.join(out), True, html
            block = False
            i = end + 2
            continue
        if html:
            end = line.find('-->', i)
            if end == -1:
                return ''.join(out), block, True
            html = False
            i = end + 3
            continue
        if line.startswith('//', i):
            break
        if line.startswith('/*', i):
            block = True
            i += 2
            continue
        if line.startswith('<!--', i):
            html = True
            i += 4
            continue
        out.append(line[i])
        i += 1
    return ''.join(out), block, html


def audit_noncomment_han() -> dict[str, object]:
    violations = []
    comment_lines = []
    for path in source_files():
        block = False
        html = False
        for lineno, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
            had_han = bool(HAN.search(line))
            visible, block, html = strip_comments(line, block, html)
            if not had_han:
                continue
            if HAN.search(visible):
                violations.append({'file': str(path), 'line': lineno, 'text': line.strip(), 'visible_part': visible.strip()})
            else:
                comment_lines.append({'file': str(path), 'line': lineno, 'text': line.strip()})
    return {
        'stats': {'noncomment_han_violations': len(violations), 'han_comment_lines': len(comment_lines)},
        'noncomment_han_violations': violations,
        'han_comment_lines': comment_lines,
    }


def main() -> None:
    Path('.localization').mkdir(exist_ok=True)
    fixes = apply_fixes()
    audit = audit_noncomment_han()
    Path('.localization/final-visible-fixes.json').write_text(json.dumps(fixes, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    Path('.localization/final-source-han-audit.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'fixes': sum(int(x.get('count', 0)) for x in fixes), **audit['stats']}, ensure_ascii=False, indent=2))
    if audit['noncomment_han_violations']:
        print(json.dumps(audit['noncomment_han_violations'][:50], ensure_ascii=False, indent=2))
        raise SystemExit('Chinese text remains outside comments')


if __name__ == '__main__':
    main()
