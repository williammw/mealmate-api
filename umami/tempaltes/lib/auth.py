from flask import Flask, Blueprint, jsonify, request
from twilio.rest import Client as TwilioClient
import requests
from dotenv import load_dotenv
from umami.lib.cms import initialize_firebase
import os

auth = Blueprint('auth', __name__)


load_dotenv()  
# db = initialize_firebase()

@auth.route('/signup', methods=['POST'])
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
        # security_code = generate_security_code()
        security_code = "999999"
        # Add the user data to Firestore
        user_ref = db.collection('users').document(user.uid)
        user_ref.set({
            'email_or_phone': email_or_phone,
            'full_name': full_name,
            'username': username,
            'date_of_birth': date_of_birth,
            'people_dining': people_dining,
            'bio': '',
            'avatar_url':'',
            'current_chat_id' : '',
            'userId': '',
            'preferred_language' : 'zh-hk',
        })

        # Send a security code to the user (via email or SMS)
        
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
            twilio_client = TwilioClient(os.environ["TWILIO_ACCOUNT_SID"], os.environ["TWILIO_AUTH_TOKEN"])
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



@auth.route('/verify_security_code', methods=['POST'])
def verify_security_code():
    email = request.form.get('email')
    user_input_security_code = request.form.get('security_code')
    uid = request.form.get('auth_token')  # Assuming you're getting uid from the form.

    # Get the user data from Firestore
    user_doc_ref = db.collection('users').document(uid)
    user_doc = user_doc_ref.get()

    print(f"Email: {email}")
    print(f"User Input Security Code: {user_input_security_code}")

    if user_doc.exists:
        user_data = user_doc.to_dict()
        print(f"User Data: {user_data}")
        stored_security_code = user_data.get('security_code')
        print(f"Stored security code: {stored_security_code}")

        if user_input_security_code == stored_security_code:
            # Verification successful
            return jsonify({"message": "Security code verified successfully"}), 200
        else:
            # Verification failed
            return jsonify({"error": "Invalid security code"}), 400
    else:
        print("User not found in database.")
        return jsonify({"error": "User data not found"}), 404
    




@auth.route('/login', methods=['POST'])
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

@auth.route('/logout', methods=['POST'])
def logout():
    if 'user_id' in session:
        session.pop('user_id', None)
        return jsonify({"status": "success", "message": "User logged out"}), 200
    else:
        return jsonify({"status": "failure", "message": "No user logged in"}), 400

@auth.route('/is_logged_in', methods=['POST'])
def is_logged_in():
    id_token = request.json.get("idToken")

    if not id_token:
        return jsonify({"status": "failure", "message": "Missing idToken"}), 400

    decoded_token = verify_id_token(id_token)

    if decoded_token:
        return jsonify({"status": "success", "message": "User is logged in", "user": decoded_token["uid"]}), 200
    else:
        return jsonify({"status": "failure", "message": "User is not logged in"}), 401

