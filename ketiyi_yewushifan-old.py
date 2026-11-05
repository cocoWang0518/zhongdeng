import pandas as pd
import pymysql
import os
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np


# ================= 配置区域 =================
# 强制设置 Pandas 显示精度，不隐藏小数
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)
pd.set_option('display.float_format', '{:.8f}'.format)

PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(PROJECT_ROOT / ".env.local", override=True)

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "db"),
    "charset": os.getenv("DB_CHARSET", "utf8mb4"),
    "port": int(os.getenv("DB_PORT", "3306")),
}

client = OpenAI(
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL", "https://api.deepseek.com"),
)


def get_feature_mapping_from_db(table_name):
    """
    ✨ 新增：动态从 MySQL 系统表读取指定表的列注释，生成特征映射字典
    """
    conn = pymysql.connect(**DB_CONFIG)
    mapping_dict = {}
    try:
        with conn.cursor() as cursor:
            # 查询该表所有列的列名和注释
            sql = """
                SELECT COLUMN_NAME, COLUMN_COMMENT 
                FROM information_schema.COLUMNS 
                WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
            """
            cursor.execute(sql, (DB_CONFIG["database"], table_name))
            rows = cursor.fetchall()

            for col_name, col_comment in rows:
                if col_comment:  # 只有写了注释的才记录
                    # 💡 关键点：将库里的下划线/小写（如 f1）转为大写（F1），以对齐代码里的 Feature 名
                    mapping_dict[col_name.upper()] = col_comment
    except Exception as e:
        print(f"❌ 从数据库读取列注释失败: {e}")
    finally:
        conn.close()
    return mapping_dict


def apply_feature_mapping_to_result(result, mapping_dict):
    """
    🎯 修改：不再读取 CSV 文件，直接传入通过数据库注释生成的 mapping_dict
    """
    if not mapping_dict:
        return result

    for model_name, model_data in result.items():
        if "importance" in model_data:
            df = model_data["importance"].copy()
            if "Feature" in df.columns:
                df["Feature"] = df["Feature"].map(mapping_dict).fillna(df["Feature"])
                result[model_name]["importance"] = df
    return result


def get_feature_col_names(bond_type=None):
    cols = []

    if bond_type == "信用债":
        cols += [f'F{i}' for i in range(1, 48)]
        cols += [f'M{i}' for i in range(1, 119)]
        cols += [f'NF{i}' for i in range(1, 36)]
        cols += [f'B{i}' for i in range(1, 10)]
    elif bond_type == "ABS债":
        cols += [f'F{i}' for i in range(1, 52)]
        cols += [f'M{i}' for i in range(1, 119)]
    # ✨ 修改点1：更名为“债项主体”
        # 找到 get_feature_col_names 内部，在“债项主体”后面加上城投主体的范围：
    elif bond_type == "债项主体":
        cols += [f'F{i}' for i in range(1, 48)]
        cols += [f'M{i}' for i in range(1, 119)]
        cols += [f'NF{i}' for i in range(1, 36)]
        # ✨ 新增：城投主体真实的特征边界
    elif bond_type == "城投主体":
        cols += [f'F{i}' for i in range(1, 77)]  # F1 - F76
        cols += [f'M{i}' for i in range(1, 124)]  # M1 - M123
        cols += [f'NF{i}' for i in range(1, 11)]  # NF1 - NF10
    else:
        cols += [f'F{i}' for i in range(1, 77)]
        cols += [f'M{i}' for i in range(1, 124)]
        cols += [f'NF{i}' for i in range(1, 11)]
        cols += [f'B{i}' for i in range(1, 6)]

    return cols


def auto_detect_bond_type(conn, keyword):
    """
    ✨ 新增：根据用户输入的关键词，去映射表中自动查找它属于什么债券/主体类型
    """
    try:
        with conn.cursor() as cursor:
            # 支持模糊查询资产代码或资产名称
            sql = """
                SELECT `适用模型` FROM `asset_model_mapping`
                WHERE `资产代码` LIKE %s OR `资产名称` LIKE %s
                LIMIT 1
            """
            search_pattern = f"%{keyword}%"
            cursor.execute(sql, (search_pattern, search_pattern))
            result = cursor.fetchone()

            if not result:
                return None  # 没查到映射关系

            db_model_name = result[0]

            # 将数据库里存的模型名称，翻译成你代码里使用的 bond_type 字符串
            mapping = {
                "信用债模型": "信用债",
                "城投债模型": "城投债",
                "ABS模型": "ABS债",
                "债项主体模型": "债项主体",
                "城投主体模型": "城投主体",
                "基金模型": "基金",
                "基金主体模型": "基金主体"  # ✨ 新增这一行
            }
            return mapping.get(db_model_name, None)

    except Exception as e:
        print(f"❌ 自动识别债券类型失败: {e}")
        return None


def get_Explanation(feature_importance, mapping_file="file/content_tezheng.csv"):
    """
    🎯 已修改：按绝对值大小筛选前20个特征，并在筛选前计算全局重要性百分比
    """
    if isinstance(feature_importance, list):
        feature_importance_df = pd.DataFrame(feature_importance, columns=["Feature", "Importance"])
    else:
        feature_importance_df = feature_importance.copy()

    if feature_importance_df.empty:
        return feature_importance_df, "未查询到有效的特征重要性数据。"

    # ✨ 核心修改 1：计算所有特征绝对值的总和，并生成新的“百分比”列
    total_abs_importance = feature_importance_df["Importance"].abs().sum()
    if total_abs_importance > 0:
        feature_importance_df["Importance_Pct"] = (feature_importance_df["Importance"] / total_abs_importance) * 100
    else:
        feature_importance_df["Importance_Pct"] = 0.0

    # ✨ 核心修改 2：按绝对值(key=abs)降序排序，精准拦截影响力最大的前20个特征
    feature_importance_df = feature_importance_df.sort_values(by="Importance", key=abs, ascending=False).head(20)

    # 映射特征含义（直接复制已在前面映射好的中文）
    feature_importance_df["特征含义"] = feature_importance_df["Feature"]

    # 调用大模型生成解释总结（此时带有正负号的数据会诚实地传给大模型）
    explanation_text = get_llm_explanation(feature_importance_df)
    print("模型解释总结：\n", explanation_text)

    return feature_importance_df, explanation_text

def get_llm_explanation(feature_importance_df):
    """
    调用深度求索大模型生成解释总结
    """
    feature_info = feature_importance_df.to_csv(index=False)

    prompt = (
        "请根据以下特征重要性数据，分析该债券样本的预测结果：\n"
        "结合债券市场知识综合分析这些特征的影响\n"
        "数据如下：\n\n"
        f"{feature_importance_df.to_csv(index=False)}\n\n"
        "请用专业但易懂的中文成段说明，尽可能少的分条，但要有结构化一点。"
    )
    try:
        response = client.chat.completions.create(
            model=os.getenv("LLM_MODEL", "deepseek-chat"),
            messages=[
                {"role": "system", "content": "您是债券市场分析师，擅长用SHAP值解释模型预测，使用markdown格式输出内容，使用加粗来强调，加粗的**与文字之间要有空格"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            stream=False
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"DeepSeek API 调用失败: {e}")
        return "网络错误，请修复网络后重试"


def generate_plot(plot_data, output_path):
    """
    ✨ 已优化：绘制高颜值的“蝴蝶双向特征图”（高级金融研报质感）
    🎯 已修改：使用百分比（Importance_Pct）替代绝对数值进行绘图
    """
    import matplotlib.pyplot as plt
    import matplotlib.font_manager as fm

    font_path = "font/SimHei.ttf"  # 保证存在
    my_font = fm.FontProperties(fname=font_path)
    plt.rcParams["axes.unicode_minus"] = False

    # 按照百分比绝对值从小到大排序，这样画横向条形图时，影响力最大的特征会被顶在最上面
    plot_df = plot_data.copy()
    plot_df = plot_df.sort_values(by="Importance_Pct", key=abs, ascending=True)

    # 正数用偏暖的“珊瑚红”，负数用偏冷的“沉稳蓝”
    colors = ['#E66C64' if x >= 0 else '#4C72B0' for x in plot_df['Importance_Pct']]

    # 添加画板背景色，提升研报质感 (浅灰白)
    fig, ax = plt.subplots(figsize=(11, 8.5), dpi=300, facecolor='#F8F9FA')
    ax.set_facecolor('#F8F9FA')

    # 💡 修改点：将画图使用的数据列由 Importance 改为 Importance_Pct
    bars = ax.barh(plot_df['Feature'], plot_df['Importance_Pct'],
                   color=colors, edgecolor='none', height=0.65, alpha=0.95)

    # 清理视觉噪音
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_color('#CCCCCC')  # 底部边框调浅

    # 弱化网格线
    ax.set_axisbelow(True)
    ax.grid(axis='x', linestyle='--', color='#E0E0E0', linewidth=0.8, alpha=0.7)

    # 在中间 0 的位置画一条清晰但克制的分割线
    ax.axvline(0, color='#555555', linestyle='-', linewidth=1.2, alpha=0.8)

    # 💡 修改点：X轴标签改为百分比说明
    ax.set_xlabel("特征重要性全局占比 (%)", fontproperties=my_font, fontsize=11, color='#555555', labelpad=12)
    ax.tick_params(axis='y', length=0, pad=10)
    plt.xticks(fontsize=10, color='#666666')
    plt.yticks(fontproperties=my_font, fontsize=11, color='#333333')

    # 💡 修改点：X轴极值基于百分比计算
    max_abs = plot_df['Importance_Pct'].abs().max()
    ax.set_xlim(-max_abs * 1.35, max_abs * 1.35)

    # 数值标注动态跟随
    for bar in bars:
        w = bar.get_width()
        y_pos = bar.get_y() + bar.get_height() / 2

        # 💡 修改点：文本标签格式加上 % 符号，并保留两位小数
        if w >= 0:
            text_color = '#C0392B'
            ax.text(w + max_abs * 0.015, y_pos, f"+{w:.2f}%",
                    va='center', ha='left', fontsize=9, fontweight='bold', color=text_color)
        else:
            text_color = '#2980B9'
            ax.text(w - max_abs * 0.015, y_pos, f"{w:.2f}%",
                    va='center', ha='right', fontsize=9, fontweight='bold', color=text_color)

    # 优化标题
    plt.title("核心特征驱动力深度分析 (Top 20)", fontproperties=my_font,
              fontsize=16, color='#2C3E50', pad=35, fontweight='bold')

    # 图例
    ax.text(0.01, 1.04, "■ 负向影响 ", color='#4C72B0', fontproperties=my_font, fontsize=10,
            transform=ax.transAxes)
    ax.text(0.25, 1.04, "■ 正向影响 ", color='#E66C64', fontproperties=my_font, fontsize=10,
            transform=ax.transAxes)

    plt.tight_layout()
    plt.subplots_adjust(top=0.88)

    # 导出
    plt.savefig(output_path, bbox_inches='tight', dpi=300, facecolor=fig.get_facecolor())
    plt.close()
    print(f"✅ 高颜值研报级双向特征图(百分比版)已生成：{output_path}")




def draw_rating_trend_with_default(df_history, bond_name, default_date=None, save_path="rating_trend.png"):
    """
    绘制指定债券的历史评级趋势图，并标记违约/风险事件点
    df_history: 必须包含 '时间' 和 模型评级列 (如 'GBDT') 的 DataFrame
    bond_name: 债券简称，用于图表标题
    default_date: 违约或风险暴露的日期，格式如 '2023-08-01'
    """
    # 1. 定义评级到数值的映射（确保 Y 轴顺序正确，越高越好）
    rating_map = {
        'AAA': 9, 'AA+': 8, 'AA': 7, 'AA-': 6,
        'A+': 5, 'A': 4, 'A-': 3, 'BBB': 2, 'BB': 1, 'B': 0, 'C': -1
    }
    # 反向映射，用于 Y 轴标签显示
    inverse_map = {v: k for k, v in rating_map.items()}

    # 2. 数据预处理
    df_plot = df_history.copy()
    df_plot['时间'] = pd.to_datetime(df_plot['时间'])
    df_plot = df_plot.sort_values('时间')  # 画图必须按时间正序

    # 将模型评级转换为数值
    # 这里以 GBDT 模型为例，你可以根据需要画多条线
    df_plot['GBDT_num'] = df_plot['GBDT'].map(rating_map)
    # 剔除无法映射的异常数据
    df_plot = df_plot.dropna(subset=['GBDT_num'])

    # 3. 开始绘图
    font_path = "font/SimHei.ttf"  # 确保你有这个中文字体文件
    my_font = fm.FontProperties(fname=font_path)
    plt.rcParams["axes.unicode_minus"] = False

    plt.figure(figsize=(10, 5), dpi=200)

    # 画评级折线
    plt.plot(df_plot['时间'], df_plot['GBDT_num'], marker='o', linestyle='-', color='#1f77b4', linewidth=2,
             label='GBDT模型预测评级')

    # 4. 标记违约事件
    if default_date:
        default_dt = pd.to_datetime(default_date)
        plt.axvline(x=default_dt, color='red', linestyle='--', linewidth=2, label='发生实质性违约/展期')

        # 在红线旁边加个文本提示
        plt.text(default_dt, df_plot['GBDT_num'].mean(), f' 风险暴露\n {default_date}',
                 color='red', fontproperties=my_font, verticalalignment='center')

    # 5. 美化图表
    # 设置 Y 轴只显示我们定义好的评级标签
    valid_y_ticks = sorted(list(df_plot['GBDT_num'].unique()))
    plt.yticks(valid_y_ticks, [inverse_map[val] for val in valid_y_ticks], fontsize=10)

    plt.title(f"【有效性回测】{bond_name} 历史模型评级趋势 vs 实际风险事件", fontproperties=my_font, fontsize=14)
    plt.xlabel("时间", fontproperties=my_font, fontsize=12)
    plt.ylabel("模型评级 (GBDT)", fontproperties=my_font, fontsize=12)

    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.legend(prop=my_font, loc='best')
    plt.xticks(rotation=45)
    plt.tight_layout()

    # 保存并关闭
    plt.savefig(save_path)
    plt.close()
    print(f"✅ 趋势图已生成：{save_path}")


def get_model_features(conn, code, year, month, latest_predictions_dict, bond_type="城投债"):
    """
    专门用于去 4 个不同的表里查询特征重要性。
    动态路由到不同的特征表，并且【隔离保护】不同债券的查询字段名。
    """
    id_col = "bond_code"

    # 找到 get_model_features 内部的 if-elif 区域，修改为：
    if bond_type == "信用债":
        model_tables = {"GBDT": "credit-gbdt_feature_importance", "RF": "credit-rf_feature_importance",
                        "XGBoost": "credit-xgboost_feature_importance",
                        "Adaboost": "credit-adaboost_feature_importance"}
        feature_date_col = "date"
    elif bond_type == "ABS债":
        model_tables = {"GBDT": "abs_gbdt_feature_importance", "RF": "abs_rf_feature_importance",
                        "XGBoost": "abs_xgboost_feature_importance", "Adaboost": "abs_adaboost_feature_importance"}
        feature_date_col = "date_col"
    # ✨ 修改点1：更名为“债项主体”
    elif bond_type == "债项主体":
        model_tables = {"RF": "bond_subject_rf_feature_importance"}
        feature_date_col = "ym_date"
        id_col = "stkcd"

    elif bond_type == "城投主体":
        model_tables = {"GBDT": "city_subject_gbdt_feature_importance"}
        feature_date_col = "date_col"  # 🎯 依据：特征表实际列名叫 date_col
        id_col = "platform_name"  # 🎯 依据：特征表实际列名叫 platform_name
    else:
        model_tables = {"GBDT": "city-gbdt_feature_importance", "RF": "city-rf_feature_importance",
                        "XGBoost": "city-xgboost_feature_importance", "Adaboost": "city-adaboost_feature_importance"}
        feature_date_col = "date"

    results = {}
    display_cols = get_feature_col_names(bond_type)
    db_cols = [c.lower() for c in display_cols]
    select_clause = ", ".join([f"`{c}`" for c in db_cols])

    for model_name, table_name in model_tables.items():
        sql_feat = f"""
            SELECT {select_clause}
            FROM `{table_name}`
            WHERE {id_col} = %s AND YEAR({feature_date_col}) = %s AND MONTH({feature_date_col}) = %s
            LIMIT 1
        """
        try:
            df_feat = pd.read_sql(sql_feat, conn, params=(code, year, month))
            if df_feat.empty:
                importance_df = pd.DataFrame(columns=['Feature', 'Importance'])
            else:
                feat_values = df_feat.iloc[0]
                data_rows = []
                for display, db in zip(display_cols, db_cols):
                    val = feat_values.get(db, 0.0)
                    if val is None: val = 0.0
                    data_rows.append({'Feature': display, 'Importance': float(val)})

                importance_df = pd.DataFrame(data_rows)
                importance_df = importance_df.sort_values(by='Importance', key=abs, ascending=False).reset_index(drop=True)
        except Exception as e:
            print(f"❌ 查询 {table_name} 出错: {e}")
            importance_df = pd.DataFrame(columns=['Feature', 'Importance'])

        results[model_name] = {
            "prediction": latest_predictions_dict.get(model_name, "无数据"),
            "importance": importance_df
        }
    return results

def get_historical_ratings_fuzzy(keyword, bond_type=None):
    """
    支持模糊查询：返回 历史趋势, 最新特征, 基础信息, 模型评估指标
    """
    """
    支持模糊查询：返回 历史趋势, 最新特征, 基础信息, 模型评估指标
    """

    # ✨ 新增前置拦截：如果用户输入的内容以“基金”开头（如“基金000001”）
    if isinstance(keyword, str) and keyword.startswith("基金") and len(keyword) > 2:
        bond_type = "基金"  # 1. 强制锁定资产类型为基金，跳过后续的自动检测
        keyword = keyword[2:].strip()  # 2. 把前面的“基金”两个字截掉，只留下纯代码（如 "000001"）
        print(f"🎯 [系统拦截] 检测到输入带有前缀，已提取核心代码 '{keyword}'，并强制锁定类型为【基金】")

    conn = pymysql.connect(**DB_CONFIG)

    # ================= 智能路由：自动检测类型 =================
    if not bond_type:
        detected_type = auto_detect_bond_type(conn, keyword)
        if detected_type:
            bond_type = detected_type
            print(f"🤖 [系统智能路由] 识别到关键字 '{keyword}' 属于: 【{bond_type}】")
        else:
            print(f"⚠️ [系统提示] 未在映射表中匹配到 '{keyword}'，默认回退使用: 【城投债】")
            bond_type = "城投债"
    else:
        print(f"📌 [系统提示] 用户手动指定类型: 【{bond_type}】")
    # ========================================================



    MODEL_EVALUATION_METRICS = {
        "信用债": [{"model": "GBDT", "Mean_MAE": 0.4473, "Mean_RMSE": 0.7288, "Mean_R2": 0.7459, "Mean_R2_os": 0.7421}, {"model": "XGBoost", "Mean_MAE": 0.4727, "Mean_RMSE": 0.7694, "Mean_R2": 0.7044, "Mean_R2_os": 0.7032}, {"model": "AdaBoost", "Mean_MAE": 0.6493, "Mean_RMSE": 0.9500, "Mean_R2": 0.6106, "Mean_R2_os": 0.5853}, {"model": "Random Forest", "Mean_MAE": 0.6209, "Mean_RMSE": 0.9852, "Mean_R2": 0.5824, "Mean_R2_os": 0.5593}],
        "城投债": [{"model": "GBDT", "Mean_MAE": 0.5105, "Mean_RMSE": 0.6970, "Mean_R2": 0.5867, "Mean_R2_os": 0.6958}, {"model": "XGBoost", "Mean_MAE": 0.5385, "Mean_RMSE": 0.7327, "Mean_R2": 0.4960, "Mean_R2_os": 0.6086}, {"model": "AdaBoost", "Mean_MAE": 0.7253, "Mean_RMSE": 0.9446, "Mean_R2": 0.3374, "Mean_R2_os": 0.5020}, {"model": "Random Forest", "Mean_MAE": 0.7040, "Mean_RMSE": 0.9681, "Mean_R2": 0.3027, "Mean_R2_os": 0.4665}],
        "ABS债": [{"model": "GBDT", "Mean_MAE": 0.2270, "Mean_RMSE": 0.3041, "Mean_R2": 0.6255, "Mean_R2_os": 0.6578}, {"model": "XGBoost", "Mean_MAE": 0.2307, "Mean_RMSE": 0.3113, "Mean_R2": 0.5962, "Mean_R2_os": 0.6453}, {"model": "AdaBoost", "Mean_MAE": 0.2738, "Mean_RMSE": 0.3592, "Mean_R2": 0.5062, "Mean_R2_os": 0.5370}, {"model": "Random Forest", "Mean_MAE": 0.2656, "Mean_RMSE": 0.3572, "Mean_R2": 0.5096, "Mean_R2_os": 0.5368}],
        "债项主体": [{"model": "Random Forest", "Mean_MAE": 0.5480, "Mean_RMSE": 0.8357, "Mean_R2": 0.7296}],
        "城投主体": [{"model": "GBDT", "Mean_MAE": 0.5623, "Mean_RMSE": 0.7531, "Mean_R2": 0.5443, "Mean_R2_os": 0.6927}],
        "基金": [{"model": "FundModel", "Mean_MAE": 0.0, "Mean_RMSE": 0.0, "Mean_R2": 0.0, "Mean_R2_os": 0.0}],
        "基金主体": [{"model": "FundSubjectModel", "Mean_MAE": 0.0, "Mean_RMSE": 0.0, "Mean_R2": 0.0, "Mean_R2_os": 0.0}]
    }

    model_metrics = MODEL_EVALUATION_METRICS.get(bond_type, [])

    # 2. 修改下方的表名路由判断：
    if bond_type == "信用债":
        main_table, name_col, date_col, id_col = "credit_bond_all_models_features", "bond_name", "ym", "bond_code"
    elif bond_type == "ABS债":
        main_table, name_col, date_col, id_col = "abs_bond_all_models_features", "bond_code", "ym", "bond_code"
    # ✨ 更名为“债项主体”，确保表名是 bond_subject_all_models_features_new
    elif bond_type == "债项主体":
        main_table, name_col, date_col, id_col = "bond_subject_all_models_features", None, "ym", "stkcd"
    # ✨ 新增“城投主体”主表路由
    elif bond_type == "城投主体":
        main_table, name_col, date_col, id_col = "city_subject_all_model_features", None, "ym", "城投平台"
    elif bond_type == "基金":
        main_table, name_col, date_col, id_col = "fund_bond_all_models_features", "证券简称", "year", "基金代码"
    elif bond_type == "基金主体":  # ✨ 新增整个分支
        main_table, name_col, date_col, id_col = "fund_subject_rating_features", "公司名称", "年份", "公司名称"

    else:
        main_table, name_col, date_col, id_col = "city_bond_all_models_features", "abbr", "date", "bond_code"

    try:
        # 1. 模糊匹配 (区分有没有名称列)
        if bond_type in ["债项主体", "城投主体"]:
            sql_find_code = f"SELECT DISTINCT {id_col} FROM {main_table} WHERE {id_col} LIKE %s LIMIT 1"
            with conn.cursor() as cursor:
                cursor.execute(sql_find_code, (f"%{keyword}%",))
                match = cursor.fetchone()
            if not match: return pd.DataFrame(), {}, {}, model_metrics, bond_type
            real_bond_code, real_bond_name = match[0], None
        elif bond_type == "基金":
            # ✨ 针对基金：用 LPAD 把 int 补全成 6 位字符串进行查询匹配
            sql_find_code = f"SELECT DISTINCT {id_col}, {name_col} FROM `{main_table}` WHERE LPAD(CAST({id_col} AS CHAR), 6, '0') LIKE %s OR {name_col} LIKE %s LIMIT 1"
            search_pattern = f"%{keyword}%"
            with conn.cursor() as cursor:
                cursor.execute(sql_find_code, (search_pattern, search_pattern))
                match = cursor.fetchone()
            if not match: return pd.DataFrame(), {}, {}, model_metrics, bond_type
            real_bond_code, real_bond_name = match[0], match[1]
        elif bond_type == "基金主体":  # ✨ 新增整个分支
            sql_find_code = f"SELECT DISTINCT {id_col} FROM `{main_table}` WHERE {id_col} LIKE %s LIMIT 1"
            search_pattern = f"%{keyword}%"
            with conn.cursor() as cursor:
                cursor.execute(sql_find_code, (search_pattern,))
                match = cursor.fetchone()
            if not match: return pd.DataFrame(), {}, {}, model_metrics, bond_type
            real_bond_code, real_bond_name = match[0], match[0]
        else:
            sql_find_code = f"SELECT DISTINCT {id_col}, {name_col} FROM {main_table} WHERE {id_col} LIKE %s OR {name_col} LIKE %s LIMIT 1"
            search_pattern = f"%{keyword}%"
            with conn.cursor() as cursor:
                cursor.execute(sql_find_code, (search_pattern, search_pattern))
                match = cursor.fetchone()
            if not match: return pd.DataFrame(), {}, {}, model_metrics, bond_type
            real_bond_code, real_bond_name = match[0], (match[1] if bond_type != "ABS债" else f"{match[0]}(ABS)")

        # 2. 获取历史信息
        sql_info = f"SELECT * FROM {main_table} WHERE {id_col} = %s ORDER BY {date_col} DESC"
        df_info = pd.read_sql(sql_info, conn, params=(real_bond_code,))

        if bond_type == "债项主体":
            with conn.cursor() as cursor:
                cursor.execute("SELECT MAX(ym_date) FROM bond_subject_rf_feature_importance WHERE stkcd = %s",
                               (real_bond_code,))
                max_feat_date = cursor.fetchone()[0]
            if max_feat_date:
                df_info = df_info[pd.to_datetime(df_info[date_col]) <= pd.to_datetime(max_feat_date)]
            # ✨ 新增：城投主体防骗对齐

        elif bond_type == "城投主体":
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT MAX(date_col) FROM city_subject_gbdt_feature_importance WHERE platform_name = %s",
                    (real_bond_code,)
                )
                max_feat_date = cursor.fetchone()[0]
            if max_feat_date:
                df_info = df_info[pd.to_datetime(df_info[date_col]) <= pd.to_datetime(max_feat_date)]

                # （接上文模糊匹配和读取 df_info 之后...）
        latest_info = df_info.iloc[0]

        # 🎯【修改点 1】把“基金主体”和“基金”合并处理，因为它们的 date_col 都是纯数字年份
        if bond_type in ["基金", "基金主体"]:
            latest_date = pd.to_datetime(f"{latest_info[date_col]}-12-31")
        else:
            latest_date = pd.to_datetime(latest_info[date_col])

        # 3. 组装基础公开信息表
        identifier_data = {
            '代码': real_bond_code,
            '时间': str(latest_date)[:10],
            '资产类型': bond_type
        }

        if real_bond_name:  # 只有非主体债才插入名称
            identifier_data['债券名称'] = real_bond_name

        if bond_type == "信用债":
            identifier_data.update({'中信一级行业': latest_info.get('citic_industry', '未知'),
                                    '信用评级': latest_info.get('credit_rating', '未知')})
        elif bond_type == "ABS债":
            identifier_data.update({'基础资产类别': latest_info.get('underlying_asset_class', '未知'),
                                    '信用评级': latest_info.get('credit_rating', '未知')})
        elif bond_type == "债项主体":
            identifier_data.update({'信用评级': latest_info.get('credit_rating', '未知')})
            try:
                sql_subject_detail = """
                                                SELECT `company_name_cn`, `listing_board`, `establish_date`, `ipo_date`,
                                                       `registered_capital`, `office_address`, `province`, `city`, `county`,
                                                       `industry_sector`, `citic_industry`, `business_scope`
                                                FROM `bond_subject_info_table` WHERE `stkcd` = %s LIMIT 1
                                            """
                df_subject = pd.read_sql(sql_subject_detail, conn, params=(real_bond_code,))
                if not df_subject.empty:
                    sub_row = df_subject.iloc[0]
                    identifier_data.update({
                        '公司中文名称': sub_row.get('company_name_cn', '无数据'),
                        '上市板块': sub_row.get('listing_board', '无数据'),
                        '成立日期': str(sub_row.get('establish_date', '无数据'))[:10] if sub_row.get(
                            'establish_date') else '无数据',
                        '首发上市日期': str(sub_row.get('ipo_date', '无数据'))[:10] if sub_row.get(
                            'ipo_date') else '无数据',
                        '注册资本': f"{sub_row.get('registered_capital'):,.2f}" if sub_row.get(
                            'registered_capital') is not None else '无数据',
                        '办公地址': sub_row.get('office_address', '无数据'),
                        '所在省份': sub_row.get('province', '无数据'),
                        '所在地级市': sub_row.get('city', '无数据'),
                        '所在县级市': sub_row.get('county', '无数据'),
                        '所属产业板块': sub_row.get('industry_sector', '无数据'),
                        '中信一级行业': sub_row.get('citic_industry', '无数据')
                    })
            except Exception as e:
                print(f"⚠️ 从 bond_subject_info_table 查询主体详情失败: {e}")
        elif bond_type == "城投主体":
            identifier_data.update({'信用评级': latest_info.get('rating', '未知')})
        elif bond_type == "基金":
            identifier_data.update({'基金管理人': latest_info.get('基金管理人', '未知'),
                                    '基金评级分组': latest_info.get('基金评级分组', '未知')})
        elif bond_type == "基金主体":
            # 🎯 限制得分小数点后两位
            score_val = latest_info.get('场内基金管理公司主体信用得分')
            formatted_score = f"{score_val:.2f}" if isinstance(score_val, (int, float)) and not pd.isna(
                score_val) else '未知'

            identifier_data.update({
                '主体信用分组': latest_info.get('主体信用分组', '未知'),
                '主体信用得分': formatted_score
            })
        else:
            identifier_data.update(
                {'所属省份': latest_info.get('province', '未知'), '所在城市': latest_info.get('city', '未知')})

        # 4. 获取预测结果与特征重要性
        if bond_type == "债项主体":
            latest_preds = {"RF": str(latest_info.get('credit_rating', '无数据'))}
        elif bond_type == "城投主体":
            latest_preds = {"GBDT": str(latest_info.get('rating', '无数据'))}
        elif bond_type == "基金":
            latest_preds = {"FundModel": str(latest_info.get('基金评级分组', '无数据'))}
            result = {}
        elif bond_type == "基金主体":  # 🎯 将评级结果安全存入 result，不设置为空字典
            latest_preds = {"FundSubjectModel": str(latest_info.get('主体信用分组', '无数据'))}
            result = {
                "FundSubjectModel": {
                    "prediction": latest_preds["FundSubjectModel"],
                    "importance": pd.DataFrame()  # 基金主体不需要特征重要性，传空 DataFrame 即可
                }
            }
        else:
            latest_preds = {m: str(latest_info.get(f'{m.lower()}_adjusted_rating', '无数据')) for m in
                            ["GBDT", "RF", "XGBoost", "Adaboost"]}

        # 🎯【修改点 2】改成 not in 数组，彻底把“基金”和“基金主体”挡在外面，不让它们去查查不到的特征表
        if bond_type not in ["基金", "基金主体"]:
            result = get_model_features(conn, real_bond_code, latest_date.year, latest_date.month, latest_preds,
                                        bond_type)

        # 5. 组装历史评级记录
        if bond_type == "债项主体":
            history_records = df_info.apply(
                lambda row: {"时间": str(row[date_col])[:10], "RF": str(row.get('credit_rating', 'NaN'))},
                axis=1).tolist()
            df_history = pd.DataFrame(history_records).replace(r'^\s*(NaN|None|nan|)\s*$', np.nan, regex=True).dropna(
                subset=["RF"], how='all')
        elif bond_type == "城投主体":
            history_records = df_info.apply(
                lambda row: {"时间": str(row[date_col])[:10], "GBDT": str(row.get('rating', 'NaN'))}, axis=1).tolist()
            df_history = pd.DataFrame(history_records).replace(r'^\s*(NaN|None|nan|)\s*$', np.nan, regex=True).dropna(
                subset=["GBDT"], how='all')
        elif bond_type == "基金":
            # ✨ 新增：基金的历史评级记录
            history_records = df_info.apply(
                lambda row: {"时间": f"{row[date_col]}-12-31", "FundModel": str(row.get('基金评级分组', 'NaN'))},
                axis=1).tolist()
            df_history = pd.DataFrame(history_records).replace(r'^\s*(NaN|None|nan|)\s*$', np.nan, regex=True).dropna(
                subset=["FundModel"], how='all')
        elif bond_type == "基金主体":  # ✨ 新增
            history_records = df_info.apply(
                lambda row: {"时间": f"{row[date_col]}-12-31", "FundSubjectModel": str(row.get('主体信用分组', 'NaN'))},
                axis=1).tolist()
            df_history = pd.DataFrame(history_records).replace(r'^\s*(NaN|None|nan|)\s*$', np.nan, regex=True).dropna(
                subset=["FundSubjectModel"], how='all')

        else:
            # ✨ 补回信用债、城投债、ABS债原本的多模型历史记录提取逻辑
            history_records = df_info.apply(lambda row: {
                "时间": str(row[date_col])[:10],
                "GBDT": str(row.get('gbdt_adjusted_rating', 'NaN')),
                "RF": str(row.get('rf_adjusted_rating', 'NaN')),
                "XGBoost": str(row.get('xgboost_adjusted_rating', 'NaN')),
                "Adaboost": str(row.get('adaboost_adjusted_rating', 'NaN'))
            }, axis=1).tolist()
            df_history = pd.DataFrame(history_records).replace(r'^\s*(NaN|None|nan|)\s*$', np.nan, regex=True).dropna(
                subset=["GBDT", "RF", "XGBoost", "Adaboost"], how='all')

        return df_history, result, identifier_data, model_metrics, bond_type

    except Exception as e:
        print(f"Error: {e}")
        # 报错时也要对应返回 5 个值
        return pd.DataFrame(), {}, {}, model_metrics, bond_type
    finally:
        conn.close()



# ================= 调用验证 =================
if __name__ == "__main__":

    #code = '112063'  #信用债用这个测试
    #code =  '1080172'  #城投用这个
    #code = '1489092'  #ABS
    #code = '000001'  # 债项主体用这个
    #code = '上海市漕河泾新兴技术开发区发展总公司' #城投主体用这个
    #code = '000001' #基金用这个
    code = '万家基金' #基金主体用这个


    bond_type = ""
    print(f">>> 开始查询: {code} ...")

    # 接收三个返回值
    #df_history, result, identifier_data = get_historical_ratings_fuzzy(code)
    # 查询城投债 (默认)
    ## 信用债，城投债和ABS债

    df_history, result, identifier_data, model_metrics, detected_type = get_historical_ratings_fuzzy(code,bond_type)
    biaoge = df_history.to_json(orient="records", force_ascii=False)

    # 查询信用债 (传入新参数)
    # df_history, result, identifier_data = get_historical_ratings_fuzzy('你的信用债代码', bond_type="信用债")


    print("\n--- 历史评级表 ---")
    print(df_history.head(10))
    print("\n--- 基础信息 ---")
    print(identifier_data)
    print("\n--- 模型评估 ---")
    print(model_metrics)

    if result:
        if detected_type == '基金主体':
            # 🎯 基金主体在此处直接拦截展示评级结果，不参与后面的映射和画图逻辑
            print("\n--- 模型评级结果 ---")
            print(f"模型预测评级: {result['FundSubjectModel']['prediction']}")

        elif detected_type != '基金':
            if detected_type == '信用债':
                db_mapping = get_feature_mapping_from_db("credit-gbdt_feature_importance")
            elif detected_type == '债项主体':
                db_mapping = get_feature_mapping_from_db("bond_subject_rf_feature_importance")
            elif detected_type == 'ABS债':
                db_mapping = get_feature_mapping_from_db("abs_gbdt_feature_importance")
            elif detected_type == '城投主体':
                db_mapping = get_feature_mapping_from_db("city_subject_gbdt_feature_importance")
            else:
                db_mapping = get_feature_mapping_from_db("city-gbdt_feature_importance")

            result = apply_feature_mapping_to_result(result, db_mapping)

            # 动态配置分析和画图使用的模型名称
            if detected_type == '债项主体':
                model_name = 'RF'
            elif detected_type == '城投主体':
                model_name = 'GBDT'
            else:
                model_name = 'GBDT'

            feature_importance = result[model_name]["importance"]
            all_plot_data, model_text = get_Explanation(feature_importance.to_dict(orient="records"))
            generate_plot(all_plot_data, "all_output_plot.png")
