import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Follow, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(
            username='test_author',
            first_name='Тест -',
            last_name='Автор',
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='posts/'
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Тестовый пост, тестовый текст',
            author=cls.user,
            group=cls.group,
            image=cls.uploaded,
        )
        cls.index_url = reverse('posts:index')
        cls.profile_url = reverse(
            'posts:profile',
            kwargs={'username': cls.post.author}
        )
        cls.post_detail_url = reverse(
            'posts:post_detail',
            kwargs={'post_id': cls.post.pk}
        )
        cls.post_edit_url = reverse(
            'posts:post_edit',
            kwargs={'post_id': cls.post.pk}
        )
        cls.post_create_url = reverse(
            'posts:post_create'
        )
        cls.group_list_url = reverse(
            'posts:group_list',
            kwargs={'slug': cls.group.slug}
        )

    def check_post_context(self, first, latest):
        assert first.image == latest.image, (f'Неверное изображение '
                                             f'поста {latest}')
        assert first.text == latest.text, f'Неверный текст поста {latest}'
        assert first.group == latest.group, f'Неверная группа поста {latest}'
        assert first.author == latest.author, f'Неверный автор поста {latest}'
        assert first.pub_date == self.post.pub_date, ('Некорректная дата '
                                                      'публикации поста')

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostPagesTests.user)
        cache.clear()

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""

        templates_pages_names = {
            self.index_url: 'posts/index.html',
            self.profile_url: 'posts/profile.html',
            self.post_detail_url: 'posts/post_detail.html',
            self.post_edit_url: 'posts/create_post.html',
            self.post_create_url: 'posts/create_post.html',
            self.group_list_url: 'posts/group_list.html',
        }

        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(
                    response,
                    template,
                    msg_prefix=f'Шаблон не соответствует адресу {reverse_name}'
                )

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""

        response = self.authorized_client.get(reverse('posts:index'))
        self.assertIn(
            'page_obj',
            response.context,
            'Не найден "page_obj" в контексте функции'
        )
        first_object = response.context['page_obj'][0]
        latest_post = Post.objects.latest('id')
        self.check_post_context(first_object, latest_post)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""

        response = self.authorized_client.get(
            reverse(
                'posts:group_list',
                kwargs={
                    'slug': self.post.group.slug,
                }
            )
        )
        self.assertIn(
            'page_obj',
            response.context,
            'Не найден "page_obj" в контексте функции'
        )
        first_object = response.context['page_obj'][0]
        latest_post = Post.objects.filter(group=self.group).latest('id')
        self.check_post_context(first_object, latest_post)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""

        response = self.authorized_client.get(
            reverse(
                'posts:profile',
                kwargs={
                    'username': self.post.author,
                }
            )
        )
        self.assertIn(
            'page_obj',
            response.context,
            'Не найден "page_obj" в контексте функции'
        )
        first_object = response.context['page_obj'][0]
        latest_post = Post.objects.filter(author=self.user).latest('id')
        self.check_post_context(first_object, latest_post)

    def test_post_detail_pages_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(
                'posts:post_detail',
                kwargs={
                    'post_id': self.post.pk,
                }
            )
        )
        post = response.context.get('post')
        self.check_post_context(post, self.post)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""

        response = self.authorized_client.get(
            reverse(
                'posts:post_edit',
                kwargs={
                    'post_id': self.post.pk,
                }
            )
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(
                    form_field,
                    expected,
                    'У формы создания поста отсутсвуют необходимые поля'
                )

    def test_post_create_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(
                    form_field,
                    expected,
                    'У формы редактирования поста отсутсвуют необходимые поля',
                )

    def test_index_page_cache(self):
        """Проверяем работу кеша на главной странице"""
        response_before_deletion = self.authorized_client.get(
            reverse('posts:index')
        )
        Post.objects.latest('id').delete()
        response_after_deletion = self.authorized_client.get(
            reverse('posts:index')
        )
        self.assertEqual(
            response_before_deletion.content,
            response_after_deletion.content,
            'Содержимое главной страницы изменилось. Кеш работает некорректно'
        )
        cache.clear()
        response_cache_clear = self.authorized_client.get(
            reverse('posts:index')
        )
        self.assertNotEqual(
            response_after_deletion.content,
            response_cache_clear.content,
            'Кеш на главной странице работает некорректно'
        )


class PaginatorViewsTest(TestCase):
    """Тестируем паджинатор"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='test_author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        posts = []
        for i in range(13):
            posts.append(
                Post(
                    text=f'Тестовый текст {i}',
                    author=cls.author,
                    group=cls.group,
                )
            )
        Post.objects.bulk_create(posts)

    def setUp(self):
        self.user = User.objects.create_user(username='UserNotAuthor')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_pages_contains_right_amount_records(self):
        """
        Проверяем, что количество постов на первой странице адресов
        posts:index, posts:group_list, posts:profile равно 10 и на второй - 3
        """
        urls = [
            reverse('posts:index'),
            reverse(
                'posts:group_list',
                kwargs={
                    'slug': self.group.slug,
                }
            ),
            reverse(
                'posts:profile',
                kwargs={
                    'username': self.author,
                }
            ),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(
                    len(response.context['page_obj']),
                    10,
                    'Неверное количество постов на 1ой странице',
                )
                response = self.client.get(url + '?page=2')
                self.assertEqual(
                    len(response.context['page_obj']),
                    3,
                    'Неверное количество постов на 2ой странице',
                )


class FollowTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(
            username='test_author',
            first_name='Тест -',
            last_name='Автор',
        )
        cls.post = Post.objects.create(
            text='Подписывайтесь!',
            author=cls.author,
        )
        cls.follow_author = reverse(
            'posts:profile_follow', kwargs={'username': cls.author}
        )

    def setUp(self):
        self.authorized_client = Client()
        self.user = User.objects.create_user(username='UserNotAuthor')
        self.authorized_client.force_login(self.user)

    def test_follow_author(self):
        """Проверяем сервис подписки на автора"""
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertIn(
            'page_obj',
            response.context,
            'Не найден "page_obj" в контексте функции'
        )
        posts_before_follow = len(response.context['page_obj'])
        self.authorized_client.post(self.follow_author)
        follow = Follow.objects.filter(
            author=self.author, user=self.user
        ).latest('id')
        self.assertEqual(
            self.author,
            follow.author,
            'Автор поста не совпадает с автором, на которого подписаны'
        )
        follow_author_posts = Post.objects.filter(
            author=follow.author
        ).count()
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertEqual(
            len(response.context['page_obj']),
            posts_before_follow + follow_author_posts,
            'Не появились посты автора на странице подписок'
        )

    def test_unfollow_author(self):
        """Проверяем возможность отписаться от автора"""

        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.authorized_client.post(self.follow_author)
        response = self.authorized_client.get(reverse('posts:follow_index'))
        posts_before_unfollow = len(response.context['page_obj'])
        follow = Follow.objects.filter(
            author=self.author, user=self.user
        ).latest('id')
        follow_author_posts = Post.objects.filter(
            author=follow.author
        ).count()
        self.authorized_client.post(
            reverse(
                'posts:profile_unfollow', kwargs={'username': follow.author})
        )
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertEqual(
            len(response.context['page_obj']),
            posts_before_unfollow - follow_author_posts,
            'Посты автора, от которого отписались, остались на странце '
            'follow_index'
        )
