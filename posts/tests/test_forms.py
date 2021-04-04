import shutil
import tempfile

from datetime import datetime

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Group, Post, User


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(dir=settings.BASE_DIR))
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.uploaded2 = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.form = PostForm()
        self.test_group = Group.objects.create(
            title='Тестовая группа',
            description='В этой группе должен быть пост',
            slug='test-group'
        )
        self.test_user = User.objects.create_user(username='Mr. Test')
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.test_user)

    def test_create_post_authorized(self):
        """Валидная форма создает запись в Post."""
        form_data = {
            'text': 'Текст тестового поста',
            'group': self.test_group.id,
            'image': PostFormTests.uploaded,
        }
        time_start_publish = str(datetime.utcnow())
        # Отправляем POST-запрос
        response = self.authorized_client.post(
            reverse('new_post'),
            data=form_data,
            follow=True
        )
        time_end_publish = str(datetime.utcnow())
        # Проверяем, добавился ли пост в БД
        self.assertEqual(Post.objects.count(), 1)
        # Проверяем, сработал ли редирект
        self.assertRedirects(response, reverse('index'))
        # Проверяем, что создалась запись с правильными значениями
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                group=form_data['group'],
                author=self.test_user.id,
                pub_date__range=[time_start_publish, time_end_publish],
                image=f'posts/{form_data["image"]}'
            ).exists()
        )

    def test_create_post_guest(self):
        """Неавторизованный пользователь не может создать запись в Post."""
        form_data = {
            'text': 'Текст тестового поста',
            'group': self.test_group.id,
            'image': PostFormTests.uploaded2,
        }
        self.guest_client.post(
            reverse('new_post'),
            data=form_data,
            follow=True
        )
        # Проверяем, что запись не добавилась в БД
        self.assertFalse(
            Post.objects.exists(),
            'Неавторизованный пользователь не должен '
            'иметь возможность создать запись в Post'
        )

    def test_edit_post(self):
        """Форма редактирует запись в Post."""
        old_post = Post.objects.create(
            text='Текст тестового поста',
            author=self.test_user,
            image=PostFormTests.uploaded,
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        new_image = SimpleUploadedFile(
            name='new.gif',
            content=small_gif,
            content_type='image/gif'
        )
        old_post_id = old_post.id
        forms_new_data = {
            'text': 'Отредактированный тестовый пост',
            'group': self.test_group.id,
            'image': new_image,
        }
        # Отправляем POST-запрос
        response = self.authorized_client.post(
            reverse(
                'post_edit',
                kwargs={
                    'username': self.test_user.username,
                    'post_id': old_post_id,
                }
            ),
            data=forms_new_data,
            follow=True
        )
        # Проверяем, сработал ли редирект
        self.assertRedirects(
            response,
            reverse(
                'post',
                kwargs={
                    'username': self.test_user.username,
                    'post_id': old_post_id
                }
            )
        )
        # Проверяем, что старая запись изменилась
        # и имеет правильный контекст
        self.assertTrue(
            Post.objects.filter(
                id=old_post_id,
                text=forms_new_data['text'],
                group=forms_new_data['group'],
                author=self.test_user.id,
                image=f'posts/{forms_new_data["image"]}'
            ).exists()
        )
        # Проверяем, что в БД не появилось лишних записей
        self.assertEqual(Post.objects.count(), 1)
