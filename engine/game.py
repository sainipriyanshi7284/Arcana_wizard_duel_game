import cv2
from vision.camera import Camera

from vision.mediapipe_tracker import HandTracker
import time


class Game:
    def __init__(self):
        self.camera = Camera()
        self.prev_time=0
        self.start_time=time.time()
        self.hand_tracker = HandTracker()

   

    def display_text(self,frame):
         self.camera.get_dimensions()

         current_time=time.time()
         if current_time-self.start_time <10:
              cv2.putText(frame,"WELCOME TO ARCANA",
                          (170,50),cv2.FONT_HERSHEY_COMPLEX,
                          1.0,(0,0,225),5)
         cv2.putText(frame,"PRESS Q TO QUIT",
                      (10,470),cv2.FONT_HERSHEY_COMPLEX_SMALL,
                      0.5,(0,0,225),2)
         return frame
    
    def display_fps(self,frame):
        current_time=time.time()

        fps=1/(current_time-self.prev_time)

        self.prev_time=current_time

        cv2.putText(frame,f"FPS = {int(fps)}",
                    (600,470),cv2.FONT_HERSHEY_COMPLEX_SMALL,
                     0.5,(0,0,225),2)

        return frame
    
    def divide_frame(self,frame):
        w,h =self.camera.get_dimensions()
        cv2.line(frame,(w//2,0),(w//2,h),(0,0,225),5)
        return frame

    def run(self):
        if not self.camera.open_camera():
            return
        
        width, height = self.camera.get_dimensions()
        print(f"Camera Resolution : {width} x {height}")

        while True:
            frame = self.camera.get_frame()
            if frame is None:
                print("Error: Failed to capture frame.")
                break

            timestamp = int(time.time() * 1000)
            frame = cv2.flip(frame, 1)

            result = self.hand_tracker.process_frame(frame,timestamp)
            frame = self.hand_tracker.draw_connections(frame,result)
            frame = self.hand_tracker.draw_landmarks(frame, result)

            frame = self.display_text(frame)
            frame = self.display_fps(frame)
            frame=self.divide_frame(frame)

            cv2.imshow("ARCANA", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
        self.camera.release_camera()