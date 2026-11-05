# ============================================================
# Basel AR（Accuracy Ratio）
# 主体评级：逐月计算 1-Year AR + 月度 AR 等权平均
#
# 模型：3月递归-财务+非财务
# ============================================================

import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.metrics import roc_auc_score

# ============================================================
# 0. 文件路径
# ============================================================

INPUT_FILE = (
    "/Users/guochenwei/Library/Mobile Documents/com~apple~CloudDocs/"
    "PycharmProjects/PythonProject2/output/"
    "上市公司主体评级结果-3月递归-财务+非财务.xlsx"
)

OUTPUT_DIR = Path(
    "/Users/guochenwei/Library/Mobile Documents/com~apple~CloudDocs/"
    "PycharmProjects/PythonProject2/output"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_MONTHLY = OUTPUT_DIR / "AR结果_3月递归_财务+非财务_逐月.xlsx"
OUTPUT_CAP = OUTPUT_DIR / "AR结果_3月递归_财务+非财务_CAP明细.xlsx"

DEFAULT_DATA_END = pd.Timestamp("2025-09-01")


# ============================================================
# 1. 字段名称
# ============================================================

ID_COL = "stkcd"
DATE_COL = "ym"
RATING_COL = "信用评级"
DEFAULT_DATE_COL = "首次违约日期"


# ============================================================
# 2. 评级风险顺序
# 数字越大 = 风险越高
# ============================================================

RATING_MAP = {
    "AAA": 1,
    "AA+": 2,
    "AA": 3,
    "AA-": 4,
    "A+": 5,
    "A": 6,
    "A-": 7,
    "BBB+": 8,
    "BBB": 9,
    "BBB-": 10,
    "BB+": 11,
    "BB": 12,
    "BB-": 13,
    "B+": 14,
    "B": 15,
    "B-": 16,
    "CCC": 17,
    "CC": 18,
    "C": 19,
    "D": 20,
}


# ============================================================
# 3. 日期解析
# ============================================================

def parse_ym(series):

    s = series.copy()

    if pd.api.types.is_datetime64_any_dtype(s):
        return pd.to_datetime(s).dt.to_period("M").dt.to_timestamp()

    s = s.astype(str).str.strip()
    s = s.str.replace(r"\.0$", "", regex=True)

    result = pd.Series(pd.NaT, index=s.index, dtype="datetime64[ns]")

    mask_yyyymm = s.str.fullmatch(r"\d{6}", na=False)

    result.loc[mask_yyyymm] = pd.to_datetime(
        s.loc[mask_yyyymm],
        format="%Y%m",
        errors="coerce"
    )

    mask_other = ~mask_yyyymm

    result.loc[mask_other] = pd.to_datetime(
        s.loc[mask_other],
        errors="coerce"
    )

    return result.dt.to_period("M").dt.to_timestamp()


# ============================================================
# 4. Basel CAP / AR
# ============================================================

def calculate_basel_ar(month_df):

    d = month_df[
        ["risk_rank", "default_1y"]
    ].dropna().copy()

    n_total = len(d)
    n_default = int(d["default_1y"].sum())
    n_nondefault = n_total - n_default

    if n_default == 0 or n_nondefault == 0:
        return np.nan, np.nan, np.nan, None

    grouped = (
        d.groupby("risk_rank", as_index=False)
        .agg(
            n=("default_1y", "size"),
            defaults=("default_1y", "sum")
        )
        .sort_values("risk_rank", ascending=False)
        .reset_index(drop=True)
    )

    grouped["nondefaults"] = grouped["n"] - grouped["defaults"]

    grouped["cum_n"] = grouped["n"].cumsum()
    grouped["cum_defaults"] = grouped["defaults"].cumsum()

    grouped["cap_x"] = grouped["cum_n"] / n_total
    grouped["cap_y"] = grouped["cum_defaults"] / n_default

    x = np.concatenate(
        ([0.0], grouped["cap_x"].to_numpy())
    )

    y = np.concatenate(
        ([0.0], grouped["cap_y"].to_numpy())
    )

    if x[-1] < 1:
        x = np.append(x, 1.0)
        y = np.append(y, 1.0)

    actual_cap_area = np.trapezoid(y, x)

    random_cap_area = 0.5

    a_R = actual_cap_area - random_cap_area

    default_rate = n_default / n_total

    perfect_cap_area = 1 - default_rate / 2

    a_P = perfect_cap_area - random_cap_area

    if a_P <= 0:
        ar_cap = np.nan
    else:
        ar_cap = a_R / a_P

    auc = roc_auc_score(
        d["default_1y"],
        d["risk_rank"]
    )

    ar_auc = 2 * auc - 1

    cap_detail = grouped.copy()

    cap_detail["N_total"] = n_total
    cap_detail["N_default"] = n_default
    cap_detail["default_rate"] = default_rate

    cap_detail["actual_cap_area"] = actual_cap_area
    cap_detail["random_cap_area"] = random_cap_area
    cap_detail["perfect_cap_area"] = perfect_cap_area

    cap_detail["a_R"] = a_R
    cap_detail["a_P"] = a_P

    cap_detail["AR_CAP"] = ar_cap
    cap_detail["AUC"] = auc
    cap_detail["AR_2AUC_minus_1"] = ar_auc

    return ar_cap, auc, ar_auc, cap_detail


# ============================================================
# 5. 读取数据
# ============================================================

print("=" * 70)
print("开始读取数据：3月递归-财务+非财务")
print("=" * 70)

df = pd.read_excel(INPUT_FILE)

print(f"原始行数：{len(df):,}")
print(f"原始列数：{len(df.columns):,}")

print("\n字段：")
for c in df.columns:
    print(" -", c)


required_cols = [
    ID_COL,
    DATE_COL,
    RATING_COL,
    DEFAULT_DATE_COL
]

missing_cols = [
    c for c in required_cols
    if c not in df.columns
]

if missing_cols:
    raise ValueError(
        f"缺少必要字段：{missing_cols}"
    )


# ============================================================
# 6. 基础清洗
# ============================================================

df[ID_COL] = (
    df[ID_COL]
    .astype(str)
    .str.strip()
    .str.replace(r"\.0$", "", regex=True)
)

df["rating_month"] = parse_ym(
    df[DATE_COL]
)

df["first_default_date"] = pd.to_datetime(
    df[DEFAULT_DATE_COL],
    errors="coerce"
)

df["rating_clean"] = (
    df[RATING_COL]
    .astype(str)
    .str.strip()
    .str.upper()
    .str.replace("＋", "+", regex=False)
    .str.replace("－", "-", regex=False)
)

df.loc[
    df["rating_clean"].isin(
        ["NAN", "NONE", "", "NULL"]
    ),
    "rating_clean"
] = np.nan


observed_ratings = sorted(
    df["rating_clean"]
    .dropna()
    .unique()
    .tolist()
)

unknown_ratings = [
    r for r in observed_ratings
    if r not in RATING_MAP
]

print("\n数据中的评级：")
print(observed_ratings)

if unknown_ratings:

    print("\n⚠️ 以下评级尚未进入 RATING_MAP：")
    print(unknown_ratings)

    raise ValueError(
        "请先补充 RATING_MAP 后再运行。"
    )


df["risk_rank"] = (
    df["rating_clean"]
    .map(RATING_MAP)
)


before = len(df)

df = df.dropna(
    subset=[
        ID_COL,
        "rating_month",
        "rating_clean",
        "risk_rank"
    ]
).copy()

print(
    f"\n删除缺失主体/月份/评级后："
    f"{before:,} -> {len(df):,}"
)


# ============================================================
# 7. 检查主体×月重复
# ============================================================

dup = df.duplicated(
    subset=[
        ID_COL,
        "rating_month"
    ],
    keep=False
)

if dup.any():

    dup_df = (
        df.loc[
            dup,
            [
                ID_COL,
                "rating_month",
                "rating_clean",
                "risk_rank"
            ]
        ]
        .sort_values(
            [
                ID_COL,
                "rating_month"
            ]
        )
    )

    print("\n⚠️ 发现主体×月份重复：")
    print(dup_df.head(30))

    nunique_check = (
        df.loc[dup]
        .groupby(
            [
                ID_COL,
                "rating_month"
            ]
        )["rating_clean"]
        .nunique()
    )

    conflict = nunique_check[
        nunique_check > 1
    ]

    if len(conflict) > 0:
        raise ValueError(
            "存在同一主体同一月份多个不同评级，"
            "需要先确定保留规则。"
        )

    df = df.drop_duplicates(
        subset=[
            ID_COL,
            "rating_month"
        ],
        keep="first"
    )

    print(
        f"相同评级重复记录已去重，"
        f"剩余：{len(df):,}"
    )


# ============================================================
# 8. 剔除评级时已经违约
# ============================================================

already_defaulted = (
    df["first_default_date"].notna()
    &
    (
        df["first_default_date"]
        <= df["rating_month"]
    )
)

print(
    f"\n评级时已经违约的记录："
    f"{already_defaulted.sum():,}"
)

df = df.loc[
    ~already_defaulted
].copy()


# ============================================================
# 9. 构造未来1年观察窗口
# ============================================================

df["horizon_end_1y"] = (
    df["rating_month"]
    + pd.DateOffset(years=1)
)

complete_1y = (
    df["horizon_end_1y"]
    <= DEFAULT_DATA_END
)

print(
    f"没有完整未来1年观察窗口的记录："
    f"{(~complete_1y).sum():,}"
)

df = df.loc[
    complete_1y
].copy()


# ============================================================
# 10. 构造未来1年违约变量
# ============================================================

df["default_1y"] = (
    df["first_default_date"].notna()
    &
    (
        df["first_default_date"]
        > df["rating_month"]
    )
    &
    (
        df["first_default_date"]
        <= df["horizon_end_1y"]
    )
).astype(int)


# ============================================================
# 11. 样本描述
# ============================================================

print("\n" + "=" * 70)
print("AR 样本构造完成")
print("=" * 70)

print(
    f"最终主体×月记录："
    f"{len(df):,}"
)

print(
    f"主体数："
    f"{df[ID_COL].nunique():,}"
)

print(
    f"评级月份数："
    f"{df['rating_month'].nunique():,}"
)

print(
    f"未来1年违约记录数："
    f"{df['default_1y'].sum():,}"
)

print(
    f"总体未来1年违约比例："
    f"{df['default_1y'].mean():.4%}"
)

if len(df) > 0:

    print(
        f"评级月份范围："
        f"{df['rating_month'].min().date()} 至 "
        f"{df['rating_month'].max().date()}"
    )


# ============================================================
# 12. 逐月计算 AR
# ============================================================

monthly_results = []
all_cap_details = []

months = sorted(
    df["rating_month"].unique()
)

print("\n" + "=" * 70)
print("开始逐月计算 Basel AR")
print("=" * 70)

for month in months:

    m = df.loc[
        df["rating_month"] == month
    ].copy()

    n = len(m)
    d = int(
        m["default_1y"].sum()
    )

    nd = n - d

    ar_cap, auc, ar_auc, cap_detail = (
        calculate_basel_ar(m)
    )

    valid = not pd.isna(
        ar_cap
    )

    monthly_results.append(
        {
            "month": month,
            "N": n,
            "N_default_1y": d,
            "N_nondefault_1y": nd,
            "default_rate_1y": (
                d / n
                if n > 0
                else np.nan
            ),
            "AR_CAP": ar_cap,
            "AUC": auc,
            "AR_2AUC_minus_1": ar_auc,
            "AR_difference_check": (
                ar_cap - ar_auc
                if valid
                else np.nan
            ),
            "valid_AR": int(valid)
        }
    )

    if cap_detail is not None:

        cap_detail.insert(
            0,
            "month",
            month
        )

        all_cap_details.append(
            cap_detail
        )

    if valid:

        print(
            f"{pd.Timestamp(month):%Y-%m} | "
            f"N={n:5d} | "
            f"Default={d:4d} | "
            f"AR={ar_cap: .4f} | "
            f"AUC={auc: .4f}"
        )

    else:

        print(
            f"{pd.Timestamp(month):%Y-%m} | "
            f"N={n:5d} | "
            f"Default={d:4d} | "
            f"AR=无法计算"
        )


# ============================================================
# 13. 月度汇总
# ============================================================

monthly_df = pd.DataFrame(
    monthly_results
)

valid_monthly = monthly_df.loc[
    monthly_df["valid_AR"] == 1
].copy()

mean_monthly_ar = (
    valid_monthly["AR_CAP"].mean()
)

median_monthly_ar = (
    valid_monthly["AR_CAP"].median()
)

std_monthly_ar = (
    valid_monthly["AR_CAP"].std()
)

min_monthly_ar = (
    valid_monthly["AR_CAP"].min()
)

max_monthly_ar = (
    valid_monthly["AR_CAP"].max()
)

mean_auc = (
    valid_monthly["AUC"].mean()
)

n_valid_months = len(
    valid_monthly
)


summary_df = pd.DataFrame(
    {
        "指标": [
            "模型",
            "违约预测窗口",
            "有效AR月份数",
            "月度AR平均值",
            "月度AR中位数",
            "月度AR标准差",
            "月度AR最小值",
            "月度AR最大值",
            "月度AUC平均值",
            "违约数据截止日期"
        ],
        "结果": [
            "3月递归-财务+非财务",
            "未来1年",
            n_valid_months,
            mean_monthly_ar,
            median_monthly_ar,
            std_monthly_ar,
            min_monthly_ar,
            max_monthly_ar,
            mean_auc,
            DEFAULT_DATA_END.strftime(
                "%Y-%m-%d"
            )
        ]
    }
)


if all_cap_details:

    cap_df = pd.concat(
        all_cap_details,
        ignore_index=True
    )

else:

    cap_df = pd.DataFrame()


# ============================================================
# 14. 输出 Excel
# ============================================================

with pd.ExcelWriter(
    OUTPUT_MONTHLY,
    engine="openpyxl"
) as writer:

    summary_df.to_excel(
        writer,
        sheet_name="Summary",
        index=False
    )

    monthly_df.to_excel(
        writer,
        sheet_name="Monthly_AR",
        index=False
    )

    df[
        [
            ID_COL,
            "rating_month",
            "rating_clean",
            "risk_rank",
            "first_default_date",
            "horizon_end_1y",
            "default_1y"
        ]
    ].to_excel(
        writer,
        sheet_name="AR_Sample",
        index=False
    )


if not cap_df.empty:

    cap_df.to_excel(
        OUTPUT_CAP,
        index=False
    )


# ============================================================
# 15. 最终打印
# ============================================================

print("\n" + "=" * 70)
print("最终结果：3月递归-财务+非财务")
print("=" * 70)

print(
    f"有效月份数："
    f"{n_valid_months}"
)

print(
    f"月度 AR 等权平均："
    f"{mean_monthly_ar:.6f}"
)

print(
    f"月度 AR 中位数："
    f"{median_monthly_ar:.6f}"
)

print(
    f"月度 AR 标准差："
    f"{std_monthly_ar:.6f}"
)

print(
    f"月度 AR 最小值："
    f"{min_monthly_ar:.6f}"
)

print(
    f"月度 AR 最大值："
    f"{max_monthly_ar:.6f}"
)

print(
    f"月度 AUC 平均值："
    f"{mean_auc:.6f}"
)

print("\nCAP公式与AUC公式最大差异：")

if len(valid_monthly) > 0:

    max_diff = (
        valid_monthly[
            "AR_difference_check"
        ]
        .abs()
        .max()
    )

    print(
        f"{max_diff:.12f}"
    )

print("\n输出文件：")
print(OUTPUT_MONTHLY)

if not cap_df.empty:
    print(OUTPUT_CAP)

print("\n✅ Basel AR 计算完成")