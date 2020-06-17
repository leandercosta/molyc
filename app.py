import numpy as np
import cv2 as cv
import Person
import time



import sqlite3

from sqlite3 import Error

# CONFIG DO CLIENTE

clientId = 234
spotId = 1

# CONFIG DO CLIENTE


# CONFIG BASE LOCAL

try:
    sqliteConnection = sqlite3.connect('data/5M3HJPZC7SU.sqlite') #VARIA DE ACORDO COM O CLIENTE
    sqliteConnection.execute('pragma journal_mode=wal')
    cursor = sqliteConnection.cursor()
    print("CONNECTED TO DB")
except:
    print("SQLITE ERROR")

# CONFIG BASE LOCAL


# ESCRITA LOG

try:
    log = open('log.txt',"w")
except:
    print( "ERRO AO LER O LOG")

# ESCRITA LOG


# CONTADORES INICIAIS

cnt_up   = 0
cnt_down = 0

# CONTADORES INICIAIS


cap = cv.VideoCapture(0)
#cap = cv.VideoCapture('sample.mp4')
kernel = np.ones((5,5), np.uint8)
key = True


for i in range(19):
    print( i, cap.get(i))

h = 480
w = 640
frameArea = h*w
areaTH = frameArea/250
print( 'Threshold', areaTH)

#line_up = int(2*(h/5))
#line_down   = int(3*(h/5))

line_up = 200
line_down = 230

up_limit = 140
down_limit = 290

#up_limit =   int(1*(h/5))
#down_limit = int(4*(h/5))

print( "ENTRADA:",str(line_down))
print( "SAIDA:", str(line_up))
line_down_color = (255,0,0)
line_up_color = (0,0,255)
pt1 =  [0, line_down];
pt2 =  [w, line_down];
pts_L1 = np.array([pt1,pt2], np.int32)
pts_L1 = pts_L1.reshape((-1,1,2))
pt3 =  [0, line_up];
pt4 =  [w, line_up];
pts_L2 = np.array([pt3,pt4], np.int32)
pts_L2 = pts_L2.reshape((-1,1,2))

pt5 =  [0, up_limit];
pt6 =  [w, up_limit];
pts_L3 = np.array([pt5,pt6], np.int32)
pts_L3 = pts_L3.reshape((-1,1,2))
pt7 =  [0, down_limit];
pt8 =  [w, down_limit];
pts_L4 = np.array([pt7,pt8], np.int32)
pts_L4 = pts_L4.reshape((-1,1,2))

fgbg = cv.createBackgroundSubtractorMOG2(detectShadows = True)

kernelOp = np.ones((3,3),np.uint8)
kernelOp2 = np.ones((5,5),np.uint8)
kernelCl = np.ones((11,11),np.uint8)

font = cv.FONT_HERSHEY_SIMPLEX
persons = []
max_p_age = 5
pid = 1

while(cap.isOpened()):
    ret, frame = cap.read()

    for i in persons:
        i.age_one() 
    
    fgmask = fgbg.apply(frame)
    fgmask2 = fgbg.apply(frame)

    try:
        ret,imBin= cv.threshold(fgmask,200,255,cv.THRESH_BINARY)
        ret,imBin2 = cv.threshold(fgmask2,200,255,cv.THRESH_BINARY)
        mask = cv.morphologyEx(imBin, cv.MORPH_OPEN, kernelOp)
        mask2 = cv.morphologyEx(imBin2, cv.MORPH_OPEN, kernelOp)
        mask =  cv.morphologyEx(mask , cv.MORPH_CLOSE, kernelCl)
        mask2 = cv.morphologyEx(mask2, cv.MORPH_CLOSE, kernelCl)
    except:
        print('EOF')
        print( 'UP:',cnt_up)
        print ('DOWN:',cnt_down)
        break
    
    _, contours0, hierarchy = cv.findContours(mask2,cv.RETR_EXTERNAL,cv.CHAIN_APPROX_SIMPLE)
    for cnt in contours0:
        area = cv.contourArea(cnt)
        if area > areaTH:
            
            M = cv.moments(cnt)
            cx = int(M['m10']/M['m00'])
            cy = int(M['m01']/M['m00'])
            x,y,w,h = cv.boundingRect(cnt)

            new = True
            if cy in range(up_limit,down_limit):
                for i in persons:
                    if abs(x-i.getX()) <= w and abs(y-i.getY()) <= h:
                        new = False
                        i.updateCoords(cx,cy)   #actualiza coordenadas en el objeto and resets age
                        if i.going_UP(line_down,line_up) == True:
                            cnt_up += 1;
                            print( "ID:",i.getId(),'ENTRADA',time.strftime("%c"))
                            log.write("ID: "+str(i.getId())+' ENTRADA' + time.strftime("%c") + '\n')

                            count = cursor.execute("INSERT INTO logs (clientId, spotId, actionId, status, datetime) values (?,?,?,?,?)",(clientId, spotId, 1, 0, time.strftime("%c")))
                            sqliteConnection.commit()
                            print("GRAVADO!", cursor.rowcount)

                        elif i.going_DOWN(line_down,line_up) == True:
                            cnt_down += 1;
                            print( "ID:",i.getId(),'SAIDA',time.strftime("%c"))
                            log.write("ID: " + str(i.getId()) + 'SAIDA' + time.strftime("%c") + '\n')

                            count = cursor.execute("INSERT INTO logs (clientId, spotId, actionId, status, datetime) values (?,?,?,?,?)",(clientId, spotId, 0, 0, time.strftime("%c")))
                            sqliteConnection.commit()
                            print("GRAVADO!", cursor.rowcount)

                        break
                    if i.getState() == '1':
                        if i.getDir() == 'down' and i.getY() > down_limit:
                            i.setDone()
                        elif i.getDir() == 'up' and i.getY() < up_limit:
                            i.setDone()
                    if i.timedOut():
                        index = persons.index(i)
                        persons.pop(index)
                        del i     #liberar la memoria de i
                if new == True:
                    p = Person.MyPerson(pid,cx,cy, max_p_age)
                    persons.append(p)
                    pid += 1     
            cv.circle(frame,(cx,cy), 5, (0,0,255), -1)
          #   img = cv.rectangle(frame,(x,y),(x+w,y+h),(0,255,0),2)            
            
    for i in persons:
        cv.putText(frame, str(i.getId()),(i.getX(),i.getY()),font,0.3,i.getRGB(),1,cv.LINE_AA)
        
    str_up = 'ENTRADA: '+ str(cnt_up)
    str_down = 'SAIDA: '+ str(cnt_down)
    frame = cv.polylines(frame,[pts_L1],False,line_down_color,thickness=2)
    frame = cv.polylines(frame,[pts_L2],False,line_up_color,thickness=2)
    frame = cv.polylines(frame,[pts_L3],False,(255,255,255),thickness=1)
    frame = cv.polylines(frame,[pts_L4],False,(255,255,255),thickness=1)
    cv.putText(frame, str_up ,(10,40),font,0.7,(255,255,255),1,cv.LINE_AA)
    cv.putText(frame, str_down ,(10,90),font,0.7,(255,255,255),1,cv.LINE_AA)

    cv.imshow('Frame',frame)
    cv.imshow('Mask',mask)    
    

    k = cv.waitKey(30) & 0xff
    if k == 27:
        break

log.flush()
log.close()
cap.release()
cv.destroyAllWindows()
