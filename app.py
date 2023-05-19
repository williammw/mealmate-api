import os
import openai
from dotenv import load_dotenv
from flask import Flask, request, jsonify, session,url_for, redirect
from datetime import datetime

import firebase_admin
from firebase_admin import credentials, auth, exceptions as firebase_exceptions, firestore
import requests
import json
import uuid
from flask import session
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from twilio.rest import Client as TwilioClient
# Generate a random UUID (UUID version 4)
random_uuid = uuid.uuid4()

# Convert the UUID object to a string representation
uuid_string = str(random_uuid)
# print(os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"))

load_dotenv()  # This line loads the environment variables from the .env file
app = Flask(__name__)
openai.api_key = os.environ["OPENAI_API_KEY"]
app.secret_key = os.environ["FLASK_SECRET_KEY"]

sendgrid_api_key = os.environ["SENDGRID_API_KEY"]
twilio_account_sid = os.environ["TWILIO_ACCOUNT_SID"]
twilio_auth_token = os.environ["TWILIO_AUTH_TOKEN"]

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
# just 9copy from stackoverflow
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join(os.getcwd(), "mealmate-b3b1e-ebfd113a2e1f.json")
# print("GOOGLE_APPLICATION_CREDENTIALS: ", os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'))

cred = credentials.Certificate(firebase_service_account_dict)
default_app = firebase_admin.initialize_app(cred)

print("Current Working Directory: ", os.getcwd())
print("Files in Current Directory: ", os.listdir())
print("GOOGLE_APPLICATION_CREDENTIALS: ", os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'))
print("DEFAULT APP NAME",default_app.name) 

db = firestore.client()


PROMPTS = {
    'en':
    "I am an AI chatbot designed to help users read restaurant menus and create personalized menu suggestions in English. I can provide recommendations on what to order, how to eat specific dishes, and cater to individual dietary preferences and restrictions.",
    'zh-cn': "我是一个AI聊天机器人，设计用于帮助用户阅读中文（中国）餐厅菜单并创建个性化菜单建议。我可以提供有关订购什么、如何品尝特定菜肴以及满足个人饮食偏好和限制的建议。",
    'zh-tw': "我是一個AI聊天機器人，設計用於幫助用戶閱讀中文（台灣）餐廳菜單並創建個性化菜單建議。我可以提供有關訂購什麼、如何品嚐特定菜餚以及滿足個人飲食偏好和限制的建議。",
    'zh-hk': "我係一個AI嘅聊天機械人，設計用嚟幫助用戶閱讀粵語餐廳菜單同創建個性化嘅菜單建議。我可以提供點單、食咩同適應個人飲食偏好同限制方面嘅建議。",
    'ja': "私は、英語でレストランのメニューを読んで、ユーザー向けのパーソナライズされたメニュー提案を作成するように設計されたAIチャットボットです。注文すべきものや特定の料理の食べ方、個々の食事の好みや制限に合わせる方法などの提案を提供できます。",
}



DEFAULT_MESSAGES = {
    'en': 'Hello! I\'m your restaurant chatbot, powered by OpenAI GPT-3.5. '
        'I can help you find the best restaurants nearby, recommend dishes, '
        'and answer any questions you might have about dining. Just type your '
        'question or request, and I\'ll do my best to assist you. Let\'s get started!',
    'zh-cn': '您好！我是您的餐厅聊天机器人，我可以帮助您找到附近最好的餐厅，推荐菜肴，'
        '并回答您可能对餐饮有的任何问题。只需要输入您的问题或请求，我将尽我所能为您提供帮助。让我们开始吧！',
    'zh-tw': '您好！我是您的餐廳聊天機器人，我可以幫助您找到附近最好的餐廳，推薦菜餚，'
        '並回答您可能對餐飲有的任何問題。只需要輸入您的問題或請求，我將盡我所能為您提供幫助。讓我們開始吧！',
    'zh-hk': '您好！我是您的餐廳聊天機器人，我可以幫助您找到附近最好的餐廳，推薦菜餚，'
        '並回答您可能對餐飲有的任何問題。只需要輸入您的問題或請求，我將盡我所能為您提供幫助。讓我們開始吧！',
    'ja': 'こんにちは！私はあなたのレストランチャットボットで、'
        '近くの最高のレストランを見つけること、料理をお勧めすること、ダイニングに関するあなたが持っているかもしれない質問に答えることができます。'
        'あなたの質問やリクエストを入力するだけで、私はあなたを最善にサポートします。始めましょう！'
}

@app.route('/get_default_message', methods=['POST'])
def get_default_message():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Invalid JSON data"}), 400

        language_code = data.get('language_code', 'en')  # default to English if no language code is provided
        default_message = DEFAULT_MESSAGES.get(language_code, DEFAULT_MESSAGES['en'])  # default to English message if no message for the requested language
        
        return jsonify({"default_message": default_message}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500




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
    data = request.json
    print(f'Request data: {data}')
    email_or_phone = data.get('email_or_phone')
    full_name = data.get('full_name')
    username = data.get('username')
    password = data.get('password')
    date_of_birth = data.get('date_of_birth')
    people_dining = data.get('people_dining')

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


@app.route('/save_user_data', methods=['POST'])
def save_user_data():
    email = request.form.get('email')
    security_code = request.form.get('security_code')

    # Save the user data to Firestore
    user_ref = db.collection('users').add({
        'email': email,
        'security_code': security_code
    })

    return jsonify({"message": "User data saved successfully"}), 200



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
import requests

def send_security_code(recipient, security_code, method=None):
    if method == "email":
        try:
            response = requests.post(
                "https://api.mailgun.net/v3/your-domain.com/messages",
                auth=("api", os.environ["MAIL_GUM_API"]),
                data={"from": "Excited User <mailgun@your-domain.com>",
                    "to": recipient,
                    "subject": "Your security code",
                    "text": f"Your security code is: {security_code}"})
            print("Email sent successfully.")
        except Exception as e:
            print("Error sending email:", e)

    elif method == "sms":
        try:
            twilio_client = TwilioClient(twilio_account_sid, twilio_auth_token)
            message = twilio_client.messages.create(
                body=f"Your security code is: {security_code}",
                from_="+85293203871",  # Replace with your Twilio phone number
                to=recipient,
            )
            print("SMS sent successfully.")
        except Exception as e:
            print("Error sending SMS:", e)
    else:
        print("Invalid method specified.")



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





# Mock database for users
users = {
    "user1": {
        "uid": "user1",
        "email": "user1@example.com",
        "displayName": "User One",
        "photoURL": "https://example.com/user1.jpg",
        "createdAt": "2023-05-01T00:00:00Z"
    },
    # Other users...
}

# get_user_details
@app.route('/get_user_details', methods=['GET'])
def get_user_details():
    # Get user ID from query parameters
    uid = request.args.get('uid')

    # Query Firestore for user details
    doc_ref = db.collection('users').document(uid)
    doc = doc_ref.get()
    if doc.exists:
        return jsonify(doc.to_dict()), 200
    else:
        return jsonify({"error": "User not found"}), 404


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


@app.route('/get_chat', methods=['GET'])
def get_chat():
    chat_id = request.args.get('chat_id')
    user_id = request.args.get('user_id')  # Add this line
    if not chat_id or not user_id:  # Update this line
        return jsonify({'error': 'Missing chat_id or user_id'}), 400

    chat_ref = db.collection('users').document(user_id).collection('chats').document(chat_id)
    chat = chat_ref.get()
    if not chat.exists:
        return jsonify({'error': 'Chat not found'}), 404

    return jsonify(chat.to_dict()), 200



@app.route('/get_chats', methods=['POST'])
def get_chats():
    user_id = request.form.get('user_id')

    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400

    user_chats = []
    chat_refs = db.collection('chats').where('user_id', '==', user_id).get()

    for chat_ref in chat_refs:
        chat_data = chat_ref.to_dict()
        chat_data['chat_id'] = chat_ref.id
        user_chats.append(chat_data)

    return jsonify(user_chats), 200



@app.route('/get_user_chats', methods=['GET'])
def get_user_chats():
    user_id = request.args.get('user_id')
    chats_ref = db.collection('chats')
    user_chats = chats_ref.where('user_id', '==', user_id).stream()
    user_chats_list = [chat.to_dict() for chat in user_chats]
    return jsonify({'success': True, 'chats': user_chats_list})



@app.route('/create_new_chat', methods=['POST'])
def create_new_chat():
    user_id = request.json.get('user_id')
    if not user_id:
        return jsonify({'error': 'Missing user_id'}), 400

    chat_id = str(uuid.uuid4())
    chat_data = {
        'createdAt': datetime.utcnow(),
        'updatedAt': datetime.utcnow(),
    }
    db.collection('users').document(user_id).collection('chats').document(chat_id).set(chat_data)

    user_ref = db.collection('users').document(user_id)
    user_ref.update({
        'currentChatId': chat_id,
    })

    return jsonify({'success': True, 'message': 'New chat created', 'chatId': chat_id, 'chat': chat_data}), 200


@app.route('/update_user_details', methods=['PUT'])
def update_user_details():
    user_id = request.json['user_id']
    user_details = request.json['user_details']

    user_ref = db.collection('users').document(user_id)

    # First, check if the user exists
    if not user_ref.get().exists:
        return jsonify({'error': 'User not found'}), 404

    # Update the user's details
    user_ref.update(user_details)

    return jsonify({'success': True, 'message': 'User details updated'})


@app.route('/add_message', methods=['POST'])
def add_message():
    user_id = request.json['user_id']
    chat_id = request.json['chat_id']
    message_content = request.json['message_content']
    message_id = str(uuid.uuid4())
    message_data = {
        'messageId': message_id,
        'createdAt': datetime.utcnow(),
        'updatedAt': datetime.utcnow(),
        'type': 'text',  # For simplicity, type is hard-coded as 'text'. You can update this based on your requirements
        'content': message_content,
        'sender': 'user',  # For simplicity, sender is hard-coded as 'user'. You can update this based on your requirements
        'processed': False,
        'response': {
            'content': '',
            'createdAt': None
        }
    }
    chat_ref = db.collection('users').document(user_id).collection('chats').document(chat_id)
    chat_data = chat_ref.get().to_dict()
    chat_data['messages'][message_id] = message_data
    chat_data['updatedAt'] = datetime.utcnow()
    chat_ref.set(chat_data)
    return jsonify({'success': True, 'message': 'New message added', 'message': message_data})


@app.route('/add_summary', methods=['POST'])
def add_summary():
    user_id = request.json['user_id']
    chat_id = request.json['chat_id']
    summary_content = request.json['summary_content']
    summary_id = str(uuid.uuid4())
    summary_data = {
        'summaryId': summary_id,
        'createdAt': datetime.utcnow(),
        'updatedAt': datetime.utcnow(),
        'content': summary_content
    }
    db.collection('users').document(user_id).collection('chats').document(chat_id).collection('summary').document(summary_id).set(summary_data)
    return jsonify({'success': True, 'message': 'New summary added', 'summary': summary_data})




@app.route('/store_message', methods=['POST'])
def store_message():
    print('/store_message')
    message_data = request.get_json()

    required_fields = ['id', 'chatId', 'senderId', 'content', 'type', 'status', 'timestamp']
    if not all(field in message_data for field in required_fields):
        return jsonify({"error": "Missing one or more required fields"}), 400

    db = firestore.Client()

    # Fetch the document that matches the id
    docs = db.collection('messages').where('id', '==', message_data['id']).stream()

    # If the document exists, update it with the new message
    for doc in docs:
        doc_ref = db.collection('messages').document(doc.id)
        doc_ref.update({
            'chatId': message_data['chatId'],
            'senderId': message_data['senderId'],
            'content': message_data['content'],
            'type': message_data['type'],
            'status': message_data['status'],
            'attachments': message_data.get('attachments', []),
            'timestamp': message_data['timestamp']
        })
        return jsonify({"message": "Message updated successfully"}), 200

    # If the document does not exist, create a new one
    doc_ref = db.collection('messages').document()
    doc_ref.set({
        'id': message_data['id'],
        'chatId': message_data['chatId'],
        'senderId': message_data['senderId'],
        'content': message_data['content'],
        'type': message_data['type'],
        'status': message_data['status'],
        'attachments': message_data.get('attachments', []),
        'timestamp': message_data['timestamp']
    })

    return jsonify({"message": "Message stored successfully"}), 200


@app.route('/get_messages_for_chat', methods=['POST'])
def get_messages_for_chat():
    data = request.get_json()
    chat_id = data['chat_id']
    limit = data.get('limit', 100)  # Use a default limit if one is not provided

    # Query Firestore for messages
    messages_ref = db.collection('messages')
    messages = messages_ref.where('chat_id', '==', chat_id).order_by('createdAt', direction=firestore.Query.DESCENDING).limit(limit).stream()

    # Convert message documents to dictionaries
    messages_dicts = [msg.to_dict() for msg in messages]

    return jsonify(messages_dicts)





@app.route("/")
def home():
    return "<h1>MealMate(temp) 0.0.9</h1>"



if __name__ == "__main__":
    app.run(debug=True)
