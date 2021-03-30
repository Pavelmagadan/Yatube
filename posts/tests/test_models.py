from django.test import TestCase

from posts.models import Group, Post, User


class ModelPostTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        test_user = User.objects.create(
            username='Mr_Test',
            email='test@mail.com',
            password='test_password',
        )
        cls.post = Post.objects.create(
            text='Какой-то текст для проверки длинной больше 15 символов',
            author=test_user,
        )

    def test_verbose_name(self):
        """verbose_name полей "text" и "group" совпадает с ожидаемым."""
        post = ModelPostTests.post
        field_verboses = {
            'text': 'Текст',
            'group': 'Группа',
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).verbose_name, expected)

    def test_help_text(self):
        """help_text полей "text" и "group" совпадает с ожидаемым."""
        post = ModelPostTests.post
        field_help_texts = {
            'text': 'Здесь напечатайте текст вашей публикации',
            'group': 'Выберете группу в которой хотите сделать публикацию',
        }
        for value, expected in field_help_texts.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).help_text, expected)

    def test_object_name_is_text_field(self):
        """__str__ модели 'Post' возвращает 15 символов поля 'text'"""
        post = ModelPostTests.post
        expected_object_name = post.text[:15]
        self.assertEquals(expected_object_name, str(post))


class ModelGroupTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-group',
            description='Описание',
        )

    def test_object_name_is_text_field(self):
        """__str__ модели 'Group' название группы (поле "title")"""
        group = ModelGroupTests.group
        expected_object_name = group.title
        self.assertEquals(expected_object_name, str(group))
