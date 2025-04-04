import whisper
import glob

class AudioSub:
    def __init__(self, audio_path: str):
        self.audio_path = audio_path
        self.model = whisper.load_model("base")  # Load the Whisper model, you can choose other models like "small", "medium", "large"

    def transcribe(self):
        audio_files = glob.glob(self.audio_path + '\\*.wav')
        if not audio_files:
            raise FileNotFoundError("No audio files found in the specified directory.")

        transcriptions = []
        for audio_file in audio_files:
            result = self.model.transcribe(audio_file)  # Specify the language if needed
            text = result['text']  # Get the transcribed text and strip any leading/trailing whitespace
            transcriptions.append(text)

        return "\n".join(transcriptions)