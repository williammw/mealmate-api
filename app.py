import os
import openai
from dotenv import load_dotenv
from flask import Flask, request, jsonify, session,url_for, redirect

import firebase_admin
from firebase_admin import credentials, auth, exceptions as firebase_exceptions, firestore
import requests
import json
import uuid
from flask import session
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
db = firestore.client()


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
    


@app.route('/signup', methods=['POST'])
def signup():
    email_or_phone = request.form.get('email_or_phone')
    full_name = request.form.get('full_name')
    username = request.form.get('username')
    password = request.form.get('password')
    date_of_birth = request.form.get('date_of_birth')
    people_dining = request.form.get('people_dining')

    try:
        # Create the user with Firebase Authentication
        if '@' in email_or_phone:
            user = auth.create_user(
                email=email_or_phone,
                password=password
            )
        else:
            user = auth.create_user(
                phone_number=email_or_phone,
                password=password
            )
        
        # Add the user data to Firestore
        user_ref = db.collection('users').document(user.uid)
        user_ref.set({
            'email_or_phone': email_or_phone,
            'full_name': full_name,
            'username': username,
            'date_of_birth': date_of_birth,
            'people_dining': people_dining,
            'bio': '',
        })

        # Send a security code to the user (via email or SMS)
        security_code = generate_security_code()
        if '@' in email_or_phone:
            send_security_code(email_or_phone, security_code, method="email")
        else:
            send_security_code(email_or_phone, security_code, method="sms")

        # Store the security code in Firestore
        user_ref.update({
            'security_code': security_code
        })

        return jsonify({"message": "User created successfully", "user_id": user.uid, "email_or_phone": email_or_phone}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/verify_security_code', methods=['POST'])
def verify_security_code():
    email = request.form.get('email')
    user_input_security_code = request.form.get('security_code')

    print(f"Email: {email}")
    print(f"User Input Security Code: {user_input_security_code}")


    # Get the user data from Firestore
    user_ref = db.collection('users').where('email', '==', email).get()

    if user_ref:
        print(f"User Data: {user_ref[0].to_dict()}")
        stored_security_code = user_ref[0].to_dict().get('security_code')

        if user_input_security_code == stored_security_code:
            # Verification successful
            return jsonify({"message": "Security code verified successfully"}), 200
        else:
            # Verification failed
            return jsonify({"error": "Invalid security code"}), 400
    else:
        return jsonify({"error": "User data not found"}), 404

def generate_security_code():
    # Implement your code generation logic here
    pass

def send_security_code(email, security_code):
    # Implement your email sending logic here
    pass

@app.route('/get_user_data', methods=['POST'])
def get_user_data():
    email = request.form.get('email')

    # Get the user data from Firestore
    user_ref = db.collection('users').document(email)
    user_data = user_ref.get().to_dict()

    if user_data:
        return jsonify(user_data)
    else:
        return jsonify({"error": "User data not found"}), 404


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


@app.route("/")
def home():
    return "<h1>nothing special here 0.0.1</h1>"



if __name__ == "__main__":
    app.run(debug=True)
