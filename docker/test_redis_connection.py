"""
Redis 연결 문제 진단

실행 방법:
python test_redis_connection.py
"""

import sys

print("=" * 80)
print("Redis 연결 진단")
print("=" * 80)

# ========== 1. Redis 패키지 확인 ==========

print("\n[STEP 1] Redis 패키지 확인")
print("-" * 80)

try:
    import redis
    print(f"✅ redis 패키지 설치됨: {redis.__version__}")
except ImportError as e:
    print(f"❌ redis 패키지 없음: {e}")
    print("   설치 명령: pip install redis")
    sys.exit(1)

# ========== 2. 직접 Redis 연결 테스트 ==========

print("\n[STEP 2] 직접 Redis 연결 테스트")
print("-" * 80)

# 2-1. localhost:6380 연결
print("\n테스트 2-1: localhost:6380 (Docker 포트 매핑)")
try:
    r = redis.Redis(host='localhost', port=6380, db=0, decode_responses=True)
    r.ping()
    print("✅ 연결 성공!")
    
    # 간단한 테스트
    r.set('test_key', 'test_value')
    value = r.get('test_key')
    print(f"✅ 데이터 저장/조회 성공: {value}")
    r.delete('test_key')
    
except redis.exceptions.ConnectionError as e:
    print(f"❌ 연결 실패: {e}")
    print("   원인: Redis 서버가 6380 포트에서 응답하지 않음")
except Exception as e:
    print(f"❌ 오류: {e}")

# 2-2. 127.0.0.1:6380 연결
print("\n테스트 2-2: 127.0.0.1:6380")
try:
    r = redis.Redis(host='127.0.0.1', port=6380, db=0, decode_responses=True)
    r.ping()
    print("✅ 연결 성공!")
except redis.exceptions.ConnectionError as e:
    print(f"❌ 연결 실패: {e}")
except Exception as e:
    print(f"❌ 오류: {e}")

# 2-3. Docker 내부 포트 (6379) 테스트
print("\n테스트 2-3: localhost:6379 (내부 포트)")
try:
    r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    r.ping()
    print("✅ 연결 성공! (내부 포트로 연결됨)")
except redis.exceptions.ConnectionError as e:
    print(f"❌ 연결 실패: {e}")
    print("   정상: Docker는 6380으로 매핑되어야 함")
except Exception as e:
    print(f"❌ 오류: {e}")

# ========== 3. Django Redis 설정 확인 ==========

print("\n" + "=" * 80)
print("[STEP 3] Django Redis 설정 확인")
print("-" * 80)

try:
    import django
    import os
    
    # Django 설정 찾기
    possible_settings = [
        'backend.settings',
        'config.settings',
        'settings',
    ]
    
    settings_found = False
    for setting in possible_settings:
        try:
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', setting)
            django.setup()
            settings_found = True
            print(f"✅ Django 설정 찾음: {setting}")
            break
        except Exception:
            continue
    
    if not settings_found:
        print("❌ Django 설정을 찾을 수 없습니다")
        print("   manage.py를 확인하여 DJANGO_SETTINGS_MODULE 값을 확인하세요")
    else:
        from django.conf import settings
        
        # CACHES 설정 출력
        print("\n현재 CACHES 설정:")
        if hasattr(settings, 'CACHES'):
            import pprint
            pprint.pprint(dict(settings.CACHES))
            
            # Redis 위치 확인
            default_cache = settings.CACHES.get('default', {})
            location = default_cache.get('LOCATION')
            
            if location:
                print(f"\n✅ Redis 위치: {location}")
                
                # URL 파싱
                if 'redis://' in location:
                    parts = location.replace('redis://', '').split(':')
                    if len(parts) >= 2:
                        host = parts[0]
                        port = parts[1].split('/')[0]
                        print(f"   호스트: {host}")
                        print(f"   포트: {port}")
                        
                        # 실제 연결 테스트
                        print(f"\n테스트: {host}:{port} 직접 연결")
                        try:
                            test_redis = redis.Redis(host=host, port=int(port), db=0)
                            test_redis.ping()
                            print("✅ 직접 연결 성공!")
                        except Exception as e:
                            print(f"❌ 직접 연결 실패: {e}")
            else:
                print("❌ LOCATION 설정이 없습니다")
        else:
            print("❌ CACHES 설정이 없습니다")
        
        # Django cache 테스트
        print("\n[Django cache 테스트]")
        try:
            from django.core.cache import cache
            cache.set('django_test', 'value', timeout=10)
            value = cache.get('django_test')
            if value == 'value':
                print("✅ Django cache 동작 성공!")
                cache.delete('django_test')
            else:
                print(f"❌ 값이 다름: {value}")
        except Exception as e:
            print(f"❌ Django cache 실패: {e}")
            import traceback
            print(traceback.format_exc())

except ImportError:
    print("❌ Django가 설치되지 않았습니다")
except Exception as e:
    print(f"❌ Django 설정 확인 중 오류: {e}")
    import traceback
    print(traceback.format_exc())

# ========== 4. Windows 방화벽 확인 ==========

print("\n" + "=" * 80)
print("[STEP 4] 네트워크 및 방화벽 확인")
print("-" * 80)

import socket

print("\n호스트명 확인:")
try:
    hostname = socket.gethostname()
    print(f"  호스트명: {hostname}")
    
    local_ip = socket.gethostbyname(hostname)
    print(f"  로컬 IP: {local_ip}")
except Exception as e:
    print(f"  오류: {e}")

print("\n포트 6380 접근 가능 여부:")
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    result = sock.connect_ex(('localhost', 6380))
    sock.close()
    
    if result == 0:
        print("  ✅ 포트 6380 열려 있음")
    else:
        print(f"  ❌ 포트 6380 접근 불가 (에러 코드: {result})")
        print("     원인 가능성:")
        print("     1. Docker 컨테이너가 실제로 6380 포트를 listen하지 않음")
        print("     2. Windows 방화벽이 차단")
        print("     3. 다른 프로그램이 6380 포트 사용 중")
except Exception as e:
    print(f"  ❌ 포트 확인 실패: {e}")

# ========== 5. Docker 컨테이너 상태 확인 ==========

print("\n" + "=" * 80)
print("[STEP 5] Docker 컨테이너 확인")
print("-" * 80)

print("\n다음 명령을 실행하여 Redis 컨테이너 상태를 확인하세요:")
print("  1. docker ps -a | findstr redis")
print("  2. docker logs redis-stack")
print("  3. docker exec -it redis-stack redis-cli ping")
print("  4. docker port redis-stack")

# ========== 6. 해결 방법 제시 ==========

print("\n" + "=" * 80)
print("[해결 방법]")
print("=" * 80)

print("""
1. Docker 컨테이너 재시작:
   docker-compose restart redis-stack
   
2. Redis URL 확인:
   settings.py에서 CACHES['default']['LOCATION'] 확인
   예: redis://localhost:6380/0
   
3. Docker 포트 매핑 확인:
   docker-compose.yml에서 ports 확인
   예: "6380:6379"
   
4. Redis 컨테이너 로그 확인:
   docker logs redis-stack
   
5. Redis CLI 직접 테스트:
   docker exec -it redis-stack redis-cli
   > ping
   PONG
   
6. Windows 방화벽 확인:
   - 제어판 > Windows Defender 방화벽
   - 고급 설정 > 인바운드 규칙
   - 6380 포트 허용 확인
""")

print("\n" + "=" * 80)
print("진단 완료")
print("=" * 80)