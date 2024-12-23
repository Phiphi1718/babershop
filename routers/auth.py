# routers/auth.py

from flask import Blueprint, request, current_app, jsonify
from datetime import datetime, timedelta
from extensions import db, bcrypt
from models.user import User
import jwt
from functools import wraps
import random
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

load_dotenv()  # Load biến môi trường từ file .env

auth_bp = Blueprint('auth', __name__)

# Secret key cho JWT
SECRET_KEY = "n7clxzu#tm^#pdlym2ma5^bznvi2fl4yv47*tl59#5aj7l*w_4"

# Decorator để check JWT token
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token khong ton tai!'}), 401
        try:
            token = token.split(" ")[1]  # Lấy token từ "Bearer <token>"
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            current_user = User.query.filter_by(userID=data['user_id']).first()
        except:
            return jsonify({'message': 'Token khong hop le!'}), 401
        return f(current_user, *args, **kwargs)
    return decorated

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    # Kiểm tra dữ liệu đầu vào
    required_fields = ['fullName', 'email', 'phone', 'password']
    for field in required_fields:
        if field not in data:
            return jsonify({"message": f"Thieu truong {field}"}), 400

    # Kiểm tra email đã tồn tại
    if User.query.filter_by(email=data['email']).first():
        return jsonify({"message": "Email da ton tai!"}), 400

    # Mã hóa mật khẩu
    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')

    # Tạo user mới với typeID = 2 (user thường)
    new_user = User(
        fullName=data['fullName'],
        email=data['email'],
        phone=data['phone'],
        passwordHash=hashed_password,
        typeID=2,  # Mặc định là user thường
        createdAt=datetime.utcnow(),
        updatedAt=datetime.utcnow()
    )

    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify({
            "message": "Dang ky thanh cong!",
            "user": {
                "id": new_user.userID,
                "fullName": new_user.fullName,
                "email": new_user.email,
                "typeID": new_user.typeID
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Loi khi dang ky!", "error": str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    if not data or not data.get('email') or not data.get('password'):
        return jsonify({"message": "Thieu email hoac mat khau!"}), 400

    user = User.query.filter_by(email=data['email']).first()

    if not user:
        return jsonify({"message": "Email hoac mat khau khong dung!"}), 401

    if bcrypt.check_password_hash(user.passwordHash, data['password']):
        # Tạo JWT token
        token = jwt.encode({
            'user_id': user.userID,
            'email': user.email,
            'exp': datetime.utcnow() + timedelta(hours=24)
        }, SECRET_KEY)

        return jsonify({
            "message": "Dang nhap thanh cong!",
            "token": token,
            "user": {
                "id": user.userID,
                "fullName": user.fullName,
                "email": user.email,
                "typeID": user.typeID
            }
        }), 200

    return jsonify({"message": "Email hoac mat khau khong dung!"}), 401

# API xem thông tin profile (yêu cầu đăng nhập)
@auth_bp.route('/profile', methods=['GET'])
@token_required
def get_profile(current_user):
    return jsonify({
        "user": {
            "id": current_user.userID,
            "fullName": current_user.fullName,
            "email": current_user.email,
            "phone": current_user.phone
        }
    })

# API cập nhật profile (yêu cầu đăng nhập)
@auth_bp.route('/profile/update', methods=['PUT'])
@token_required
def update_profile(current_user):
    data = request.get_json()
    
    if 'fullName' in data:
        current_user.fullName = data['fullName']
    if 'phone' in data:
        current_user.phone = data['phone']
    
    current_user.updatedAt = datetime.utcnow()
    
    try:
        db.session.commit()
        return jsonify({
            "message": "Cap nhat thong tin thanh cong!",
            "user": {
                "id": current_user.userID,
                "fullName": current_user.fullName,
                "email": current_user.email,
                "phone": current_user.phone
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Loi khi cap nhat thong tin!", "error": str(e)}), 500

# API đổi mật khẩu (yêu cầu đăng nhập)
@auth_bp.route('/update-password', methods=['POST'])
def update_password():
    data = request.get_json()
    
    # Kiểm tra dữ liệu đầu vào
    required_fields = ['email', 'current_password', 'new_password', 'confirm_password']
    for field in required_fields:
        if field not in data:
            return jsonify({"message": f"Thieu truong {field}"}), 400

    # Kiểm tra mật khẩu mới và xác nhận mật khẩu
    if data['new_password'] != data['confirm_password']:
        return jsonify({"message": "Mat khau moi va xac nhan mat khau khong khop!"}), 400

    user = User.query.filter_by(email=data['email']).first()
    if not user:
        return jsonify({"message": "Email khong ton tai!"}), 404

    # Kiểm tra mật khẩu hiện tại
    if not bcrypt.check_password_hash(user.passwordHash, data['current_password']):
        return jsonify({"message": "Mat khau hien tai khong dung!"}), 401

    try:
        # Cập nhật mật khẩu mới
        user.passwordHash = bcrypt.generate_password_hash(data['new_password']).decode('utf-8')
        user.updatedAt = datetime.utcnow()
        db.session.commit()
        return jsonify({"message": "Doi mat khau thanh cong!"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Loi khi doi mat khau!", "error": str(e)}), 500

# Hàm gửi email
def send_email(to_email, subject, body):
    try:
        msg = MIMEMultipart()
        msg['From'] = os.getenv('MAIL_USERNAME')
        msg['To'] = to_email
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(os.getenv('MAIL_SERVER'), int(os.getenv('MAIL_PORT')))
        server.starttls()
        server.login(os.getenv('MAIL_USERNAME'), os.getenv('MAIL_PASSWORD'))
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Loi gui email: {str(e)}")
        return False

# Hàm tạo mật khẩu ngẫu nhiên
def generate_password():
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for i in range(10))

# API quên mật khẩu
@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    data = request.get_json()
    
    if not data or not data.get('email'):
        return jsonify({"message": "Vui long nhap email!"}), 400

    user = User.query.filter_by(email=data['email']).first()
    if not user:
        return jsonify({"message": "Email khong ton tai!"}), 404

    # Tạo mật khẩu mới
    new_password = generate_password()
    
    # Gửi email
    email_subject = "Reset Mat Khau - Hair Salon"
    email_body = f"""
    Xin chao {user.fullName},
    
    Mat khau moi cua ban la: {new_password}
    
    Vui long dang nhap va doi mat khau ngay sau khi nhan duoc email nay.
    
    Tran trong,
    Hair Salon Team
    """

    if send_email(user.email, email_subject, email_body):
        # Cập nhật mật khẩu mới trong database
        user.passwordHash = bcrypt.generate_password_hash(new_password).decode('utf-8')
        user.updatedAt = datetime.utcnow()
        
        try:
            db.session.commit()
            return jsonify({"message": "Mat khau moi da duoc gui den email cua ban!"}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"message": "Loi khi cap nhat mat khau!", "error": str(e)}), 500
    else:
        return jsonify({"message": "Loi khi gui email!"}), 500
