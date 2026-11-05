"""统一指标目录：现有分类读取数据库，更新分类使用经过核对的文件定义。"""
from functools import lru_cache
from pathlib import Path
import json

from api.services.indicator_definitions import apply_verified_definitions

CATALOG_PATH = Path(__file__).resolve().parents[2] / "file" / "indicator_catalog_20261020.json"

CATEGORY_LEGACY_MODELS = {
    "非金融主体": "债项主体模型",
    "非金融债": "信用债模型",
    "城投主体": "城投主体模型",
    "城投债": "城投债模型",
    "银行主体": "银行主体模型",
    "银行债": "银行债券模型",
    "保险主体": "保险主体模型",
    "保险债": "保险债项模型",
    "证券主体": "券商主体模型",
    "证券公司债": "券商债券模型",
    "信托主体": None,
    "信托公司债": None,
    "资产管理产品": None,
    "信贷类ABS": "ABS模型",
    "场内基金管理人主体": "基金主体模型",
}
FEATURE_CATEGORIES = tuple(CATEGORY_LEGACY_MODELS)
LEGACY_CATEGORY_ALIASES = {old: new for new, old in CATEGORY_LEGACY_MODELS.items() if old}
FILE_CATEGORIES = {"银行主体", "银行债", "保险主体", "保险债", "信托主体", "信托公司债", "资产管理产品", "信贷类ABS"}
FIELDS = ("feature_name", "actual_meaning", "data_source", "feature_category", "calculation_method")


@lru_cache(maxsize=1)
def load_file_catalog():
    with CATALOG_PATH.open(encoding="utf-8") as stream:
        catalog = json.load(stream)
    if tuple(catalog["categories"]) != FEATURE_CATEGORIES:
        raise ValueError("指标文件的分类及顺序与系统配置不一致。")
    return catalog


def build_indicator_catalog(connection_factory):
    """数据库暂不可用时使用已核对的本地快照，不阻断文件分类。"""
    catalog = load_file_catalog()
    result = {category: [dict(row) for row in catalog["categories"][category]] for category in FEATURE_CATEGORIES}
    database_available = False
    try:
        connection = connection_factory()
        with connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT * FROM feature_info_mapping ORDER BY id"
                )
                rows = cursor.fetchall()
        # 文件已更新的银行、保险、信托、资管产品和ABS不被旧库定义覆盖。
        grouped = {}
        for row in rows:
            category = LEGACY_CATEGORY_ALIASES.get(row["used_model"])
            if category and category not in FILE_CATEGORIES:
                grouped.setdefault(category, []).append({field: row.get(field) for field in FIELDS})
        for category, items in grouped.items():
            result[category] = items
        database_available = True
    except Exception as exc:
        # 原始快照有完整的旧分类及公共因子，连接失败仍返回真实已有定义。
        print(f"指标目录使用已保存的指标快照（{type(exc).__name__}）")
    # 必须在数据库覆盖之后核对，防止原库的串填说明重新污染页面。
    apply_verified_definitions(result)
    for category, rows in result.items():
        for index, row in enumerate(rows, start=1):
            row.update(id=index, index=index, used_model=category)
    return result, database_available, catalog["version"]
