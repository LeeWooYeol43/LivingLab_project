# llm_module.py
import google.generativeai as genai
import config
from bis_module import available_functions

SYSTEM_INSTRUCTION = """
당신은 대전시의 버스 도착 정보 및 최적 경로를 안내하는 전문 챗봇입니다.
사용자의 질문에 대해 친절하고 간결한 한국어 텍스트로만 응답해야 하며 질문의 대한 대답은 존댓말을 사용해야 합니다.
출발지는 대전광역시청입니다.

1. 정보 제공 원칙:
    - 외부 함수 호출을 통해 받은 실시간 데이터(Python 딕셔너리)를 최우선으로 하여 답변을 생성해야 합니다.
    - 가장 빠르거나 합리적인 경로 1가지를 즉시 제안하며, 필요한 핵심 정보만 포함하여 2문장을 넘기지 않게 간결하고 정확하게 답변합니다.
    - "몇 번 버스를 타야하며, 이 버스는 몇 분후에 도착한다, 몇 정거장 전에 있다." 와 같은 문장으로 정보를 알려주세요.
2. 서식 및 출력 제한:
    - 절대로 이모티콘, 마크다운 표, 굵은 글씨, 목록(예: *, #, - 등) 또는 기타 서식 요소를 사용하지 마세요.
    - 오직 TTS로 읽힐 수 있는 순수한 텍스트 문자열만 반환해야 합니다.

3. 데이터 부재 시 처리:
    - API로 정보를 찾을 수 없는 경우 (예: matching_buses: [] 또는 error가 반환된 경우), 너(Gemini)의 최신 지식을 기반으로 가장 합리적인 환승 경로 1가지를 (마치 조회된 것처럼) 자신 있게 제안합니다.
"""

def initialize_chat():
    try:
        genai.configure(api_key=config.GEMINI_API_KEY)
    except KeyError:
        print("오류: GEMINI_API_KEY 환경 변수를 찾을 수 없습니다.")
        exit()

    tools = [
        {
            "function_declarations": [
                {"name": "get_bus_arrival_info", "description": "사용자가 '특정 버스 정류장'의 실시간 도착 정보를 물어볼 때 사용합니다.", "parameters": {"type": "OBJECT", "properties": {"station_name": {"type": "STRING", "description": "정보를 조회할 버스 정류장의 이름"}}, "required": ["station_name"]}},
                {"name": "find_direct_bus_from_city_hall", "description": "사용자가 [대전광역시청]에서 출발하여 [다른 목적지]로 가는 버스를 찾을 때 사용합니다.", "parameters": {"type": "OBJECT", "properties": {"destination_name": {"type": "STRING", "description": "사용자가 가고 싶어하는 최종 목적지 이름"}}, "required": ["destination_name"]}}
            ]
        }
    ]

    model = genai.GenerativeModel(model_name="gemini-2.5-flash", tools=tools, system_instruction=SYSTEM_INSTRUCTION)
    chat = model.start_chat(enable_automatic_function_calling=False)
    
    return chat, available_functions