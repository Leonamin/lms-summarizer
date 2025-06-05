# LMS 요약

## 환경설정

### 파이썬 버전 설정

whisper를 사용하기 때문에 적정 버전인 3.9.9 사용(3.13은 openai-whisper 다운로드가 안될거임)

직접 설치 또는 pyenv 사용하여 파이썬 버전 관리

### Mac OS pyenv 설정

pyenv 설치

```
brew install pyenv
```

.zshrc에 아래 내용 작성

```
# [pyenv]
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init --path)"
```

```
source ~/.zshrc
```

3.9.9 버전 설치 및 사용

```
pyenv install 3.9.9

pyenv local 3.9.9
```

현재 폴더에 .python-version 생기면 성공!

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

### ffmpeg 설치

동영상 파일을 wav로 바꾸어야하기 때문에 ffmpeg을 설치한다

```
brew install ffmpeg
```

### .env 설정

```
USERID=(아이디)학번
PASSWORD=비밀번호
```

### 리턴제로 API 키 설정

그냥 whisper 사용할거면 안해도 됨
여기에서 API 키 발급 한달 600분 무료 https://developers.rtzr.ai/

.env에 다음 항목을 추가

```
RETURNZERO_CLIENT_ID=~~~~~~~~
RETURNZERO_CLIENT_SECRET=~~~~~~~~~
```

### openai API 키 설정

```
OPENAI_API_KEY=~~~~~~~~
```

### 최종 .env 모습

```
USERID=(아이디)학번
PASSWORD=비밀번호
RETURNZERO_CLIENT_ID=~~~~~~~~
RETURNZERO_CLIENT_SECRET=~~~~~~~~
OPENAI_API_KEY=~~~~~~~~
```

### user_settings.json 설정

없어도 동작은 함

```
{
  "video": [
    "https://canvas.ssu.ac.kr/courses/35082/modules/items/3160477?return_url=/courses/35082/external_tools/71",
    "https://canvas.ssu.ac.kr/courses/35082/modules/items/3160478?return_url=/courses/35082/external_tools/71",
    "https://canvas.ssu.ac.kr/courses/35082/modules/items/3160479?return_url=/courses/35082/external_tools/71"
  ]
}
```

## 예시

```
https://canvas.ssu.ac.kr/courses/35082/modules/items/3149344?return_url=/courses/35082/external_tools/71
```

## 에러 발생의 경우

### 단위 테스트 파일 실행 실패 시 PYTHONPATH 설정

예 ModuleNotFoundError: No module named 'audio_pipeline' 같은 에러 발생 시 파이썬 상대경로 문제(파이썬은 엄밀히 따지면 루트가 되는 프로젝트 시작점이 따로 없음 그래서 PYTHONPATH로 설정해야함)

```
export PYTHONPATH="${PYTHONPATH}:/Users/lsm/dev/project/lms-summarizer/src"
```
