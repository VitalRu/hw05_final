from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост, тестовый текст',
        )

    def test_models_have_correct_object_names(self):
        """Объекты моделей имеют корректные имена"""
        group = self.group
        post = self.post
        expected_group_name = group.title
        expected_post_name = post.text[:15]
        self.assertEqual(
            expected_group_name,
            str(group),
            'Некорректная работа метода __str__',
        )
        self.assertEqual(
            expected_post_name,
            str(post),
            'Некорректная работа метода __str__',
        )
