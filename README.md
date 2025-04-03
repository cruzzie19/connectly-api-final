# Connectly API

Welcome to the Connectly API repository. This project is implemented in Python and provides various functionalities for managing connections and related operations.

## Table of Contents

- [Introduction](#introduction)
- [Technologies Used](#technologies-used)
- [Installation](#installation)
- [Usage](#usage)
- [Implementations](#implementations)
  - [Likes & Comments System](#likes-comments-system)
  - [Google OAuth Integration](#google-oauth-integration)
  - [News Feed with Pagination](#news-feed-with-pagination)
  - [RBAC (Role-Based Access Control)](#rbac-role-based-access-control)
  - [Privacy Settings](#privacy-settings)
- [Contributing](#contributing)
- [License](#license)

## Introduction

Connectly API is designed to manage connections and related operations efficiently. This project is built with Python and follows best practices for API development.

## Technologies Used

- Python
- Django
- Django Rest Framework
- Django Allauth
- Google OAuth2

## Installation

To get started with the Connectly API, follow these steps:

1. Clone the repository:
   ```bash
   git clone https://github.com/cruzzie19/connectly-api-final.git
   ```
2. Navigate to the project directory:
   ```bash
   cd connectly-api-final
   ```
3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

To run the API, use the following command:
```bash
python app.py
```

## Implementations

### Likes & Comments System

- **File:** [posts/views.py](https://github.com/cruzzie19/connectly-api-final/blob/main/posts/views.py)
- **Description:** Implements the API for liking/unliking posts and managing comments.
  ```python
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
  ```

### Google OAuth Integration

- **File:** [connectly_project/settings.py](https://github.com/cruzzie19/connectly-api-final/blob/main/connectly_project/settings.py)
- **File:** [.env](https://github.com/cruzzie19/connectly-api-final/blob/main/.env)
- **File:** [posts/views.py](https://github.com/cruzzie19/connectly-api-final/blob/main/posts/views.py)
- **Description:** Configures Google OAuth settings and implements the API for Google login.
  ```python
  # settings.py
  SOCIALACCOUNT_PROVIDERS = {
      'google': {
          'SCOPE': ['profile', 'email'],
          'AUTH_PARAMS': {'access_type': 'offline'},
          'OAUTH_PKCE_ENABLED': True,
      }
  }
  
  # .env
  GOOGLE_OAUTH2_CLIENT_ID=your_client_id
  GOOGLE_OAUTH2_CLIENT_SECRET=your_client_secret
  GOOGLE_OAUTH2_REDIRECT_URI=http://127.0.0.1:8000/posts/auth/google/callback/
  
  # views.py
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
  ```

### News Feed with Pagination

- **File:** [posts/views.py](https://github.com/cruzzie19/connectly-api-final/blob/main/posts/views.py)
- **Description:** Implements the personalized news feed with pagination.
  ```python
  # Personalized News Feed
  class NewsFeedAPIView(generics.ListAPIView):
      serializer_class = PostSerializer
      permission_classes = [IsAuthenticated]
      pagination_class = PostPagination
  
      def get_queryset(self):
          return Post.objects.filter(privacy='public').order_by('-created_at')
  ```

### RBAC (Role-Based Access Control)

#### User Model

- **File:** [posts/models.py](https://github.com/cruzzie19/connectly-api-final/blob/main/posts/models.py)
- **Description:** The `User` model includes a `role` field with choices for 'admin', 'user', and 'guest'.
  ```python
  from django.contrib.auth.models import AbstractUser 
  from django.db import models
  
  class User(AbstractUser):
      email = models.EmailField(unique=True)
      created_at = models.DateTimeField(auto_now_add=True)
      role = models.CharField(max_length=10, choices=[('admin', 'Admin'), ('user', 'User'), ('guest', 'Guest')], default='user')
  
      REQUIRED_FIELDS = ['email']
  
      def __str__(self):
          return self.username
  ```

#### Role-Based Access Control in Views

- **File:** [posts/views.py](https://github.com/cruzzie19/connectly-api-final/blob/main/posts/views.py)
- **Description:** The `PostDetail` view includes logic to check if the user is the author of the post or an admin before allowing deletion.
  ```python
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
  ```

### Privacy Settings

- **File:** [posts/views.py](https://github.com/cruzzie19/connectly-api-final/blob/main/posts/views.py)
- **Description:** Implements privacy settings for posts.
  ```python
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
  ```

## Contributing

We welcome contributions from the community. Please read our [Contributing Guidelines](CONTRIBUTING.md) for more information.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.