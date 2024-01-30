from pathlib import Path
import cv2
import time
import easyocr
import string
import serial

COM_NUM = 3
BAUD = 115200
COMMAND_OPEN = "1"

CARS_DB = [

    
]

# Custom funtions for ALPR process

def check_file_name(path, exist_ok=False, sep='', mkdir=False):
    path = Path(path)
    if path.exists() and not exist_ok:
        path, suffix = (path.with_suffix(''), path.suffix) if path.is_file() else (path, '')

    if mkdir:
        path.mkdir(parents=True, exist_ok=True)  # make directory

    return path

def crop_prepare(crop):
    # Przeprowadz zamiane na odcienie szarosci oraz progowanie

    #_, crop_tresh = cv2.threshold(blackhat, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
    #kernel = np.ones((3, 3), np.uint8)
    #img_erosion = cv2.erode(img_dilation, kernel, iterations=1)  #moze inv i wtedy dylatacja znowu?
    #img_dilation = cv2.dilate(blackhat, kernel, iterations=1)
    #closing = cv2.morphologyEx(crop_tresh, cv2.MORPH_CLOSE, kernel)

    blur = cv2.GaussianBlur(crop, (7, 7), 0)
    crop_gray = cv2.cvtColor(blur, cv2.COLOR_BGR2GRAY)
    rectKernel = cv2.getStructuringElement(cv2.MORPH_RECT, (13, 5))
    blackhat = cv2.morphologyEx(crop_gray, cv2.MORPH_BLACKHAT, rectKernel)
    _, tresh = cv2.threshold(blackhat, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)

    return tresh

def anpr(ocr_reader, ocr_input, relay):
    # Run ANPR process on cropped image  
    start = time.time()
    anpr = []
    ocr_result = ocr_reader.readtext(ocr_input, detail=0, min_size=20, allowlist = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    ocr_time = time.time() - start
    if len(ocr_result):
        print("OCR result: ", ocr_result)
        for plate in ocr_result:
            if  len(plate) >= 1 and len(plate) <= 8: #and \
                #(plate[0] in string.ascii_uppercase) and \
                #(plate[1] in string.ascii_uppercase): #and \
                #(plate[2] in string.ascii_uppercase or plate[2] in ['0','1','2','3','4','5','6','7','8','9']) and \
                #(plate[3] in string.ascii_uppercase or plate[3] in ['0','1','2','3','4','5','6','7','8','9']) and \
                #(plate[4] in string.ascii_uppercase or plate[4] in ['0','1','2','3','4','5','6','7','8','9']) and \
                #(plate[5] in string.ascii_uppercase or plate[5] in ['0','1','2','3','4','5','6','7','8','9']) and \
                #(plate[6] in string.ascii_uppercase or plate[6] in ['0','1','2','3','4','5','6','7','8','9']):
                anpr.append(str(plate))
        for plate in anpr:
            if plate in CARS_DB:
                print(f"Access granted! Opening the gate for the {plate}...")
                gate_open(relay)
                time.sleep(5)
            else:
                print("Access denied!")
    else:
        print("Access denied!")

    return anpr, ocr_time

def gate_open(arduino):
    # Change relay state
    time.sleep(0.5)
    arduino.write(COMMAND_OPEN.encode('utf-8'))
    time.sleep(0.05)
    arduino_data = arduino.readline().decode('utf-8')
    print(arduino_data)
    time.sleep(0.5)
    arduino_data = arduino.readline().decode('utf-8')
    print(arduino_data)
    #arduino.close()

def alpr_init():
    #OCR detector init
    ocr_reader = easyocr.Reader(['en'], gpu=False, verbose=False)

    #Relay init
    relay = serial.Serial(("COM" + str(COM_NUM)), BAUD)

    return ocr_reader, relay