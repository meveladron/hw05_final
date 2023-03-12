from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class URLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.no_authorized_client = Client()
        cls.author = User.objects.create_user(username='TestUser')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.author)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
            group=cls.group,
        )
        cls.urls_client = {
            '/',
            f'/group/{cls.group.slug}/',
            f'/profile/{cls.author.username}/',
            f'/posts/{cls.post.id}/'
        }
        cls.templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{cls.post.group.slug}/': 'posts/group_list.html',
            f'/profile/{cls.post.author}/': 'posts/profile.html',
            f'/posts/{cls.post.id}/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            '/unexisting_page/': 'core/404.html',
        }
        cls.urls_all_client = {
            '/': HTTPStatus.OK,
            f'/group/{cls.group.slug}/': HTTPStatus.OK,
            f'/profile/{cls.author.username}/': HTTPStatus.OK,
            f'/posts/{cls.post.id}/': HTTPStatus.OK,
            'unexisting_page/': HTTPStatus.NOT_FOUND,
        }
        cls.nonexistent_url = (
            '/nonexistent/',
            'core/404.html',
        )

    def test_urls_all_client(self):
        """Тестирование страниц для всех пользователей"""
        urls = self.urls_all_client
        for url, status_code in urls.items():
            with self.subTest(url=url):
                self.assertEqual(
                    self.no_authorized_client.get(url).status_code,
                    status_code
                )

    def test_urls_no_authorized_client(self):
        """Тестирование доступов для неавторизованного пользователя"""
        urls = self.urls_client
        for url in urls:
            response = self.no_authorized_client.get(url)
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_authorized_client(self):
        """Тестирование доступов для авторизованного пользователя"""
        urls = self.urls_client
        for url in urls:
            response = self.authorized_client.get(url)
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template(self):
        urls = self.templates_url_names
        for adress, template in urls.items():
            with self.subTest(adress=adress):
                self.assertTemplateUsed(
                    self.authorized_client.get(adress),
                    template
                )

    def test_404_page(self):
        """Тест на возврат ошибки 404 в случае, если страница не существует"""
        response = self.no_authorized_client.get(
            '/existing_page/'
        )
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_nonexistent_url_uses_correct_template(self):
        """Несуществующий URL-адрес имеет кастомный шаблон"""
        response = self.client.get(self.nonexistent_url[0])
        self.assertTemplateUsed(response, self.nonexistent_url[1])
