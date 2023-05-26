from flask import Blueprint, jsonify, request
import openai
api = Blueprint('api', __name__)

PROMPTS = {
    'en':"I am an AI chatbot that finds and lists restaurants according to user preferences, providing personalized menu selection from specified restaurants. I also offer translation and analysis of menus, providing customized menus based on budget and number of people.",
    'zh-cn': "我是一个AI聊天机器人，根据用户喜好查找并列出餐厅，将指定餐厅的菜单为用户提供个性化菜单选择。我还提供菜单的翻译和分析，根据预算和人数提供定制的菜单。",
    'zh-tw': "我是一個AI聊天機器人，根據用戶喜好查找並列出餐廳，將指定餐廳的菜單為用戶提供個人化菜單選擇。我還提供菜單的翻譯和分析，根據預算和人數提供客製化的菜單。",
    'zh-hk': "我是一個AI聊天機器人，根據用戶喜好尋找並列舉餐廳，將指定餐廳的菜單為用戶提供個人化菜單選擇。亦提供翻譯和分析菜單，從預算和人數提供客製化的菜單。",
    'ja': "私はAIチャットボットで、ユーザーの好みに基づいてレストランを見つけてリスト化し、特定のレストランのメニューからパーソナライズされたメニュー選択を提供します。また、メニューの翻訳と分析を行い、予算と人数に基づいたカスタマイズされたメニューを提供します。",
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



@api.route('/get_default_message', methods=['POST'])
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



@api.route("/send_message", methods=["POST"])
def send_message():
    
    data = request.json
    message = data.get("message")
    language_code = data.get("language_code")
    print("send_message called")
    print(message)
    print(language_code)
    if not message or not language_code:
        return jsonify({"error": "Missing message or language_code"}), 400

    language_prompt = PROMPTS.get(language_code, PROMPTS["en"])

    messages = [
        {"role": "system", "content": language_prompt},
        {"role": "user", "content": message}
    ]

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
        print('try call openAI')
        response_text = response['choices'][0]['message']['content'].strip()
        print(f'Raw response text: {response}')
        print(response_text)
        return jsonify({"response": response_text})
    except Exception as e:
        print(str(e))  # Log the exception
        return jsonify({"error": str(e)}), 500

@api.route("/send_message_davinci", methods=["POST"])
def send_message_davinci():
    
    data = request.json
    message = data.get("message")
    language_code = data.get("language_code")
    print("send_message_davinci called")
    print(message)
    print(language_code)
    if not message or not language_code:
        return jsonify({"error": "Missing message or language_code"}), 400
        
    language_prompt = PROMPTS.get(language_code, PROMPTS["en"])

    messages = [
        {"role": "system", "content": language_prompt},
        {"role": "user", "content": message}
    ]

    conversation_history = "\n".join(f'{msg["role"].title()}: {msg["content"]}' for msg in messages)

    try:
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=conversation_history + "\nAI:",
            temperature=0.9,
            max_tokens=1000,
            top_p=0.1,
            frequency_penalty=0.0,
            presence_penalty=0.6,
            stop=[" Human:", " AI:"]
        )
        print('try call openAI')
        response_text = response['choices'][0]['text'].strip()
        print(f'Raw response text: {response}')
        print(response_text)
        return jsonify({"response": response_text})
    except Exception as e:
        print(str(e))  # Log the exception
        return jsonify({"error": str(e)}), 500

