from __future__ import print_function
import datetime
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os
import time, datetime
import playsound
import speech_recognition as sr
import pyttsx3
import pytz
import subprocess
import requests, json


SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
DAYS = ['monday','tuesday','wednesday','thursday','friday','saturday','sunday']
MONTHS = ['january','february','march','april','may','june','july','august','september','october','november','december']
DAY_EXTENTIONS = ['rd','st','th','nd']


def speak(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.setProperty('rate',100)  #120 words per minute
    engine.setProperty('volume',0.9)
    engine.runAndWait()


def get_audio():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        playsound.playsound("beep.mp3")
        audio = r.listen(source)
        text = ""

        try:
            text = r.recognize_google(audio)
            print(text)
        except Exception as e:
            print("Exception: " + str(e))
    return text.lower()


def authenticate_google():
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    creds = None

    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)
    return service


def get_events(day,service):
    date = datetime.datetime.combine(day,datetime.datetime.min.time())
    end_date = datetime.datetime.combine(day,datetime.datetime.max.time())
    utc = pytz.UTC
    date = date.astimezone(utc)
    end_date = end_date.astimezone(utc)

    events_result = service.events().list(calendarId='primary', timeMin=date.isoformat(), timeMax=end_date.isoformat(),
                                        singleEvents=True,
                                        orderBy='startTime').execute()
    events = events_result.get('items', [])

    if not events:
        speak('No upcoming events found.')
    else:
        speak(f"You have {len(events)} events on this day.")
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            print(start, event['summary'])
            start_time = str(start.split("T")[1].split(":")[0])

            if int(start_time.split(":")[0]) < 12:
                start_time += "am"
            else:
                start_time = str(int(start_time.split(":")[0] - 12)) + start_time.split(":")[1]
                start_time += "pm"

            speak(event["summary"] + " at " + start_time)


def get_date(text):
    text = text.lower()
    today = datetime.date.today()

    if text.count("today") > 0:
        return today

    day = -1
    day_of_week = -1
    month = -1
    year = today.year

    for word in text.split():
        if word in MONTHS:
            month = MONTHS.index(word) +  1
        elif word in DAYS:
            day_of_week = DAYS.index(word)
        elif word.isdigit():
            day = int(word)
        else:
            for ext in DAY_EXTENTIONS:
                found = word.find(ext)
                if found > 0:
                    try:
                        day = int(word[:found])
                    except:
                        pass

    if month < today.month and month !=-1:
        year += 1

    if day < today.day and month == -1 and day != -1:
        month += 1

    if month == -1 and day == -1 and day_of_week != -1:
        current_day_of_week = today.weekday()
        diff = day_of_week - current_day_of_week

        if diff < 0:
            diff += 7
            if text.count("next") >= 1:
                diff += 7

        return today + datetime.timedelta(diff)

    if month == -1 or day == -1:
        return None

    return datetime.date(day=day,month=month,year=year)


def note(text):
    date = datetime.datetime.now()
    file_name = str(date).replace(":", "-") + "-note.txt"
    with open(file_name,"w") as f:
        f.write(text)

    subprocess.Popen(["notepad.exe",file_name])



def weatherInfo(city_name):
    api_key = "42516aebf94284d22530445053e47ea6"
    base_url = "http://api.openweathermap.org/data/2.5/weather?"
    
    try:
        complete_url = base_url + "appid=" + api_key + "&q=" + city_name
        response = requests.get(complete_url)
        x = response.json()

        if x["cod"] != "404":
            y = x["main"]

            current_temperature = y["temp"]
            current_pressure = y["pressure"]
            current_humidity = y["humidity"]
            z = x["weather"]
            weather_description = z[0]["description"]

            speak("Temperature "+str(int(current_temperature - 273))+" Celcius")
            speak("Pressure "+str(current_pressure/1000)+" bar")
            speak("Humidity "+str(current_humidity)+" %")
            speak("Description "+str(weather_description))
        else:
            speak("City not found")

    except:
        pass




# note("Jai bholenaath")

WAKE = "jarvis"
CALENDER_ET = ["what do i have","do i have plans","am i busy"]
NOTE_ET = ["make a note","write it down","note it down","note this down","record this"]
WEATHER_ET = ["how's the weather","weather","how's the climate","climate"]

SERVICE = authenticate_google()
print("Start")

while True:
    text = get_audio()

    if text.count(WAKE) > 0:
        speak("Jarvis at your service")
        text = get_audio()

        if any(phrase in text for phrase in CALENDER_ET):
            date = get_date(text)
            if date:
                get_events(date,SERVICE)
            else:
                speak("I don't understand.")


        if any(phrase in text for phrase in NOTE_ET):
            speak("What do you want me to note down?")
            note_text = get_audio()
            note(note_text)
            speak("I've made a note of that.")


        if any(phrase in text for phrase in WEATHER_ET):
            speak("What city?")
            city = get_audio()
            weatherInfo(city)


