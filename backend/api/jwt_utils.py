from datetime import datetime, timedelta, timezone as dt_timezone

import jwt
from django.conf import settings


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

