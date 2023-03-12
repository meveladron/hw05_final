import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Comment, Follow, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class ViewTests(TestCase):
    """Создание тестового юзера и постов в группу"""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
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
            content_type='image/gif'
        )
        cls.user = User.objects.create_user(username='TestUser')
        cls.no_authorized_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.follow_author = User.objects.create_user(username='follow-author')
        cls.group = Group.objects.create(
            title='Тестовое название гурппы',
            slug='test-slug',
            description='Тестовое описание группы'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст публикации',
            group=cls.group,
            image=cls.uploaded
        )
        cls.post_follow = Post.objects.create(
            author=cls.follow_author,
            text='Тестовый пост',
        )
        cls.comment = Comment.objects.create(
            author=cls.user,
            text='Тестовый комментарий к посту',
            post=cls.post
        )
        cls.templates = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list', kwargs={'slug': cls.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile', kwargs={'username': cls.post.author}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail', kwargs={'post_id': cls.post.id}
            ): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse(
                'posts:post_edit', kwargs={'post_id': cls.post.id}
            ): 'posts/create_post.html',
        }

    @classmethod
    def tearDownClass(cls):
        """Удаляем тестовые медиа."""
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_pages_uses_correct_template(self):
        '''URL-адрес использует соответствующий шаблон.'''
        for template, reverses in self.templates.items():
            with self.subTest(reverse=reverse):
                response = self.authorized_client.get(template)
                self.assertTemplateUsed(response, reverses)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.no_authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}))
        post_response = response.context.get('post')
        self.assertEqual(post_response.text, self.post.text)
        self.assertEqual(post_response.author, self.post.author)
        self.assertEqual(post_response.group, self.post.group)
        self.assertEqual(post_response.image, self.post.image)

    def test_post_detail_show_comment(self):
        """Шаблон post_detail отображает новый комментарий."""
        response = self.authorized_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.pk}
            )
        )
        self.assertIn(self.comment, response.context['comments'])

    def test_post_create_page_show_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.ImageField
        }
        for value, context in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, context)

    def test_post_edit_page_show_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.ImageField
        }
        for value, context in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, context)

    def test_cache_context(self):
        '''Проверка кэширования страницы index'''
        before_create_post = self.authorized_client.get(
            reverse('posts:index'))
        first_item_before = before_create_post.content
        Post.objects.create(
            author=self.user,
            text='Тестовый пост',
            group=self.group)
        after_create_post = self.authorized_client.get(reverse('posts:index'))
        first_item_after = after_create_post.content
        self.assertEqual(first_item_after, first_item_before)
        cache.clear()
        after_clear = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(first_item_after, after_clear)

    def test_follow_author(self):
        """Тестирование на добавление автора в подписки"""
        self.authorized_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.follow_author.username}))
        self.assertTrue(Follow.objects.filter(
            user=self.user, author=self.follow_author
        ).exists())

    def test_unfollow_author(self):
        """Тестирование на удаление автора из подписок"""
        self.authorized_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.follow_author.username}
        )
        )
        self.authorized_client.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': self.follow_author.username}
        )
        )
        self.assertFalse(Follow.objects.filter(
            user=self.user,
            author=self.follow_author
        )
            .exists()
        )

    def test_new_post_in_correct_follow_pages(self):
        """Тестирование на отображении новой
        записи автора на странице подписок"""
        self.authorized_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.follow_author.username})
        )
        response = self.authorized_client.get(
            reverse('posts:follow_index'))
        self.assertIn(self.post_follow, response.context['page_obj'])

    def test_unfollowing_posts(self):
        """Тестирование отсутствия поста автора у нового пользователя."""
        response = self.authorized_client.get(
            reverse('posts:follow_index')
        )
        context = response.context
        self.assertEqual(len(context['page_obj']), 0)


class PostViewsPaginatorTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.group = Group.objects.create(
            title='Тестовя группа',
            slug='test-slug',
            description='Тестовое описание группы'
        )
        cls.posts_count = 10
        bulk_size = 15
        posts = [
            Post(
                text=f'Тестовый текст {number_post}',
                author=cls.user,
                group=cls.group
            )
            for number_post in range(bulk_size)
        ]
        Post.objects.bulk_create(posts, bulk_size)

    def setUp(self):
        self.paginator_length = self.posts_count
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.index = reverse('posts:index')
        self.profile = reverse('posts:profile', kwargs={
            'username': f'{self.user.username}'
        })
        self.group_list = reverse('posts:group_list', kwargs={
            'slug': f'{self.group.slug}'
        })

    def test_views_paginator(self):
        """Проверка работы пагинатора на необходимых страницах"""
        pages = [self.index, self.profile, self.group_list]
        posts_count = Post.objects.count()
        second_page_count = posts_count - self.paginator_length
        for page in pages:
            with self.subTest(page=page):
                response = self.authorized_client.get(page)
                response2 = self.authorized_client.get(page + '?page=2')
                self.assertEqual(
                    len(response.context['page_obj']),
                    self.paginator_length
                )
                self.assertEqual(
                    len(response2.context['page_obj']),
                    second_page_count
                )
