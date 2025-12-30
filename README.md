# 🚌 대전 버스 안내 AI 시스템 (대화로)

이 프로젝트는 대전광역시청을 중심으로 **버스 도착 정보**와 **최적 경로**를 음성으로 안내해 주는 AI 챗봇 시스템입니다.  
사용자의 음성을 인식(STT)하여 Google Gemini LLM으로 의도를 파악하고, 대전 BIS(버스 정보 시스템) API를 통해 실시간 데이터를 조회한 뒤, 음성(TTS)으로 답변을 제공합니다.

---

## ✨ 주요 기능

- **음성 대화 인터페이스**: 마이크를 통해 질문을 듣고 스피커로 답변을 말합니다.
- **실시간 버스 정보 조회**: 대전 BIS API와 연동하여 실제 버스 도착 정보를 제공합니다.
  - 특정 정류장의 버스 도착 정보 조회
  - 대전광역시청에서 특정 목적지까지 가는 직행 버스 검색
- **AI 기반 자연어 처리**: Google Gemini API를 사용하여 사용자의 자연어 질문을 이해하고 적절한 함수를 호출하거나 답변을 생성합니다.

---

## 📂 프로젝트 구조

| 파일명 | 설명 |
| --- | --- |
| `main.py` | 프로그램의 진입점. STT, LLM, TTS 과정을 조율하고 메인 루프를 실행합니다. |
| `config.py` | API 키, 오디오 설정(샘플 레이트, 장치 인덱스), BIS API URL 등 환경 변수를 관리합니다. |
| `bis_module.py` | 대전 BIS Open API와 통신하여 정류소 ID 검색 및 도착 정보를 파싱(XML)합니다. |
| `llm_module.py` | Google Gemini API를 설정하고, 시스템 프롬프트 및 도구(Function Calling)를 정의합니다. |
| `stt_module.py` | Google Cloud Speech-to-Text를 사용하여 실시간 음성 인식을 처리합니다. (PyAudio 사용) |
| `tts_module.py` | Google Cloud Text-to-Speech를 사용하여 텍스트를 음성으로 변환하고 재생합니다. (`mpg123` 사용) |

---

## 🛠️ 설치 및 환경 설정

이 프로젝트는 **Python 3.x** 환경에서 실행되며, 오디오 입출력을 위한 시스템 패키지가 필요합니다.

### 1) 시스템 패키지 설치 (Linux/Ubuntu 기준)

오디오 재생 및 녹음을 위한 라이브러리를 설치해야 합니다.

```bash
sudo apt-get update
sudo apt-get install python3-pyaudio mpg123 libasound2-dev alsa-utils
```

### 2) Python 라이브러리 설치

필요한 Python 패키지를 설치합니다.

```bash
pip install google-cloud-speech google-cloud-texttospeech google-generativeai python-dotenv pyaudio requests
```

### 3) 환경 변수 설정 (`.env`)

프로젝트 루트 경로에 `.env` 파일을 생성하고 아래 내용을 채워주세요.

```ini
# 대전 공공데이터 포털 API 키 (BIS)
DAEJEON_API_KEY=your_daejeon_bis_api_key_here

# BIS API 엔드포인트 (기본값)
URL_SEARCH_STATION=http://openapitraffic.daejeon.go.kr/api/rest/busRouteInfo/getStaionByRouteAll
URL_GET_ARRIVAL=http://openapitraffic.daejeon.go.kr/api/rest/arrive/getArrInfoByStopID

# Google Gemini API 키
GEMINI_API_KEY=your_gemini_api_key_here

# Google Cloud 서비스 계정 키 경로 (json 파일 경로)
# STT 및 TTS 사용을 위해 필요합니다.
GOOGLE_APPLICATION_CREDENTIALS="path/to/your/service-account-file.json"
```

### 4) 오디오 장치 설정

`config.py` 파일에서 마이크 장치 인덱스를 확인하고 본인의 환경에 맞게 수정해야 할 수 있습니다.

```python
# config.py
MIC_DEVICE_INDEX = 1  # 사용 중인 마이크 장치 번호로 변경 (PyAudio 기준)
```

---

## 🚀 실행 방법

모든 설정이 완료되면 아래 명령어로 프로그램을 실행합니다.

```bash
python main.py
```

프로그램이 시작되면  
`"안녕하세요! 대전 버스 안내 시스템 대화로입니다."`  
라는 음성과 함께 대기가 시작됩니다.

---

## 📝 사용 예시

- "대전시청에서 유성온천역 가는 버스 알려줘."
- "갤러리아 타임월드 정류장에 버스 언제 와?"
- "종료해줘." (프로그램 종료)

---

## ⚠️ 주의 사항

- 이 프로젝트는 **대전광역시청**을 주요 출발지로 가정하고 로직이 구성되어 있습니다.  
  (예: `find_direct_bus_from_city_hall`)
- Google Cloud API (STT, TTS) 및 Gemini API는 사용량에 따라 과금될 수 있습니다.

---


- **설치 패키지**: 코드의 `import` 구문을 통해 필요한 라이브러리(`google-cloud-*`, `pyaudio` 등)를 추론하여 작성했습니다.
- **환경 변수**: `config.py`에서 `os.environ`으로 불러오는 키값들을 기준으로 작성했습니다.
- **시스템 패키지**: `subprocess`로 `mpg123`과 `amixer`를 호출하는 부분이 있어 해당 패키지 설치 내용을 포함했습니다.
