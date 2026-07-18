import cv2
import mediapipe as mp

from mediapipe.tasks import python
from mediapipe.tasks.python import vision


class GestureRecognizer:

    def __init__(self):

        options = vision.GestureRecognizerOptions(

            base_options=python.BaseOptions(
                model_asset_path="model/gesture_recognizer.task"
            ),

            running_mode=vision.RunningMode.VIDEO,

            num_hands=2

        )

        self.recognizer = vision.GestureRecognizer.create_from_options(options)

    def recognize(self, frame, timestamp):

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb
        )

        result = self.recognizer.recognize_for_video(
            mp_image,
            timestamp
        )

        return result
    