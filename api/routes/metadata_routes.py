import traceback

import pymysql
from flask import Blueprint, jsonify, request

from api.routes.db_routes import _get_db_config
from api.services.indicator_catalog import (
    FEATURE_CATEGORIES,
    LEGACY_CATEGORY_ALIASES,
    build_indicator_catalog,
)

metadata_bp = Blueprint("metadata", __name__)

FEATURE_MODELS = FEATURE_CATEGORIES

ASSET_MODELS = (
    "信用债模型",
    "债项主体模型",
    "ABS模型",
    "城投债模型",
    "城投主体模型",
    "基金模型",
    "基金主体模型",
    "保险主体模型",
    "保险债项模型",
    "券商主体模型",
    "券商债项模型",
    "银行主体模型",
    "银行债项模型",
)


def _get_connection():
    return pymysql.connect(**_get_db_config(), cursorclass=pymysql.cursors.DictCursor)


def _validate_model(model, allowed_models):
    selected_model = (model or allowed_models[0]).strip()
    if selected_model not in allowed_models:
        return None, (
            jsonify(
                {
                    "status": "error",
                    "message": f"model 必须为: {', '.join(allowed_models)}",
                }
            ),
            400,
        )
    return selected_model, None


def _build_model_counts(cursor, table_name, model_column, allowed_models):
    cursor.execute(
        f"""
        SELECT `{model_column}` AS model, COUNT(*) AS count
        FROM `{table_name}`
        GROUP BY `{model_column}`
        """
    )
    count_map = {row["model"]: row["count"] for row in cursor.fetchall()}
    return [
        {"label": model, "value": model, "count": int(count_map.get(model, 0))}
        for model in allowed_models
    ]


@metadata_bp.route("/metadata/features", methods=["GET"])
def get_feature_metadata():
    requested_model = (request.args.get("model") or "").strip()
    selected_model, error_response = _validate_model(
        LEGACY_CATEGORY_ALIASES.get(requested_model, requested_model),
        FEATURE_MODELS,
    )
    if error_response:
        return error_response

    try:
        def connect_indicators():
            return pymysql.connect(
                **_get_db_config(), cursorclass=pymysql.cursors.DictCursor,
                connect_timeout=1, read_timeout=3,
            )

        catalog, database_available, version = build_indicator_catalog(connect_indicators)
        models = [
            {"label": category, "value": category, "count": len(catalog[category])}
            for category in FEATURE_MODELS
        ]
        items = catalog[selected_model]

        return jsonify(
            {
                "status": "success",
                "models": models,
                "selected_model": selected_model,
                "total": len(items),
                "items": items,
                "catalog_version": version,
                "database_available": database_available,
            }
        )
    except Exception as exc:
        error_msg = traceback.format_exc()
        print(f"指标元数据接口错误: {error_msg}")
        return jsonify({"status": "error", "message": str(exc)}), 500


@metadata_bp.route("/metadata/assets", methods=["GET"])
def get_asset_metadata():
    selected_model, error_response = _validate_model(
        request.args.get("model"),
        ASSET_MODELS,
    )
    if error_response:
        return error_response

    try:
        conn = _get_connection()
        with conn:
            with conn.cursor() as cursor:
                models = _build_model_counts(
                    cursor,
                    "asset_model_mapping",
                    "适用模型",
                    ASSET_MODELS,
                )
                cursor.execute(
                    """
                    SELECT id, `资产代码`, `资产名称`, `适用模型`
                    FROM asset_model_mapping
                    WHERE `适用模型` = %s
                    ORDER BY id
                    """,
                    (selected_model,),
                )
                items = cursor.fetchall()

        for index, item in enumerate(items, start=1):
            item["index"] = index

        return jsonify(
            {
                "status": "success",
                "models": models,
                "selected_model": selected_model,
                "total": len(items),
                "items": items,
            }
        )
    except Exception as exc:
        error_msg = traceback.format_exc()
        print(f"资产元数据接口错误: {error_msg}")
        return jsonify({"status": "error", "message": str(exc)}), 500
