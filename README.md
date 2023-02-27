# Redacting PII from Audio.....quietly


 -Demo file
#### Step 1: Set up Python Enviroment
```code
python3 -m venv venv

source venv/bin/activate
```

#### Step 2: Install requirements
``` code
pip install -r requirements.txt
```

#### Step 3: Run the program with demo data
```code
export ASSEMBLYAI_API_KEY=YOUR_API_KEY_HERE 

python3 silence_PII.py
```

#### Step 4: Compare output

The original redacted audio is located in:
```
./data/redaction/location_data.mp3
```
Silently redacted audio 
```
./silenced_audio.wav
```

#### Step 5: Use your own data
- The code example uses an example that has been processed and downloaded ahead of time.

- To try this on your own data, uncomment lines 121 - 138 in silence_PII.py

- Change the ```mp3_file``` variable on line 115 of silence_PII.py to refer to the path location of the file you would like to process.

- This will take much longer as the transcript needs to be processed by the API