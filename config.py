# config.py
import os
from dotenv import load_dotenv

# .env 로드 및 환경 변수 설정
load_dotenv(dotenv_path="")
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = ""

# 오디오 설정 상수
MIC_DEVICE_INDEX = 1
RATE = 44100
CHUNK = int(RATE / 10)

# BIS(버스) API 설정
DAEJEON_API_KEY = os.environ.get('DAEJEON_API_KEY')
URL_SEARCH_STATION = os.environ.get('URL_SEARCH_STATION')
URL_GET_ARRIVAL = os.environ.get('URL_GET_ARRIVAL')
CITY_HALL_STATION_ID = '8001378' 
CITY_HALL_STATION_NAME = "대전광역시청" 

# Gemini API 키
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")