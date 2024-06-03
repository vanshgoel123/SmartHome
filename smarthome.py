import streamlit as st
import speech_recognition as sr
import serial
import time
from twilio.rest import Client
import random
import cv2
import pyttsx3
import os
import pygame

# Initialize recognizer
recognizer = sr.Recognizer()

# Initialize other necessary components
camera = cv2.VideoCapture(0)
engine = pyttsx3.init()
pygame.mixer.init()

# Function to recognize voice
def recognize_voice():
    with sr.Microphone() as source:
        st.write("Listening...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)

        try:
            command = recognizer.recognize_google(audio).lower()
            st.write("You said:", command)
            return command
        except sr.UnknownValueError:
            st.write("Sorry, I could not understand what you said.")
            return None
        except sr.RequestError as e:
            st.write(f"Could not request results from Google Speech Recognition service; {e}")
            return None

# Function for speech output
def speak(text):
    engine.say(text)
    engine.runAndWait()

# Function to send SMS
def send_sms(message):
    account_sid = ''# Enter your Twilio account SID here
    auth_token = ''# Enter your Twilio auth token here
    
    client = Client(account_sid, auth_token)
    try:
        message = client.messages.create(
            body=message,
            from_=''   # Enter your Twilio phone number here,
            to=''      # Enter your phone number here
        )
        st.write("SMS message sent successfully:", message.sid)
        return True
    except Exception as e:
        st.write(f"Error sending SMS: {e}")
        return False

# Function to generate random PIN
def generate_pin():
    return ''.join(random.choices('0123456789', k=4))

# Function to control the bulbs
def control_bulbs(command, arduino):
    while True:
        if command == "start":
            st.write("Sending command to Arduino to turn on all bulbs...")
            arduino.write(b's')
            speak("All LEDs turned on")
        elif command == "medium":
            st.write("Sending command to Arduino to turn off mid LED...")
            arduino.write(b'm')
            speak("Medium LED turned off")
        elif command == "reset":
            st.write("Sending command to Arduino to reset all LEDs...")
            arduino.write(b'r')
            speak("All LEDs reset")
        elif command == "dim":
            st.write("Sending command to Arduino to turn on only one LED...")
            arduino.write(b'l')
            speak("Only one LED turned on")
        elif command == "exit":
            speak("Moving to choice part")
            st.write("Exiting control smart LEDs...")
            break
        else:
            st.write("Invalid command")
            st.write(command)
            speak("Invalid command")
        
        st.write("Listening for next command...")
        command = recognize_voice()

# Function to control the servo motor
def control_servo(arduino):
    arduino.write(b'u')  # Send 'u' to Arduino to rotate servo motor
    time.sleep(2)
    response = arduino.readline().decode().strip()
    st.write("Response from Arduino:", response)

# Function to capture photo
def capture_photo():
    return_value, image = camera.read()
    if return_value:
        cv2.imwrite("intruder.jpg", image)
        st.write("Photo of intruder captured.")
    else:
        st.write("Failed to capture photo of intruder.")

# Function to play music
def play(playlist, index):
    pygame.mixer.music.load(playlist[index])
    pygame.mixer.music.play()

def next_track(playlist, index):
    index = (index + 1) % len(playlist)
    pygame.mixer.music.load(playlist[index])
    pygame.mixer.music.play()
    return index

def prev_track(playlist, index):
    index = (index - 1) % len(playlist)
    pygame.mixer.music.load(playlist[index])
    pygame.mixer.music.play()
    return index

def play_music():
    music_directory = r"C:\Users\Public\Music"
    playlist = [os.path.join(music_directory, file) for file in os.listdir(music_directory) if file.endswith((".mp3", ".wav"))]
    if not playlist:
        st.write("No music files found in the specified directory.")
        return

    index = 0
    play(playlist, index)

    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.write("Listening...")
        recognizer.adjust_for_ambient_noise(source)
        while True:
            audio = recognizer.listen(source)
            try:
                command = recognizer.recognize_google(audio)
                st.write(command)
                if "next" in command:
                    index = next_track(playlist, index)
                elif "previous" in command:
                    index = prev_track(playlist, index)
                elif "exit" in command:
                    pygame.mixer.music.stop()
                    break
            except sr.UnknownValueError:
                st.write("Could not understand audio")
            except sr.RequestError as e:
                st.write("Could not request results; {0}".format(e))

# Main function
def main():
    arduino_port = 'COM8'# Enter your Arduino port here
    arduino_baudrate = 9600
    arduino = serial.Serial(arduino_port, arduino_baudrate)
    time.sleep(2)  # Wait for Arduino to initialize

    attempt_count = 0

    while True:
        st.write("What do you want to do?")
        st.write("Option 1: Control Smart LED")
        st.write("Option 2: Unlock Door with OTP")
        st.write("Option 3: Smart Speaker")
        st.write("Option 4: Exit")
        choice = recognize_voice()

        if choice == "control smart led" or choice == "option 1":
            st.write("Choice 1 for controlling smart LEDs")
            st.write("Listening for command to control smart LEDs...")
            command = recognize_voice()
            control_bulbs(command, arduino)

        elif choice == "unlock door with otp" or choice == "option 2":
            st.write("Choice 2 for unlocking door with OTP")
            otp = generate_pin()  # Generate OTP
            send_sms(otp)  # Send OTP

            while attempt_count < 3:
                st.write("Please speak the OTP received on your phone")
                otp_spoken = recognize_voice()
                if otp_spoken == otp:
                    st.write("OTP matched. Door unlocking...")
                    control_servo(arduino)
                    break
                else:
                    attempt_count += 1
                    st.write("OTP did not match. Please try again.")
            else:
                st.write("Three unsuccessful attempts. Capturing photo of intruder and sending SMS alert.")
                capture_photo()
                send_sms("Intruder Alert! Possible unauthorized access detected.")
                break

        elif choice == "smart speaker" or choice == "option 3":
            st.write("Choice 3 for controlling smart speaker")
            st.write("Listening for music command...")
            play_music()

        elif choice == "exit" or choice == "option 4":
            st.write("Exiting program")
            break

        else:
            st.write("Invalid choice. Please try again.")

    arduino.close()

if __name__ == "__main__":
    main()
