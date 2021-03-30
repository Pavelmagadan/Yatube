import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post, User


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        cls.guest_client = Client()
        cls.test_user = User.objects.create_user(username='AndreyG')
        cls.authorized_client = Client()
        PostPagesTests.authorized_client.force_login(PostPagesTests.test_user)
        cls.group_with_post = Group.objects.create(
            title='Группа с постом',
            description='В этой группе должен быть пост',
            slug='group-post'
        )
        cls.group_without_post = Group.objects.create(
            title='Группа без поста',
            description='В этой группе не должно быть постов',
            slug='group-no-post'
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.test_post = Post.objects.create(
            text='Текст поста № 1',
            author=PostPagesTests.test_user,
            group=PostPagesTests.group_with_post,
            image=uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_posts_pages_uses_correct_template(self):
        """URL-адрес app posts использует соответствующий шаблон."""
        templates_pages_names = {
            'index.html': reverse('index'),
            'new.html': reverse('new_post'),
            'group.html': (
                reverse('group', kwargs={'slug': 'group-post'})
            ),
        }

        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = PostPagesTests.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон страницы index сформирован с правильным контекстом.
        При создании поста с указанием группы запись появилась на
        странице index."""
        expected_post = PostPagesTests.test_post
        response = PostPagesTests.authorized_client.get(
            reverse('index')
        )
        self.assertEqual(response.context['page'][0], expected_post)

    def test_group_post_page_show_correct_context(self):
        """Шаблон страницы group/group-post/ сформирован с правильным
         контекстом. При создании поста с указанием группы запись
          появилась на странице group/group-post/."""
        response = PostPagesTests.authorized_client.get(
            reverse(
                'group',
                kwargs={'slug': PostPagesTests.group_with_post.slug}
            )
        )
        expected_post = PostPagesTests.test_post
        expected_group = PostPagesTests.group_with_post
        context_correspond_to_expection = {
            response.context['page'][0]: expected_post,
            response.context['group']: expected_group,
        }
        for (
            contects_object,
            expected_object
        ) in context_correspond_to_expection.items():
            with self.subTest(contects_object=contects_object):
                self.assertEqual(contects_object, expected_object)

    def test_group_no_post_page_show_correct_context(self):
        """В шаблон страницы group/group-no-post/ не передан лишний пост."""
        response = PostPagesTests.authorized_client.get(
            reverse(
                'group',
                kwargs={'slug': PostPagesTests.group_without_post.slug}
            )
        )
        self.assertFalse(response.context['page'].object_list.exists())

    def test_profile_page_show_correct_context(self):
        """Шаблон страницы /<userneme>/ сформирован с правильным
         контекстом."""
        response = PostPagesTests.authorized_client.get(
            reverse(
                'profile',
                kwargs={'username': PostPagesTests.test_user.username}
            )
        )
        context_correspond_to_expection = {
            response.context['page'][0]: PostPagesTests.test_post,
            response.context['author']: PostPagesTests.test_user,
            response.context['posts_count']: 1,
        }
        for (
            contects_object,
            expected_object
        ) in context_correspond_to_expection.items():
            with self.subTest(contects_object=contects_object):
                self.assertEqual(contects_object, expected_object)

    def test_authors_post_page_show_correct_context(self):
        """Шаблон страницы /<userneme>/<post_id> сформирован с правильным
         контекстом."""
        response = PostPagesTests.authorized_client.get(
            reverse(
                'post',
                kwargs={
                    'username': PostPagesTests.test_user.username,
                    'post_id': PostPagesTests.test_post.id,
                }
            )
        )
        context_correspond_to_expection = {
            response.context['post']: PostPagesTests.test_post,
            response.context['author']: PostPagesTests.test_user,
            response.context['posts_count']: 1,
        }
        for (
            contects_object,
            expected_object
        ) in context_correspond_to_expection.items():
            with self.subTest(contects_object=contects_object):
                self.assertEqual(contects_object, expected_object)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон страницы /<userneme>/<post_id>/edit/ сформирован с правильным
         контекстом."""
        response = PostPagesTests.authorized_client.get(
            reverse(
                'post_edit',
                kwargs={
                    'username': PostPagesTests.test_user.username,
                    'post_id': PostPagesTests.test_post.id,
                }
            )
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        field_values = {
            'text': self.test_post.text,
            'group': self.test_post.group.id,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

        for value, expected in field_values.items():
            with self.subTest(value=value):
                fields_value = response.context['form'][value].value()
                self.assertEqual(fields_value, expected)

    def test_new_post_page_show_correct_context(self):
        """В шаблон страницы new/ передан правильный контекст."""
        response = PostPagesTests.authorized_client.get(reverse('new_post'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_user = User.objects.create_user(username='Mr. Test')
        cls.authorized_client = Client()
        PaginatorViewsTest.authorized_client.force_login(
            PaginatorViewsTest.test_user
        )
        cls.test_group = Group.objects.create(
            title='Группа с постами',
            description='В этой группе будет 13 постов',
            slug='test-group'
        )
        number_of_posts = 13
        for num in range(1, number_of_posts + 1):
            Post.objects.create(
                text=f'Текст поста № {num}',
                author=PaginatorViewsTest.test_user,
                group=PaginatorViewsTest.test_group
            )

    def test_first_page_containse_ten_records(self):
        """Количество постов на первой странице index и group/test-group
         равно 10"""
        reverse_names = [
            reverse('index'),
            reverse('group', kwargs={'slug': 'test-group'})
        ]

        for reverse_name in reverse_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(
                    len(response.context.get('page').object_list),
                    10
                )

    def test_second_page_containse_three_records(self):
        """Количество постов на второй странице index и group/test-group
         равно 3"""
        reverse_names = [
            reverse('index'),
            reverse('group', kwargs={'slug': 'test-group'})
        ]
        for reverse_name in reverse_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name + '?page=2')
                self.assertEqual(
                    len(response.context.get('page').object_list),
                    3
                )

    def test_first_page_sorted_by_date(self):
        """Посты отсортированны на странице index и group/test-group
         по времени публикации"""
        reverse_names = [
            reverse('index'),
            reverse('group', kwargs={'slug': 'test-group'})
        ]
        for reverse_name in reverse_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                pages_posts_list = response.context.get('page').object_list
                pub_date_later_post = pages_posts_list[0].pub_date

                for posts_number in range(1, len(pages_posts_list)):
                    pub_date_early_post = pages_posts_list[
                        posts_number
                    ].pub_date
                    self.assertTrue(
                        pub_date_later_post >= pub_date_early_post
                    )
                    pub_date_later_post = pub_date_early_post


class CashTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_user = User.objects.create_user(username='Mr. Test')
        cls.guest_client = Client()
        number_of_posts = 13
        for num in range(1, number_of_posts + 1):
            Post.objects.create(
                text=f'Текст поста № {num}',
                author=CashTest.test_user
            )

    def test_index_page_cash(self):
        """Посты страницы Index хранятся в cash и обновляются
        каждые 20 сек"""
        response_start = CashTest.guest_client.get(
            reverse('index') + '?page=2'
        )
        Post.objects.create(
            text='Новый пост',
            author=CashTest.test_user
        )
#        start = len(response_start.context['page'])
        response_cashe = CashTest.guest_client.get(
            reverse('index') + '?page=2'
        )
        # cash = len(response_cashe.context['page'])
        cache.clear()
        response_timeout = CashTest.guest_client.get(
            reverse('index') + '?page=2'
        )
        self.assertEqual(
            response_start.content,
            response_cashe.content,
            'Контент не был закеширован!')
        self.assertNotEqual(
            response_start.content,
            response_timeout.content,
            'При отчистке кеша контент не изменился!')
        # self.assertEqual(
        #     start,
        #     cash)
