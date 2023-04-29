import os
import openai
from flask import Flask, request, jsonify

from dotenv import load_dotenv
from functools import wraps
from firebase_admin import credentials, auth

import uuid

# Generate a random UUID (UUID version 4)
random_uuid = uuid.uuid4()

# Convert the UUID object to a string representation
uuid_string = str(random_uuid)


load_dotenv()  # This line loads the environment variables from the .env file
app = Flask(__name__)
openai.api_key = os.environ["OPENAI_API_KEY"]

# Get the Firebase service account credentials from the environment variable
firebase_service_account = os.environ.get('FIREBASE_SERVICE_ACCOUNT')

# Convert the service account credentials from a single-line JSON string to a dictionary
firebase_service_account_dict = json.loads(firebase_service_account)

# Initialize the Firebase app with the service account credentials
cred = credentials.Certificate(firebase_service_account_dict)
firebase_app = initialize_app(cred)


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


def login(email, password):
    try:
        user = auth.get_user_by_email(email)
    except auth.UserNotFoundError:
        return {"error": "User not found"}

    # You can implement password verification here
    # Note: Firebase handles password hashing and verification on the client side
    # So you may need to use the Firebase client SDK for authentication in your Flutter app

    return {"uid": user.uid, "email": user.email}


def signup(email, password, display_name):
    try:
        user = auth.create_user(
            email=email, password=password, display_name=display_name)
        return {"uid": user.uid, "email": user.email}
    except auth.EmailAlreadyExistsError:
        return {"error": "Email already in use"}


app = Flask(__name__)


@app.route("/login", methods=["POST"])
def login_route():
    email = request.form.get("email")
    password = request.form.get("password")
    result = login(email, password)
    return jsonify(result)


@app.route("/signup", methods=["POST"])
def signup_route():
    email = request.form.get("email")
    password = request.form.get("password")
    display_name = request.form.get("display_name")
    result = signup(email, password, display_name)
    return jsonify(result)


@app.route("/")
def home():
    return "<h1>nothing special here</h1>"


if __name__ == "__main__":
    app.run(debug=True)
