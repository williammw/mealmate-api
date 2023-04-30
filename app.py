import os
import openai
from flask import Flask, request, jsonify

from dotenv import load_dotenv
from functools import wraps
from firebase_admin import credentials, auth as firebase_auth, initialize_app


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
default_app = initialize_app(cred)


PROMPTS = {
    'en':
    "I am an AI chatbot designed to help users read restaurant menus and create personalized menu suggestions in English. I can provide recommendations on what to order, how to eat specific dishes, and cater to individual dietary preferences and restrictions.",
    'zh-cn': "我是一个AI聊天机器人，设计用于帮助用户阅读中文（中国）餐厅菜单并创建个性化菜单建议。我可以提供有关订购什么、如何品尝特定菜肴以及满足个人饮食偏好和限制的建议。",
    'zh-tw': "我是一個AI聊天機器人，設計用於幫助用戶閱讀中文（台灣）餐廳菜單並創建個性化菜單建議。我可以提供有關訂購什麼、如何品嚐特定菜餚以及滿足個人飲食偏好和限制的建議。",
    'zh-hk': "我係一個AI嘅聊天機械人，設計用嚟幫助用戶閱讀粵語餐廳菜單同創建個性化嘅菜單建議。我可以提供點單、食咩同適應個人飲食偏好同限制方面嘅建議。",
    'ja': "私は、英語でレストランのメニューを読んで、ユーザー向けのパーソナライズされたメニュー提案を作成するように設計されたAIチャットボットです。注文すべきものや特定の料理の食べ方、個々の食事の好みや制限に合わせる方法などの提案を提供できます。",
}


def api_key_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get("X-API-Key")
        if not api_key or api_key != os.environ["API_KEY"]:
            return jsonify({"error": "Invalid or missing API key"}), 401
        return f(*args, **kwargs)
    return decorated_function


@app.route("/send_message", methods=["POST"])
@api_key_required
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


@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')

    try:
        # Verify the email and password provided by the user
        user = firebase_auth.sign_in_with_email_and_password(email, password)

        # Get a custom token for the user
        custom_token = firebase_auth.create_custom_token(user['localId'])

        # Sign in the user with the custom token and get the ID token
        id_token = firebase_auth.verify_id_token(custom_token)

        return jsonify({"status": "success", "user": user['localId'], "id_token": id_token}), 200
    except Exception as e:
        return jsonify({"status": "failure", "message": str(e)}), 400


@app.route('/signup', methods=['POST'])
def signup():
    email = request.form.get('email')
    password = request.form.get('password')
    display_name = request.form.get('display_name')

    try:
        user = firebase_auth.create_user(
            email=email, password=password, display_name=display_name)
        return jsonify({"status": "success", "user": user.uid}), 201
    except Exception as e:
        return jsonify({"status": "failure", "message": str(e)}), 400


@app.route('/logout', methods=['POST'])
def logout():
    id_token = request.form.get('id_token')

    try:
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token['uid']
        auth.revoke_refresh_tokens(uid)
        return jsonify({"status": "success", "message": "Logout successful"}), 200
    except Exception as e:
        return jsonify({"status": "failure", "message": str(e)}), 400


@app.route("/")
def home():
    return "<h1>nothing special here</h1>"


# @app.route('/test_signup', methods=['GET'])
# def test_signup():
#     base_url = "http://127.0.0.1:5000"

#     signup_data = {
#         "email": "william@xcxcxxc.com",
#         "password": "1234567z",
#         "display_name": "Test User"
#     }
#     signup_response = requests.post(f"{base_url}/signup", data=signup_data)
#     print("Signup response:", signup_response.json())
#     return signup_response.json()
#     return jsonify({"status": "success", "message": "Test signup complete"})


# @app.route('/test_login', methods=['GET'])
# def test_login():
#     base_url = "http://127.0.0.1:5000"

#     login_data = {
#         "email": "william@xcxcxxc.com",
#         "password": "1234567z",
#     }
#     login_response = requests.post(f"{base_url}/login", data=login_data)
#     return login_response.json()
#     print("Login response:", login_response.json())
#     id_token = login_response.json().get("id_token")

#     return jsonify({"status": "success", "message": "Test login complete", "id_token": id_token})


# @app.route('/test_logout', methods=['GET'])
# def test_logout():
#     base_url = "http://127.0.0.1:5000"

#     # Call the test_login function to get the login response
#     login_response = test_login()
#     # Extract the id_token from the login response
#     id_token = login_response.json.get("id_token")

#     if id_token:
#         logout_data = {
#             "id_token": id_token
#         }
#         logout_response = requests.post(f"{base_url}/logout", data=logout_data)
#         print("Logout response:", logout_response.json())
#         return logout_response.json()
#         return jsonify({"status": "success", "message": "Test logout complete"})
#     else:
#         logout_response.json()
#         return jsonify({"status": "failure", "message": "Test logout skipped due to login failure"})


# test_auth_functions()

if __name__ == "__main__":
    app.run(debug=True)
