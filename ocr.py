import datetime
import os
import sys
import time
import pika
import cv2
import threading
import numpy as np
import textdistance

from settings import *
from registery import get_reg, set_reg
from tables import save_into_database
import activation
from lane_detection import determine_lane_and_update_speed

try:
    activation_state = get_reg("StopOCRTemp1")

    is_activated = False
    if int(activation_state) == 1:
        is_activated = True
    else:
        serial = activation.SerialNumber()
        is_activated, uuid, did = serial.check_activation_status(type='R')

        if is_activated is True:
            set_reg("StopOCRTemp1", "1")

    if is_activated is False:
        print("[  INFO  ] Device is not activated.")
        print("[  INFO  ] Device ID:", uuid)
        print("[  INFO  ] In order to activate this device, please call Fard Iran.")
        time.sleep(30)
        sys.exit()
    else:
        print("[  INFO  ] Device is activated. Device ID:", uuid)

except ValueError as e:
    print("[  EROR  ]", e)
    time.sleep(30)
    sys.exit()

CARS_QUEUE = []
lock = threading.RLock()
exit_event = threading.Event()

# Load character model
char_model = cv2.dnn.readNetFromONNX(CHAR_MODEL_WEIGHT_PATH)

# Load number model
num_model = cv2.dnn.readNetFromONNX(NUM_MODEL_WEIGHT_PATH)

config_path = os.path.abspath(SEGMENTATION_CONFIG)
weights_path = os.path.abspath(SEGMENTATION_WEIGHTS)

yolo_network = cv2.dnn.readNetFromDarknet(config_path, weights_path)

bad_plate = cv2.imread(BAD_PLATE_TEMPLATE_PATH, 0)

# Plate detection model initialization
plate_cascade = cv2.CascadeClassifier(CASCADE_MODEL_PATH)

# if SEND2FRONT:
#     # Declare the queue
#     print("[  INFO  ] Declaring FRONT-END queue")
#     front_channel = connection.channel()
#     front_channel.queue_declare(queue='frontend')
#
# if SEND2WIM:
#     # Declare the queue
#     print("[  INFO  ] Declaring WIM queue")
#     wim_channel = connection.channel()
#     wim_channel.queue_declare(queue='wim')


# Configuring logging format
class Logger(object):
    def __init__(self):
        self.terminal = sys.stdout
        self.log = open("ocr.log", "a")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

    def flush(self):
        # this flush method is needed for python 3 compatibility.
        # this handles the flush command by doing nothing.
        # you might want to specify some extra behavior here.
        pass


sys.stdout = Logger()


def segment_plate(image, network, threshold):
    try:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        (H, W) = image.shape[:2]
    except:
        return [], []

    ln = network.getLayerNames()
    ln = [ln[i[0] - 1] for i in network.getUnconnectedOutLayers()]

    blob = cv2.dnn.blobFromImage(image, 1 / 255.0, (512, 128), swapRB=True, crop=False)
    network.setInput(blob)

    layerOutputs = network.forward(ln)

    boxes = []
    confidences = []
    classIDs = []

    for output in layerOutputs:
        for detection in output:
            scores = detection[5:]
            classID = np.argmax(scores)
            confidence = scores[classID]
            if confidence > threshold:
                box = detection[0:4] * np.array([W, H, W, H])
                (centerX, centerY, width, height) = box.astype("int")
                x = int(centerX - (width / 2))
                y = int(centerY - (height / 2))
                boxes.append([x, y, int(width), int(height)])
                confidences.append(float(confidence))
                classIDs.append(classID)
    idxs = cv2.dnn.NMSBoxes(boxes, confidences, threshold, 0.3)

    aa = []
    if len(idxs) > 0:
        # loop over the indexes we are keeping
        for i in idxs.flatten():
            # extract the bounding box coordinates
            (x, y) = (boxes[i][0], boxes[i][1])
            (w, h) = (boxes[i][2], boxes[i][3])

            a = [
                int(classIDs[i]),
                confidences[i],
                boxes[i][0],
                boxes[i][1],
                boxes[i][2],
                boxes[i][3],
            ]

            aa.append(a)
    else:
        return [], []

    aa = np.array(aa)
    sorted_array = aa[np.argsort(aa[:, 2])]
    croped_image = []

    for i in range(len(sorted_array)):
        row1 = int(sorted_array[i, 3]) - 1
        if row1 < 0:
            row1 = 0

        row2 = int(sorted_array[i, 3] + sorted_array[i, 5] + 1)
        if row2 >= H:
            row2 = H - 1

        col1 = int(sorted_array[i, 2]) - 1
        if col1 < 0:
            col1 = 0

        col2 = int(sorted_array[i, 2] + sorted_array[i, 4] + 1)
        if col2 >= W:
            col2 = W - 1

        croped_image.append(
            image[row1: row2, col1: col2]
        )

    return croped_image, sorted_array


def predict_number(im):
    # K.set_session
    im = im / 255.0
    try:
        im = cv2.resize(im, (28, 28))
        image2 = im.reshape(-1, 28, 28, 1)
        num_model.setInput(image2)
        ynew = num_model.forward()
        lab = ynew.argmax()
    except:
        return "?", 0
    return lab, ynew[0][lab]


def predict_character(im):
    # K.set_session
    im = im / 255.0
    try:
        im = cv2.resize(im, (28, 28))
        image2 = im.reshape(-1, 28, 28, 1)
        char_model.setInput(image2)
        ynew = char_model.forward()
        lab = ynew.argmax()
    except:
        return "?", 0
    return CHAR_DIC[lab], ynew[0][lab]


def translate_plate(plate_image):
    cropped_image, sorted_array = segment_plate(plate_image, network=yolo_network, threshold=0.3)

    segmentation_succeed = True
    if len(cropped_image) < 8:
        cropped_image, sorted_array = segment_plate(plate_image, network=yolo_network, threshold=0.1)

    elif len(cropped_image) > 8:
        cropped_image, sorted_array = segment_plate(plate_image, network=yolo_network, threshold=0.6)

    if len(cropped_image) != 8:
        segmentation_succeed = False

    digits = []
    confidences = []

    if segmentation_succeed:
        digit, conf = predict_number(cropped_image[0])
        digits.append(digit)
        confidences.append(conf)
        digit, conf = predict_number(cropped_image[1])
        digits.append(digit)
        confidences.append(conf)
        digit, conf = predict_character(cropped_image[2])
        digits.append(digit)
        confidences.append(conf)
        digit, conf = predict_number(cropped_image[3])
        digits.append(digit)
        confidences.append(conf)
        digit, conf = predict_number(cropped_image[4])
        digits.append(digit)
        confidences.append(conf)
        digit, conf = predict_number(cropped_image[5])
        digits.append(digit)
        confidences.append(conf)
        digits.append("_")
        confidences.append(1)
        digit, conf = predict_number(cropped_image[6])
        digits.append(digit)
        confidences.append(conf)
        digit, conf = predict_number(cropped_image[7])
        digits.append(digit)
        confidences.append(conf)
    else:
        print("[  WARN  ] Bad number of segments to OCR. Segments: ", len(cropped_image))
        indicators = sorted_array[:, 0]

        for idx in range(0, len(indicators)):
            if indicators[idx] > 0:
                digit, conf = predict_number(cropped_image[idx])
                digits.append(digit)
            else:
                digit, conf = predict_character(cropped_image[idx])
                digits.append(digit)

        plate_string = ''.join(str(x) for x in digits)
        return plate_string, [], False

    plate_string = ''.join(str(x) for x in digits)

    if plate_string.find("?") != -1:
        return plate_string, [], False

    if LOCATION == "GORGAN":
        if (plate_string[7] == '6' or plate_string[7] == '5') and plate_string[8] == '1':
            plate_string[8] = '9'

        for ite in range(8):
            if plate_string[ite] == '0':
                plate_string[ite] = '9'

    return plate_string, confidences, True


def process_recent_cars_queue():
    global CARS_QUEUE

    while True:
        if exit_event.is_set():
            break

        with lock:
            for ite in range(len(CARS_QUEUE)):
                if (time.time() - CARS_QUEUE[ite][5]) > 5:
                    final_plate = CARS_QUEUE[ite][0]
                    only_name = CARS_QUEUE[ite][9]
                    cap_time = CARS_QUEUE[ite][15]
                    line_status = CARS_QUEUE[ite][6]
                    speed = CARS_QUEUE[ite][7]
                    frame = CARS_QUEUE[ite][10]
                    plate_image = CARS_QUEUE[ite][11]
                    frame_side = CARS_QUEUE[ite][12]
                    is_ocr_succeed = CARS_QUEUE[ite][13]
                    is_bad_plate = CARS_QUEUE[ite][14]
                    directory = CARS_QUEUE[ite][17]
                    side_dir = CARS_QUEUE[ite][18]
                    filename = CARS_QUEUE[ite][19]
                    reg_counter = CARS_QUEUE[ite][20]
                    car_type = CARS_QUEUE[ite][21]
                    CARS_QUEUE[ite][16] = 1

                    if not os.path.exists(OUT_MOTION + only_name[8:10]):
                        os.mkdir(OUT_MOTION + only_name[8:10])

                    if not os.path.exists(OUT_MOTION + "/" + only_name[8:10] + "/" + only_name[11:13]):
                        os.mkdir(OUT_MOTION + "/" + only_name[8:10] + "/" + only_name[11:13])

                    if DEPLOY:
                        if is_ocr_succeed:
                            out_filename = only_name + "-" + final_plate + "-o" + ".jpg"
                            save_into_database(cap_time, final_plate, "O", line_status,
                                               "%s%s" % ("", OUT_MOTION + only_name[8:10] + "/" + only_name[
                                                                                                  11:13] + "/") + out_filename,
                                               "%s%s" % ("", OUT_OCR) + out_filename,
                                               "%s%s" % ("", OUT_SIDE) + out_filename,
                                               speed, WIM_ID, reg_counter, reg_counter, car_type)

                            # frame = cv2.resize(frame, (OUT_FRAME_WIDTH, OUT_FRAME_HEIGHT))
                            frame[0:plate_image.shape[0], 0:plate_image.shape[1]] = plate_image
                            cv2.imwrite(OUT_MOTION + only_name[8:10] + "/" + only_name[11:13] + "/" + out_filename,
                                        frame[:, :, 0], [cv2.IMWRITE_PNG_COMPRESSION, 0])

                            if frame_side is not None:
                                # frame_side = cv2.resize(frame_side, (OUT_FRAME_WIDTH, OUT_FRAME_HEIGHT))
                                cv2.imwrite(OUT_SIDE + out_filename, frame_side,
                                            [cv2.IMWRITE_PNG_COMPRESSION, 0])

                            if plate_image.shape[0] != 0 and plate_image.shape[1] != 0:
                                cv2.imwrite(OUT_OCR + out_filename, plate_image[:, :, 0],
                                            [cv2.IMWRITE_PNG_COMPRESSION, 0])

                        elif is_bad_plate:
                            out_filename = only_name + "-" + final_plate + "-p" + ".jpg"

                            save_into_database(cap_time, final_plate, "P", line_status,
                                               "%s%s" % ("", OUT_MOTION + only_name[8:10] + "/" + only_name[
                                                                                                  11:13] + "/") + out_filename,
                                               "%s%s" % ("", OUT_OCR) + out_filename,
                                               "%s%s" % ("", OUT_SIDE) + out_filename,
                                               speed, WIM_ID, reg_counter, reg_counter, car_type)

                            # frame = cv2.resize(frame, (OUT_FRAME_WIDTH, OUT_FRAME_HEIGHT))
                            frame[0:plate_image.shape[0], 0:plate_image.shape[1]] = plate_image
                            cv2.imwrite(OUT_MOTION + only_name[8:10] + "/" + only_name[11:13] + "/" + out_filename,
                                        frame[:, :, 0], [cv2.IMWRITE_PNG_COMPRESSION, 0])

                            if frame_side is not None:
                                # frame_side = cv2.resize(frame_side, (OUT_FRAME_WIDTH, OUT_FRAME_HEIGHT))
                                cv2.imwrite(OUT_SIDE + out_filename, frame_side, [cv2.IMWRITE_PNG_COMPRESSION, 0])

                            if plate_image.shape[0] != 0 and plate_image.shape[1] != 0:
                                cv2.imwrite(OUT_OCR + out_filename, plate_image[:, :, 0],
                                            [cv2.IMWRITE_PNG_COMPRESSION, 0])

                        else:
                            out_filename = only_name + "-" + final_plate + "-p" + ".jpg"

                            save_into_database(cap_time, final_plate, "N", line_status,
                                               "%s%s" % ("", OUT_MOTION + only_name[8:10] + "/" + only_name[
                                                                                                  11:13] + "/") + out_filename,
                                               "%s%s" % ("", OUT_OCR) + out_filename,
                                               "%s%s" % ("", OUT_SIDE) + out_filename,
                                               speed, WIM_ID, reg_counter, reg_counter, car_type)

                            # frame = cv2.resize(frame, (OUT_FRAME_WIDTH, OUT_FRAME_HEIGHT))
                            frame[0:bad_plate.shape[0], 0:bad_plate.shape[1], 0] = bad_plate
                            cv2.imwrite(OUT_MOTION + only_name[8:10] + "/" + only_name[11:13] + "/" + out_filename,
                                        frame[:, :, 0], [cv2.IMWRITE_PNG_COMPRESSION, 0])

                            if frame_side is not None:
                                # frame_side = cv2.resize(frame_side, (OUT_FRAME_WIDTH, OUT_FRAME_HEIGHT))
                                cv2.imwrite(OUT_SIDE + out_filename, frame_side, [cv2.IMWRITE_PNG_COMPRESSION, 0])

                            cv2.imwrite(OUT_OCR + out_filename, frame[:, :, 0], [cv2.IMWRITE_PNG_COMPRESSION, 0])

                        try:
                            # Sending message to the frontend
                            # if SEND2FRONT:
                            #     image_file_name = OUT_SIDE + out_filename
                            #     message = "{}|{}|{}|{}|{}|{}|{}".format("ocr",
                            #                                             image_file_name,
                            #                                             final_plate,
                            #                                             line_status,
                            #                                             car_type,
                            #                                             cap_time,
                            #                                             speed)
                            #
                            #     front_channel.basic_publish(exchange='',
                            #                                 routing_key='frontend',
                            #                                 body=message.encode('utf8'),
                            #                                 properties=pika.BasicProperties(expiration='5000', )
                            #                                 )

                            os.remove(directory + filename)
                            if side_dir is not None:
                                os.remove(side_dir + filename)
                        except:
                            print("[  WARN  ] File not found to delete", filename)

            temporary = [s for s in CARS_QUEUE if s[16] == 0]
            CARS_QUEUE = temporary

        time.sleep(2)


def similar(a, b):
    return textdistance.hamming.normalized_similarity(a, b)
    # return SequenceMatcher(None, a, b).ratio()


def process_image_file(directory, filename, speed, car_number, x, y, w, h, seen_time_epoch, side_dir, lane_id,
                       reg_counter, has_side_image, car_type):
    global CARS_QUEUE

    confident = 0

    if speed is None:
        speed = SPEED_AVG_FOR_BYPASS_EXCEPTIONS
    else:
        try:
            speed = int(float(speed))
        except ValueError:
            speed = SPEED_AVG_FOR_BYPASS_EXCEPTIONS

    is_ocr_succeed = False
    is_bad_plate = False

    # Read frame
    frame = cv2.imread(directory + filename)
    if frame is None:
        print("[  EROR  ] File not found!!!")
        return

    # Read side image
    if has_side_image == 1:
        frame_side = cv2.imread(side_dir + filename)
    else:
        print("[  WARN  ] Side frame not found!!!")
        frame_side = frame

    # Logging to output
    track_time = time.strftime('%Y-%m-%d-%H-%M-%S', time.localtime(seen_time_epoch))
    print("[  INFO  ] {} {}".format(filename, track_time))

    # Select useful part of image
    if OCR_POST_PROCESS_PLATE is False:
        plate_image = frame[y:y + h, x:x + w + 10]
    else:
        yy = y - 50
        xx = x - 50
        ww = w + 50
        hh = h + 100

        plateSample = frame[yy:(yy + hh), xx:(xx + ww)]

        plate = plate_cascade.detectMultiScale(
            image=plateSample,
            scaleFactor=1.15,
            minNeighbors=3,
            minSize=(65, 13),
            maxSize=(200, 90),
        )

        if len(plate) > 0 and plate[0][1] is not None:
            xx = plate[0][0]
            yy = plate[0][1]
            ww = plate[0][2]
            hh = plate[0][3]

            plate_image = plateSample[yy - 5:yy + hh + 5, xx - 5:xx + ww + 40]
        else:
            plate_image = frame[y:y + h, x:x + w + 10]

    if plate_image is not None:
        cap_time = datetime.datetime.fromtimestamp(seen_time_epoch).isoformat()
        cap_time = cap_time[:-3]

        if plate_image.shape[0] != 0 and plate_image.shape[1] != 0:
            plate_image = cv2.resize(plate_image, (280, 85))

        try:
            final_plate, confident, is_ocr_succeed = translate_plate(plate_image)
        except:
            final_plate = "00#000_00"

        if is_ocr_succeed is False:
            for counter in range(1, 4):
                temporary_plate_image = plate_image / 255

                if counter == 3:
                    temporary_plate_image = temporary_plate_image ** (1 / 2)
                else:
                    temporary_plate_image = temporary_plate_image ** counter

                temporary_plate_image = (temporary_plate_image * 255)
                temporary_plate_image = np.array(temporary_plate_image, dtype='uint8')

                try:
                    final_plate, confident, is_ocr_succeed = translate_plate(temporary_plate_image)
                except:
                    final_plate = "00#000_00"

                if is_ocr_succeed:
                    if counter == 1:
                        print("[  INFO  ] Car image success")
                    elif counter == 2:
                        print("[  INFO  ] Power image success")

                    break
                else:
                    is_bad_plate = True

        # Determining plate position
        if x is not None:
            line_status, speed, car_type = determine_lane_and_update_speed(x=x,
                                                                           y=y,
                                                                           w=w,
                                                                           h=h,
                                                                           speed=speed,
                                                                           frame=frame)

            # if SEND2WIM:
            #     message = "{}|{}|{}".format(seen_time_epoch, line_status, reg_counter)
            #     wim_channel.basic_publish(exchange='', routing_key='wim', body=message.encode('utf8'))

            if SHOW_LINES:
                tFrame = cv2.line(frame, (ROAD_L1P1_X, int(ROAD_L1_A * ROAD_L1P1_X + ROAD_L1_B)),
                                  (ROAD_L1P2_X, int(ROAD_L1_A * ROAD_L1P2_X + ROAD_L1_B)), (0, 0, 0), 6)
                tFrame = cv2.line(tFrame, (ROAD_L2P1_X, int(ROAD_L2_A * ROAD_L2P1_X + ROAD_L2_B)),
                                  (ROAD_L2P2_X, int(ROAD_L2_A * ROAD_L2P2_X + ROAD_L2_B)), (0, 0, 0), 6)
                tFrame = cv2.line(tFrame, (ROAD_L3P1_X, int(ROAD_L3_A * ROAD_L3P1_X + ROAD_L3_B)),
                                  (ROAD_L3P2_X, int(ROAD_L3_A * ROAD_L3P2_X + ROAD_L3_B)), (0, 0, 0), 6)
                tFrame = cv2.line(tFrame, (ROAD_L4P1_X, int(ROAD_L4_A * ROAD_L4P1_X + ROAD_L4_B)),
                                  (ROAD_L4P2_X, int(ROAD_L4_A * ROAD_L4P2_X + ROAD_L4_B)), (0, 0, 0), 6)
                tFrame = cv2.line(tFrame, (ROAD_C1P1_X, int(ROAD_C1_A * ROAD_C1P1_X + ROAD_C1_B)),
                                  (ROAD_C1P2_X, int(ROAD_C1_A * ROAD_C1P2_X + ROAD_C1_B)), (0, 0, 0), 6)
                tFrame = cv2.line(tFrame, (ROAD_C2P1_X, int(ROAD_C2_A * ROAD_C2P1_X + ROAD_C2_B)),
                                  (ROAD_C2P2_X, int(ROAD_C2_A * ROAD_C2P2_X + ROAD_C2_B)), (0, 0, 0), 6)
                tFrame = cv2.putText(tFrame, line_status, (1720, 100), cv2.FONT_HERSHEY_SIMPLEX, 4, (0, 0, 0), 10,
                                     cv2.LINE_AA)
                cv2.imshow("LANES", cv2.resize(tFrame, None, fx=1 / 3, fy=1 / 3))
                cv2.waitKey(1)

    is_new_car = True
    need_for_update = False

    only_name = track_time + "-" + line_status

    try:
        min_conf = np.min(confident)
    except:
        min_conf = 0

    for ite in range(len(CARS_QUEUE)):
        # Check for duplicate plate
        if is_ocr_succeed and final_plate == CARS_QUEUE[ite][0]:
            print("[  WARN  ] Duplicate plate detected. Plate: ", final_plate)
            is_new_car = False

            try:
                os.remove(directory + filename)
                if side_dir is not None:
                    os.remove(side_dir + filename)
            except:
                print("[  WARN  ] File not found to delete", filename)

            break

        # Check for similar plates
        elif is_ocr_succeed and similar(final_plate, CARS_QUEUE[ite][0]) >= OCR_SIMILARITY_RATIO:
            print("[  WARN  ] Similar plates detected. Plate: {}, Similar: {}".format(final_plate, CARS_QUEUE[ite][0]))
            is_new_car = False

            try:
                os.remove(directory + filename)
                if side_dir is not None:
                    os.remove(side_dir + filename)
            except:
                print("[  WARN  ] File not found to delete", filename)

            break

            # ToDo: Find a good solution to update CARS_QUEUE in similar plates condition
            # This section commented till I make a good solution in order to update CARS_QUEUE when it is accessing by
            # two separate threads
            # if min_conf > CARS_QUEUE[ite][22]:
            #     CARS_QUEUE[ite] = [final_plate,
            #                        x,
            #                        y,
            #                        w,
            #                        h,
            #                        seen_time_epoch,
            #                        line_status,
            #                        speed,
            #                        WIM_ID,
            #                        only_name,
            #                        frame,  # 10
            #                        plate_image,  # 11
            #                        frame_side,  # 12
            #                        is_ocr_succeed,
            #                        is_bad_plate,
            #                        cap_time,
            #                        0,
            #                        directory,
            #                        side_dir,
            #                        filename,
            #                        reg_counter,
            #                        car_type,
            #                        min_conf]
            # else:
            #     try:
            #         os.remove(directory + filename)
            #         if side_dir is not None:
            #             os.remove(side_dir + filename)
            #     except:
            #         print("[  WARN  ] File not found to delete", filename)
            #
            # break

    if is_new_car:
        with lock:
            CARS_QUEUE.append([final_plate,
                               x,
                               y,
                               w,
                               h,
                               seen_time_epoch,
                               line_status,
                               speed,
                               WIM_ID,
                               only_name,
                               frame,  # 10
                               plate_image,  # 11
                               frame_side,  # 12
                               is_ocr_succeed,
                               is_bad_plate,
                               cap_time,
                               0,
                               directory,
                               side_dir,
                               filename,
                               reg_counter,
                               car_type,
                               min_conf])


def on_message_received(msg):
    decoded_message = msg.decode('utf-8').split("|")

    print("[  INFO  ] Received message: ", decoded_message[1])

    process_image_file(directory=decoded_message[0],
                       filename=decoded_message[1],
                       speed=decoded_message[2],
                       car_number=decoded_message[3],
                       x=int(decoded_message[4]),
                       y=int(decoded_message[5]),
                       w=int(decoded_message[6]),
                       h=int(decoded_message[7]),
                       seen_time_epoch=np.float(decoded_message[8]),
                       side_dir=decoded_message[9],
                       lane_id=decoded_message[10],
                       reg_counter=decoded_message[11],
                       has_side_image=int(decoded_message[12]),
                       car_type=decoded_message[13])


def ocr():
    try:
        if not os.path.exists(OUT_DIR):
            os.mkdir(OUT_DIR)

        if not os.path.exists(OUT_MOTION):
            os.mkdir(OUT_MOTION)

        if not os.path.exists(OUT_SIDE):
            os.mkdir(OUT_SIDE)

        if not os.path.exists(OUT_OCR):
            os.mkdir(OUT_OCR)

    except PermissionError as e:
        print("[  EROR  ]", e)
        time.sleep(10)
        sys.exit()

    process_recent_cars_queue_thread = threading.Thread(target=process_recent_cars_queue)
    process_recent_cars_queue_thread.start()

    try:
        # RabbitMQ configurations
        print("[  INFO  ] Broker Configuration")
        credentials = pika.PlainCredentials(RABBIT_USER, RABBIT_PASSWORD)
        parameters = pika.ConnectionParameters(RABBIT_ADDRESS, credentials=credentials, heartbeat=RABBIT_HEARTBEAT)
        connection = pika.BlockingConnection(parameters)

        # Setup the channel
        print("[  INFO  ] Setting up channel")
        anpr_channel = connection.channel()

        # Declare the queue
        print("[  INFO  ] Declaring ANPR queue")
        anpr_channel.queue_declare(queue=ANPR_CHANNEL)

        # Callback function
        def callback(ch, method, properties, body):
            if process_recent_cars_queue_thread.is_alive() is False:
                process_recent_cars_queue_thread.start()
                print("[  WARN  ] Camera thread started after it has been killed")

            on_message_received(body)

        # Subscribe to the queue
        anpr_channel.basic_consume(ANPR_CHANNEL,
                                   callback,
                                   auto_ack=True)

        print("[  INFO  ] Start consuming")
        anpr_channel.start_consuming()

        print("[  INFO  ] Closing connection")
        connection.close()

    except pika.exceptions.ConnectionClosed:
        print("[  EROR  ] Connection closed")

    except pika.exceptions.AMQPConnectionError:
        print("[  EROR  ] Error in connection")

    except pika.exceptions.ChannelWrongStateError:
        print("[  EROR  ] Channel is in wrong state")

    finally:
        try:
            connection.close()
        except:
            pass
        exit_event.set()
        time.sleep(10)


if __name__ == "__main__":
    forever = True
    while forever:
        ocr()
        time.sleep(1)
        exit_event.clear()
