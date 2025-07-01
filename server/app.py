from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
import pandas as pd

app = Flask(__name__)
CORS(app)  # 允許 Android 存取

# PostgreSQL 連線設定
conn = psycopg2.connect(
    host="localhost",      # 或你 PostgreSQL server 的 IP
    port="5433",           # 預設是 5432
    database="app",  # 資料庫名稱
    user="postgres",       # PostgreSQL 使用者
    password="1111"     # 替換成你設定的密碼
)

@app.route("/login", methods=["POST"])
def login():
    
    student_id = request.form.get("StudentID")  # 注意大小寫
	id_number = request.form.get("IDNumber")


    cur = conn.cursor()
    cur.execute("SELECT role FROM users WHERE studentid=%s AND idnumber=%s", (student_id, id_number))
    result = cur.fetchone()
    cur.close()

    if result:
        return jsonify({"success": True, "role": result[0]})
    else:
        return jsonify({"success": False})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
