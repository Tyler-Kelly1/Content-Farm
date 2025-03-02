from moviepy import *

import os
import time
import requests
from openai import OpenAI
from dotenv import load_dotenv, find_dotenv
from pathlib import Path
import re

#font loading
font = "font4.ttf"

#loading AI Key
_ = load_dotenv(find_dotenv())

#Connecting Client to Open AI Server
client = OpenAI(
    api_key=os.environ.get('OPENAI_API_KEY2'),
)

###
#Docker Run
#docker run -P lowerquality/gentle

def align_audio_with_gentle(audio_path, transcript, server_url="http://localhost:8765/transcriptions?async=false"):
    """
    Send audio and transcript to Gentle server and get the alignment result.

    Args:
        audio_path (str): Path to the audio file.
        transcript (str): The text to align against the audio.
        server_url (str): URL of the Gentle server's transcription endpoint.

    Returns:
        dict: The JSON response from the Gentle server, containing the alignment.
    """
    try:
        # Prepare the payload
        files = {
            'audio': open(audio_path, 'rb'),
            'transcript': (None, transcript)
        }

        # Send POST request to Gentle server
        response = requests.post(server_url, files=files)

        # Check for successful response
        if response.status_code == 200:
            return response.json()  # Return the alignment result as JSON
        else:
            print(f"Error: Received status code {response.status_code}")
            print(response.text)
            return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
    
def parse_gentle_json_to_tuples(json_data, offset = 0.0):
    """
    Convert Gentle JSON alignment data to a list of tuples.

    Args:
        json_data (dict): The JSON response from Gentle server.

    Returns:
        list: A list of tuples in the format (word, start_time, end_time).
    """
    result = []
    for word_entry in json_data.get("words", []):
        word = word_entry.get("word", "")  # Extract the word
        start_time = word_entry.get("start", None)  # Extract start time (if available)
        end_time = word_entry.get("end", None)  # Extract end time (if available)

        # Only include entries where timing information is available
        if start_time is not None and end_time is not None:
            result.append((word, float(round(start_time, 2) + offset), float(round(end_time,2)+offset)))
    
    return result

def genrateAudio(story,fn):
    speech_file_path = Path(__file__).parent / "speech.mp3"
    response = client.audio.speech.create(
        model="tts-1",
        voice="onyx",
        input=story,
    )
    response.stream_to_file(fn)

def generateStory(devolperPrompt, userPrompt):

    completion = client.chat.completions.create(

        model="gpt-4o-mini",

        messages=[
            {"role": "developer", "content": devolperPrompt},
            {
                "role": "user",

                "content": userPrompt
            }

        ]
    )

    return completion.choices[0].message.content

def returnTitle(story):
    titleRePattern = "\*+([a-zA-z\s\d]+)\*+"
    titleMatch = re.search(titleRePattern, story)
    titleMatch = (titleMatch.group(1)).lower()
    return titleMatch

def generateTitleText(story,font, textSize = 70):

    titleText = returnTitle(story)

    title = TextClip(
    font = font,
    text = titleText,
    font_size= textSize,
    color = "#FFFFFF",
    duration = 2.9,
    )

    title = title.with_position(("center", 0.50), relative=True)

    titleTTS = genrateAudio(titleText, "title.wav")
    time.sleep(5)
    title = title.with_audio(titleTTS)

    return title

def returnStory(story):
    titleRePattern = "\*+[a-zA-z\s\d]+\*+"
    return re.sub(titleRePattern, '', story)

def generateBrainRot(bgFN = '', bgMusicFN = '', bgMusicVol = 0.5, ttsVol = 1.5, devPrompt = '', userPrompt = '', outPutFile = 'output.mp4', titleSize = 70, wordSize = 100, titleFontNameFN = "redditFont.ttf", wordFontFN = "font4.ttf"):
    
    #Load BG Video File
    bgVid = VideoFileClip(bgFN)
    bgVid = bgVid.with_end(59)

    #Generating Story
    print("Generating Story...")
    story = generateStory(devPrompt, userPrompt)

    #Fomartting the Title.
    title = generateTitleText(story, titleFontNameFN, textSize = titleSize)

    #Generate Title Audio.
    fn = "title.wav"
    print("Generating Title TTS...")
    genrateAudio(returnTitle(story), fn)
 
    #Officallize the audio
    time.sleep(5)

    #Convert the audio into an AudioFileClip
    titleAudio = AudioFileClip(fn)
    titleAudio = titleAudio.with_start(0)

    #Load BG Music
    bgMusic = AudioFileClip(bgMusicFN)
    bgMusic = bgMusic.with_start(0)
    bgMusic = bgMusic.with_end(59)
    bgMusic = bgMusic.with_effects([afx.MultiplyVolume(bgMusicVol)])

    #Composite Audio Clip
    audioClips = [bgMusic,titleAudio]

    #split the background into to vids.
    intro = bgVid.with_end(2.9)
    intro = intro.without_audio()
    body = bgVid.subclipped(2.9,-1)
    body = body.without_audio()
    body = body.with_start(2.9)

    #Seperates the story and the title
    story = returnStory(story)

    #Generate the audio file
    print("Generating TTS...")
    genrateAudio(story, "audio.wav")

    # Pause for 5 seconds, allows for audio file to completely generate and render
    time.sleep(5)  

    #Lets uses Alginer to get time stamps for the

    # Creates an audio clip object
    fn = "audio.wav"
    voiceOver = AudioFileClip(fn)
    voiceOver = voiceOver.with_start(2.9)
    voiceOver = voiceOver.with_effects([afx.MultiplyVolume(ttsVol)])
    voiceOver = voiceOver.with_end(59)

    #adding voice over to composite audio
    audioClips.append(voiceOver)
    master_audio = CompositeAudioClip(audioClips)
    master_audio.write_audiofile("MasterAudio.mp3")
    time.sleep(5)

    #Create Master Audio Clip
    fn = "MasterAudio.mp3"
    masterAudioClip = AudioFileClip(fn)

    #Creates black background
    bg = ColorClip(size=(1080,1920), color = (0,0,0), duration = 60)
    bg = bg.with_audio(masterAudioClip)

    #Generate Time Stamps for the text using Gentle
    print("Generating Time Stamps...")
    fn = "audio.wav"
    result = align_audio_with_gentle(fn,story)
    timeStamps = parse_gentle_json_to_tuples(result, offset=2.9)

    #A list of clips to be rendered
    textClips = [bg, intro, title, body]

    #generate a text clip for each word
    for word in timeStamps:

        wordStr, start, end = word

        text = TextClip(
            font=wordFontFN,
            text = wordStr,
            font_size= wordSize,
            color = "#FFFDD0",
            duration = 0,
        )

        #Applying Glow and animation
        text = text.resized(lambda t: 1 + t * 0.3)

        #Set the starting and ending time of each clip
    
        text = text.with_start(start)
        text = text.with_end(end)

        #postioning the text
        text = text.with_position(("center", 0.50), relative=True)

        textClips.append(text)

    
    final_clip = CompositeVideoClip(textClips)
    final_clip = final_clip.with_end(60)
    final_clip.write_videofile(outPutFile, fps = 30)




    return True

#Prompts

devPrompt1 = """
You are a redditer posting a creepy pasta. You will never reveal it is a fake story. You will refer to yourself as I, and are a male in his 30s. You story will be no more than 1000 characthers.
However the First line will always be a short 5 word title for the story. It will be formated with **title name**, This story will be both enganing and creepy. It will have an ending where the speaker barely got away.
Try to base the story on real life places to make the story feel more real. Add creepy details as well.

It is CRITICAL that you format your title **title name**. If you dont do this your story will not be valid and no one will read it ever. You will fails as a writer and as a person.
Never forgot to format the title.
"""

prompt1 = """
Tell me a one minuete story from your past, it should be real and have details that make it feel real.
"""


#Generate 3 Vids
for i in range(1):
    value = generateBrainRot(
        bgFN = "output.mp4",
        bgMusicFN= "bgMus.mp3",
        bgMusicVol=0.1,
        ttsVol=1.5,
        devPrompt = devPrompt1,
        userPrompt = prompt1,
        titleSize= 65,
        wordSize = 120,
        outPutFile = f"vid_{i}.mp4",
        titleFontNameFN= "redditFont.ttf",
        wordFontFN = "font4.ttf",
    )
