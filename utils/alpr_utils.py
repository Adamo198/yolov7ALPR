from pathlib import Path
import cv2
import time
import easyocr
import string
import serial
import numpy as np
from scipy.ndimage import interpolation as inter
import sqlite3

COM_NUM = 'COM3'
BAUD = 115200
COMMAND_OPEN = "1"
ANPR_ON = "AON\n"
ANPR_OFF = "AOFF\n"
TIMEOUT = 0.01


# Custom funtions for ALPR process


def crop_prepare(crop):
    #preprocessing of detected license plate

    #_, crop_tresh = cv2.threshold(blackhat, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
    #kernel = np.ones((3, 3), np.uint8)
    #img_erosion = cv2.erode(img_dilation, kernel, iterations=1)  #moze inv i wtedy dylatacja znowu?
    #img_dilation = cv2.dilate(blackhat, kernel, iterations=1)
    #closing = cv2.morphologyEx(crop_tresh, cv2.MORPH_CLOSE, kernel)

    skew = correct_skew(crop)

    gray = cv2.cvtColor(skew, cv2.COLOR_BGR2GRAY)
    gray = cv2.threshold(gray, 0, 255,cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    gray = cv2.medianBlur(gray, 3) 

    #blur = cv2.GaussianBlur(crop, (7, 7), 0)
    #crop_gray = cv2.cvtColor(blur, cv2.COLOR_BGR2GRAY)
    #rectKernel = cv2.getStructuringElement(cv2.MORPH_RECT, (13, 5))
    #blackhat = cv2.morphologyEx(crop_gray, cv2.MORPH_BLACKHAT, rectKernel)
    #_, tresh = cv2.threshold(blackhat, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)

    return gray

# Skew Correction (projection profile)
def _find_score(arr, angle):
    data = inter.rotate(arr, angle, reshape=False, order=0)
    hist = np.sum(data, axis=1)
    score = np.sum((hist[1:] - hist[:-1]) ** 2)
    return hist, score

def _find_angle(img, delta = 0.5,  limit = 10):
    angles = np.arange(-limit, limit+delta, delta)
    scores = []
    for angle in angles:
        hist, score = _find_score(img, angle)
        scores.append(score)
    best_score = max(scores)
    best_angle = angles[scores.index(best_score)]
    print(f'Best skew correction angle: {best_angle}')
    return best_angle

def correct_skew(img):
    # correctskew
    best_angle =_find_angle(img)
    data = inter.rotate(img, best_angle, reshape=False, order=0)
    return data


def anpr(ocr_reader, ocr_input, relay, cars_db):
    # Run ANPR process on license plate image  
    anpr = []
    ocr_result = ocr_reader.readtext(ocr_input, detail=0, min_size=25, allowlist = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    if len(ocr_result):
        cars_db = access_database(cars_db)
        print("OCR result: ", ocr_result)
        for ocr in ocr_result:
            if len(ocr) in [7, 8] and \
                all(ocr[i] in string.ascii_uppercase for i in range(0, 2)) and \
                all(ocr[i] in string.ascii_uppercase or ocr[i] in string.digits for i in range(2, 7)):
            #if  len(ocr) >= 4 and len(ocr) <= 8 and \
            #    (ocr[0] in string.ascii_uppercase) and \
            #    (ocr[1] in string.ascii_uppercase) and \
            #    (ocr[2] in string.ascii_uppercase or ocr[2] in ['0','1','2','3','4','5','6','7','8','9']) and \
            #    (ocr[3] in string.ascii_uppercase or ocr[3] in ['0','1','2','3','4','5','6','7','8','9']): #and \
                #(ocr[4] in string.ascii_uppercase or ocr[4] in ['0','1','2','3','4','5','6','7','8','9']) and \
                #(ocr[5] in string.ascii_uppercase or ocr[5] in ['0','1','2','3','4','5','6','7','8','9']) and \
                #(ocr[6] in string.ascii_uppercase or ocr[6] in ['0','1','2','3','4','5','6','7','8','9']):
                anpr.append(str(ocr))
        for plate in anpr:
            if plate in cars_db:
                print(f"Access granted! Opening the gate for the {plate}...")
                gate_open(relay)
                time.sleep(5) #sleep time to avoid next detection
            else:
                print("Access denied!")
    else:
        print("Access denied!")

    return anpr

def gate_open(arduino):
    # Change relay state
    arduino.write(COMMAND_OPEN.encode('utf-8'))
    time.sleep(0.1)
    arduino_data = arduino.readline().decode('utf-8')
    print(arduino_data)
    time.sleep(0.5)
    arduino_data = arduino.readline().decode('utf-8')
    print(arduino_data)
    #arduino.close()

def anpr_init():
    #OCR detector init
    ocr_reader = easyocr.Reader(['en'], gpu=False, verbose=False)

    #Arduino communication init
    ardu_serial = serial.Serial(COM_NUM, BAUD, timeout=TIMEOUT)

    return ocr_reader, ardu_serial


def access_database(plate_numbers):
    try:
        # Try to connect to the database and retrieve values
        conn = sqlite3.connect('license_plates.db')
        c = conn.cursor()
        c.execute("SELECT plate_number FROM license_plates WHERE plate_type != 'inactive'") #ignore inactive numbers
        plates_from_database = [row[0] for row in c.fetchall()]
        conn.close()

        # Use the values retrieved from the database
        plate_numbers = plates_from_database

    except sqlite3.Error:
        # Handle the case where accessing the database fails
        print("Failed to retrieve plate numbers from the database. Using last read plate numbers.")
        plate_numbers = plate_numbers

    return plate_numbers

def system_switch(switch_state):
    try:
        conn = sqlite3.connect('license_plates.db')
        c = conn.cursor()
        c.execute('SELECT system_power FROM system_switch WHERE id = 1')
        row = c.fetchone()
        power_switch = bool(row[0]) if row else True
        conn.close()

        switch_state = power_switch

    except sqlite3.Error:
        print("Failed to system switch state. Using last read switch position.")
        switch_state = switch_state

    return bool(switch_state)

def detection_trigger(arduino, current_state):
    arduino_trigger = arduino.readline().decode('utf-8')
    if (arduino_trigger == ANPR_ON):
        current_state = 1
        time.sleep(0.1)
    elif (arduino_trigger == ANPR_OFF): 
        current_state = 0
        time.sleep(0.1)
    else:
        current_state = current_state
   
    return current_state