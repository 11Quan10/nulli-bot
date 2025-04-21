import torch
from transformers import pipeline
from transformers.utils import is_flash_attn_2_available
import glob
from kokoro import KPipeline
import soundfile as sf

class AudioSub:
    def __init__(self, audio_path: str):
        self.audio_path = audio_path
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

    def transcribe(self):
        audio_files = glob.glob(self.audio_path + "\\*.wav")
        if not audio_files:
            raise FileNotFoundError("No audio files found in the specified directory.")

        transcriptions = []
        for audio_file in audio_files:
            result = self.pipe(audio_file, chunk_length_s=30, batch_size=24, return_timestamps=True)

            text = result["text"]  # Get the transcribed text and strip any leading/trailing whitespace
            transcriptions.append(text)

        return "\n".join(transcriptions)
    
    def text_to_speech(self, text: str, output_path: str):
        generator = self.tts(text, voice="jf_alpha")
        for i, (gs, ps, audio) in enumerate(generator):
            sf.write(f"{self.audio_path}\\{output_path}.wav", audio, 24000)
