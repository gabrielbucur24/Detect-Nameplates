import datetime
import os
import cv2
import numpy as np
import imutils
import easyocr
from datetime import date
from datetime import datetime

def rescale_frame(frame, percent=50):
    width = int(frame.shape[1] * percent/100)
    height = int(frame.shape[0] * percent/100)
    dim = (width, height)
    return cv2.resize(frame, dim, interpolation=cv2.INTER_AREA)


def grayscale_frame(imagine, cadru_curent):
    name_gray = './frames/frame' + str(cadru_curent) + '_gray.jpg'
    gray = cv2.cvtColor(imagine, cv2.COLOR_BGR2GRAY)
    cv2.imwrite(name_gray, gray)
    return gray


def filtru_zgomot(cadru_gri, cadru_curent):
    bfilter = cv2.bilateralFilter(cadru_gri, 11, 17, 17) # reduce zgomot
    edged = cv2.Canny(bfilter, 30, 200) # detectare margini
    cv2.imwrite('./frames/filtered' + str(cadru_curent) + '.jpg', edged)
    return edged

def gaseste_contur_placuta(edged):
    keypoints = cv2.findContours(edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contur = imutils.grab_contours(keypoints)
    contur = sorted(contur, key=cv2.contourArea, reverse=True)[:10]

    location = None
    for contour in contur:
        approx = cv2.approxPolyDP(contour, 10, True)
        if len(approx) == 4:
            location = approx
            break
    return location

filename = "Video for test.mp4"
whitelist = ["CA455822"]

video = cv2.VideoCapture(filename)
reader = easyocr.Reader(['en'])
bec_stins = cv2.imread('light_bulb_off.png')
bec_rosu = cv2.imread('light_bulb_red.png')
bec_albastru = cv2.imread('light_bulb_blue.png')
marime_bec = 100

bec_stins = cv2.resize(bec_stins, (marime_bec, marime_bec))
bec_rosu = cv2.resize(bec_rosu, (marime_bec, marime_bec))
bec_albastru = cv2.resize(bec_albastru, (marime_bec, marime_bec))
bec_curent = bec_stins

current_frame = 0
counter = 0
numere_de_inmatriculare = ['-']
caractere = [".",",","/","?",">","<",";",":","'","\"","\\","|","]","}",":","[","{","=","+","-","_",")","(","*",
            "&","^","%","$","#","@","!","~","`"," "]

font = cv2.FONT_HERSHEY_SIMPLEX

today_date = date.today().strftime("%d/%m/%y")
ore_identificare = ['-']

video_type = ''
if video != cv2.VideoCapture(filename):
    video_type = "Video File"
else:
    video_type = "Other type"

while video.isOpened():
    ret, frame = video.read()
    width = int(video.get(3))
    height = int(video.get(4))
    if ret == False:
        frame75 = cv2.putText(frame75, 'Press any key to exit!', (400, 400), font, 1, (0, 0, 0), 2, cv2.LINE_AA)
        cv2.imshow('Frame', frame75)
        cv2.waitKey(0)
        break
    frame75 = rescale_frame(frame)

    frame75[10:110, 70:170] = bec_curent

    if cv2.waitKey(25) & 0xFF == ord('q'):
        break

    if counter == 25:
        name = './frames/frame' + str(current_frame) + '.jpg'
        cv2.imwrite(name, frame75)
        gray = grayscale_frame(frame75,current_frame)
        edged = filtru_zgomot(gray, current_frame)
        locatie_placuta = gaseste_contur_placuta(edged)
        if locatie_placuta is not None:
            masca = np.zeros(gray.shape, np.uint8)
            new_image = cv2.drawContours(masca, [locatie_placuta], 0, 255, -1)
            new_image = cv2.bitwise_and(frame75, frame75, mask=masca)
            cv2.imwrite('./frames/masca' + str(current_frame) + '.jpg', new_image)
            (x, y) = np.where(masca==255)
            (x1, y1) = (np.min(x), np.min(y))
            (x2, y2) = (np.max(x), np.max(y))
            cropped_image = gray[x1:x2+1, y1:y2+1]
            cv2.imwrite('./frames/placuta' + str(current_frame) + '.jpg', cropped_image)
            rezultat = reader.readtext(cropped_image)
            if len(rezultat) > 0:
                tpl = rezultat[0]
                _, nr, _ = tpl
                for i in caractere:
                    nr = nr.replace(i, "")
                if len(nr) > 5:
                    numere_de_inmatriculare.append(nr)
                    if nr in whitelist:
                        bec_curent = bec_albastru
                        frame75[70:170, 70:170] = bec_curent
                ore_identificare.append(datetime.now().strftime("%H:%M:%S"))
        counter = 0

    frame75 = cv2.rectangle(frame75, (0, 0), (270, 150), (0, 0, 0), 1)
    frame75 = cv2.putText(frame75, "Numar detectat: " + numere_de_inmatriculare[-1], (10, 20),
                          font, .6, (0, 0, 0), 1, cv2.LINE_AA)
    frame75 = cv2.putText(frame75, "Data: " + today_date, (10, 40),
                          font, .6, (0, 0, 0), 1, cv2.LINE_AA)
    frame75 = cv2.putText(frame75, "Ora: " + ore_identificare[-1], (10, 60),
                          font, .6, (0, 0, 0), 1, cv2.LINE_AA)
    frame75 = cv2.putText(frame75, "Video Source: " + video_type, (10, 100),
                          font, .6, (0, 0, 0), 1, cv2.LINE_AA)
    frame75 = cv2.putText(frame75, f"Rezolutie: {str(width)}x{str(height)}", (10, 120),
                          font, .6, (0, 0, 0), 1, cv2.LINE_AA)
    frame75 = cv2.putText(frame75, f"Fisier: '{filename}'", (10, 140),
                          font, .6, (0, 0, 0), 1, cv2.LINE_AA)
    cv2.imshow('Frame', frame75)

    counter += 1
    current_frame += 1

video.release()
cv2.destroyAllWindows()
print('Numarul este: ',numere_de_inmatriculare)

#TODO alarma masina care nu este in baza de date
#TODO package in executabil

#TODO afisare beculet verde daca numarul se afla in baza de date, rosu daca masinii ii este interzis sa intre
#TODO si valori intre (whitelist si blacklist)

#TODO partea scrisa: de scris despre sisteme asemanatoare existente

