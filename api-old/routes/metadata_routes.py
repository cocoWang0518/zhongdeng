import traceback

import pymysql
from flask import Blueprint, jsonify, request

from api.routes.db_routes import _get_db_config

metadata_bp = Blueprint("metadata", __name__)

FEATURE_MODELS = (
    "信用债模型",
    "债项主体模型",
    "ABS模型",
    "城投债模型",
    "城投主体模型",
    "基金主体模型",
)

ASSET_MODELS = (
    "信用债模型",
    "债项主体模型",
    "ABS模型",
    "城投债模型",
    "城投主体模型",
    "基金模型",
    "基金主体模型",
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
    selected_model, error_response = _validate_model(
        request.args.get("model"),
        FEATURE_MODELS,
    )
    if error_response:
        return error_response

    try:
        conn = _get_connection()
        with conn:
            with conn.cursor() as cursor:
                models = _build_model_counts(
                    cursor,
                    "feature_info_mapping",
                    "used_model",
                    FEATURE_MODELS,
                )
                cursor.execute(
                    """
                    SELECT
                        id,
                        feature_name,
                        actual_meaning,
                        data_source,
                        feature_category,
                        calculation_method,
                        used_model
                    FROM feature_info_mapping
                    WHERE used_model = %s
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
