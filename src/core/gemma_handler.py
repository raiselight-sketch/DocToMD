from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

class GemmaAIHandler:
    """Gemma 모델을 사용하여 텍스트를 처리하는 핸들러."""

    def __init__(self, model_name="google/gemma-2-2b"):
        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        self.load_model()

    def load_model(self):
        """모델과 토크나이저를 로드합니다."""
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto"
            )
            print(f"Gemma 모델 {self.model_name} 로드 완료")
        except Exception as e:
            print(f"모델 로드 실패: {e}")
            self.model = None

    def process_text(self, text: str, prompt: str = "다음 텍스트를 Markdown 형식으로 변환해 주세요:\n\n") -> str:
        """텍스트를 Gemma 모델로 처리합니다."""
        if not self.model or not self.tokenizer:
            return text  # 모델이 없으면 원본 반환

        try:
            input_text = prompt + text
            inputs = self.tokenizer(input_text, return_tensors="pt").to(self.model.device)
            
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=512,
                    temperature=0.7,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            # 프롬프트 제거
            result = generated_text[len(input_text):].strip()
            return result if result else text
        except Exception as e:
            print(f"텍스트 처리 실패: {e}")
            return text

class GemmaChatHandler:
    """Gemma 모델을 사용하여 대화하는 핸들러."""

    def __init__(self, model_name="google/gemma-2-7b"):
        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        self.conversation_history = []
        self.load_model()

    def load_model(self):
        """모델과 토크나이저를 로드합니다."""
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto"
            )
            print(f"Gemma 채팅 모델 {self.model_name} 로드 완료")
        except Exception as e:
            print(f"모델 로드 실패: {e}")
            self.model = None

    def chat(self, user_message: str) -> str:
        """사용자 메시지에 응답합니다."""
        if not self.model or not self.tokenizer:
            return "모델이 로드되지 않았습니다."

        try:
            # 대화 히스토리에 추가
            self.conversation_history.append(f"User: {user_message}")
            
            # 히스토리를 하나의 텍스트로 결합
            conversation_text = "\n".join(self.conversation_history) + "\nAssistant:"
            
            inputs = self.tokenizer(conversation_text, return_tensors="pt").to(self.model.device)
            
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=256,
                    temperature=0.8,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id,
                    eos_token_id=self.tokenizer.eos_token_id
                )
            
            full_response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # 응답 추출 (Assistant: 이후)
            if "Assistant:" in full_response:
                response = full_response.split("Assistant:")[-1].strip()
            else:
                response = full_response[len(conversation_text):].strip()
            
            # 히스토리에 응답 추가
            self.conversation_history.append(f"Assistant: {response}")
            
            return response
        except Exception as e:
            print(f"채팅 실패: {e}")
            return "응답 생성에 실패했습니다."

    def clear_history(self):
        """대화 히스토리를 초기화합니다."""
        self.conversation_history = []

# 인스턴스 생성
gemma_2b = GemmaAIHandler("google/gemma-2-2b")
gemma_4b = GemmaAIHandler("google/gemma-2-7b")  # 7B 모델 사용
gemma_chat = GemmaChatHandler("google/gemma-2-7b")