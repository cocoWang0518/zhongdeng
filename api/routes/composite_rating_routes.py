import re
from pathlib import Path

import numpy as np
from flask import Blueprint, current_app, jsonify, request
from pandas.errors import OutOfBoundsDatetime

from ketiyi_licha import (
    DATASET_MAPPING,
    RATING_LABELS,
    _to_native,
    load_dataset_by_name,
    predict_single_month,
    ratings_from_percentiles,
)

composite_rating_bp = Blueprint("composite_rating", __name__)
DATA_DIR = Path(__file__).resolve().parents[2] / "converted_data"

REGRESSION_WEIGHT = 1.0
CLASSIFICATION_WEIGHT = 0.0


def composite_ratings(regression_percentiles, classification_percentiles=None):
    """合并方向一致的风险百分位（数值越高，风险越高）。"""
    score = REGRESSION_WEIGHT * regression_percentiles
    if CLASSIFICATION_WEIGHT:
        if classification_percentiles is None:
            raise ValueError("分类模型参与计分时需要提供逐条匹配的风险百分位")
        score = score + CLASSIFICATION_WEIGHT * classification_percentiles
    return ratings_from_percentiles(score)


@composite_rating_bp.get("/ketiyi/composite-rating/options")
def composite_rating_options():
    dataset = request.args.get("dataset")
    if dataset is None:
        return jsonify({"datasets": list(DATASET_MAPPING)})
    if dataset not in DATASET_MAPPING:
        return jsonify({"message": "请选择有效的债券类型"}), 400

    try:
        data = load_dataset_by_name(DATA_DIR, dataset, columns=["ym", "CS"])
        if data is None:
            return jsonify({"months": []})
        training_months = set(data.loc[np.isfinite(data["CS"]), "ym_period"])
        available = [
            str(month) for month in sorted(set(data["ym_period"]), reverse=True)
            if any(month - offset in training_months for offset in range(1, 7))
        ]
        return jsonify({"months": available})
    except Exception:
        current_app.logger.exception("读取综合评级月份失败")
        return jsonify({"message": "读取可用月份失败，请稍后重试"}), 500


@composite_rating_bp.get("/ketiyi/composite-rating")
def get_composite_rating():
    dataset = request.args.get("dataset", "")
    month = request.args.get("month", "")
    if dataset not in DATASET_MAPPING:
        return jsonify({"message": "请选择有效的债券类型"}), 400
    if not re.fullmatch(r"[0-9]{4}-(0[1-9]|1[0-2])", month) or month.startswith("0000"):
        return jsonify({"message": "请选择有效的评级月份"}), 400

    try:
        meta, rows, metrics = predict_single_month(
            str(DATA_DIR), dataset, month, rating_rule=composite_ratings,
            skip_missing_targets=True,
        )
        if rows is None:
            return jsonify({"message": f"{dataset}在 {month} 缺少可用的训练或评级样本"}), 404

        counts = metrics["各评级数量统计"]
        return jsonify({
            "dataset": dataset,
            "month": month,
            "training_window": meta["训练窗口"],
            "distribution": [
                {"rating": rating, "count": counts.get(rating, 0)}
                for rating in RATING_LABELS
            ],
            "bonds": _to_native(
                rows[["代码", "预测利差", "评级结果"]]
                .rename(columns={"代码": "code", "预测利差": "spread", "评级结果": "rating"})
                .to_dict(orient="records")
            ),
        })
    except OutOfBoundsDatetime:
        return jsonify({"message": f"{dataset}在 {month} 缺少可用的训练或评级样本"}), 404
    except Exception:
        current_app.logger.exception("生成综合评级失败")
        return jsonify({"message": "生成综合评级失败，请稍后重试"}), 500
