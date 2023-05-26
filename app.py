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
from umami.lib.cms import initialize_firebase
from umami.lib.api import api
from umami.lib.cms import cms
from umami.lib.auth import auth


# Generate a random UUID (UUID version 4)
random_uuid = uuid.uuid4()

# Convert the UUID object to a string representation
uuid_string = str(random_uuid)
# print(os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"))

load_dotenv()  # This line loads the environment variables from the .env file
app = Flask(__name__)

app.register_blueprint(api, url_prefix='/api')
app.register_blueprint(cms, url_prefix='/cms')
app.register_blueprint(auth, url_prefix='/auth')

openai.api_key = os.environ["OPENAI_API_KEY"]
app.secret_key = os.environ["FLASK_SECRET_KEY"]

# db = initialize_firebase()


# Initialize Firebase and get Firestore client



if __name__ == '__main__':
    app.run(debug=True)


# @app.route('/store_message', methods=['POST'])
# def store_message():
#     print('/store_message')
#     message_data = request.get_json()

#     required_fields = ['id', 'chatId', 'senderId', 'content', 'type', 'status', 'timestamp']
#     if not all(field in message_data for field in required_fields):
#         return jsonify({"error": "Missing one or more required fields"}), 400

#     db = firestore.Client()

#     # Fetch the document that matches the id
#     docs = db.collection('messages').where('id', '==', message_data['id']).stream()

#     # If the document exists, update it with the new message
#     for doc in docs:
#         doc_ref = db.collection('messages').document(doc.id)
#         doc_ref.update({
#             'chatId': message_data['chatId'],
#             'senderId': message_data['senderId'],
#             'content': message_data['content'],
#             'type': message_data['type'],
#             'status': message_data['status'],
#             'attachments': message_data.get('attachments', []),
#             'timestamp': message_data['timestamp']
#         })
#         return jsonify({"message": "Message updated successfully"}), 200

#     # If the document does not exist, create a new one
#     doc_ref = db.collection('messages').document()
#     doc_ref.set({
#         'id': message_data['id'],
#         'chatId': message_data['chatId'],
#         'senderId': message_data['senderId'],
#         'content': message_data['content'],
#         'type': message_data['type'],
#         'status': message_data['status'],
#         'attachments': message_data.get('attachments', []),
#         'timestamp': message_data['timestamp']
#     })

#     return jsonify({"message": "Message stored successfully"}), 200




@app.route("/")
def home():
    return "<h1>MealMate(temp) 0.1.0</h1>"



