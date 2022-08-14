from django.urls import include, path
from rest_framework import routers

from .views import (CategoriesViewSet, CommentViewSet, GenresViewSet,
                    ReviewViewSet, TitleViewSet, UserViewSet, signup_post,
                    token_post)

app_name = 'api'

router = routers.DefaultRouter()
router.register('users', UserViewSet, 'user')
router.register('categories', CategoriesViewSet, 'categories')
router.register('genres', GenresViewSet, 'genres')
router.register('titles', TitleViewSet, 'titles')
router.register(
    r'titles/(?P<title_id>[\d]+)/reviews',
    ReviewViewSet,
    basename='reviews',
)
router.register(
    r'titles/(?P<title_id>[\d]+)/reviews/(?P<review_id>[\d]+)/comments',
    CommentViewSet,
    basename='comments',
)

urlpatterns = [
    path('v1/', include(router.urls)),
    path('v1/auth/token/', token_post, name='token_post'),
    path('v1/auth/signup/', signup_post, name='signup_post'),
]
