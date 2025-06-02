# SSUpernova

## 환경설정

### venv 설정
```
python3 -m venv .venv
```


1. Mac OS

```
source .venv/bin/activate
```

2. Windows

```
.venv/bin/Activate.ps1
```

### 라이브러리 설치

아래 명령어를 실행해서 라이브러리 설치

```
pip3 install -r requirements.txt
```

라이브러리를 설치하면 매번 꼭 업데이트 해주자

```
pip3 freeze >> requirements.txt
```

playwright 용 특별 설치

```
playwright install
```

### .env 설정
```
USERID=(아이디)학번
PASSWORD=비밀번호
```

## 예시
```
https://canvas.ssu.ac.kr/courses/35082/modules/items/3149344?return_url=/courses/35082/external_tools/71
```