from django.test import Client, TestCase


class StaticUrlTests(TestCase):

    def setUp(self):
        self.guest_client = Client()

    def test_author_page(self):
        """URL - страница об авторе"""
        response = self.guest_client.get('/about/author/')
        self.assertEqual(response.status_code, 200)

    def test_tech_page(self):
        """URL - страница об использованных технологиях"""
        response = self.guest_client.get('/about/tech/')
        self.assertEqual(response.status_code, 200)
