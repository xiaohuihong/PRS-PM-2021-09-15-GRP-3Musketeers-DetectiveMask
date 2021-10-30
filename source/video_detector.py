import time
import numpy as np
import cv2
import imutils
from imutils.video import VideoStream
from tensorflow import keras
from tensorflow.python.keras.applications.mobilenet_v2 import preprocess_input
import os
import requests
import subprocess
import pathlib
from PIL import Image  
import PIL  
import matplotlib
import datetime

from source.utils import preprocess_face_frame, decode_prediction, write_bb, load_cascade_detector

#model = keras.models.load_model('F:\\NUS-ISS Intelligent Systems\\2. Pattern Recognition Systems\\Practice Module\\PRS-PM-2021-09-15-GRP-3Musketeers-DetectiveMask\\models\\mask_mobilenet.hdf5')
model_path = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath("__file__")), "..")) + "\\models\\mask_mobilenet.hdf5"
model = keras.models.load_model(model_path)
face_detector = load_cascade_detector()

tele_timerglob = datetime.datetime.now()



def video_mask_detector():
    # src=0, use system camera
    # src=1, use phone camera
    video = VideoStream(src=0).start()
    time.sleep(1.0)
    while True:
        # Capture frame-by-frame
        frame = video.read()
        frame = detect_mask_in_frame(frame)
        # Display the resulting frame
        # show the output frame
        cv2.imshow("Mask detector", frame)

        key = cv2.waitKey(1) & 0xFF
        # if the `q` key was pressed, break from the loop
        if key == ord("q"):
            break
    # cleanup
    cv2.destroyAllWindows()
    video.stop()


def detect_mask_in_frame(frame):
    frame = imutils.resize(frame, width=500)

    # convert an image from one color space to another
    # (to grayscale)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    faces = face_detector.detectMultiScale(gray,
                                           scaleFactor=1.1,
                                           minNeighbors=5,
                                           minSize=(40, 40),
                                           flags=cv2.CASCADE_SCALE_IMAGE,
                                           )

    faces_dict = {"faces_list": [],
                  "faces_rect": []
                  }

    for rect in faces:
        (x, y, w, h) = rect
        face_frame = frame[y:y + h, x:x + w]
        # preprocess image
        face_frame_prepared = preprocess_face_frame(face_frame)

        faces_dict["faces_list"].append(face_frame_prepared)
        faces_dict["faces_rect"].append(rect)

    if faces_dict["faces_list"]:
        faces_preprocessed = np.array(faces_dict["faces_list"])
        faces_preprocessed = faces_preprocessed.astype('float32')/255
        preds = model.predict(faces_preprocessed)

        for i, pred in enumerate(preds):
            mask_or_not, confidence = decode_prediction(pred)
            write_bb(mask_or_not, confidence, faces_dict["faces_rect"][i], frame)
        future_time = globals()['tele_timerglob'] + datetime.timedelta(seconds=30)
        time_now = datetime.datetime.now()

        if mask_or_not == 'No mask' and time_now >= future_time: 
            globals()['tele_timerglob']  = datetime.datetime.now()
            im = Image.fromarray(gray)
            im.save("tele.jpeg")
            files = {'photo' :open('tele.jpeg','rb')}
            text_to_post = "https://api.telegram.org/bot2082046165:AAHSgQj1eJB_9LapseXcFtR1EGslk0k99ig/sendPhoto?chat_id=-718206058&caption=No mask detected on " + str(datetime.datetime.now().strftime("%b %d %Y %H:%M:%S"))
            requests.post(text_to_post,files=files)
            
    return frame


if __name__ == '__main__':
    video_mask_detector()
