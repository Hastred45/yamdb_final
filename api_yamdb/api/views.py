import uuid

from django.conf import settings
from django.core.mail import send_mail
from django.db import IntegrityError
from django.db.models import Avg
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.pagination import (LimitOffsetPagination,
                                       PageNumberPagination)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken
from reviews.models import Category, Genre, Review, Title
from users.models import User

from .filters import TitleFilter
from .mixins import CreateListDestroyViewSet
from .permissions import (AuthorAndStaffOrReadOnly, IsAdminOrReadOnly,
                          OwnerOrAdmins)
from .serializers import (CategorySerializer, CommentSerializer,
                          GenreSerializer, MeSerializer, ReviewSerializer,
                          SignUpSerializer, TitleCreateSerializer,
                          TitleDisplaySerializer, TokenSerializer,
                          UserSerializer)


@api_view(['POST'])
def signup_post(request):
    serializer = SignUpSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    email = serializer.validated_data['email']
    username = serializer.validated_data['username']
    try:
        user, _ = User.objects.get_or_create(
            username=username,
            email=email
        )
    except IntegrityError:
        return Response(
            'Такой логин или email уже существуют',
            status=status.HTTP_400_BAD_REQUEST
        )
    confirmation_code = str(uuid.uuid4())
    user.confirmation_code = confirmation_code
    user.save()
    send_mail(
        'Код подверждения', confirmation_code,
        settings.DEFAULT_FROM_EMAIL, (email, ), fail_silently=False
    )
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
def token_post(request):
    serializer = TokenSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    username = serializer.validated_data['username']
    confirmation_code = serializer.validated_data['confirmation_code']
    user_base = get_object_or_404(User, username=username)
    if confirmation_code == user_base.confirmation_code:
        token = str(AccessToken.for_user(user_base))
        return Response({'token': token}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = PageNumberPagination
    permission_classes = (OwnerOrAdmins, )
    filter_backends = (filters.SearchFilter, )
    filterset_fields = ('username')
    search_fields = ('username', )
    lookup_field = 'username'

    @action(
        methods=['get', 'patch'],
        detail=False,
        url_path='me',
        permission_classes=(IsAuthenticated, )
    )
    def get_patch_me(self, request):
        user = request.user
        if request.method == 'GET':
            serializer = MeSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        if request.method == 'PATCH':
            serializer = MeSerializer(user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)


class CategoriesViewSet(CreateListDestroyViewSet):
    '''
    Категории.
    Вьюсет дает возможности:
    1. Получить список всех категорий. Доступно без токена.
       Поддерживается поиск по названию.
    2. Добавить категорию. Доступно только администратору.
    3. Удалить категорию. Доступно только администратору.
    '''
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = (filters.SearchFilter,)
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    pagination_class = LimitOffsetPagination
    search_fields = ('name', '=slug')
    lookup_field = 'slug'


class GenresViewSet(CreateListDestroyViewSet):
    '''
    Жанры.
    Вьюсет дает возможности:
    1. Получить список всех жанров. Доступно без токена.
       Поддерживается поиск по названию.
    2. Добавить жанр. Доступно только администратору.
    3. Удалить жанр. Доступно только администратору.
    '''
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = (filters.SearchFilter,)
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    lookup_field = 'slug'
    pagination_class = LimitOffsetPagination
    filter_backends = (filters.SearchFilter, )
    search_fields = ('=name',)


class TitleViewSet(viewsets.ModelViewSet):
    '''
    Произведения.
    Вьюсет дает возможности:
    1. Получить список всех произведений. Доступно без токена.
       Поддерживается фильтрация полученных произведений
       по обязательным полям.
    2. Добавить произведение. Доступно только администратору.
    3. Получить произведение по id. Доступно без токена.
    4. Частично обновить информацию о произведением.
       Доступно только администратору.
    5. Удалить произведение. Доступно только администратору.
    '''
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = (DjangoFilterBackend, filters.SearchFilter,)
    queryset = Title.objects.annotate(
        rating=Avg('reviews__score')).all()
    pagination_class = LimitOffsetPagination
    filter_class = TitleFilter
    search_fields = ('category', 'genre', 'name', 'year')

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return TitleDisplaySerializer
        if self.action in ['create', 'update', 'partial_update']:
            return TitleCreateSerializer


class ReviewViewSet(viewsets.ModelViewSet):
    '''
    Отзывы.
    Вьюсет дает возможности:
    1. Получить список всех отзывов. Доступно без токена.
    2. Добавить новый отзыв. Пользователь может оставить
       только один отзыв на произведение.
       Доступно только аутентифицированным пользователям.
    3. Получить отзыв по id для указанного произведения. Доступно без токена.
    4. Частично обновить отзыв по id.
       Доступно только авторам отзыва, модераторам или администраторам.
    5. Удалить отзыв по id. Доступно только авторам отзыва,
       модераторам или администраторам.
    '''
    serializer_class = ReviewSerializer
    pagination_class = LimitOffsetPagination
    permission_classes = [AuthorAndStaffOrReadOnly]

    def get_queryset(self):
        title_id = self.kwargs.get("title_id")
        title_u = get_object_or_404(Title, pk=title_id)
        n_queryset = title_u.reviews.all()

        return n_queryset

    def perform_create(self, serializer):
        title_id = self.kwargs.get("title_id")
        title_u = get_object_or_404(Title, pk=title_id)
        serializer.save(author=self.request.user, title=title_u)


class CommentViewSet(viewsets.ModelViewSet):
    '''
    Комментарии.
    Вьюсет дает возможности:
    1. Получить список всех комментариев к отзыву по id. Доступно без токена.
    2. Добавить новый комментарий для отзыва.
       Доступно только аутентифицированным пользователям.
    3. Получить комментарий для отзыва по id. Доступно без токена.
    4. Частично обновить комментарий к отзыву по id.
       Доступно только авторам комментария, модераторам или администраторам.
    5. Удалить комментарий к отзыву по id.
       Доступно только авторам комментария, модераторам или администраторам.
    '''
    serializer_class = CommentSerializer
    pagination_class = LimitOffsetPagination
    permission_classes = [AuthorAndStaffOrReadOnly]

    def get_queryset(self):
        title_id = self.kwargs.get('title_id')
        title = get_object_or_404(Title, pk=title_id)
        review_id = self.kwargs.get("review_id")
        review_u = get_object_or_404(Review, pk=review_id, title=title)
        n_queryset = review_u.comments.all()
        return n_queryset

    def perform_create(self, serializer):
        title_id = self.kwargs.get('title_id')
        title = get_object_or_404(Title, pk=title_id)
        review_id = self.kwargs.get("review_id")
        review_u = get_object_or_404(Review, pk=review_id, title=title)
        serializer.save(author=self.request.user, review=review_u)
