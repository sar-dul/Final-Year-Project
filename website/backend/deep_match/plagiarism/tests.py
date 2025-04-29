from django.test import TestCase
from plagiarism.helper import get_sentences, get_embeddings, detect_plagiarism
import numpy as np
from django.urls import reverse
from plagiarism.models import PlagiarismReport
from django.contrib.auth import get_user_model
from users.models import User
from plagiarism.models import PlagiarismSession

class HelperFunctionTests(TestCase):
    def test_get_sentences(self):
        text = "This is a test sentence. This is another one. And yet another."
        expected = [
            "This is a test sentence.",
            "This is another one.",
            "And yet another."
        ]
        result = get_sentences(text)
        self.assertEqual(result, expected)

    def test_get_embeddings(self):
        sentences = ["Hello world", "This is a test"]
        result = get_embeddings(sentences)
        
        # Check it's a dict
        self.assertIsInstance(result, dict)
        
        # Check keys match sentences
        self.assertEqual(set(result.keys()), set(sentences))
        
        # Check each value is a NumPy array of expected length
        for embedding in result.values():
            self.assertIsInstance(embedding, np.ndarray)
            self.assertEqual(len(embedding.shape), 1)  # should be 1D


    def test_detect_plagiarism(self):
        # Dummy embeddings: 2 identical sentences, 1 different
        embeddings_self = {
            "Sentence A": np.array([1.0, 0.0]),
            "Sentence B": np.array([0.0, 1.0]),
            "Sentence C": np.array([0.5, 0.5])
        }

        # First other document with similar embeddings to Sentence A and B
        other_embeddings_1 = {
            "Copy of Sentence A": np.array([1.0, 0.0]),
            "Copy of Sentence B": np.array([0.0, 1.0])
        }

        # Second other document (not similar)
        other_embeddings_2 = {
            "Different sentence": np.array([-1.0, -1.0])
        }

        plagiarized_sentences, plagiarism_percentage = detect_plagiarism(
            embeddings_self,
            [other_embeddings_1, other_embeddings_2],
            similarity_threshold=0.9
        )

        # Expected: Sentence A and B are plagiarized, C is not
        self.assertIn("Sentence A", plagiarized_sentences)
        self.assertIn("Sentence B", plagiarized_sentences)
        self.assertNotIn("Sentence C", plagiarized_sentences)

        self.assertEqual(plagiarism_percentage, round((2/3) * 100, 2))


class ResultViewTestCase(TestCase):
    def setUp(self):
        # Use get_user_model() to get the correct User model
        User = get_user_model()
        
        # Create a test user with name and email
        self.user = User.objects.create_user(
            username='testuser',
            name='Test User',
            email='testuser@example.com',
            password='password123'
        )

        # Create a test PlagiarismReport and associate it with the test user
        self.report = PlagiarismReport.objects.create(
            file_name='test_report.pdf',
            uploaded_at='2025-01-01 10:00:00',
            plagiarism_percent=25.5,
            base64_pdf='somebase64data',
            user=self.user  # Assign the user to the plagiarism report
        )

    def test_result_view(self):
        # Get the URL for the result view
        url = reverse('view_report', kwargs={'report_id': self.report.id})
        
        # Send a GET request to the view
        response = self.client.get(url)
        
        # Check if the response status code is 200 (OK)
        self.assertEqual(response.status_code, 200)
        
        # Check if the context contains the expected data
        self.assertContains(response, 'Checked Date')
        self.assertContains(response, 'Plagiarism Detected:')
        self.assertContains(response, f"highlighted_{self.report.file_name}")
        
        # Check if the content matches the test data (the date should be in the expected range)
        checked_date_str = self.report.uploaded_at.strftime('%B %d, %Y')  # Format as April 29, 2025
        self.assertIn(checked_date_str, response.content.decode())
        self.assertIn(str(self.report.plagiarism_percent), response.content.decode())


class PlagiarismSessionModelTest(TestCase):
    def test_create_session(self):
        user = User.objects.create_user(
            username='testuser',
            name='Test User',
            email='test@example.com',
            password='testpass123'
        )
        session = PlagiarismSession.objects.create(user=user)
        
        self.assertEqual(session.user, user)
        self.assertIsNotNone(session.submitted_at)
        self.assertIn("Session by", str(session))

class PlagiarismReportModelTest(TestCase):
    def test_create_report_with_session(self):
        user = User.objects.create_user(
            username='reportuser',
            name='Report User',
            email='report@example.com',
            password='pass1234'
        )
        session = PlagiarismSession.objects.create(user=user)

        report = PlagiarismReport.objects.create(
            session=session,
            user=user,
            file_name='report123.pdf',
            original_file_name='original_report.pdf',
            plagiarism_percent=42.7,
            highlighted_file_path='media/highlighted/report123.pdf',
            base64_pdf='dGVzdA=='  # base64 for "test"
        )

        self.assertEqual(report.session, session)
        self.assertEqual(report.user.username, 'reportuser')
        self.assertEqual(report.plagiarism_percent, 42.7)
        self.assertIn('report123.pdf', str(report))