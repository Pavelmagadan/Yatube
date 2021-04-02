from django.shortcuts import reverse
from django.test import Client, TestCase

from posts.models import Group, Post, User


class URLAccessTests(TestCase):
    def setUp(self):
        self.test_group = Group.objects.create(
            title='Тестовый заголовок',
            description='Тестовое описание',
            slug='test-group-slug'
        )
        self.guest_client = Client()
        self.user_petr = User.objects.create_user(username='Petr')
        self.user_mike = User.objects.create_user(username='Mike')
        self.authorized_client_petr = Client()
        self.authorized_client_mike = Client()
        self.authorized_client_petr.force_login(self.user_petr)
        self.authorized_client_mike.force_login(self.user_mike)
        self.petrs_post = Post.objects.create(
            text='Это текст поста Петра',
            author=self.user_petr,
        )
        self.mikes_post = Post.objects.create(
            text='Это текст поста Майка',
            author=self.user_mike,
        )

    def test_available_page_for_anonymous_user(self):
        """Неавторизованный пользователь имеет доступ только"""
        """к ожидаемым страницам"""
        url_list = [
            reverse('index'),
            reverse(
                'group',
                kwargs={'slug': self.test_group.slug}
            ),
            reverse(
                'profile',
                kwargs={'username': self.user_petr.username}
            ),
            reverse(
                'post',
                kwargs={
                    'username': self.user_petr.username,
                    'post_id': self.petrs_post.id
                }
            ),
        ]

        for url in url_list:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_available_page_for_authorized_user(self):
        """Авторизованный пользователь имеет доступ к ожидаемым страницам"""
        url_list = [
            reverse('new_post'),
            reverse(
                'post_edit',
                kwargs={
                    'username': self.user_petr.username,
                    'post_id': self.petrs_post.id
                }
            )
        ]

        for url in url_list:
            with self.subTest(url=url):
                response = self.authorized_client_petr.get(url)
                self.assertEqual(response.status_code, 200)

    def test_redirect_from_page_for_anonymous_user(self):
        """Ананимный пользователь отсылается на ожидаемые страницы """
        """при попытке доступа к запрещенным страницам"""
        new_post_url = reverse('new_post')
        new_post_redirect_url = '/auth/login/?next=/new/'
        post_edit_url = reverse(
            'post_edit',
            kwargs={
                'username': self.user_petr.username,
                'post_id': self.petrs_post.id
            }
        )
        post_edit_redirect_url = reverse(
            'post',
            kwargs={
                'username': self.user_petr.username,
                'post_id': self.petrs_post.id
            }
        )
        redirect_dict = {
            new_post_url: new_post_redirect_url,
            post_edit_url: post_edit_redirect_url
        }

        for url, expected_page in redirect_dict.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url, follow=True)
                self.assertRedirects(response, expected_page)

    def test_redirect_from_post_edit_page(self):
        """Авторизованный пользователь отсылается на ожидаемую страницу """
        """при попытке доступа к странице редактирования чужого поста"""
        post_edit_url = reverse(
            'post_edit',
            kwargs={
                'username': self.user_mike.username,
                'post_id': self.mikes_post.id
            }
        )
        post_edit_redirect_url = reverse(
            'post',
            kwargs={
                'username': self.user_mike.username,
                'post_id': self.mikes_post.id
            }
        )
        response = self.authorized_client_petr.get(post_edit_url, follow=True)
        self.assertRedirects(response, post_edit_redirect_url)


class PostsTemplatesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            description='Тестовое описание',
            slug='test-group'
        )
        cls.user = User.objects.create_user(username='Mr Test')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.post = Post.objects.create(
            text='Это текст тестового поста',
            author=cls.user,
        )

    def test_urls_uses_correct_template(self):
        """Страницы используют коректные шаблоны."""
        templates_url_names = {
            reverse('index'): 'index.html',
            reverse(
                'group',
                kwargs={'slug': PostsTemplatesTests.group.slug}
            ): 'group.html',
            reverse('new_post'): 'new.html',
            reverse(
                'profile',
                kwargs={'username': PostsTemplatesTests.user.username}
            ): 'profile.html',
            reverse(
                'post',
                kwargs={
                    'username': PostsTemplatesTests.user.username,
                    'post_id': PostsTemplatesTests.post.id,
                }
            ): 'post.html',
            reverse(
                'post_edit',
                kwargs={
                    'username': PostsTemplatesTests.user.username,
                    'post_id': PostsTemplatesTests.post.id,
                }
            ): 'new.html',
        }

        for reverse_name, template in templates_url_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = PostsTemplatesTests.authorized_client.get(
                    reverse_name
                )
                self.assertTemplateUsed(response, template)


class ErrorPageTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_404_page(self):
        """При обращении к несуществующей странице возвращается код 404"""
        url_dict = {
            reverse(
                'group',
                kwargs={'slug': 'non-existent-slug'}
            ): 404,
        }

        for url, status_code in url_dict.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, status_code)
