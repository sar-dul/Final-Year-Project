from django.test import TestCase
from django.urls import reverse
from django.contrib.messages import get_messages
from django.contrib.auth import get_user_model
from users.models import User

class UserRegistrationTestCase(TestCase):
    def setUp(self):
        self.url = reverse('register')  # URL for your registration view

    def test_register_user_success(self):
        # Data for a new user
        data = {
            'name': 'John Doe',
            'username': 'johndoe',
            'email': 'johndoe@example.com',
            'password': 'password123',
            'role': 'student'
        }

        # Send POST request to register
        response = self.client.post(self.url, data)

        # Check if user was created
        user = User.objects.get(email='johndoe@example.com')
        self.assertEqual(user.name, 'John Doe')
        self.assertEqual(user.username, 'johndoe')
        self.assertTrue(user.check_password('password123'))

        # Check if redirect is correct
        self.assertRedirects(response, reverse('login'))

        # Check for success message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "Registration successful! Please log in.")

    def test_register_user_email_exists(self):
        # Create a user first
        User.objects.create_user(
            name='Jane Doe',
            username='janedoe',
            email='janedoe@example.com',
            password='password123',
            role='student'
        )

        # Data with an existing email
        data = {
            'name': 'John Doe',
            'username': 'johndoe',
            'email': 'janedoe@example.com',  # Same email as the existing user
            'password': 'password123',
            'role': 'student'
        }

        # Send POST request to register
        response = self.client.post(self.url, data)

        # Check if the user is not created
        self.assertEqual(User.objects.filter(email='janedoe@example.com').count(), 1)

        # Check for error message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "Email already registered.")

class UserLoginTestCase(TestCase):
    def setUp(self):
        self.url = reverse('login')  # URL for your login view
        # Create a user for testing
        self.user = get_user_model().objects.create_user(
            name='John Doe',
            username='johndoe',
            email='johndoe@example.com',
            password='password123',
            role='student'
        )

    def test_login_user_success(self):
        # Data with valid credentials
        data = {
            'username': 'johndoe',
            'password': 'password123'
        }

        # Send POST request to login
        response = self.client.post(self.url, data)

        # Check if login is successful (redirect to the welcome page)
        self.assertRedirects(response, reverse('welcome'))

        # Check if user is logged in
        user = response.wsgi_request.user
        self.assertTrue(user.is_authenticated)

    def test_login_user_invalid_credentials(self):
        # Data with invalid credentials (wrong password)
        data = {
            'username': 'johndoe',
            'password': 'wrongpassword'
        }

        # Send POST request to login
        response = self.client.post(self.url, data)

        # Check if the login fails (stay on the login page)
        self.assertTemplateUsed(response, 'users/login.html')

        # Check for error message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "Invalid username or password.")