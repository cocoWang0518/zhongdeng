"""沿用交付脚本的 Basel CAP / AR、未来一年窗口及月度等权汇总口径。"""
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

DEFAULT_DATA_END = "2025-09-01"
RATING_MAP = {rating: index + 1 for index, rating in enumerate([
    "AAA", "AA+", "AA", "AA-", "A+", "A", "A-", "BBB+", "BBB", "BBB-",
    "BB+", "BB", "BB-", "B+", "B", "B-", "CCC", "CC", "C", "D",
])}


def parse_dates(series):
    if pd.api.types.is_datetime64_any_dtype(series):
        return pd.to_datetime(series)
    text = series.astype("string").str.strip().str.replace(r"\.0$", "", regex=True)
    result = pd.Series(pd.NaT, index=series.index, dtype="datetime64[ns]")
    for pattern, fmt in [(r"\d{6}", "%Y%m"), (r"\d{8}", "%Y%m%d")]:
        mask = text.str.fullmatch(pattern, na=False)
        result.loc[mask] = pd.to_datetime(text.loc[mask], format=fmt, errors="coerce")
    other = ~text.str.fullmatch(r"\d{6}|\d{8}", na=False)
    kwargs = {"format": "mixed"} if int(pd.__version__.split('.')[0]) >= 2 else {}
    result.loc[other] = pd.to_datetime(text.loc[other], errors="coerce", **kwargs)
    return result


def calculate_basel_ar(month_df):
    data = month_df[["risk_rank", "default_1y"]].dropna()
    n = len(data)
    defaults = int(data["default_1y"].sum())
    if defaults == 0 or defaults == n:
        return None, None
    grouped = (data.groupby("risk_rank", as_index=False)
               .agg(n=("default_1y", "size"), defaults=("default_1y", "sum"))
               .sort_values("risk_rank", ascending=False))
    x = np.r_[0., grouped["n"].cumsum().to_numpy() / n]
    y = np.r_[0., grouped["defaults"].cumsum().to_numpy() / defaults]
    # 兼容原系统的 NumPy 1.x；与交付脚本 np.trapezoid 完全相同。
    integrate = np.trapezoid if hasattr(np, "trapezoid") else np.trapz
    ar = (integrate(y, x) - 0.5) / (0.5 - defaults / n / 2)
    auc = roc_auc_score(data["default_1y"], data["risk_rank"])
    return float(ar), float(auc)


def evaluate_ar(data, data_end=DEFAULT_DATA_END, id_col="stkcd", date_col="ym",
                rating_col="信用评级", default_date_col="首次违约日期"):
    columns = [id_col, date_col, rating_col, default_date_col]
    if len(set(columns)) != 4:
        raise ValueError("主体、月份、评级和违约日期必须选择四个不同字段")
    missing = [name for name in columns if name not in data.columns]
    if missing:
        raise ValueError("缺少必要字段：" + "、".join(missing))
    if data.empty:
        raise ValueError("文件中没有数据记录")
    end = parse_dates(pd.Series([data_end])).iloc[0]
    if pd.isna(end):
        raise ValueError("请输入有效的违约数据截止日期")
    frame = data[columns].copy()
    frame.columns = ["subject", "month", "rating", "default_date"]
    input_rows = len(frame)
    frame["subject"] = frame["subject"].astype("string").str.strip().str.replace(r"\.0$", "", regex=True)
    frame["subject"] = frame["subject"].mask(frame["subject"].str.lower().isin(["", "nan", "none", "null"]))
    frame["month"] = parse_dates(frame["month"]).dt.to_period("M").dt.to_timestamp()
    raw_default = frame["default_date"].astype("string").str.strip()
    absent_default = raw_default.isna() | raw_default.str.lower().isin(["", "nan", "none", "null", "nat", "n/a", "na"])
    frame["default_date"] = parse_dates(frame["default_date"])
    bad_default = ~absent_default & frame["default_date"].isna()
    if bad_default.any():
        raise ValueError(f"有 {int(bad_default.sum())} 条首次违约日期无法解析，请修正；未违约请留空")
    frame["rating"] = (frame["rating"].astype("string").str.strip().str.upper()
                       .str.replace("＋", "+", regex=False).str.replace("－", "-", regex=False))
    frame["rating"] = frame["rating"].mask(frame["rating"].isin(["", "NAN", "NONE", "NULL"]))
    unknown = sorted(set(frame["rating"].dropna()) - set(RATING_MAP))
    if unknown:
        raise ValueError("存在不支持的评级：" + "、".join(unknown))
    frame["risk_rank"] = frame["rating"].map(RATING_MAP)
    frame = frame.dropna(subset=["subject", "month", "rating", "risk_rank"])
    missing_rows = input_rows - len(frame)
    groups = frame.groupby(["subject", "month"])
    if (groups["rating"].nunique() > 1).any():
        raise ValueError("同一主体同一月份存在不同评级，请先确定保留规则")
    if (groups["default_date"].nunique(dropna=False) > 1).any():
        raise ValueError("同一主体同一月份的首次违约日期不一致，请先核对")
    before = len(frame)
    frame = frame.drop_duplicates(["subject", "month"], keep="first")
    duplicate_rows = before - len(frame)
    already = frame["default_date"].notna() & (frame["default_date"] <= frame["month"])
    already_rows = int(already.sum())
    frame = frame.loc[~already].copy()
    frame["horizon_end"] = frame["month"] + pd.DateOffset(years=1)
    incomplete = frame["horizon_end"] > end
    incomplete_rows = int(incomplete.sum())
    frame = frame.loc[~incomplete].copy()
    frame["default_1y"] = (frame["default_date"].notna()
                            & (frame["default_date"] > frame["month"])
                            & (frame["default_date"] <= frame["horizon_end"])).astype(int)
    monthly = []
    for month, group in frame.groupby("month", sort=True):
        n = len(group)
        defaults = int(group["default_1y"].sum())
        ar, auc = calculate_basel_ar(group)
        monthly.append({
            "month": month.strftime("%Y-%m"), "N": n,
            "N_default_1y": defaults, "N_nondefault_1y": n - defaults,
            "default_rate_1y": defaults / n, "AR_CAP": ar, "AUC": auc,
            "AR_2AUC_minus_1": None if auc is None else 2 * auc - 1,
            "valid_AR": ar is not None,
            "reason": "" if ar is not None else ("当月无未来一年违约样本" if defaults == 0 else "当月无非违约样本"),
        })
    valid = [row for row in monthly if row["valid_AR"]]
    values = pd.Series([row["AR_CAP"] for row in valid], dtype=float)
    def finite(value):
        return float(value) if pd.notna(value) and np.isfinite(value) else None
    warnings = []
    if not monthly:
        warnings.append("筛选后没有具备完整未来一年观察窗口的有效记录，请检查数据和截止日期。")
    elif not valid:
        warnings.append("各月均未同时包含违约与非违约样本，无法计算有效AR。")
    return {
        "summary": {
            "overall_ar": finite(values.mean()),
            "overall_method": "有效月份AR等权平均（沿用原代码）",
            "valid_months": len(valid), "total_months": len(monthly),
            "median_ar": finite(values.median()), "std_ar": finite(values.std()),
            "min_ar": finite(values.min()), "max_ar": finite(values.max()),
            "mean_auc": finite(pd.Series([row["AUC"] for row in valid], dtype=float).mean()),
            "sample_count": len(frame), "subject_count": int(frame["subject"].nunique()),
            "default_count": int(frame["default_1y"].sum()),
            "data_end": end.strftime("%Y-%m-%d"), "horizon": "未来1年",
            "max_formula_difference": max((abs(row["AR_CAP"] - row["AR_2AUC_minus_1"]) for row in valid), default=None),
        },
        "monthly": monthly, "warnings": warnings,
        "cleaning": {"input_rows": input_rows, "missing_rows": missing_rows,
                     "duplicate_rows": duplicate_rows, "already_defaulted_rows": already_rows,
                     "incomplete_window_rows": incomplete_rows},
    }
