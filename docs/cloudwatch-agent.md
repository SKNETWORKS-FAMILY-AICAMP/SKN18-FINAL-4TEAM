# CloudWatch Logs (EC2)

이 프로젝트는 Django 로깅을 통해 요청 단위 JSON 로그를 stdout으로 출력합니다.  
CloudWatch Agent로 `/var/lib/docker/containers/*/*.log`를 수집합니다.

## 1) 에이전트 설치
Ubuntu 예시:
```
sudo apt-get update
sudo apt-get install -y amazon-cloudwatch-agent
```

## 2) 에이전트 설정
`/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json` 생성:
```
{
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/var/lib/docker/containers/*/*.log",
            "log_group_name": "/jobtory/docker",
            "log_stream_name": "{instance_id}",
            "timezone": "UTC"
          }
        ]
      }
    }
  }
}
```

## 3) 에이전트 시작
```
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
  -a fetch-config \
  -m ec2 \
  -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json \
  -s
```

## 4) 사용자 로그 조회
CloudWatch Logs Insights에서:
```
fields @timestamp, @message
| filter @message like '"user_id"'
| sort @timestamp desc
| limit 50
```

팁: `/jobtory/docker` 로그 그룹에 보존 기간(retention)을 설정하세요.
