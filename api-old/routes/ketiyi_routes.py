from flask import Blueprint, request, jsonify
from pathlib import Path
import traceback
import pandas as pd
from ketiyi_yewushifan import (
    get_historical_ratings_fuzzy,
    apply_feature_mapping_to_result,
    get_feature_mapping_from_db,
    get_Explanation,
    draw_rating_trend_with_default,
)

ketiyi_bp = Blueprint("ketiyi", __name__)

VALID_QUERY_BOND_TYPES = ("", "基金")
VALID_DETAIL_BOND_TYPES = ("城投债", "信用债", "ABS债", "债项主体", "城投主体")
BOND_TYPE_MAPPING_TABLES = {
    "城投债": "city-gbdt_feature_importance",
    "信用债": "credit-gbdt_feature_importance",
    "ABS债": "abs_gbdt_feature_importance",
    "债项主体": "bond_subject_rf_feature_importance",
    "城投主体": "city_subject_gbdt_feature_importance",
}


def get_feature_mapping_for_type(bond_type):
    """根据识别出的资产类型读取数据库列注释映射。"""
    table_name = BOND_TYPE_MAPPING_TABLES.get(bond_type)
    if not table_name:
        return {}
    return get_feature_mapping_from_db(table_name)


@ketiyi_bp.route("/ketiyi/query", methods=["POST"])
def ketiyi_query():
    """
    查询接口：模糊搜索债券并返回评级结果 + 历史评级
    请求参数：
    {
        "keyword": "194788",
        "bond_type": ""   // "" 自动识别 | "基金" 基金专用查询
    }
    """
    try:
        data = request.get_json()

        if not data:
            return (
                jsonify(
                    {"status": "error", "message": "请求体不能为空，需要JSON格式数据"}
                ),
                400,
            )

        keyword = data.get("keyword", "").strip()
        bond_type = (data.get("bond_type") or "").strip()

        if not keyword:
            return (
                jsonify({"status": "error", "message": "缺少必需参数: keyword"}),
                400,
            )

        if bond_type not in VALID_QUERY_BOND_TYPES:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": 'bond_type 只能为 ""（正常查询）或 "基金"',
                    }
                ),
                400,
            )

        df_history, result, identifier_data, model_metrics, detected_type = get_historical_ratings_fuzzy(
            keyword, bond_type=bond_type
        )
        effective_type = detected_type or identifier_data.get("资产类型") or bond_type

        if not identifier_data:
            return (
                jsonify({"status": "error", "message": "未找到匹配数据"}),
                404,
            )

        if result and effective_type != "基金":
            mapping_dict = get_feature_mapping_for_type(effective_type)
            result = apply_feature_mapping_to_result(result, mapping_dict)

        result_records = []
        if result:
            result_records = pd.DataFrame(
                {
                    "模型名称": list(result.keys()),
                    "模型评级": [result[model]["prediction"] for model in result.keys()],
                    "importance": [
                        result[model]["importance"].to_dict(orient="records")
                        for model in result.keys()
                    ],
                }
            ).to_dict("records")
        elif effective_type == "基金":
            result_records = [
                {
                    "模型名称": "FundModel",
                    "模型评级": str(identifier_data.get("基金评级分组", "无数据")),
                    "importance": [],
                }
            ]

        history_records = []
        if not df_history.empty:
            history_records = df_history.to_dict(orient="records")

        response_data = {
            "status": "success",
            "data": {
                "bond_type": effective_type,
                "detected_type": effective_type,
                "model_metrics": model_metrics,
                "identifier_data": identifier_data,
                "df_results": result_records,
                "df_history": history_records,
            },
        }

        return jsonify(response_data)

    except Exception as e:
        error_msg = traceback.format_exc()
        print(f"查询接口错误: {error_msg}")
        return (
            jsonify({"status": "error", "message": str(e), "traceback": error_msg}),
            500,
        )


@ketiyi_bp.route("/ketiyi/trend", methods=["POST"])
def ketiyi_trend():
    """
    趋势图接口：根据历史评级数据生成评级趋势图
    请求参数：
    {
        "df_history": [{"时间": "2023-01", "GBDT": "AA", ...}, ...],
        "bond_name": "22渠县02",
        "default_date": "2023-08-01"   // 可选，违约日期
    }
    """
    try:
        data = request.get_json()
        if not data:
            return (
                jsonify({"status": "error", "message": "请求体不能为空"}),
                400,
            )

        history = data.get("df_history")
        bond_name = data.get("bond_name", "未知债券")
        default_date = data.get("default_date")

        if not history or not isinstance(history, list):
            return (
                jsonify({"status": "error", "message": "缺少必需参数: df_history"}),
                400,
            )

        df_history = pd.DataFrame(history)

        import base64
        from pathlib import Path
        from uuid import uuid4

        tmp_dir = Path(__file__).resolve().parents[2] / "tmp"
        tmp_dir.mkdir(parents=True, exist_ok=True)
        temp_path = tmp_dir / f"trend_{uuid4().hex}.png"

        try:
            draw_rating_trend_with_default(
                df_history, bond_name, default_date=default_date, save_path=str(temp_path)
            )
            img_base64 = base64.b64encode(temp_path.read_bytes()).decode("utf-8")
        finally:
            try:
                temp_path.unlink(missing_ok=True)
            except Exception:
                pass

        return jsonify(
            {
                "status": "success",
                "data": {
                    "trend_image": "data:image/png;base64," + img_base64,
                },
            }
        )

    except Exception as e:
        error_msg = traceback.format_exc()
        print(f"趋势图接口错误: {error_msg}")
        return (
            jsonify({"status": "error", "message": str(e), "traceback": error_msg}),
            500,
        )


@ketiyi_bp.route("/ketiyi/detail", methods=["POST"])
def ketiyi_detail():
    """
    详情接口：根据特征重要性(result[model_name]["importance"])生成模型解释文本和可视化图片
    请求参数：
    {
        "importance": [
            {"Feature": "F1", "Importance": 0.123},
            {"Feature": "F2", "Importance": 0.089},
            ...
        ],
        "bond_type": "城投债"  // 可选，城投债 | 信用债 | ABS债
    }

    兼容旧字段：feature_importance
    """
    try:
        # 获取JSON请求数据
        data = request.get_json()

        # 验证必需参数
        if not data:
            return (
                jsonify(
                    {"status": "error", "message": "请求体不能为空，需要JSON格式数据"}
                ),
                400,
            )

        feature_importance = data.get("importance")
        if feature_importance is None:
            feature_importance = data.get("feature_importance")
        bond_type = (data.get("bond_type") or "城投债").strip()

        # 验证必需参数
        if feature_importance is None:
            return (
                jsonify({"status": "error", "message": "缺少必需参数: importance"}),
                400,
            )

        # 允许前端把 JSON 字符串直接传过来
        if isinstance(feature_importance, str):
            import json

            try:
                feature_importance = json.loads(feature_importance)
            except Exception:
                return (
                    jsonify(
                        {
                            "status": "error",
                            "message": "importance 不是合法的 JSON 字符串",
                        }
                    ),
                    400,
                )

        # 兼容 DataFrame.to_json(orient='columns') 等 dict 结构
        if isinstance(feature_importance, dict):
            # 期望: {"Feature": [...], "Importance": [...]}
            if (
                "Feature" in feature_importance
                and "Importance" in feature_importance
                and isinstance(feature_importance.get("Feature"), list)
                and isinstance(feature_importance.get("Importance"), list)
            ):
                features = feature_importance.get("Feature")
                importances = feature_importance.get("Importance")
                if len(features) != len(importances):
                    return (
                        jsonify(
                            {
                                "status": "error",
                                "message": "importance 字段中 Feature 与 Importance 长度不一致",
                            }
                        ),
                        400,
                    )
                feature_importance = [
                    {"Feature": f, "Importance": imp}
                    for f, imp in zip(features, importances)
                ]
            else:
                return (
                    jsonify(
                        {
                            "status": "error",
                            "message": "importance 必须是数组(list)或包含 Feature/Importance 列表的对象(dict)",
                        }
                    ),
                    400,
                )

        if not isinstance(feature_importance, list):
            return (
                jsonify({"status": "error", "message": "importance 必须是数组格式"}),
                400,
            )

        if len(feature_importance) == 0:
            return (
                jsonify({"status": "error", "message": "importance 不能为空"}),
                400,
            )

        if bond_type not in VALID_DETAIL_BOND_TYPES:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": f"bond_type 必须为: {', '.join(VALID_DETAIL_BOND_TYPES)}",
                    }
                ),
                400,
            )

        mapping_dict = get_feature_mapping_for_type(bond_type)
        if mapping_dict:
            for item in feature_importance:
                feature = item.get("Feature")
                if feature in mapping_dict:
                    item["Feature"] = mapping_dict[feature]

        # 调用get_Explanation函数获取解释文本和处理后的数据
        all_plot_data, model_text = get_Explanation(
            feature_importance,
        )

        # 生成图片并转换为base64
        import base64
        from pathlib import Path
        from uuid import uuid4

        from ketiyi_yewushifan import generate_plot

        # Windows 下 NamedTemporaryFile 可能导致文件占用/写入失败；统一使用项目目录 tmp/ 生成临时文件
        tmp_dir = Path(__file__).resolve().parents[2] / "tmp"
        tmp_dir.mkdir(parents=True, exist_ok=True)

        temp_path = tmp_dir / f"ketiyi_detail_{uuid4().hex}.png"
        try:
            generate_plot(all_plot_data, str(temp_path))
            img_base64 = base64.b64encode(temp_path.read_bytes()).decode("utf-8")
        finally:
            try:
                temp_path.unlink(missing_ok=True)
            except Exception:
                pass

        # 构建响应数据
        # 避免 DataFrame 中的 NaN 导致 jsonify 输出 NaN（非标准 JSON），从而前端解析失败
        import math

        plot_records = all_plot_data.to_dict("records")
        for row in plot_records:
            for k, v in list(row.items()):
                if isinstance(v, float) and math.isnan(v):
                    row[k] = None

        response_data = {
            "status": "success",
            "data": {
                "model_text": model_text,
                "plot_image": "data:image/png;base64," + img_base64,
                "plot_data": plot_records,
            },
        }

        return jsonify(response_data)

    except Exception as e:
        error_msg = traceback.format_exc()
        print(f"详情接口错误: {error_msg}")
        return (
            jsonify({"status": "error", "message": str(e), "traceback": error_msg}),
            500,
        )
