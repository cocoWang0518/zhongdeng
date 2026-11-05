"""按原始指标名称核对说明，避免空白单元格被上一行公式污染。"""
from functools import lru_cache
from pathlib import Path
import json
import re

REFERENCE_PATH = Path(__file__).resolve().parents[2] / 'file/indicator_definition_reference_20261020.json'
TARGET_CATEGORIES = {'非金融主体', '非金融债', '城投主体', '城投债'}


def normalize_meaning(value):
    return re.sub(r'\s+', '', value or '').casefold()


def indicator_family(category, code):
    city = category in {'城投主体', '城投债'}
    prefix = re.sub(r'\d+$', '', code or '')
    if prefix in {'M', 'AM', 'CM'}:
        return '城投宏观' if city else '公共宏观'
    if prefix == 'NF':
        return '城投非财务' if city else '公共非财务'
    if category in TARGET_CATEGORIES:
        if prefix in {'F', 'CF'}:
            return '城投财务' if city else '非金融财务'
        if prefix == 'B':
            return '城投债项' if city else '非金融债项'
    return None


@lru_cache(maxsize=1)
def load_reference_index():
    with REFERENCE_PATH.open(encoding='utf-8') as stream:
        source = json.load(stream)
    index = {}
    for row in source['references']:
        index.setdefault((row['family'], normalize_meaning(row['actual_meaning'])), []).append(row)
    return index


def find_reference(category, row):
    family = indicator_family(category, row.get('feature_name'))
    if family is None:
        return None
    candidates = load_reference_index().get((family, normalize_meaning(row.get('actual_meaning'))), [])
    if not candidates:
        return None
    # 一份资料留空不等于否定另一份资料的明确说明；例如GDP的“单位：亿元”有报告依据，应保留。
    provided = [item for item in candidates if item['calculation_method'] and item['calculation_method'].strip() not in {'/', '-'}]
    if provided:
        candidates = provided
    priority = min(item['priority'] for item in candidates)
    candidates = [item for item in candidates if item['priority'] == priority]
    same_code = [item for item in candidates if item['feature_name'] == row.get('feature_name')]
    if same_code:
        candidates = same_code
    methods = {normalize_meaning(item['calculation_method']) for item in candidates}
    return candidates[0] if len(methods) == 1 else None


def apply_verified_definitions(catalog):
    """同时作用于实时数据库返回和离线目录，不修改指标条数和原库。"""
    audit = []
    for category, rows in catalog.items():
        for row in rows:
            if indicator_family(category, row.get('feature_name')) is None:
                continue
            reference = find_reference(category, row)
            before = row.get('calculation_method')
            method = reference['calculation_method'] if reference else None
            method = method.strip() if method and method.strip() not in {'/', '-'} else None
            row['calculation_method'] = method
            row['calculation_method_status'] = ('verified' if method else 'not_provided') if reference else 'unverified'
            if before != method:
                audit.append(dict(category=category, feature_name=row.get('feature_name'),
                    actual_meaning=row.get('actual_meaning'), before=before, after=method,
                    status=row['calculation_method_status'], reference=reference))
    return audit
