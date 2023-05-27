import os
from dotenv import load_dotenv
from flask import Flask, Blueprint
from google.oauth2 import service_account

import uuid

from flask import Flask, request, jsonify, session,url_for, redirect
from datetime import datetime

import firebase_admin
from firebase_admin import initialize_app, credentials, auth, exceptions as firebase_exceptions, firestore
import requests
import json

default_app = None
db = None
cms = Blueprint('cms', __name__)

def initialize_firebase():
    global default_app
    global db

    if not default_app:
        # Generate a random UUID (UUID version 4)
        random_uuid = uuid.uuid4()
        # Convert the UUID object to a string representation
        uuid_string = str(random_uuid)

        load_dotenv()  # This line loads the environment variables from the .env file

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

        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join(os.getcwd(), "mealmate-b3b1e-ebfd113a2e1f.json")

        cred = credentials.Certificate(firebase_service_account_dict)
        default_app = initialize_app(cred)

        print("Current Working Directory: ", os.getcwd())
        print("Files in Current Directory: ", os.listdir())
        print("GOOGLE_APPLICATION_CREDENTIALS: ", os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'))
        print("DEFAULT APP NAME", default_app.name) 

    if not db:
        db = firestore.client()

    return db

db = initialize_firebase()




@cms.route('/save_user_data', methods=['POST'])
def save_user_data():
    email = request.form.get('email')
    security_code = request.form.get('security_code')
    uid = request.form.get('auth_token')

    user_ref = db.collection('users').document(uid)

    # Save the user data to Firestore
    user_ref.update({
        # 'email': email,
        'security_code': security_code
    })

    return jsonify({"message": "User data saved successfully"}), 200





def generate_security_code():
    # Implement your code generation logic here
    pass
import requests


@cms.route('/get_user_data', methods=['POST'])
def get_user_data():
    email = request.form.get('email')

    # Get the user data from Firestore
    user_ref = db.collection('users').document(email)
    user_data = user_ref.get().to_dict()

    if user_data:
        return jsonify(user_data)
    else:
        return jsonify({"error": "User data not found"}), 404




# get_user_details
@cms.route('/get_user_details', methods=['GET'])
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


@cms.route('/get_chat', methods=['GET'])
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



@cms.route('/get_chats', methods=['POST'])
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



@cms.route('/get_user_chats', methods=['GET'])
def get_user_chats():
    user_id = request.args.get('user_id')
    chats_ref = db.collection('chats')
    user_chats = chats_ref.where('user_id', '==', user_id).stream()
    user_chats_list = [chat.to_dict() for chat in user_chats]
    return jsonify({'success': True, 'chats': user_chats_list})



@cms.route('/create_new_chat', methods=['POST'])
def create_new_chat():
    user_id = request.json.get('user_id')
    if not user_id:
        return jsonify({'error': 'Missing user_id'}), 400

    chat_id = str(uuid.uuid4())
    chat_data = {
        'createdAt': datetime.utcnow().isoformat() + 'Z',  # ISO 8601 format
        'updatedAt': datetime.utcnow().isoformat() + 'Z',  # ISO 8601 format
    }
    # Create the chat
    chat_ref = db.collection('users').document(user_id).collection('chats').document(chat_id)
    chat_ref.set(chat_data)

    # Create the initial message
    message_data = {
        'chat_id': chat_id,
        'content': "Hello! How can I assist you today on restaurant menus?",
        'created_at': firestore.SERVER_TIMESTAMP,
        'message_id': "bot",
        'processed': True,
        'sender': "bot",
        'type': "text",
        'updated_at': firestore.SERVER_TIMESTAMP,
    }
    chat_ref.collection('messages').document().set(message_data)

    # Update the user document
    user_ref = db.collection('users').document(user_id)
    user_ref.update({
        'current_chat_id': chat_id,
    })

    return jsonify({'success': True, 'message': 'New chat created', 'chatId': chat_id, 'chat': chat_data}), 200


@cms.route("/store_message", methods=["POST"])
def store_message():
    data = request.get_json()

    user_id = data.get("user_id")
    chat_id = data.get("chat_id")
    message = data.get("message")

    if not user_id or not chat_id or not message:
        return jsonify({"error": "Missing user_id, chat_id, or message"}), 400
    
    # Add created_at and updated_at fields
    # now = datetime.datetime.now().isoformat()
    message['created_at'] = firestore.SERVER_TIMESTAMP
    message['updated_at'] = firestore.SERVER_TIMESTAMP


    try:
        print(f'storing message {message}');
        db.collection('users').document(user_id).collection('chats').document(chat_id).collection('messages').add(message)
        return jsonify({"success": "Message stored successfully"}), 200
    except Exception as e:
        print(f"Failed to store message. Error: {str(e)}")  # Log the error
        return jsonify({"error": str(e)}), 500


@cms.route('/update_user_details', methods=['PUT'])
def update_user_details():
    data = request.get_json()

    if 'user_id' in data and 'user_details' in data:
        user_id = data['user_id']
        user_details = data['user_details']

        # Check if user_details contains 'preferredLanguage' field
        if 'preferredLanguage' not in user_details:
            return jsonify({'error': 'Missing preferredLanguage in user details'}), 400

        user_ref = db.collection('users').document(user_id)

        # First, check if the user exists
        if not user_ref.get().exists:
            return jsonify({'error': 'User not found'}), 404

        # Update the user's details
        user_ref.update(user_details)

        return jsonify({'success': True, 'message': 'User details updated'}), 200
    else:
        return jsonify({'error': 'Missing user_id or user_details in request data'}), 400



@cms.route('/add_message', methods=['POST'])
def add_message():
    user_id = request.json['user_id']
    chat_id = request.json['chat_id']
    message_content = request.json['message_content']
    message_id = str(uuid.uuid4())
    message_data = {
        'messageId': message_id,
        'createdAt': firestore.SERVER_TIMESTAMP,
        'updatedAt': firestore.SERVER_TIMESTAMP,
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
    chat_data['updatedAt'] = firestore.SERVER_TIMESTAMP
    chat_ref.set(chat_data)
    return jsonify({'success': True, 'message': 'New message added', 'message': message_data})


@cms.route('/add_summary', methods=['POST'])
def add_summary():
    user_id = request.json['user_id']
    chat_id = request.json['chat_id']
    summary_content = request.json['summary_content']
    summary_id = str(uuid.uuid4())
    summary_data = {
        'summaryId': summary_id,
        'createdAt': firestore.SERVER_TIMESTAMP,
        'updatedAt': firestore.SERVER_TIMESTAMP,
        'content': summary_content
    }
    db.collection('users').document(user_id).collection('chats').document(chat_id).collection('summary').document(summary_id).set(summary_data)
    return jsonify({'success': True, 'message': 'New summary added', 'summary': summary_data})




@cms.route('/get_messages_for_chat', methods=['POST'])
def get_messages_for_chat():
    print("Inside get_messages_for_chat")  # Add this line
    data = request.get_json()
    chat_id = data['chat_id']
    user_id = data['user_id']
    limit = data.get('limit', 40)  # Default limit is 40
    # print(f"data: {data}")
    print(f"chat_id: {chat_id}")
    print(f"user_id: {user_id}")
    print(f"limit: {limit}")
    try:
        # Query Firestore for all messages in a chat
        messages_ref = db.collection('users').document(user_id).collection('chats').document(chat_id).collection('messages')
        messages_query = messages_ref.order_by('created_at', direction=firestore.Query.DESCENDING).limit(limit)
        messages = messages_query.stream()
        

        messages_list = [msg.to_dict() for msg in messages]

        if messages_list:
            return jsonify(messages_list), 200
        else:
            return jsonify({'message': 'No messages found'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@cms.route('/get_message_test', methods=['GET'])
def get_message():
    print("Inside get_message")
    chat_id = request.args.get('chat_id')
    user_id = request.args.get('user_id')
    limit = request.args.get('limit', default=40, type=int)
    print(f"chat_id: {chat_id}")
    print(f"user_id: {user_id}")
    print(f"limit: {limit}")
    try:
        # Query Firestore for all messages in a chat
        messages_ref = db.collection('users').document(user_id).collection('chats').document(chat_id).collection('messages')
        messages_query = messages_ref.order_by('created_at', direction=firestore.Query.DESCENDING) # ASCENDING
        messages = messages_query.stream()

        messages_list = [msg.to_dict() for msg in messages]

        if messages_list:
            return jsonify(messages_list), 200
        else:
            return jsonify({'message': 'No messages found'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500



@cms.route('/get_messages_for_chat_v2', methods=['GET'])
def get_messages_for_chat_v2():
    chat_id = request.args.get('chat_id')
    user_id = request.args.get('user_id')

    # Query Firestore for all messages in a chat
    messages_ref = db.collection('users').document(user_id).collection('chats').document(chat_id).collection('messages')
    messages = messages_ref.stream()

    messages_list = []
    for message in messages:
        messages_list.append(message.to_dict())

    if messages_list:
        return jsonify(messages_list), 200
    else:
        return jsonify({'message': 'No messages found'}), 404
