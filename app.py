import os
import openai
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from functools import wraps

load_dotenv()  # This line loads the environment variables from the .env file
app = Flask(__name__)
openai.api_key = os.environ["OPENAI_API_KEY"]

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


@app.route("/")
def home():
    return "<h1>Welcome to the MealMate API!</h1>"




if __name__ == "__main__":
    app.run(debug=True)
