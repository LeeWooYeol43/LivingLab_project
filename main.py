# main.py
import time
import subprocess
import atexit
from google.cloud import texttospeech
from google.cloud import speech_v1p1beta1 as speech
import google.api_core.exceptions
import config
import tts_module
import stt_module
import llm_module
# bis_module은 llm_module을 통해 간접적으로 혹은 available_functions 호출을 위해 필요 시 사용

class Pipeline():
    def __init__(self):
        print("🚀 시스템 초기화 중...")
        
        # TTS 클라이언트 생성
        self.TTS_client = texttospeech.TextToSpeechClient()
        
        # 볼륨 설정 (한 번만)
        subprocess.run(["amixer", "set", "PCM", "85%"], check=False)
        
        # STT 클라이언트 생성
        self.STT_client = speech.SpeechClient()
        
        # STT 설정
        self.stt_config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=config.RATE,
            language_code="ko-KR",
            enable_automatic_punctuation=True,
            model="latest_short",
            use_enhanced=True
        )
        
        self.streaming_config = speech.StreamingRecognitionConfig(
            config=self.stt_config,
            interim_results=False,
            single_utterance=True
        )

        # LLM 설정
        self.chat, self.available_functions = llm_module.initialize_chat()

    def speak(self, text):
        """TTS 음성 출력"""
        tts_module.synthesize_and_play(text, self.TTS_client)
    
    def listen(self):
        """STT 음성 입력"""
        # 프롬프트 재생 콜백
        prompt_callback = lambda: self.speak("질문을 말씀해 주세요.")
        return stt_module.start_stt_recognition(
            self.STT_client,
            self.streaming_config,
            prompt_callback
        )

    def handle_function_call(self, function_call):
        """
        LLM의 함수 호출 처리 (일반화)
        
        Args:
            function_call: Gemini의 function_call 객체
            
        Returns:
            dict: 함수 실행 결과
        """
        function_name = function_call.name
        
        if function_name not in self.available_functions:
            return {"error": f"알 수 없는 함수: {function_name}"}
        
        print(f"🤖 Gemini (판단): '{function_name}' 함수를 호출합니다.")
        print(f"   인자: {dict(function_call.args)}")
        
        ###오류잃수도
        try:
            # 함수 동적 호출
            func = self.available_functions[function_name]

            result = func(**dict(function_call.args))
            # if function_name == "get_bus_arrival_info":
            #     result = func(station_name=function_call.args['station_name'])
            # elif function_name == "find_direct_bus_from_city_hall":
            #     result = func(destination_name=function_call.args['destination_name'])
            
            return result
        except Exception as e:
            print(f"❌ 함수 실행 오류: {e}")
            return {"error": str(e)}
    
    def process_llm_response(self, user_prompt):
        """
        LLM 응답 처리 (함수 호출 포함)
        
        Args:
            user_prompt: 사용자 입력
            
        Returns:
            str: 최종 답변
        """
        try:
            # 첫 번째 LLM 호출
            response = self.chat.send_message(user_prompt)
            message = response.candidates[0].content
            
            # 함수 호출이 필요한 경우
            if message.parts and message.parts[0].function_call:
                function_call = message.parts[0].function_call
                
                # 함수 실행
                api_result = self.handle_function_call(function_call)
                
                # 함수 결과를 LLM에 전달
                function_response_part = {
                    "function_response": {
                        "name": function_call.name,
                        "response": api_result 
                    }
                }
                
                # 두 번째 LLM 호출 (최종 답변 생성)
                response = self.chat.send_message(function_response_part)
                message = response.candidates[0].content
            
            # 텍스트 답변 추출
            if message.parts and message.parts[0].text:
                return message.parts[0].text
            else:
                return "응답을 생성하지 못했습니다."
                
        except google.api_core.exceptions.ResourceExhausted:
            return "API 사용량 한도를 초과했습니다. 잠시 후 다시 시도해주세요."
        except Exception as e:
            print(f"❌ LLM 처리 오류: {e}")
            return "응답 처리 중 문제가 발생했습니다."

    def run(self):
        """메인 루프"""
        greeting_message = "안녕하세요! 대전 버스 안내 시스템 대화로입니다."
        print(f"🚌 {greeting_message}")
        self.speak(greeting_message)
        
        while True:
            print("\n" + "="*50)
            
            stt_start = time.time()
            user_prompt = self.listen()
            stt_elapsed = time.time() - stt_start
            
            print(f'⏱️ STT 소요시간: {stt_elapsed:.2f}초')
            
            if user_prompt in ["STT 통신 오류", "인식 실패 (침묵 또는 시간 초과)", "마이크 오류"]:
                print(f"🚫 STT 오류 감지: {user_prompt}")
                self.speak(f"죄송합니다. {user_prompt}. 다시 시도해주세요.")
                time.sleep(1)
                continue
            
            print(f"👤 사용자 음성 입력: {user_prompt}")
            
            if "종료" in user_prompt:
                self.speak("이용해주셔서 감사합니다.")
                break

            llm_start = time.time()
            final_answer = self.process_llm_response(user_prompt)
            llm_time = time.time() - llm_start
            print(f'⏱️ LLM: {llm_time:.2f}초')
            
            print(f"🤖 챗봇:\n{final_answer}")

            tts_start = time.time()
            self.speak(final_answer)
            tts_time = time.time() - tts_start
            print(f'⏱️ TTS: {tts_time:.2f}초')
            
            print(f'📊 전체 처리시간: {stt_time + llm_time + tts_time:.2f}초')
            time.sleep(0.5)

    def cleanup(self):
        """리소스 정리"""
        print("🧹 리소스 정리 중...")
        stt_module.cleanup()
        print("✅ 정리 완료!")


def main():
    pipeline = Pipeline()
    
    # 종료 시 자동 정리
    atexit.register(pipeline.cleanup)
    
    try:
        pipeline.run()
    except KeyboardInterrupt:
        print("\n\n⚠️ 사용자에 의해 중단됨")
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류: {e}")
    finally:
        pipeline.cleanup()

if __name__ == "__main__":
    main()