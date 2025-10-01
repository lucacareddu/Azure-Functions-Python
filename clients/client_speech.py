import os
import ffmpy
import base64
import requests


path = "speech.wav"
temp_file = "temp_out.wav"
url = 'http://localhost:7071/api/speech_to_text/'

ff = ffmpy.FFmpeg(inputs={path: None}, outputs={f"{temp_file}": "-ar 16000 -ac 1 -sample_fmt s16 -y -hide_banner -loglevel error"})
ff.run() # Resample audio to 16kHz

try:
    with open(temp_file, "rb") as speech:
        speech.read(44) # Remove RIFF header
        encoded = base64.b64encode(speech.read()).decode('utf-8')

    r = requests.post(url, json={"speech": encoded})
    transcript = r.json().get("text")

    print(transcript)
except Exception as e:
    print(str(e))
finally:
    os.remove(temp_file)
