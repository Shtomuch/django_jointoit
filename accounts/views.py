from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.models import User
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from .serializers import (
    UserSerializer,
    RegisterSerializer,
    ChangePasswordSerializer,
    UpdateUserSerializer
)


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data['user'] = UserSerializer(self.user).data
        return data


@extend_schema(
    tags=['Authentication'],
    summary='User Login',
    description='Authenticate user and receive JWT tokens',
    request={
        'application/json': {
            'example': {
                'username': 'testuser',
                'password': 'testpass123'
            }
        }
    },
    responses={
        200: {
            'description': 'Login successful',
            'content': {
                'application/json': {
                    'example': {
                        'access': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...',
                        'refresh': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...',
                        'user': {
                            'id': 1,
                            'username': 'testuser',
                            'email': 'test@example.com',
                            'first_name': 'Test',
                            'last_name': 'User'
                        }
                    }
                }
            }
        },
        401: {
            'description': 'Invalid credentials',
            'content': {
                'application/json': {
                    'example': {
                        'detail': 'No active account found with the given credentials'
                    }
                }
            }
        }
    }
)
class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


@extend_schema(
    tags=['Authentication'],
    summary='User Registration',
    description='Register a new user account',
    request={
        'application/json': {
            'example': {
                'username': 'newuser',
                'email': 'newuser@example.com',
                'password': 'SecurePass123!',
                'password2': 'SecurePass123!',
                'first_name': 'John',
                'last_name': 'Doe'
            }
        }
    },
    responses={
        201: {
            'description': 'User created successfully',
            'content': {
                'application/json': {
                    'example': {
                        'username': 'newuser',
                        'email': 'newuser@example.com',
                        'first_name': 'John',
                        'last_name': 'Doe'
                    }
                }
            }
        },
        400: {
            'description': 'Validation error',
            'content': {
                'application/json': {
                    'example': {
                        'username': ['A user with that username already exists.'],
                        'password': ['Password fields didn\'t match.']
                    }
                }
            }
        }
    }
)
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer


@extend_schema(
    tags=['User Profile'],
    summary='Get Current User Profile',
    description='Retrieve profile information of the authenticated user',
    responses={
        200: {
            'description': 'User profile retrieved successfully',
            'content': {
                'application/json': {
                    'example': {
                        'id': 1,
                        'username': 'testuser',
                        'email': 'test@example.com',
                        'first_name': 'Test',
                        'last_name': 'User'
                    }
                }
            }
        },
        401: {
            'description': 'Authentication required',
            'content': {
                'application/json': {
                    'example': {
                        'detail': 'Authentication credentials were not provided.'
                    }
                }
            }
        }
    }
)
class ProfileView(generics.RetrieveAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


@extend_schema(
    tags=['User Profile'],
    summary='Update User Profile',
    description='Update profile information of the authenticated user',
    request={
        'application/json': {
            'example': {
                'username': 'updateduser',
                'email': 'updated@example.com',
                'first_name': 'Updated',
                'last_name': 'Name'
            }
        }
    },
    responses={
        200: {
            'description': 'Profile updated successfully',
            'content': {
                'application/json': {
                    'example': {
                        'username': 'updateduser',
                        'email': 'updated@example.com',
                        'first_name': 'Updated',
                        'last_name': 'Name'
                    }
                }
            }
        },
        400: {
            'description': 'Validation error',
            'content': {
                'application/json': {
                    'example': {
                        'email': ['This email is already in use.']
                    }
                }
            }
        },
        401: {
            'description': 'Authentication required'
        }
    }
)
class UpdateProfileView(generics.UpdateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UpdateUserSerializer

    def get_object(self):
        return self.request.user


@extend_schema(
    tags=['User Profile'],
    summary='Change Password',
    description='Change password for the authenticated user',
    request={
        'application/json': {
            'example': {
                'old_password': 'currentPassword123',
                'new_password': 'newSecurePassword123!'
            }
        }
    },
    responses={
        200: {
            'description': 'Password changed successfully',
            'content': {
                'application/json': {
                    'example': {
                        'detail': 'Password updated successfully'
                    }
                }
            }
        },
        400: {
            'description': 'Validation error',
            'content': {
                'application/json': {
                    'example': {
                        'old_password': ['Old password is not correct']
                    }
                }
            }
        },
        401: {
            'description': 'Authentication required'
        }
    }
)
class ChangePasswordView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response(
                {"detail": "Password updated successfully"}, 
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
