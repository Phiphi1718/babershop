from flask import Flask, jsonify
from flask_cors import CORS
from extensions import db, bcrypt
from sqlalchemy import text
import os
from dotenv import load_dotenv
from routers.auth import auth_bp  # Import blueprint

load_dotenv()

def create_app():
    app = Flask(__name__)
    
    # Cấu hình CORS
    CORS(app, resources={r"/*": {"origins": "*"}})

    # Cấu hình database
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URL',
    'mssql+pyodbc://localhost/HairSalon?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes&TrustServerCertificate=yes'
)
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'n@)_tcqh0w_)+29#*8096nh4sw3#p&ojmlm$&r$z#j2y6+amet')

    # Khởi tạo extensions
    db.init_app(app)
    bcrypt.init_app(app)

    with app.app_context():
        try:
            # Test kết nối database
            db.session.execute(text('SELECT 1'))
            print("Kết nối database thành công!")
            # Tạo tất cả bảng trong database
            db.create_all()
        except Exception as e:
            print(f"Lỗi kết nối database: {str(e)}")
            raise e

    # Đăng ký blueprint
    app.register_blueprint(auth_bp, url_prefix='/api/auth')

    @app.route('/')
    def home():
        return jsonify({
            "message": "Welcome to Hair Salon API",
            "status": "running"
        })

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 8000)), debug=True)
