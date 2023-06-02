import requests
from flask import Blueprint, request, jsonify
from dotenv import load_dotenv
from umami.lib.cms import initialize_firebase
import os


# You might use some configuration function or environment variables to get your Cloudflare API credentials
# from config import get_cloudflare_api_key, get_cloudflare_email

# Create a Flask Blueprint. This allows us to divide our routes into separate files
cdn = Blueprint('cdn', __name__)

load_dotenv()  
db = initialize_firebase()


CLOUDFLARE_API_URL = "https://api.cloudflare.com/client/v4/"


def get_headers():
    """
    This function returns the required headers to make API requests to Cloudflare.
    """
    api_key = os.environ["CLOUD_FLARE_STREAM_AND_IMAGES_API_TOKEN"]
    email = os.environ["CLOUDFLARE_EMAIL"]

    headers = {
        "X-Auth-Email": email,
        "X-Auth-Key": api_key,
        "Content-Type": "application/json"
    }

    return headers


@cdn.route('/upload', methods=['POST'])
def upload():
    """
    Upload an image to Cloudflare.
    """
    image = request.files.get('image')

    if not image:
        return jsonify({"error": "No image provided"}), 400

    # Make your API call to Cloudflare to upload the image

    # Return some response
    return jsonify({"message": "Image uploaded successfully"})


@cdn.route('/delete/<image_id>', methods=['DELETE'])
def delete(image_id):
    """
    Delete an image from Cloudflare.
    """
    # Make your API call to Cloudflare to delete the image

    # Return some response
    return jsonify({"message": "Image deleted successfully"})





# More routes and helper functions can be added as needed.
# https://developers.cloudflare.com/api/operations/cloudflare-images-list-images
@cdn.route('/list_images', methods=['GET'])
def list_images():
    url = f"https://api.cloudflare.com/client/v4/accounts/{os.environ['CLOUDFLARE_IMAGES_ACCOUNT_ID']}/images/v1"
    headers = {
        'Authorization': os.environ["CLOUD_FLARE_STREAM_AND_IMAGES_API_TOKEN"],
        'Content-Type': 'application/json'
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return jsonify(response.json())
    else:
        return jsonify({"error": "Unable to fetch images"}), response.status_code


@cdn.route('/verify', methods=['GET'])
def verify_token():
    url = "https://api.cloudflare.com/client/v4/user/tokens/verify"
    headers = {
        "Authorization": os.environ["CLOUD_FLARE_STREAM_AND_IMAGES_API_TOKEN"],
        "Content-Type": "application/json",
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        # Handle error response
        return jsonify({"error": "Failed to verify token"}), response.status_code
    
    return jsonify(response.json())


# list videos
@cdn.route('/list_videos', methods=['GET'])
def get_videos():
    url = f"https://api.cloudflare.com/client/v4/accounts/{os.environ['CLOUDFLARE_IMAGES_ACCOUNT_ID']}/stream"
    headers = {'Authorization': os.environ["CLOUD_FLARE_STREAM_AND_IMAGES_API_TOKEN"]}
    response = requests.get(url, headers=headers)
    print(response.text)  # Add this line to print the response to the console
    if response.status_code == 200:
        return jsonify(response.json()), 200
    else:
        return jsonify(response.json()), response.status_code
