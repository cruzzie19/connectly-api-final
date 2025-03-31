from django.urls import path, include
from rest_framework.authtoken.views import obtain_auth_token
from .views import (
    UserListCreate, UserDetail, 
    PostListCreate, PostDetail, PostLikeToggle, 
    CommentListCreate, CommentDetail, GoogleLoginCallbackApi, GoogleLoginRedirectApi,
    NewsFeedAPIView
)
from . import views
urlpatterns = [
    # User Endpoints
    path('users/', UserListCreate.as_view(), name='user-list-create'),
    path('users/<int:pk>/', UserDetail.as_view(), name='user-detail'), 

    # Post Endpoints
    path('posts/', PostListCreate.as_view(), name='post-list-create'),
    path('posts/<int:pk>/', PostDetail.as_view(), name='post-detail'),  
    path('posts/<int:pk>/like/', PostLikeToggle.as_view(), name='post-like-toggle'), 

    # Comment Endpoints
    path('comments/', CommentListCreate.as_view(), name='comment-list-create'),
    path('comments/<int:pk>/', CommentDetail.as_view(), name='comment-detail'), 

    # Google Authentication
    path('auth/google/login/', GoogleLoginRedirectApi.as_view(), name='google-login-redirect'),
    path('auth/google/callback/', GoogleLoginCallbackApi.as_view(), name='google-login-callback'),
    path('auth/google/redirect/', GoogleLoginRedirectApi.as_view(), name='google-auth-redirect'),


    path('auth/', include('dj_rest_auth.urls')),  
    path('auth/registration/', include('dj_rest_auth.registration.urls')),  
    path('auth/google/', include('allauth.socialaccount.urls')),  

    
    # News Feed
    path('newsfeed/', NewsFeedAPIView.as_view(), name='news-feed'),

    # Token Authentication
    path('api/token/', obtain_auth_token, name='api_token_auth'),
    
    path("logout", views.logout_view)
]
