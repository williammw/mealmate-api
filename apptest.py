import requests

def test_signup():
    url = 'http://127.0.0.1:5000/signup'  # Replace with your Flask app's address and port
    data = {
        'email': 'miji@yameida.com',
        'password': '1234567z',
        'full_name': 'Mary Doe',
        'username': 'marydoe',
        'date_of_birth': '1986-01-01',
        'people_dining': 4,
    }

    response = requests.post(url, data=data)
    print(response.status_code)
    print(response.text)

if __name__ == '__main__':
    test_signup()
