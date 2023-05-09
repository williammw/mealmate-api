import requests

def test_signup():
    url = 'http://127.0.0.1:5000/signup'  # Replace with your Flask app's address and port
    data = {
        'email': 'iamx@ddd.com',
        'password': '1234567z',
        'full_name': 'Peter Doe',
        'username': 'Peterdoe',
        'display_name': 'Slut FUck 1999',
        'date_of_birth': '1986-01-01',
        'people_dining': 4,
        'bio': 'lun dui HK ',
    }

    response = requests.post(url, data=data)
    print(response.status_code)
    print(response.text)

if __name__ == '__main__':
    test_signup()
