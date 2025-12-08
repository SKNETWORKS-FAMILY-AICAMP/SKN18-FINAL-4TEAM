# 오류 기록 

-> redis를 docker 로 띄움
-> 기존에 redis가 있다면, 충돌 발생으로 langgraph가 실행이 안됨!!! (알고 싶지 않았어요....)

## 충돌이 발생했다면?? 
- 관리자 console에서 langgraph를 호출 할 수 없습니다. 이러면서 FT__ ~~ , JSON ~ 문제 라면??
-> 충돌 발생!!!
-> 기존 버전 Ubuntu에서 실행되고 있을 가능성이 있음

### 확인 방법 
- 터미널에 wsl -l -v 입력
- Ubuntu 가 띄어져 있다 ? -> 삐빅 충돌 발생 지점 입니다.


# redis 기존 Ubuntu 버전 없애는 법

- wsl 에서 입력 

wsl -d Ubuntu
sudo service redis-server stop      # 서비스일 때
sudo systemctl disable redis-server # 자동 시작 해제(가능한 경우)
pkill redis-server                  # 단순 프로세스면 강제 종료
exit

--> 오류 해결 ~~~