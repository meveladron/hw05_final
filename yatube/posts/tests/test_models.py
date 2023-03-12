from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()

TEXT_LENGHT: int = 15


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Test group name',
            slug='test_slug',
            description='Test description',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовое описание публикации',
        )
        cls.verbose_argument = {
            'text': 'Описание',
            'pub_date': 'Дата публикации',
            'group': 'Группа публикации',
            'author': 'Автор'
        }
        cls.help_text_argument = {
            'text': 'Введите текст публикации',
            'group': 'Выберите группу, соотвестсвующую публикации'
        }

    def test_models_have_correct_object_names(self):
        '''Проверка длины метода __str__ в модели Post'''
        value_posts = self.post.text[:TEXT_LENGHT]
        error = f'Ошибка. Вывод не имеет {TEXT_LENGHT} символов'
        self.assertEqual(str(self.post), value_posts, error)

    def test_verbose_name(self):
        '''Проверка заполнения поля модели verbose_name'''
        for field, value in self.verbose_argument.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.post._meta.get_field(field).verbose_name,
                    value,
                    f'Поле {field} ожидало значение {value}'
                )

    def test_help_text(self):
        '''Проверка заполнения поля модели help_text'''
        for help_text, value in self.help_text_argument.items():
            with self.subTest(help_text=help_text):
                self.assertEqual(
                    self.post._meta.get_field(help_text).help_text,
                    value,
                    f'Поле {help_text} ожидало значение {value}'
                )
