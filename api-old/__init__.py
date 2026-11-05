from flask import Flask
import os
import mimetypes

def create_app():
    """创建并配置Flask应用"""
    # 确保JavaScript模块有正确的MIME类型
    mimetypes.add_type('application/javascript', '.js')
    mimetypes.add_type('text/css', '.css')
    
    app = Flask(__name__)
    
    # 导入和注册蓝图
    from api.routes.check_routes import check_bp
    from api.routes.predict_routes import predict_bp
    from api.routes.results_routes import results_bp
    from api.routes.visualization_routes import visualization_bp
    from api.routes.static_routes import static_bp
    from api.routes.ketiyi_routes import ketiyi_bp
    from api.routes.db_routes import db_bp
    from api.routes.metadata_routes import metadata_bp

    # 注册蓝图时不添加URL前缀，使路由与原来保持一致
    app.register_blueprint(check_bp)
    app.register_blueprint(predict_bp)
    app.register_blueprint(results_bp)
    app.register_blueprint(visualization_bp)
    app.register_blueprint(ketiyi_bp)
    app.register_blueprint(db_bp)
    app.register_blueprint(metadata_bp)
    
    # 静态路由应该最后注册，以处理所有其他未匹配的路由
    app.register_blueprint(static_bp)
    
    return app 
