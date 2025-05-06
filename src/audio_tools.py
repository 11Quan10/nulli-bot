import logging
import os
import torch
from transformers import pipeline
from transformers.utils import is_flash_attn_2_available
import glob
from kokoro import KPipeline
import pyrubberband as pyrb
import soundfile as sf
import discord
from discord.ext.voice_recv.sinks import AudioSink
from discord.ext.voice_recv.opus import VoiceData, Decoder as OpusDecoder
import wave
from pydub import AudioSegment
import speech_recognition as sr
from df import enhance, init_df
from df.enhance import load_audio, save_audio
from typing import Any, Callable, Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s\t%(filename)s - %(message)s")

SRProcessDataCB = Callable[[sr.Recognizer, sr.AudioData, discord.User], Optional[str]]
SRTextCB = Callable[[discord.User, str], Any]


class AudioTools:
    def __init__(self, audio_root: str = "./audio"):
        self.audio_root = audio_root
        if not os.path.exists(self.audio_root):
            os.makedirs(self.audio_root)
        self.pipe = pipeline(
            "automatic-speech-recognition",
            model="openai/whisper-large-v3-turbo",  # select checkpoint from https://huggingface.co/openai/whisper-large-v3#model-details
            torch_dtype=torch.float32,
            device="cuda:0",  # or mps for Mac devices
            model_kwargs={"attn_implementation": "flash_attention_2"}
            if is_flash_attn_2_available()
            else {"attn_implementation": "sdpa"},
        )
        self.tts = KPipeline(lang_code="a", repo_id="hexgrad/Kokoro-82M")
        model, df_state, _ = init_df()
        self.df_noise_suppression_model = model
        self.df_state = df_state

    async def transcribe(self, audio_file: str):
        file_check = glob.glob(audio_file)
        if not file_check:
            raise FileNotFoundError("Provided file does not exist.")
        # Transcribe the audio using Transformers Pipeline for ASR

        try:
            # audio, _ = load_audio(audio_file, sr=self.df_state.sr())
            # # Denoise the audio
            # enhanced = enhance(
            #     self.df_noise_suppression_model, self.df_state, audio
            # )
            # save_audio(audio_file, enhanced, self.df_state.sr())
            # avoid transcribing silent audio because whisper will hallucinate
            if AudioSegment.from_file(audio_file, format="wav").dBFS < -45.0:
                print("Audio is silent, skipping transcription.")
                return None

            result = self.pipe(
                audio_file,
                chunk_length_s=10,
                batch_size=24,
                return_timestamps=True,
                max_new_tokens=256,
                generate_kwargs={"language": "en"},
            )

            return result
        except Exception as e:
            print(f"Error transcribing audio file \'{audio_file}\'", e)

        return None

    async def text_to_speech(self, text: str):
        rate = 24000
        generator = self.tts(text, voice="af_heart")
        max_i = -1
        for i, (gs, ps, audio) in enumerate(generator):
            max_i = i
            audio = audio.numpy()
            audio = pyrb.time_stretch(audio, rate, 0.95)
            audio = pyrb.pitch_shift(audio, rate, n_steps=3)
            sf.write(f"{self.audio_root}/{i}.wav", audio, rate)
        return max_i

    async def prepend_silence(self, audio_file: str, silence_duration_ms: float, output_file: str):
        try:
            audio = AudioSegment.from_file(audio_file)
        except Exception as e:
            return audio_file
        silence = AudioSegment.silent(duration=silence_duration_ms)
        combined = silence + audio
        combined.export(output_file, format="wav")
        return output_file

    # class StreamSink(voice_recv.extras.SpeechRecognitionSink):
    #     def __init__(self, outer_instance: "AudioTools"):
    #         self._outer_instance = outer_instance
    #         super().__init__(default_recognizer="whisper", ignore_silence_packets=False)

    #     def is_silent_dbfs(self, audio_data: sr.AudioData, dbfs_threshold: float = -45.0) -> bool:
    #         # Convert audio data to WAV for pydub
    #         sound = AudioSegment(
    #             data=audio_data.get_raw_data(),
    #             sample_width=audio_data.sample_width,
    #             frame_rate=audio_data.sample_rate,
    #             channels=1,
    #         )
    #         return sound.dBFS < dbfs_threshold

    #     def get_default_process_callback(self) -> SRProcessDataCB:
    #         def cb(recognizer: sr.Recognizer, audio: sr.AudioData, user: Optional[discord.User]) -> Optional[str]:
    #             print("Process callback called: " + user.display_name if user else "Unknown User")
    #             if self.is_silent_dbfs(audio):
    #                 return None
    #             try:
    #                 # Create a temporary WAV file from the AudioData
    #                 audio.get_raw_data()
    #                 with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
    #                     temp_wav.write(audio.get_wav_data())
    #                     temp_wav_path = temp_wav.name
    #                 # apply noise suppression to audio
    #                 audio, _ = load_audio(temp_wav_path, sr=self._outer_instance.df_state.sr())
    #                 # Denoise the audio
    #                 enhanced = enhance(
    #                     self._outer_instance.df_noise_suppression_model, self._outer_instance.df_state, audio
    #                 )
    #                 save_audio(temp_wav_path, enhanced, self._outer_instance.df_state.sr())
    #                 # avoid transcribing silent audio because whisper will hallucinate
    #                 if AudioSegment.from_file(temp_wav_path, format="wav").dBFS < -45.0:
    #                     print("Audio is silent, skipping transcription.")
    #                     return None
    #                 result = self._outer_instance.transcribe(temp_wav_path)
    #                 return result["text"]
    #             except Exception as e:
    #                 logging.exception("Error during transcription: %s", e)
    #                 return None
    #             finally:
    #                 # Clean up the temporary file
    #                 if os.path.exists(temp_wav_path):
    #                     os.remove(temp_wav_path)

    #         return cb

    #     def get_default_text_callback(self) -> SRTextCB:
    #         def cb(user: Optional[discord.User], text: Optional[str]) -> Any:
    #             if text:
    #                 logging.info("%s said: %s", user.display_name if user else "Someone", text)

    #         return cb


class WaveSinkMultipleUsers(AudioSink):
    CHANNELS = OpusDecoder.CHANNELS
    SAMPLE_WIDTH = OpusDecoder.SAMPLE_SIZE // OpusDecoder.CHANNELS
    SAMPLING_RATE = OpusDecoder.SAMPLING_RATE

    def __init__(self, destination: str):
        super().__init__()
        self._base_folder = destination
        self.users: dict[discord.User, wave.Wave_write] = {}

    def wants_opus(self) -> bool:
        return False

    def write(self, user: Optional[discord.User], data: VoiceData) -> None:
        # file might have been deleted from previous invocation
        if not os.path.exists(f"{self._base_folder}/{user.name}.wav"):
            self.users[user] = wave.open(f"{self._base_folder}/{user.name}.wav", "wb")
            self.users[user].setnchannels(self.CHANNELS)
            self.users[user].setsampwidth(self.SAMPLE_WIDTH)
            self.users[user].setframerate(self.SAMPLING_RATE)
        self.users[user].writeframes(data.pcm)

    def cleanup(self) -> None:
        try:
            for user, file in self.users.items():
                file.close()
        except Exception:
            logging.warning("WaveSink got error closing file on cleanup", exc_info=True)
