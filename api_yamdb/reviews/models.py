from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from users.models import User

from .validators import year_validator


class Category(models.Model):
    name = models.CharField(
        max_length=256,
        verbose_name='Имя категории',
    )
    slug = models.SlugField(
        unique=True,
        verbose_name='Уникальный человекочитаемый ключ для поиска категории'
    )

    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'


class Genre(models.Model):
    name = models.CharField(
        max_length=256,
        verbose_name='Имя жанра'
    )
    slug = models.SlugField(
        unique=True,
        verbose_name='Уникальный человекочитаемый ключ для поиска жанра'
    )

    class Meta:
        verbose_name = 'Genre'
        verbose_name_plural = 'Genres'


class Title(models.Model):
    name = models.CharField(
        max_length=256,
        db_index=True,
        verbose_name='Имя произведения'
    )
    year = models.PositiveSmallIntegerField(
        default="",
        validators=[year_validator],
        verbose_name='Год произведения'
    )
    description = models.CharField(
        max_length=256,
        blank=True,
        null=True,
        verbose_name='Описание произведения'
    )
    genre = models.ManyToManyField(
        Genre,
        related_name='titles',
        verbose_name='Жанр произведения',
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        related_name='titles',
        null=True,
        verbose_name='Категория произведения'
    )

    class Meta:
        verbose_name = 'Title'
        verbose_name_plural = 'Titles'

    def display_genre(self):
        return list(self.genre.all().values_list('name', flat=True))


class Review(models.Model):
    title = models.ForeignKey(
        Title,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Название произведения',
        null=False,
    )
    text = models.TextField(
        verbose_name='Отзыв',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Автор',
        null=False,
    )
    score = models.IntegerField(
        verbose_name='Оценка',
        validators=[
            MinValueValidator(
                1,
                message='The value must be at least 1.'
            ),
            MaxValueValidator(
                10,
                message='The value must be no more than 10.'
            ),
        ],
    )
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True
    )

    class Meta:
        constraints = (
            models.CheckConstraint(
                name="score_in_range_1_10",
                check=models.Q(score__gte=1) & models.Q(score__lt=11),
            ),
            models.UniqueConstraint(
                fields=('title', 'author'),
                name='unique_title_author',
            ),
        )
        verbose_name = 'Review'
        verbose_name_plural = 'Reviews'
        ordering = ['pub_date']

    def __str__(self):
        return self.text


class Comment(models.Model):
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Отзыв'
    )
    text = models.TextField(
        verbose_name='Комментарий'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Автор'
    )
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True,
    )

    class Meta:
        verbose_name = 'Comment'
        verbose_name_plural = 'Comments'
