from django.test import Client, TestCase

from http import HTTPStatus


class ViewTestClass(TestCase):

    def setUp(self):
        self.client = Client()

    def test_error_page(self):
        """Страницы ошибок"""
        response = self.client.get('/nonexist-page/')
        self.assertEqual(
            response.status_code,
            HTTPStatus.NOT_FOUND,
            'Некорректная обработка запроса несуществующей страницы'
        )
        self.assertTemplateUsed(
            response,
            'core/404.html',
            msg_prefix='Запрошенный адрес не '
                       'соответствует ожидаемому шаблону'
        )
