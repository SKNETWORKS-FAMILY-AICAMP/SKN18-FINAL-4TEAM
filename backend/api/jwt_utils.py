from datetime import datetime, timedelta, timezone as dt_timezone

import jwt
from django.conf import settings
from functools import wraps
from rest_framework import status
from rest_framework.response import Response


def create_access_token(user, expires_delta: timedelta | None = None) -> str:
  """
  간단한 HS256 JWT 액세스 토큰 발급.
  payload:
    - sub: user_id
    - email
    - iat: 발급 시각 (epoch)
    - exp: 만료 시각 (epoch)
  """
  now = datetime.now(dt_timezone.utc)
  if expires_delta is None:
    expires_delta = timedelta(hours=1)
  exp = now + expires_delta

  payload = {
      "sub": str(user.user_id),
      "email": user.email,
      "iat": int(now.timestamp()),
      "exp": int(exp.timestamp()),
  }

  token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
  return token



def jwt_required(func):
    """
    JWT 토큰을 검증하고 request.user에 사용자 객체를 설정하는 데코레이터
    """
    @wraps(func)
    def wrapper(view_instance, request, *args, **kwargs):
        # models import를 여기서 하여 순환 참조 방지
        from .models import User
        
        # Authorization 헤더에서 토큰 추출
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return Response(
                {"detail": "인증 토큰이 필요합니다."},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # "Bearer {token}" 형식에서 토큰 추출
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return Response(
                {"detail": "올바르지 않은 인증 헤더 형식입니다."},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        token = parts[1]
        
        try:
            # JWT 토큰 검증 및 디코딩
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=["HS256"]
            )
            
            # payload에서 user_id 추출 (create_access_token에서 "sub"로 저장)
            user_id = payload.get("sub")
            if not user_id:
                return Response(
                    {"detail": "유효하지 않은 토큰입니다."},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            # 사용자 조회
            user = User.objects.filter(user_id=user_id).first()
            if not user:
                return Response(
                    {"detail": "사용자를 찾을 수 없습니다."},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            # request 객체에 user 설정
            request.user = user
            
            # 원래 함수 실행
            return func(view_instance, request, *args, **kwargs)
            
        except jwt.ExpiredSignatureError:
            return Response(
                {"detail": "토큰이 만료되었습니다. 다시 로그인해주세요."},
                status=status.HTTP_401_UNAUTHORIZED
            )
        except jwt.InvalidTokenError:
            return Response(
                {"detail": "유효하지 않은 토큰입니다."},
                status=status.HTTP_401_UNAUTHORIZED
            )
        except Exception as e:
            return Response(
                {"detail": "인증 처리 중 오류가 발생했습니다."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    return wrapper