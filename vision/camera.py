import cv2

class Camera:
    cap:int
    def __init__(self):
        index=0
        self.cap = cv2.VideoCapture(index)
    
    def open_camera(self):
        if not self.cap.isOpened():
            print("Error in opening the camera")
            return False
        else:
            return True

    def get_frame(self):
            ret,frame =self.cap.read()
            if ret is not True:
               return None
            
            return frame

    def release_camera(self):
        self.cap.release()
        cv2.destroyAllWindows()

    def get_dimensions(self):
        frame_width=int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height=int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        return frame_width,frame_height
    
