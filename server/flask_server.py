import flask
import psycopg2
import sys
import json
from flask import jsonify
from flask import request
from flask import send_from_directory
import base64
import os
import uuid
#from db import get_db_connection 
#import hashlib  # 用於密碼加密

UPLOAD_FOLDER = 'uploads'  # 你的圖片存放資料夾
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = flask.Flask(__name__)

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/', methods=['GET', 'POST'])
def chat():
    msg_received = flask.request.get_json()
    msg_subject = msg_received.get("subject")
    print("📩 Received:", msg_received)

    if msg_subject == "register":
        return register(msg_received)
    elif msg_subject == "login":
        return login(msg_received)
    elif msg_subject =="addclothes":
        return addclothes(msg_received)
    elif msg_subject == "rent_clothes":
        return rent_clothes(msg_received)
    elif msg_subject == "get_num_by_size":
        return get_num_by_size(msg_received)
    else:
        print("❌ Invalid subject:", msg_subject)  # <== 加這行！
        return "Invalid request."

def register(msg_received):
    firstname = msg_received["firstname"]
    lastname = msg_received["lastname"]
    username = msg_received["username"]
    password = msg_received["password"]
    identity = msg_received['identity']

    # hashed_password = hashlib.md5(password.encode()).hexdigest()

    select_query = "SELECT * FROM login WHERE username = %s"
    db_cursor.execute(select_query, (username,))
    records = db_cursor.fetchall()

    if len(records) != 0:
        return "Another user used the username. Please choose another username."

    insert_query = """
        INSERT INTO login (first_name, last_name, username, password, identity)
        VALUES (%s, %s, %s, %s, %s)
    """
    insert_values = (firstname, lastname, username, password, identity)
    try:
        db_cursor.execute(insert_query, insert_values)
        conn.commit()
        return "success"
    except Exception as e:
        print("Error while inserting the new record:", repr(e))
        return "failure"

def login(msg_received):
    username = msg_received["username"]
    password = msg_received["password"]
    # password = hashlib.md5(password.encode()).hexdigest()

    select_query = """
        SELECT first_name, last_name, identity FROM login 
        WHERE username = %s AND password = %s
    """
    db_cursor.execute(select_query, (username, password))
    records = db_cursor.fetchall()

    if len(records) == 0:
        return "failure"
    else:
        result = {
            "status": "success",
            "identity": records[0][2],
            "lastName": records[0][1],
            "firstName": records[0][0]
        }
        return json.dumps(result)



def addclothes(msg_received):
    clothesName = msg_received.get("clothesName")
    clothesColor = msg_received.get("clothesColor")
    clothesSize = msg_received.get("clothesSize")
    clothesNum = msg_received.get("clothesNum")
    clothesType = msg_received.get("clothesType")
    suitableDance = msg_received.get("suitableDance")
    clothesPictureBase64 = msg_received.get("clothesPicture")

    if not clothesPictureBase64:
        return jsonify({"error": "No image data"}), 400

    # 去除可能的 data URI 前綴
    if ',' in clothesPictureBase64:
        clothesPictureBase64 = clothesPictureBase64.split(',', 1)[1]

    try:
        image_data = base64.b64decode(clothesPictureBase64)
    except Exception as e:
        return jsonify({"error": "Invalid base64 data"}), 400

    # 產生唯一檔名
    filename = f"{uuid.uuid4().hex}.jpg"
    image_path = os.path.join(UPLOAD_FOLDER, filename)
    '''image_path = f"http://10.0.2.2:5000/uploads/{filename}"'''

    with open(image_path, "wb") as f:
        f.write(image_data)

    insert_query = """
        INSERT INTO clothes (clothesname, clothescolor, clothessize, clothesnum, clothestype, suitabledance, clothespicture)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    insert_values = (
        clothesName,
        clothesColor,
        clothesSize,
        clothesNum,
        clothesType,
        suitableDance,
        filename
    )

    try:
        db_cursor.execute(insert_query, insert_values)
        conn.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        print("Error while inserting the new record:", repr(e))
        return jsonify({"status": "failure", "error": str(e)}), 500

@app.route("/select_rent_clothes", methods=["GET"])

def select_rent_clothes():
    try:
        db_cursor.execute("""
            SELECT clothespicture, clothesname, clothestype, clothescolor, clothesnum FROM clothes
        """)
        records = db_cursor.fetchall()

        clothes_list = []
        for row in records:
            clothes = {
                "clothesPicture": row[0],  # 應為圖片的網址
                "clothesName": row[1],
                "clothesType": row[2],
                "clothesColor": row[3],
                "clothesNum": row[4]
            }
            clothes_list.append(clothes)

        return jsonify(clothes_list)
    except Exception as e:
        print("Error while fetching clothes data:", repr(e))
        return jsonify({"status": "failure", "error": str(e)}), 500

@app.route('/rent_clothes', methods=['POST'])
def rent_clothes(msg_received):
    data = request.get_json()
    identity = msg_received.get('identity')
    first_name = msg_received.get('firstName')
    clothes_name = msg_received.get('clothesName')
    clothes_color = msg_received.get('clothesColor')
    clothes_size = msg_received.get('clothesSize')
    clothes_num = int(msg_received.get('clothesNum'))


    # 1. 查詢剩餘數量
    db_cursor.execute(
        'SELECT clothesnum FROM clothes WHERE clothesname = %s AND clothessize = %s',
        (clothes_name, clothes_size)
    )
    row = db_cursor.fetchone()

    if not row or row[0] < clothes_num:
        
        return "not_enough"

    # 2. 插入租借紀錄
    db_cursor.execute('''
        INSERT INTO rent (identity, first_name, clothesname, clothescolor, clothessize, clothesnum)
        VALUES (%s, %s, %s, %s, %s, %s)
    ''', (identity, first_name, clothes_name, clothes_color, clothes_size, clothes_num))

    # 3. 更新剩餘數量
    db_cursor.execute('''
        UPDATE clothes
        SET clothesnum = clothesnum - %s
        WHERE clothesname = %s AND clothessize = %s
    ''', (clothes_num, clothes_name, clothes_size))

    conn.commit()
    

    return "success"

@app.route("/get_num_by_size", methods=["POST"])
def get_num_by_size():
    msg_received = request.get_json()
    clothes_name = msg_received.get("clothesName")
    clothes_size = msg_received.get("clothesSize")

    if not clothes_name or not clothes_size:
        return "invalid_input", 400

    try:
        query = """
            SELECT SUM("clothesnum")
            FROM clothes
            WHERE "clothesname" = %s AND "clothessize" = %s
        """
        db_cursor.execute(query, (clothes_name, clothes_size))
        result = db_cursor.fetchone()
        total_num = result[0] if result[0] is not None else 0

        return str(total_num)

    except Exception as e:
        print("Database error:", e)
        return "server_error", 500

@app.route("/manage_rent", methods=["GET"])

def manage_rent():
    try:
        db_cursor.execute("""
            SELECT id, identity, first_name, clothesname, clothescolor, clothessize, clothesnum, status, price FROM rent
        """)
        records = db_cursor.fetchall()

        rent_list = []
        for row in records:
            rent = {
                "id": row[0],
                "identity": row[1],
                "firstName": row[2],
                "clothesName": row[3],  # 應為圖片的網址
                "clothesColor": row[4],
                "clothesSize": row[5],
                "clothesNum": row[6],
                "status": row[7],
                "price": row[8]
            }
            rent_list.append(rent)

        return jsonify(rent_list)
    except Exception as e:
        print("Error while fetching rent data:", repr(e))
        return jsonify({"status": "failure", "error": str(e)}), 500


@app.route('/update_rent_status', methods=['POST'])
def update_rent_status():
    try:
        data = request.get_json()
        id = data.get('id')
        new_status = data.get('status')

        # 先查出舊狀態和衣服資訊
        db_cursor.execute('SELECT status, clothesname, clothessize, clothesnum FROM rent WHERE id=%s', (id,))
        record = db_cursor.fetchone()

        if not record:
            return jsonify({"status": "failure", "error": "rent record not found"}), 404

        old_status, clothesname, clothessize, clothesnum = record

        # 狀態變更邏輯
        if old_status == "returned" and new_status in ("lent", "pending"):
            # 狀態從 returned 改回 lent/pending，扣回衣服數量
            db_cursor.execute('''
                UPDATE clothes
                SET clothesnum = clothesnum - %s
                WHERE clothesname = %s AND clothessize = %s
            ''', (clothesnum, clothesname, clothessize))

        elif old_status != "returned" and new_status == "returned":
            # 狀態從非 returned 變 returned，加回衣服數量
            db_cursor.execute('''
                UPDATE clothes
                SET clothesnum = clothesnum + %s
                WHERE clothesname = %s AND clothessize = %s
            ''', (clothesnum, clothesname, clothessize))


        

        db_cursor.execute("UPDATE rent SET status=%s WHERE id=%s", (new_status, id))
        conn.commit()
        return jsonify({"status": "success"}), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        print("Update error:", repr(e))
        return jsonify({"status": "failure", "error": str(e)}), 500

@app.route('/delete_rent', methods=['POST'])
def delete_rent():
    try:
        data = request.get_json()
        id = data.get('id')
        if not id:
            return jsonify({"status": "failure", "error": "missing id"}), 400

        db_cursor.execute('DELETE FROM rent WHERE id=%s', (id,))
        conn.commit()

        return jsonify({"status": "success"})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"status": "failure", "error": str(e)}), 500

@app.route('/delete_users', methods=['POST'])
def delete_users():
    try:
        data = request.get_json()
        id = data.get('id')
        if not id:
            return jsonify({"status": "failure", "error": "missing id"}), 400

        db_cursor.execute('DELETE FROM login WHERE id=%s', (id,))
        conn.commit()

        return jsonify({"status": "success"})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"status": "failure", "error": str(e)}), 500

@app.route('/get_users', methods=['GET'])
def get_users():
    db_cursor.execute('SELECT * FROM login')  # 根據你的表名可能是 users
    rows = db_cursor.fetchall()
    result = []
    for row in rows:
        result.append({
            "id": row[0],
            "firstName": row[1],
            "lastName": row[2],
            "username": row[3],
            "password": row[4],
            "registrationDate": row[5],
            "identity": row[6],
        })
    return jsonify(result)


@app.route("/check_rent", methods=["POST"])
def check_rent():
    try:
        data = request.get_json()
        identity = data.get("identity")
        first_name = data.get("firstName")

        if not identity or not first_name:
            return jsonify({"status": "failure", "error": "missing identity or firstName"}), 400

        db_cursor.execute("""
            SELECT id, identity, first_name, clothesname, clothescolor, clothessize, clothesnum, status, price
            FROM rent
            WHERE identity = %s AND first_name = %s
        """, (identity, first_name))
        records = db_cursor.fetchall()

        rent_list = []
        for row in records:
            rent = {
                "id": row[0],
                "identity": row[1],
                "firstName": row[2],
                "clothesName": row[3],
                "clothesColor": row[4],
                "clothesSize": row[5],
                "clothesNum": row[6],
                "status": row[7],
                "price": row[8]
            }
            rent_list.append(rent)

        return jsonify(rent_list)

    except Exception as e:
        print("❌ Error while fetching rent data:", repr(e))
        return jsonify({"status": "failure", "error": str(e)}), 500

@app.route('/add_money_all', methods=['POST'])
def add_money_all():
    try:
        data = request.get_json()
        year = data.get("year")
        semester = data.get("semester")
        price = data.get("price")

        if not all([year, semester, price]):
            return jsonify({"status": "failure", "error": "缺少欄位"}), 400

        # 查所有使用者
        db_cursor.execute("SELECT first_name, username FROM login")
        users = db_cursor.fetchall()

        # 對每個使用者新增一筆
        for user in users:
            first_name, username = user
            db_cursor.execute('''
                INSERT INTO money (first_name, username, year, semester, price)
                VALUES (%s, %s, %s, %s, %s)
            ''', (first_name, username, year, semester, price))

        conn.commit()
        return jsonify({"status": "success"})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"status": "failure", "error": str(e)}), 500

@app.route("/manage_money", methods=["GET"])

def manage_money():
    try:
        db_cursor.execute("""
            SELECT * FROM money
        """)
        records = db_cursor.fetchall()

        money_list = []
        for row in records:
            money = {
                "id": row[0],
                "firstName": row[1],
                "username": row[2],
                "year": row[3],  
                "semester": row[4],
                "price": row[5],
                "status": row[6],
            }
            money_list.append(money)

        return jsonify(money_list)
    except Exception as e:
        print("Error while fetching rent data:", repr(e))
        return jsonify({"status": "failure", "error": str(e)}), 500


@app.route('/update_money_status', methods=['POST'])
def update_money_status():
    try:
        data = request.get_json()
        id = data.get('id')
        new_status = data.get('status')

        # 先查出舊狀態和衣服資訊
        db_cursor.execute('SELECT status FROM money WHERE id=%s', (id,))
        record = db_cursor.fetchone()

        if not record:
            return jsonify({"status": "failure", "error": "money record not found"}), 404

        old_status = record

        db_cursor.execute("UPDATE money SET status=%s WHERE id=%s", (new_status, id))
        conn.commit()
        return jsonify({"status": "success"}), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        print("Update error:", repr(e))
        return jsonify({"status": "failure", "error": str(e)}), 500

@app.route('/delete_money', methods=['POST'])
def delete_money():
    try:
        data = request.get_json()
        id = data.get('id')
        if not id:
            return jsonify({"status": "failure", "error": "missing id"}), 400

        db_cursor.execute('DELETE FROM money WHERE id=%s', (id,))
        conn.commit()

        return jsonify({"status": "success"})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"status": "failure", "error": str(e)}), 500

@app.route("/check_money", methods=["POST"])
def check_money():
    try:
        data = request.get_json()
        first_name = data.get("firstName")

        if not first_name:
            return jsonify({"status": "failure", "error": "missing firstName"}), 400

        db_cursor.execute("""
            SELECT *
            FROM money
            WHERE first_name = %s
        """, (first_name,))  # 注意這裡是 tuple

        records = db_cursor.fetchall()

        money_list = []
        for row in records:
            money = {
                "id": row[0],
                "firstName": row[1],
                "username": row[2],
                "year": row[3],
                "semester": row[4],
                "price": row[5],
                "status": row[6]
            }
            money_list.append(money)

        return jsonify(money_list)

    except Exception as e:
        print("❌ Error while fetching money data:", repr(e))
        return jsonify({"status": "failure", "error": str(e)}), 500


    

# ✅ 連接 PostgreSQL
#def get_db_connection():
try:
    conn = psycopg2.connect(
        host="localhost",
        port="5433",
        database="app",
        user="postgres",
        password="1111"
    )
    print("✅ 成功連線資料庫")
except Exception as e:
    sys.exit(f"❌ 資料庫連線失敗：{e}")

db_cursor = conn.cursor()

# ✅ 啟動 Flask 伺服器
app.run(host="0.0.0.0", port=5000, debug=True, threaded=True)