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

load_dotenv()  # This line loads the environment variables from the .env file

app = Flask(__name__)

app.register_blueprint(api, url_prefix='/api')
app.register_blueprint(cms, url_prefix='/cms')
app.register_blueprint(auth, url_prefix='/auth')

openai.api_key = os.environ["OPENAI_API_KEY"]
app.secret_key = os.environ["FLASK_SECRET_KEY"]

@app.route("/")
def home():
    return "<h1>Umami(temp) 0.1.1</h1>"

if __name__ == '__main__':
    app.run(debug=True)
