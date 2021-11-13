from base64 import b64encode
from io import BytesIO

import cv2
import numpy as np
from PIL import Image
from flask import render_template, Response, flash, request, send_from_directory
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from werkzeug.exceptions import abort
from werkzeug.utils import secure_filename
from wtforms import FileField, SubmitField
from app.main.__inti__ import main_bp
from app.main.camera import Camera
import urllib.request
import os

from source.test_new_images import detect_mask_in_image
from source.video_detector import detect_mask_in_frame

upload_path = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath("__file__")), "..\\PRS-PM-2021-09-15-GRP-3Musketeers-DetectiveMask-main")) + "\\app\\static\\uploads\\"

@main_bp.route("/")
def home_page():
    return render_template("home_page.html")


def gen(camera):

    while True:
        frame = camera.get_frame()
        frame_processed = detect_mask_in_frame(frame)
        frame_processed = cv2.imencode('.jpg', frame_processed)[1].tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_processed + b'\r\n')


@main_bp.route('/video_feed')
def video_feed():
    return Response(gen(
        Camera()
    ),
        mimetype='multipart/x-mixed-replace; boundary=frame')


@main_bp.route('/video-mask-detector')
def video_mask_detection():
    return render_template("video_detector.html",
                           form=VideoMaskForm())



def allowed_file(filename):
    ext = filename.split(".")[-1]
    is_good = ext in ["jpg", "jpeg", "png"]
    return is_good

@main_bp.route("/image-mask-detector", methods=["GET", "POST"])
def image_mask_detection():
    return render_template("image_detector.html",
                           form=PhotoMaskForm())


@main_bp.route("/image-processing", methods=["POST"])
def image_processing():
    form = PhotoMaskForm()

    if not form.validate_on_submit():
        flash("An error occurred", "danger")
        abort(Response("Error", 400))

    pil_image = Image.open(form.image.data)
    image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    array_image = detect_mask_in_image(image)
    rgb_image = cv2.cvtColor(array_image, cv2.COLOR_BGR2RGB)
    image_detected = Image.fromarray(rgb_image, 'RGB')

    with BytesIO() as img_io:
        image_detected.save(img_io, 'PNG')
        img_io.seek(0)
        base64img = "data:image/png;base64," + b64encode(img_io.getvalue()).decode('ascii')
        return base64img


# form
class PhotoMaskForm(FlaskForm):
    image = FileField('Choose image:',
                      validators=[
                          FileAllowed(['jpg', 'jpeg', 'png'], 'The allowed extensions are: .jpg, .jpeg and .png')])

    submit = SubmitField('Detect mask')
    
# form
class VideoMaskForm(FlaskForm):
    image = FileField('Choose video:',
                      validators=[
                          FileAllowed(['mp4'], 'The allowed extensions are: .mp4')])

    submit = SubmitField('Detect mask')
 
 
@main_bp.route('/video-processing', methods=['POST', 'GET'])
def upload_video():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No image selected for uploading')
            return redirect(request.url)
        else:
            filename = secure_filename(file.filename)
            file.save(os.path.join(upload_path, 'update2.mp4'))
            #static_video_mask_detector(os.path.join(upload_path, filename))
            #flash('Video successfully uploaded and displayed below')
            return render_template('video_detector.html', filename=filename)
    else:
        return render_template('video_detector.html')
        
@main_bp.route('/video_feed_two')
def video_feed_two():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


def gen_frames(): 
    vid_cap= cv2.VideoCapture(os.path.join(upload_path, 'update2.mp4'))
    fps = vid_cap.get(cv2.CAP_PROP_FPS)
    w = int(vid_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(vid_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    while(vid_cap.isOpened()):
        ret, frame = vid_cap.read()
        if ret == False:
            break;
        
        frame_processed = detect_mask_in_frame(frame)
        frame_processed = cv2.imencode('.jpg', frame_processed)[1].tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_processed + b'\r\n')
        key = cv2.waitKey(1) & 0xFF
        # if the `q` key was pressed, break from the loop
        if key == ord("q"):
            break
    vid_cap.release()
    cv2.destroyAllWindows()
    

