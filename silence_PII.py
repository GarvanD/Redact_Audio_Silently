import json
from pydub import AudioSegment
import requests
import os
import time

ASSEMBLYAI_API_KEY = os.environ.get('ASSEMBLYAI_API_KEY')

def get_transcript_json(transcript_id):
    endpoint = "https://api.assemblyai.com/v2/transcript/" + transcript_id
    headers = {
        "authorization": ASSEMBLYAI_API_KEY,
    }
    response = requests.get(endpoint, headers=headers)
    return response.json()

def check_transcript_status(transcript_id):
    endpoint = "https://api.assemblyai.com/v2/transcript/" + transcript_id
    headers = {
        "authorization": ASSEMBLYAI_API_KEY,
    }
    response = requests.get(endpoint, headers=headers)
    return response.json()['status']

def generate_transcript(upload_url):
    endpoint = "https://api.assemblyai.com/v2/transcript"
    json = {
        "audio_url": upload_url,
        "language_code": "en",
        "redact_pii": True,
        "redact_pii_policies": ["location", "language"],
        "redact_pii_sub": "entity_name",
        "redact_pii_audio": True
    }
    headers = {
        "authorization": ASSEMBLYAI_API_KEY,
    }
    response = requests.post(endpoint, json=json, headers=headers)
    return response.json()['id']

def upload_audio_file(filename):
    def read_file(filename, chunk_size=5242880):
        with open(filename, 'rb') as _file:
            while True:
                data = _file.read(chunk_size)
                if not data:
                    break
                yield data
    headers = {
        "authorization": ASSEMBLYAI_API_KEY
    } 
    response = requests.post('https://api.assemblyai.com/v2/upload',
                            headers=headers,
                            data=read_file(filename))
    return response.json()['upload_url']

def is_redacted_word(text):
    # "###-####" or "#-#-#-#"
    if '#' in text:
        return True

    # "[NAME]" or "[LOCATION]"
    elif text.startswith('[') and text.strip('.,!?').endswith(']'):
        return True

    # not redacted
    else:
        return False

def find_redacted_timestamps(words):
    # Given a list of words like [{'text': 'foo', 'start': 1, 'end': 2}, ....],
    # find start and end timestamps of words that have "#" as text
    timestamps = []
    started_redaction = False

    for i, word in enumerate(words):
        if is_redacted_word(word['text']):
            if not started_redaction:
                started_redaction = True
                redaction_start = word['start']
        elif not is_redacted_word(word['text']) and started_redaction:
            redaction_end = words[i-1]['end']
            timestamps.append((redaction_start, redaction_end))
            started_redaction = False

    # if the last word is redacted, make sure we get the timestamps too
    if started_redaction:
        if not timestamps or timestamps[-1][0] != redaction_start:
            timestamps.append((redaction_start, words[-1]['end']))

    return timestamps

def read_json_file(path):
    with open(path, 'r') as f:
        return json.load(f)

def silence_audio(audio_path, timestamps):
    a = AudioSegment.from_mp3(audio_path)
    for i, (start, end) in enumerate(timestamps):
        if i == 0:
            redacted_audio = a[:start]
        else:
            # append the part between the muted parts
            redacted_audio = redacted_audio.append(a[prev_end:start], crossfade=0)
        s = AudioSegment.silent(duration=end-start, frame_rate=a.frame_rate)
        redacted_audio = redacted_audio.append(s, crossfade=0)
        prev_end = end

    redacted_audio.export('silenced_audio.wav', format='wav')


if __name__ == '__main__':
    # Audio file to redact
    mp3_file = './data/redaction/location_data.mp3'

    # Note: If you have the JSON already downloaded, you can skip steps 1, 2, and 3 and uncomment the code below
    # Comment out steps 1, 2, and 3
    json_response_file = './data/redaction/location_data.json'
    transcript = read_json_file(json_response_file)
    
    # Step 1: Generate Transcript from AssemblyAI
    print('Uploading audio file to AssemblyAI...')
    upload_url = upload_audio_file(mp3_file)
    transcript_id = generate_transcript(upload_url)

    # Step 2: Wait for transcript to complete
    print('Waiting for transcript to complete...')
    status = 'not ready'
    while status != 'completed' and status != 'error':
        status = check_transcript_status(transcript_id)
        print('Transcript status: ' + status)
        time.sleep(30)

    if status == 'error':
        raise Exception('Error generating transcript')
    
    # Step 3: Get transcript JSON
    transcript = get_transcript_json(transcript_id)

    # Step 4: Replace redacted words with silence
    words = transcript['words']
    timestamps = find_redacted_timestamps(words)
    if len(timestamps) == 0:
        print('No redacted words found!')
    else:
        print('Redacted words found!')
        print('Silencing redacted words...')
        silence_audio(mp3_file, timestamps)
    print('Done!')