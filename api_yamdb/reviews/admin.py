from django.contrib import admin

from .models import Category, Comment, Genre, Review, Title


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'slug',
    )
    list_filter = (
        'name',
        'slug',
    )


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'review',
        'text',
        'author',
        'pub_date',
    )
    list_filter = (
        'review',
        'author',
        'pub_date',
    )


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'slug',
    )
    list_filter = (
        'name',
        'slug',
    )


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'title',
        'text',
        'author',
        'score',
        'pub_date',
    )
    list_filter = (
        'title',
        'author',
        'score',
        'pub_date',
    )


@admin.register(Title)
class TitleAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'year',
        'description',
        'display_genre',
        'category',
    )
    list_filter = (
        'name',
        'year',
        'genre',
        'category',
    )
