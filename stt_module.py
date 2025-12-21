# stt_module.py
import queue
import pyaudio
from google.cloud import speech_v1p1beta1 as speech
import google.api_core.exceptions
import config

# PyAudio 인스턴스 전역 관리
_audio_interface = None

def _get_audio_interface():
    """PyAudio 인스턴스 재사용"""
    global _audio_interface
    if _audio_interface is None:
        _audio_interface = pyaudio.PyAudio()
    return _audio_interface

class MicrophoneStream:
    """마이크 오디오 스트림 클래스"""
    def __init__(self, rate, chunk): 
        self._rate = rate
        self._chunk = chunk
        self._buff = queue.Queue(maxsize=100)
        self.closed = True
        self._audio_stream = None
    
    def _fill_buffer(self, in_data, frame_count, time_info, status_flags):
        """오디오 콜백"""
        try:
            self._buff.put_nowait(in_data)
        except queue.Full:
            pass
        return None, pyaudio.paContinue
    
    def generator(self):
        """오디오 데이터 생성기"""
        while not self.closed:
            try:
                chunk = self._buff.get(timeout=0.1)
            except queue.Empty:
                if self.closed:
                    return
                continue
                
            if chunk is None:
                return
            
            data = [chunk]
            while True:
                try:
                    chunk = self._buff.get_nowait()
                    if chunk is None:
                        return
                    data.append(chunk)
                except queue.Empty:
                    break
            
            yield b"".join(data)
    
    def __enter__(self):
        audio_interface = _get_audio_interface()
        self._audio_stream = audio_interface.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self._rate,
            input=True,
            frames_per_buffer=self._chunk,
            input_device_index=config.MIC_DEVICE_INDEX,
            stream_callback=self._fill_buffer
        )
        self.closed = False
        return self
    
    def __exit__(self, type, value, traceback):
        self.closed = True
        if self._audio_stream:
            self._audio_stream.stop_stream()
            self._audio_stream.close()
        # 버퍼 비우기
        while not self._buff.empty():
            try:
                self._buff.get_nowait()
            except queue.Empty:
                break

def start_stt_recognition(client, streaming_config, prompt_callback):
    """
    STT 음성 인식 수행
    
    Args:
        client: STT 클라이언트
        streaming_config: 스트리밍 설정 (재사용)
        prompt_callback: 프롬프트 재생 콜백 함수
    
    Returns:
        str: 인식된 텍스트
    """
    final_transcript = ""
    
    try:
        with MicrophoneStream(config.RATE, config.CHUNK) as stream:
            # 프롬프트 재생
            if prompt_callback:
                prompt_callback()
            
            print(f"🎙️ 음성 입력 대기 중...")
            
            audio_generator = stream.generator()
            requests_gen = (
                speech.StreamingRecognizeRequest(audio_content=content)
                for content in audio_generator
            )
            
            try:
                responses = client.streaming_recognize(
                    streaming_config,
                    requests_gen,
                    timeout=10.0
                )
                
                for response in responses:
                    if not response.results:
                        continue
                    
                    result = response.results[0]
                    if result.is_final:
                        final_transcript = result.alternatives[0].transcript
                        print(f"✅ STT 최종 결과: {final_transcript}")
                        break
                        
            except google.api_core.exceptions.DeadlineExceeded:
                print("🚫 STT 시간 초과 (10초간 입력 없음)")
                return "인식 실패 (침묵 또는 시간 초과)"
            
            except google.api_core.exceptions.OutOfRange:
                print("🚫 STT 세션 종료 (자동 감지)")
                
            except Exception as e:
                print(f"STT API 통신 오류: {e}")
                return "STT 통신 오류"
    
    except Exception as e:
        print(f"마이크 스트림 오류: {e}")
        return "마이크 오류"
    
    return final_transcript if final_transcript else "인식 실패 (침묵 또는 시간 초과)"

def cleanup():
    """프로그램 종료 시 리소스 정리"""
    global _audio_interface
    if _audio_interface:
        _audio_interface.terminate()
        _audio_interface = None