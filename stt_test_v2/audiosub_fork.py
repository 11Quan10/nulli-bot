import torch
from transformers import pipeline
from transformers.utils import is_flash_attn_2_available
import glob
from kokoro import KPipeline
import soundfile as sf

class AudioSub:
    def __init__(self):
        self.pipe = pipeline(
            "automatic-speech-recognition",
            model="openai/whisper-large-v3-turbo",  # select checkpoint from https://huggingface.co/openai/whisper-large-v3#model-details
            torch_dtype=torch.float16,
            device="cuda:0",  # or mps for Mac devices
            model_kwargs={"attn_implementation": "flash_attention_2"}
            if is_flash_attn_2_available()
            else {"attn_implementation": "sdpa"},
        )
        self.tts = KPipeline(lang_code="a", repo_id="hexgrad/Kokoro-82M")

    def transcribe(self, audio_file: str):
        file_check = glob.glob(audio_file)
        if not file_check:
            raise FileNotFoundError("Provided file does not exist.")

        result = self.pipe(audio_file, 
                           chunk_length_s=30, 
                           batch_size=24, 
                           return_timestamps=True,
                           generate_kwargs={"language": "en"})

        return result["text"]  # Get the transcribed text and strip any leading/trailing whitespace
    
    def text_to_speech(self, text: str, output_path: str):
        generator = self.tts(text, voice="jf_alpha")
        for i, (gs, ps, audio) in enumerate(generator):
            sf.write(f"{self.audio_path}\\{output_path}.wav", audio, 24000)
