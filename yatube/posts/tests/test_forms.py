import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse


from ..models import Comment, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.no_authorized_client = Client()
        cls.user = User.objects.create_user(username='TestUser')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост достаточной длины',
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
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.form_data_create = {
            'text': 'Тестовый текст',
            'group': cls.group.pk,
            'image': cls.uploaded,
        }
        cls.form_data_edit = {
            'text': 'Новый тестовый текст',
            'group': cls.group.pk,
        }
        cls.form_data_comment = {
            'text': 'Тестовый текст комментария'
        }
        cls.form_data_anon_comm = {
            'text': 'Новый комментарий к посту',
        }

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post(self):
        """Тест на создание поста"""
        post_count = Post.objects.count()
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=self.form_data_create,
            follow=True
        )
        self.assertRedirects(response, reverse('posts:profile',
                             kwargs={'username': self.user}))
        self.assertEqual(Post.objects.count(), post_count + 1)

    def test_edit_post(self):
        """Тест на редактирование поста"""
        count = Post.objects.count()
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}),
            data=self.form_data_edit,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk})
        )
        self.assertEqual(Post.objects.count(), count)
        self.assertTrue(
            Post.objects.filter(
                text=self.form_data_edit['text'],
                group=self.form_data_edit['group'],
                author=self.user,
            ).exists()
        )

    def test_create_comment(self):
        """Тестовое запись комментария"""
        count = Comment.objects.count() + 1
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.pk}),
            data=self.form_data_comment,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk})
        )
        self.assertEqual(Comment.objects.count(), count)
        self.assertTrue(
            Comment.objects.filter(
                text=self.form_data_comment['text'],
                author=self.user,
                post=self.post
            ).exists()
        )

    def test_add_comment_anonymous(self):
        """Проверяем, что неавторизованный пользователь не
        может оставлять комментарии.
        """
        count = Comment.objects.count()
        self.no_authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=self.form_data_anon_comm,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), count)
