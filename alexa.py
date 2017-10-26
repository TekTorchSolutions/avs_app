import requests
import json
import re
import uuid

def get_token(self, refresh=False):
    """Returns AVS access token.


    """
    # Return saved token if one exists.
    if self._token and not refresh:
        return self._token
    # Prepare request payload
    payload = {
        "client_id" : CLIENT_ID,
        "client_secret" : CLIENT_SECRET,
        "refresh_token" : REFRESH_TOKEN,
        "grant_type" : "refresh_token"
    }
    url = "https://api.amazon.com/auth/o2/token"
    res = requests.post(url, data=payload)
    res_json = json.loads(res.text)
    self._token = res_json['access_token']
    return self._token


def get_request_params(self):
    """Returns AVS request parameters


    """
    url = "https://access-alexa-na.amazon.com/v1"
    url += "/avs/speechrecognizer/recognize"
    headers = {'Authorization' : 'Bearer %s' % self.get_token()}
    request_data = {
        "messageHeader": {
            "deviceContext": [
                {
                    "name": "playbackState",
                    "namespace": "AudioPlayer",
                    "payload": {
                        "streamId": "",
                        "offsetInMilliseconds": "0",
                        "playerActivity": "IDLE"
                    }
                }
            ]
        },
        "messageBody": {
            "profile": "alexa-close-talk",
            "locale": "en-us",
            "format": "audio/L16; rate=16000; channels=1"
        }
    }
    return url, headers, request_data


def save_response_audio(self, res, save_to=None):
    """Saves the audio from AVS response to a file

   .
    """
    if not save_to:
        save_to = "{}/{}.mp3".format(settings.TEMP_DIR, uuid.uuid4())
    with open(save_to, 'wb') as f:
        if res.status_code == requests.codes.ok:
            for v in res.headers['content-type'].split(";"):
                if re.match('.*boundary.*', v):
                    boundary =  v.split("=")[1]
            response_data = res.content.split(boundary)
            for d in response_data:
                if (len(d) >= 1024):
                    audio = d.split('\r\n\r\n')[1].rstrip('--')
            f.write(audio)
            return save_to
        # Raise exception for the HTTP status code
        print("AVS returned error: {}: {}".format(
            res.status_code, res.content))
        res.raise_for_status()


def ask(self, audio_file, save_to=None):
    """
    Send a command to Alexa

   
    """
    with open(audio_file) as in_f:
        url, headers, request_data = self.get_request_params()
        files = [
            (
                'file',
                (
                    'request', json.dumps(request_data),
                    'application/json; charset=UTF-8',
                )
            ),
            ('file', ('audio', in_f, 'audio/L16; rate=16000; channels=1'))
        ]
        res = requests.post(url, headers=headers, files=files)
        return self.save_response_audio(res, save_to)