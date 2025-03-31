from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics, permissions
from rest_framework.generics import get_object_or_404
from .models import User, Post, Comment
from .serializers import UserSerializer, PostSerializer, CommentSerializer
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from django.contrib.auth import get_user_model
from django.conf import settings
from django.shortcuts import redirect
from urllib.parse import urlencode
import requests
from django.core.cache import cache
from rest_framework.pagination import PageNumberPagination

User  = get_user_model()

# Pagination class
class PostPagination(PageNumberPagination):
    page_size = 10

def home(request):
    return render(request, "home.html")

def logout_view(request):
    logout(request)
    return redirect("posts/")

# User List & Create API
class UserListCreate(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        users = User.objects.all()
        serialized_users = []

        for user in users:
            user_data = UserSerializer(user).data
            try:
                token = Token.objects.get(user=user)
                user_data["token"] = token.key
            except Token.DoesNotExist:
                user_data["token"] = None

            serialized_users.append(user_data)

        return Response(serialized_users)

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, _ = Token.objects.get_or_create(user=user)

            return Response({
                "user": UserSerializer(user).data,
                "token": token.key
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# User Detail API
class UserDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'pk'

# Post List & Create API
class PostListCreate(generics.ListCreateAPIView):
    queryset = Post.objects.all().order_by('-created_at')
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = PostPagination

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

class PostDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        post = self.get_object()
        if post.privacy == 'private' and post.author != request.user:
            return Response({"error": "You do not have permission to view this post."}, status=status.HTTP_403_FORBIDDEN)
        return super().get(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        post = self.get_object()
        # Check if the user is the author of the post or an admin
        if post.author != request.user and request.user.role != 'admin':
            return Response({"error": "You do not have permission to delete this post."}, status=status.HTTP_403_FORBIDDEN)
        
        # Proceed with deletion
        self.perform_destroy(post)
        return Response(status=status.HTTP_204_NO_CONTENT)

        
# Like & Unlike Post API
class PostLikeToggle(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        post = get_object_or_404(Post, id=pk)
        user = request.user

        if user in post.likes.all():
            post.likes.remove(user)
            return Response({"message": "Like removed."}, status=status.HTTP_200_OK)
        else:
            post.likes.add(user)
            return Response({"message": "Post liked."}, status=status.HTTP_201_CREATED)

# Comment List & Create API
class CommentListCreate(generics.ListCreateAPIView):
    queryset = Comment.objects.all().order_by('-created_at')
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

# Comment Detail, Update, Delete API
class CommentDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

# Personalized News Feed
class NewsFeedAPIView(generics.ListAPIView):
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = PostPagination

    def get_queryset(self):
        return Post.objects.filter(privacy='public').order_by('-created_at')

# Google Login Redirect API
class GoogleLoginRedirectApi(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        google_url = "https://accounts.google.com/o/oauth2/v2/auth"
        params = {
            "client_id": settings.GOOGLE_OAUTH2_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_OAUTH2_REDIRECT_URI,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
        }
        redirect_url = f"{google_url}?{urlencode(params)}"
        return Response({"auth_url": redirect_url}, status=status.HTTP_200_OK)

# Google Login Callback API
class GoogleLoginCallbackApi(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        code = request.GET.get("code")
        if not code:
            return Response({"error": "Missing authorization code"}, status=400)

        return Response({"message": "Send this code via POST to authenticate", "code": code}, status=200)

    def post(self, request):
        code = request.data.get("code")
        if not code:
            return Response({"error": "Missing authorization code"}, status=400)

        token_url = "https://oauth2.googleapis.com/token"
        data = {
            "client_id": settings.GOOGLE_OAUTH2_CLIENT_ID,
            "client_secret": settings.GOOGLE_OAUTH2_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": settings.GOOGLE_OAUTH2_REDIRECT_URI,
        }

        token_response = requests.post(token_url, data=data)
        token_data = token_response.json()

        if "error" in token_data:
            return Response({"error": token_data["error"]}, status=400)

        access_token = token_data.get("access_token")

        # Get user info from Google
        user_info_url = "https://www.googleapis.com/oauth2/v1/userinfo"
        headers = {"Authorization": f"Bearer {access_token}"}
        user_info_response = requests.get(user_info_url, headers=headers)
        user_info = user_info_response.json()

        if "email" not in user_info:
            return Response({"error": "Failed to get email from Google"}, status=400)

        email = user_info["email"]
        name = user_info.get("name", email.split("@")[0])

        # Check if user exists
        user, created = User.objects.get_or_create(email=email, defaults={"username": name})

        # Create a token for the user
        token, _ = Token.objects.get_or_create(user=user)

        return Response({
            "token": token.key,
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.username,
            }
        })