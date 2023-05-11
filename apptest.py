import unittest
import requests
import json

class TestStoreMessage(unittest.TestCase):
    BASE_URL = 'http://localhost:5000'  # Change this to your Flask app's URL

    def test_store_message(self):
        # Define the data to send
        data = {
            'user_id': 'qJ2WatatTYdF4eByAmXGWJfLAq33',
            'message': 'test_message'
        }

        # Send a POST request to the /store_message endpoint
        response = requests.post(f'{self.BASE_URL}/store_message', json=data)

        # Check the status code
        self.assertEqual(response.status_code, 200)

        # Check the response data
        response_data = response.json()
        self.assertEqual(response_data, {"message": "Message stored successfully"})



if __name__ == '__main__':
    unittest.main()
