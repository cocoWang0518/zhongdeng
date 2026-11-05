# 重构提示：这个文件已移至模块化结构
# 请使用新的模块化结构：
# - api/ 文件夹包含所有API相关代码
# - 启动应用请使用 run.py

from api import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=11232)
