import requests

url = "http://localhost:8000/api/auth/login"
data = {
   "email": "phita1347@gmail.com",  # Thay đổi thành email bạn đã lưu
   "password": "12345"  # Thay đổi thành mật khẩu bạn đã lưu
}
response = requests.post(url, json=data)
print("Status Code:", response.status_code)
print("Response Text:", response.text)