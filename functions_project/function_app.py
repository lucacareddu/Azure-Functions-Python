from io import BytesIO
import base64
import tiktoken
from PIL import Image
import json

import azure.functions as func

from azure.core.credentials import AzureKeyCredential
import azure.cognitiveservices.speech as speechsdk

import logging

import os
from dotenv import load_dotenv

load_dotenv(".env")


app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

@app.route(route="get_factorial/{number:int}")
def get_factorial(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python "Factorial" HTTP trigger function processed a request.')

    number = req.route_params.get('number', None)
    if not number:
        try:
            req_body = req.get_json()
        except ValueError:
            logging.info('Value Error')
            pass
        else:
            number = req_body.get('number')

    if number:
        number = int(number)

        def compute_factorial(n:int) -> int:
            assert not n<0

            if n in [0,1]:
                return 1
            
            return n*compute_factorial(n-1)
        
        try:
            factorial = compute_factorial(number)
            return func.HttpResponse(f"The factorial of {number} is {factorial}.")
        
        except (AssertionError, Exception) as e:
            return func.HttpResponse(f"Please provide a positive integer. (Error: {e})",status_code=400)
        
    else:
        return func.HttpResponse("Please provide a positive integer.",status_code=400)


@app.route(route="get_tokens_number/{string:length(1,1000)}", auth_level=func.AuthLevel.FUNCTION)
def get_tokens_number(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python "Tokens" HTTP trigger function processed a request.')

    string = req.route_params.get('string')
    if not string:
        try:
            req_body = req.get_json()
        except ValueError:
            logging.info('Value Error.')
            pass
        else:
            string = req_body.get('string')
    
    if string:
        try:
            tokenizer = tiktoken.get_encoding(encoding_name="cl100k_base")
            tokens = tokenizer.encode(string, disallowed_special=())
            return func.HttpResponse(f"There are {len(tokens)} tokens in '{string}'.")
        except Exception as e:
            return func.HttpResponse(f"Internal error: {e}", status_code=500)
    else:
        return func.HttpResponse(
             "Please provide a valid string.",
             status_code=400
        )

@app.route(route="transform_image", auth_level=func.AuthLevel.FUNCTION)
def transform_image(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python "Image" HTTP trigger function processed a request.')

    try:
        req_body = req.get_json()
    except ValueError:
        logging.info('Value Error.')
        pass
    else:
        image = req_body.get('image')

    if image:
        try:
            decoded = base64.b64decode(image)

            image = Image.open(BytesIO(decoded))
            bnw_image = BytesIO()
            image.convert(mode="L").save(bnw_image, "PNG")

            encoded = base64.b64encode(bnw_image.getvalue()).decode('utf-8')

            return func.HttpResponse(json.dumps({"image":encoded}), mimetype="application/json")
        except Exception as e:
            return func.HttpResponse(f"Internal error: {e}", status_code=500)
    else:
        return func.HttpResponse(
             "Please provide a json with a 'image' key containing a base64 string.",
             status_code=400
        )

@app.route(route="speech_to_text", auth_level=func.AuthLevel.FUNCTION)
def speech_to_text(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python "Speech" HTTP trigger function processed a request.')

    try:
        req_body = req.get_json()
    except ValueError:
        logging.info('Value Error.')
        pass
    else:
        speech = req_body.get('speech')

    if speech:
        try:
            decoded = base64.b64decode(speech)

            speech_config = speechsdk.SpeechConfig(endpoint=os.getenv("SPEECH_ENDPOINT"), key_credential=AzureKeyCredential(os.getenv("SPEECH_API_KEY")))
            speech_config.speech_recognition_language = "en-US"

            # Set up the audio stream
            push_stream = speechsdk.audio.PushAudioInputStream()
            audio_config = speechsdk.audio.AudioConfig(stream=push_stream)
            speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
            
            # Read the .wav file in chunks and feed them to the speech recognizer
            push_stream.write(decoded)

            # Close the stream to signal that all audio data has been written
            push_stream.close()

            # Recognize the speech from the .wav file
            speech_recognition_result = speech_recognizer.recognize_once_async().get()

            # print(speech_recognition_result.reason)

            return func.HttpResponse(json.dumps({"text":speech_recognition_result.text}), mimetype="application/json")
        except Exception as e:
            return func.HttpResponse(f"Internal error: {e}", status_code=500)
    else:
        return func.HttpResponse(
            "Please provide a json with a 'speech' key containing a base64 string.",
             status_code=400
        )