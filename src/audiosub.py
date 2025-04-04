import speech_recognition as sr
import glob

class AudioSub:
    def __init__(self, audio_path: str):
        self.audio_path = audio_path
        self.recognizer = sr.Recognizer()

    def transcribe(self):
        audio_files = glob.glob(self.audio_path + '\\*.wav')
        if not audio_files:
            raise FileNotFoundError("No audio files found in the specified directory.")

        transcriptions = []
        for audio_file in audio_files:
            with sr.AudioFile(audio_file) as source:
                audio_data = self.recognizer.record(source)
                try:
                    text = self.recognizer.recognize_google(audio_data)
                    transcriptions.append(text)
                except sr.UnknownValueError:
                    transcriptions.append("Could not understand the audio")
                except sr.RequestError as e:
                    transcriptions.append(f"Error from Google API: {e}")

        return "\n".join(transcriptions)