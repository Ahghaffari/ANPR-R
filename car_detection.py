import os
import numpy as np
import cv2 as cv
import cv2

from settings import *

#
# Car and plate detection classifier initialization
#
car_plate_classifier_threshold = 0.6

CAR_PLATE_LABELS = [
    "Iran",
    "IranTransit",
    "Turkey",
    "Iraq1",
    "Iraq2",
    "Car",
    "Truck",
    "Motorcycle",
    "Unknown",
]

np.random.seed(42)
car_plate_network = cv.dnn.readNetFromDarknet(os.path.join(WORKING_DIR, CAR_PLATE_DETECTION_CFG_PATH),
                                              os.path.join(WORKING_DIR, CAR_PLATE_DETECTION_WEIGHT_PATH))

if CPD_GPU:
    car_plate_network.setPreferableBackend(cv.dnn.DNN_BACKEND_CUDA)
    car_plate_network.setPreferableTarget(cv.dnn.DNN_TARGET_CUDA)

# determine the output layer
car_plate_layer_names = car_plate_network.getLayerNames()
car_plate_layer_names = [car_plate_layer_names[i[0] - 1] for i in car_plate_network.getUnconnectedOutLayers()]

#
# Car classifier initialization
#
# ToDo: Add car detection to another file to prevent runtime error when executing tracker without cd.cfg and cd.w
car_classifier_threshold = 0.1

CAR_LABELS = [
    'Truck',
    'Sedan'
]

np.random.seed(42)
car_network = cv.dnn.readNetFromDarknet(os.path.join(WORKING_DIR, CAR_DETECTION_CFG_PATH),
                                        os.path.join(WORKING_DIR, CAR_DETECTION_WEIGHT_PATH))
car_layer_names = car_network.getLayerNames()
car_layer_names = [car_layer_names[i[0] - 1] for i in car_network.getUnconnectedOutLayers()]

#
# Cascade plate detection model initialization
#
cascade_classifier = cv.CascadeClassifier(CASCADE_MODEL_PATH)


#
# Determine where two shapes having shared area or not
#
def car_plate_matched(x0, y0, w0, h0, x1, y1):
    if x0 <= x1 <= (x0 + w0) and y0 <= y1 <= (y0 + h0):
        return True
    return False


#
# Detect plate and cars from image
#
if TRACKER_PD_APPROACH == 1:
    def detect_car_and_plate(frame):
        plates = cascade_classifier.detectMultiScale(
            image=frame,
            scaleFactor=CASCADE_THR,
            minNeighbors=CASCADE_NEIGHBOUR,
            minSize=(CASCADE_MIN_SIZE_W, CASCADE_MIN_SIZE_H),
            maxSize=(CASCADE_MAX_SIZE_W, CASCADE_MAX_SIZE_H),
        )

        return plates
else:
    def detect_car_and_plate(gray):
        (H, W) = gray.shape[:2]

        blob = cv.dnn.blobFromImage(gray, 1 / 255.0, (512, 320), swapRB=True, crop=False)

        car_plate_network.setInput(blob)
        outputs = car_plate_network.forward(car_plate_layer_names)

        boxes = []
        confidences = []
        classIDs = []

        for output in outputs:
            for detection in output:
                scores = detection[5:]
                classID = np.argmax(scores)
                confidence = scores[classID]

                if confidence > car_plate_classifier_threshold:
                    box = detection[0:4] * np.array([W, H, W, H])
                    (centerX, centerY, width, height) = box.astype("int")
                    x = int(centerX - (width / 2))
                    y = int(centerY - (height / 2))
                    boxes.append([x, y, int(width), int(height)])
                    confidences.append(float(confidence))
                    classIDs.append(classID)

        idxs = cv.dnn.NMSBoxes(boxes, confidences, car_plate_classifier_threshold, CAR_PLATE_DETECTION_THR)

        plates = []
        # cars = []

        if len(idxs) > 0:
            # Classify cars and plate in separate lists
            for i in idxs.flatten():
                if classIDs[i] == 0:
                    (x, y) = (boxes[i][0], boxes[i][1])
                    (w, h) = (boxes[i][2], boxes[i][3])
                    plates.append([x, y, w, h, -1])
                # elif classIDs[i] == 5 or classIDs[i] == 6:
                #     (x, y) = (boxes[i][0], boxes[i][1])
                #     (w, h) = (boxes[i][2], boxes[i][3])
                #     cars.append([x, y, w, h, classIDs[i]])

            # Append related cars and plates together based on sharing region
            # for car in cars:
            #     for plate_idx in range(len(plates)):
            #         if car_plate_matched(car[0], car[1], car[2], car[3], plates[plate_idx][0], plates[plate_idx][1]):
            #             plates[plate_idx][4] = car[4] % 5

        return plates


#
# Detect cars from image
#
def detect_car_type(gray, x_plate, y_plate):
    gray = cv2.cvtColor(gray, cv2.COLOR_BGR2GRAY)
    (H, W) = gray.shape[:2]

    blob = cv.dnn.blobFromImage(gray, 1 / 255.0, (608, 384), swapRB=True, crop=False)

    car_network.setInput(blob)
    outputs = car_network.forward(car_layer_names)

    boxes = []
    confidences = []
    classIDs = []

    for output in outputs:
        for detection in output:
            scores = detection[5:]
            classID = np.argmax(scores)
            confidence = scores[classID]

            if confidence > car_classifier_threshold:
                box = detection[0:4] * np.array([W, H, W, H])
                (centerX, centerY, width, height) = box.astype("int")
                x = int(centerX - (width / 2))
                y = int(centerY - (height / 2))
                boxes.append([x, y, int(width), int(height)])
                confidences.append(float(confidence))
                classIDs.append(classID)

    indices = cv.dnn.NMSBoxes(boxes, confidences, car_classifier_threshold, CAR_DETECTION_THR)

    if len(indices) > 0:
        for i in indices.flatten():
            (x, y) = (boxes[i][0], boxes[i][1])
            (w, h) = (boxes[i][2], boxes[i][3])

            if x <= x_plate <= (x + w) and y_plate > y:
                if classIDs[i] == 0:
                    return 1
                elif classIDs[i] == 1:
                    return 0
    return -2
