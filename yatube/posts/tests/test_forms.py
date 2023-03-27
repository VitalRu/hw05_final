import shutil
import tempfile

from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Comment, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(
            username='test_author',
            first_name='Тест -',
            last_name='Автор',
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
            name='posts/small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.small_gif_edit = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B\xFF\xFF\xFF'
        )
        cls.uploaded_edit = SimpleUploadedFile(
            name='small_edit.gif',
            content=cls.small_gif_edit,
            content_type='image/gif'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostFormTests.user)

    def test_cant_create_empty_post(self):
        """Ожидаем ошибку при попытке опубликовать пустой пост"""

        posts_count = Post.objects.count()
        form_data = {
            'text': ' ',
            'group': self.group,
        }
        response = self.authorized_client.post(
            reverse(
                'posts:post_create',
            ),
            data=form_data,
            follow=True
        )
        self.assertEqual(
            Post.objects.count(),
            posts_count,
            'Был создан пустой пост. Ожидалось сообщение об ошибке'
        )
        self.assertFormError(
            response,
            'form',
            'text',
            'Обязательное поле.',
            msg_prefix='Нет сообщения об ошибке'
        )
        self.assertEqual(
            response.status_code,
            HTTPStatus.OK,
            'Страница не вернула код 200'
        )

    def test_create_post(self):
        """Валидная форма создает запись в Post."""

        post_count = Post.objects.count()
        form_data = {
            'text': 'Новый тестовый пост',
            'group': self.group.id,
            'image': self.uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:profile',
                kwargs={
                    'username': self.user.username,
                }
            ),
            msg_prefix='Не произошел редирект на страницу '
                       'пользователя после создания поста '

        )
        self.assertEqual(
            Post.objects.count(),
            post_count + 1,
            'Количество объектов в модели Post не увеличилось'
        )
        latest_post = Post.objects.latest('id')
        self.assertEqual(
            form_data['text'],
            latest_post.text,
            'Неверный текст последнего поста'
        )
        self.assertEqual(
            form_data['group'],
            latest_post.group.id,
            'Неверное значение группы последнего поста'
        )
        image = form_data['image']
        self.assertEqual(
            f'posts/{image}',
            latest_post.image,
            f'Не найден пост с картинкой {self.uploaded.name}'
        )
        self.assertEqual(
            latest_post.author,
            self.user,
            'Неверный автор последнего поста'
        )

    def test_edit_post(self):
        """Форма вносит изменения в пост и перезаписывает его в Post"""

        post_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый пост, тестовый текст изменённый',
            'group': self.group.id,
            'image': self.uploaded_edit
        }
        response = self.authorized_client.post(
            reverse(
                'posts:post_edit',
                kwargs={
                    'post_id': self.post.pk,
                }
            ),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail',
                kwargs={
                    'post_id': self.post.pk,
                }
            ),
            msg_prefix='Не произошел редирект на страницу post_detail'
                       'после редактирования поста'
        )
        self.assertEqual(
            Post.objects.count(),
            post_count,
            'После редактирования поста количество записей в Post'
            'не должно измениться'
        )
        latest_post = Post.objects.latest('id')
        self.assertEqual(
            form_data['text'],
            latest_post.text,
            'Редактированный пост не найден'
        )
        self.assertEqual(
            form_data['group'],
            latest_post.group.id,
            'Редактированный пост не найден'
        )
        image = form_data['image']
        self.assertEqual(
            f'posts/{image}',
            latest_post.image,
            f'Не найден пост с картинкой {self.uploaded_edit.name}'
        )
        self.assertEqual(
            latest_post.author,
            self.user,
            'Редактированный пост не найден'
        )


class CommentFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(
            username='test_author',
            first_name='Тест -',
            last_name='Автор',
        )
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

    @classmethod
    def setUp(self):
        self.user = User.objects.create_user(username='UserNotAuthor')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_add_comment(self):
        """
        После отправки, комментарий должен появиться на странице поста
        """
        comment_count = Comment.objects.count()
        form_data = {'text': 'Комментарий для теста'}
        response = self.authorized_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': self.post.pk}
            ),
            data=form_data,
            follow=True
        )
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
        last_comment = Comment.objects.latest('id')
        self.assertEqual(
            form_data['text'],
            last_comment.text,
            'Неверный текст последнего поста'
        )
        self.assertEqual(
            Comment.objects.count(),
            comment_count + 1,
            'Количество объектов в модели Comment не увеличилось'
        )
        self.assertEqual(
            last_comment.author,
            self.user,
            'Не совпадают пользователь и автор комментария'
        )
        self.assertEqual(
            last_comment,
            self.post.comments.latest('id'),
            'Неверный комментарий поста'
        )
