import os
import openai
from dotenv import load_dotenv
from flask import Flask, request, jsonify, session

import firebase_admin
from firebase_admin import credentials, auth, exceptions as firebase_exceptions
import requests
import json
import uuid

# Generate a random UUID (UUID version 4)
random_uuid = uuid.uuid4()

# Convert the UUID object to a string representation
uuid_string = str(random_uuid)


load_dotenv()  # This line loads the environment variables from the .env file
app = Flask(__name__)
openai.api_key = os.environ["OPENAI_API_KEY"]
app.secret_key = os.environ["FLASK_SECRET_KEY"]

firebase_service_account_dict = {
    "type": os.environ.get("FIREBASE_TYPE"),
    "project_id": os.environ.get("FIREBASE_PROJECT_ID"),
    "private_key_id": os.environ.get("FIREBASE_PRIVATE_KEY_ID"),
    "private_key": os.environ.get("FIREBASE_PRIVATE_KEY").replace('\\n', '\n'),
    "client_email": os.environ.get("FIREBASE_CLIENT_EMAIL"),
    "client_id": os.environ.get("FIREBASE_CLIENT_ID"),
    "auth_uri": os.environ.get("FIREBASE_AUTH_URI"),
    "token_uri": os.environ.get("FIREBASE_TOKEN_URI"),
    "auth_provider_x509_cert_url": os.environ.get("FIREBASE_AUTH_PROVIDER_X509_CERT_URL"),
    "client_x509_cert_url": os.environ.get("FIREBASE_CLIENT_X509_CERT_URL"),
}

cred = credentials.Certificate(firebase_service_account_dict)
firebase_admin.initialize_app(cred)


PROMPTS = {
    'en':
    "I am an AI chatbot designed to help users read restaurant menus and create personalized menu suggestions in English. I can provide recommendations on what to order, how to eat specific dishes, and cater to individual dietary preferences and restrictions.",
    'zh-cn': "我是一个AI聊天机器人，设计用于帮助用户阅读中文（中国）餐厅菜单并创建个性化菜单建议。我可以提供有关订购什么、如何品尝特定菜肴以及满足个人饮食偏好和限制的建议。",
    'zh-tw': "我是一個AI聊天機器人，設計用於幫助用戶閱讀中文（台灣）餐廳菜單並創建個性化菜單建議。我可以提供有關訂購什麼、如何品嚐特定菜餚以及滿足個人飲食偏好和限制的建議。",
    'zh-hk': "我係一個AI嘅聊天機械人，設計用嚟幫助用戶閱讀粵語餐廳菜單同創建個性化嘅菜單建議。我可以提供點單、食咩同適應個人飲食偏好同限制方面嘅建議。",
    'ja': "私は、英語でレストランのメニューを読んで、ユーザー向けのパーソナライズされたメニュー提案を作成するように設計されたAIチャットボットです。注文すべきものや特定の料理の食べ方、個々の食事の好みや制限に合わせる方法などの提案を提供できます。",
}


    
@app.route("/send_message", methods=["POST"])
def send_message():
    message = request.json.get("message")
    language_code = request.json.get("language_code")

    if not message or not language_code:
        return jsonify({"error": "Missing message or language_code"}), 400

    language_prompt = PROMPTS.get(language_code, PROMPTS["en"])
    full_prompt = f"{language_prompt}\n\nUser: {message}"

    try:
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=full_prompt,
            max_tokens=1000,
            temperature=0.8,
        )
        response_text = response.choices[0].text.strip()
        return jsonify({"response": response_text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

from flask import session

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"status": "failure", "message": "Missing email or password"}), 400

    if 'user_id' in session:
        return jsonify({"status": "failure", "message": "User already logged in"}), 400

    try:
        user = auth.get_user_by_email(email)
        if not user:
            return jsonify({"status": "failure", "message": "User not found"}), 404

        # Add your own password verification logic here

        session['user_id'] = user.uid
        return jsonify({"status": "success", "user": user.uid}), 200
    except Exception as e:
        return jsonify({"status": "failure", "message": str(e)}), 400

@app.route('/logout', methods=['POST'])
def logout():
    if 'user_id' in session:
        session.pop('user_id', None)
        return jsonify({"status": "success", "message": "User logged out"}), 200
    else:
        return jsonify({"status": "failure", "message": "No user logged in"}), 400


# @app.route('/test_login', methods=['GET'])
# def test_login():
#     base_url = "http://127.0.0.1:5000"

#     login_data = {
#         "email": "a@a.com",
#         "password": "1234567z",
#     }
#     headers = {'Content-type': 'application/json'}

#     login_response = requests.post(f"{base_url}/login", json=login_data, headers=headers)
#     return login_response.json()

# def verify_id_token(id_token):
#     try:
#         decoded_token = auth.verify_id_token(id_token)
#         return decoded_token
#     except Exception as e:
#         print(f"Error verifying ID token: {str(e)}")
#         return None

@app.route('/is_logged_in', methods=['POST'])
def is_logged_in():
    id_token = request.json.get("idToken")

    if not id_token:
        return jsonify({"status": "failure", "message": "Missing idToken"}), 400

    decoded_token = verify_id_token(id_token)

    if decoded_token:
        return jsonify({"status": "success", "message": "User is logged in", "user": decoded_token["uid"]}), 200
    else:
        return jsonify({"status": "failure", "message": "User is not logged in"}), 401

# Update test_logout function
# @app.route('/test_logout', methods=['GET'])
# def test_logout():
#     base_url = "http://127.0.0.1:5000"

#     login_data = {
#         "email": "a@a.com",
#         "password": "1234567z",
#     }
#     headers = {'Content-type': 'application/json'}

#     login_response = requests.post(f"{base_url}/login", json=login_data, headers=headers)
#     print(f"Login Response: {login_response.json()}")  # Added print statement

#     id_token = login_response.json().get("idToken")

#     if not id_token:
#         return jsonify({"status": "failure", "message": "Login failed"}), 400

#     is_logged_in_data = {
#         "idToken": id_token,
#     }

#     is_logged_in_response = requests.post(f"{base_url}/is_logged_in", json=is_logged_in_data, headers=headers)
#     print(f"Is Logged In Response: {is_logged_in_response.json()}")

#     logout_data = {
#         "idToken": id_token,
#     }

#     logout_response = requests.post(f"{base_url}/logout", json=logout_data, headers=headers)
#     return logout_response.json()


@app.route("/")
def home():
    return "<h1>nothing special here</h1>"



if __name__ == "__main__":
    app.run(debug=True)
