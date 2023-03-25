from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post

User = get_user_model()


class PostTestUrls(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='test_author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )

        cls.post = Post.objects.create(
            text='Тестовый пост, тестовый текст',
            author=cls.author,
            group=cls.group,
        )
        cls.create_url = '/create/'
        cls.edit_url = f'/posts/{cls.post.pk}/edit/'
        cls.comment_url = f'/posts/{cls.post.pk}/comment/'
        cls.urls_for_all = {
            '/': 'posts/index.html',
            f'/group/{cls.group.slug}/': 'posts/group_list.html',
            f'/profile/{cls.author.username}/': 'posts/profile.html',
            f'/posts/{cls.post.pk}/': 'posts/post_detail.html',
        }
        cls.urls_for_authorized = {
            cls.create_url: 'posts/create_post.html',
            cls.edit_url: 'posts/create_post.html',
        }

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='UserNotAuthor')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_urls_for_all(self):
        """
        Доступность URL, не требующих авторизации, для всех посетителей
        """
        for url in self.urls_for_all.keys():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.OK,
                    f'Страница {url} недоступна '
                    'для неавторизованного пользователя'
                )

                response = self.authorized_client.get(url)
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.OK,
                    f'Страница {url} недоступна '
                    'для авторизованного пользователя'
                )

    def test_post_create_url(self):
        """
        URL - создание поста для авторизованного пользователя
        и редирект для неавторизованного на страницу авторизации
        """
        response = self.authorized_client.get(self.create_url)
        self.assertEqual(
            response.status_code,
            HTTPStatus.OK,
            'Страница создания поста недоступна'
        )
        response = self.guest_client.get(self.create_url, follow=True)
        self.assertRedirects(
            response,
            f'/auth/login/?next={self.create_url}',
            msg_prefix='Неавторизованный пользователь '
            'не был перенаправлен по ожидаемому адресу'
        )

    def test_add_comment_url(self):
        """
        Только авторизованный пользователь может добавлять комментарии
        """
        response = self.authorized_client.get(self.comment_url)
        self.assertEqual(
            response.status_code,
            HTTPStatus.FOUND,
            'Возможность комментировать недоступна'
        )
        response = self.authorized_client.get(self.comment_url, follow=True)
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail',
                kwargs={
                    'post_id': self.post.pk,
                }
            ),
            msg_prefix='Не произошел редирект на страницу post_detail'
                       'после отправки комментария'
        )

    def test_post_edit_url(self):
        """URL - редактирование поста для автора"""
        author = PostTestUrls.author
        post_author = Client()
        post_author.force_login(author)
        response = post_author.get(self.edit_url)
        self.assertEqual(
            response.status_code,
            HTTPStatus.OK,
            'Страница редактирования поста недоступна'
        )

        response = self.authorized_client.get(self.edit_url, follow=True)
        self.assertRedirects(
            response,
            f'/posts/{self.post.pk}/',
            msg_prefix='Авторизованный пользователь не был '
            'перенаправлен на страницу поста'
        )
        response = self.guest_client.get(self.edit_url)
        self.assertRedirects(
            response,
            f'/auth/login/?next={self.edit_url}',
            msg_prefix='Неавторизованный пользователь не был '
            'перенаправлен на страницу авторизации'
        )

    def test_unexisting_page(self):
        """Вызов несуществующей страницы"""
        url = '/page_does_not_exists/'
        clients = [
            self.guest_client,
            self.authorized_client,
        ]
        for client in clients:
            with self.subTest(client=client):
                response = client.get(url)
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.NOT_FOUND,
                    'Некорректная обработка запроса несуществующей страницы'
                )

    def test_correct_htmls_(self):
        """Запрошенный URL соответствует своему шаблону"""
        author = PostTestUrls.author
        post_author = Client()
        post_author.force_login(author)
        all_posts_urls = self.urls_for_all | self.urls_for_authorized
        for address, template in all_posts_urls.items():
            with self.subTest(address=address):
                response = post_author.get(address)
                self.assertTemplateUsed(
                    response,
                    template,
                    msg_prefix='Запрошенный адрес не '
                               'соответствует ожидаемому шаблону'
                )
