from django.test import TestCase
from rest_framework.test import APIClient

class BookTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_book_list(self):
        response = self.client.get('/books/')
        self.assertEqual(response.status_code, 200)
