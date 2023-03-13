from django.contrib.auth import get_user_model
from django.db import models


User = get_user_model()


class Group(models.Model):
    title = models.CharField(
        verbose_name='Название',
        help_text='Введите название публикации',
        max_length=200
    )
    slug = models.SlugField(
        verbose_name='URL',
        help_text='Введите адрес ссылки на группу',
        max_length=25,
        unique=True
    )
    description = models.TextField(
        verbose_name='Описание',
        help_text='Введите подробное описание группы'
    )

    def __str__(self) -> str:
        return self.title

    class Meta:
        verbose_name = 'группы публикаций'
        verbose_name_plural = 'Группы публикаций'


TEXT_LENGHT: int = 15


class Post(models.Model):
    text = models.TextField(
        verbose_name='Описание',
        help_text='Введите текст публикации'
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
        related_name='posts'
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='posts',
        verbose_name='Группа публикации',
        help_text='Выберите группу, соотвестсвующую публикации'
    )
    image = models.ImageField(
        'Изображение',
        upload_to='posts/',
        blank=True
    )

    class Meta:
        ordering = ['-pub_date']
        verbose_name = 'публикации'
        verbose_name_plural = 'Публикации'

    def __str__(self):
        return self.text[:TEXT_LENGHT]


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        verbose_name='Пост комментария',
        related_name='comments'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор комментария',
        related_name='comments'
    )
    text = models.TextField(
        verbose_name='Текст комментария',
        help_text='Текст комментария'
    )
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name='дата публикации',
        db_index=True
    )

    def __str__(self):
        return self.text[:TEXT_LENGHT]

    class Meta:
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'
        ordering = ('-created',)


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Пользователь')
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор')

    class Meta:
        verbose_name_plural = 'Подписки'
        verbose_name = 'Подписка'
        constraints = (models.UniqueConstraint(
            fields=['author', 'user'],
            name='unique_follow'),
        )

    def __str__(self):
        return f'{self.user} подписался на {self.author}'
