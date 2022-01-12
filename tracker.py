import copy
import threading
import cv2
import pika
import time
import sys
import win32api, win32process, win32con

import activation
from registery import get_reg, set_reg

try:
    activation_state = get_reg("StopOCRTemp2")

    is_activated = False
    if int(activation_state) == 1:
        is_activated = True
    else:
        serial = activation.SerialNumber()
        is_activated, uuid, did = serial.check_activation_status(type='R')

        if is_activated is True:
            set_reg("StopOCRTemp2", "1")

    if is_activated is False:
        print("[  INFO  ] Device is not activated.")
        print("[  INFO  ] Device ID:", uuid)
        print("[  INFO  ] In order to activate this device, please call Fard Iran.")
        time.sleep(30)
        sys.exit()
    else:
        print("[  INFO  ] Device is activated. Device ID:", uuid)

except ValueError:
    sys.exit()

from conversions import conversions
from car_detection import detect_car_and_plate
from camera import *
from settings import *

avg_speed_queue = collections.deque(maxlen=TRACKER_AVG_SPEED_QUEUE_LEN)

# RabbitMQ configurations
credentials = pika.PlainCredentials(RABBIT_USER, RABBIT_PASSWORD)
parameters = pika.ConnectionParameters(RABBIT_ADDRESS, credentials=credentials, heartbeat=RABBIT_HEARTBEAT)
connection = pika.BlockingConnection(parameters)
anpr_channel = connection.channel()
anpr_channel.queue_declare(queue=ANPR_CHANNEL)

if SEND2FRONT:
    front_channel = connection.channel()
    front_channel.queue_declare(queue='frontend')


#
# Calculate tracker speed
#
def calculate_speed(location1, location2, t1, t2, offset, a=None, b=None, c=None, d=None):

    if location1[1] == location2[1]:
        return SPEED_MIN_FOR_MATCH

    location1_distance = conversions[location1[1] + offset]
    location2_distance = conversions[location2[1] + offset]
    diff = location2_distance - location1_distance
    try:
        speed = (diff / 100) / (t2 - t1) * 3.6
    except:
        speed = SPEED_MIN_FOR_MATCH

    return speed


#
# Determine where two shapes having shared area or not
#
def are_shared(x0, y0, x1, y1):
    if abs(x0 - x1) <= 150 and abs(y0 - y1) <= 50:
        return True
    return False


#
# Process input stream
#
def tracker1():
    print("[  INFO  ] Processing frame queue in thread")

    camera_gain = CAM1_GAIN
    camera_exposure = CAM1_SHUTTER
    ir_panel_status = 0

    #
    # Load lane mask
    mask = cv2.imread(TRACKER_MASK1)
    if mask is not None:
        is_masked = True
        mask = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)
        mask = cv2.bitwise_not(mask)
    else:
        is_masked = False

    #
    # Initialize object tracker parameters
    trackers = []
    car_id = 1

    counter = 0
    while True:

        counter += 1

        if counter == TRACKER_LOG_RATE:
            print("[  INFO  ] Queue length: ", len(CAM1_QUEUE))

            if len(CAM1_QUEUE) > 20:
                # for i in range(0, 20, 2):
                #     del CAM1_QUEUE[i]
                CAM1_QUEUE.clear()
                print("[  WARN  ] Camera queue cleared in order to preventing overflow problem")
            counter = 0

        if len(CAM1_QUEUE) == 0:
            time.sleep(TRACKER_SLEEP)
        else:
            frame, frame_time, frame_side, frame_index, reg_counter, camera_gain, camera_exposure, ir_panel_status = CAM1_QUEUE.pop(0)
            try:
                length = len(frame.shape)
            except:
                continue

            if length < 2:
                continue

            plates = []
            try:
                if is_masked:
                    masked = cv2.add(frame, mask)
                else:
                    masked = frame

                if VERBOSE:
                    cv2.imshow("LIVE", cv2.resize(masked, None, fx=1 / 3, fy=1 / 3))
                    cv2.waitKey(1)

                plates = detect_car_and_plate(masked)

            except:
                print("[  ERORR  ] Problem in plate detection")
                continue

            if len(plates) == 0:
                continue

            plateCounter = 0
            x_last = 0
            y_last = 0

            for coordinate in plates:
                y = coordinate[1]
                x = coordinate[0]
                car_type = -1

                # Check for shared plate conditions
                plateCounter += 1
                if plateCounter >= 1:
                    if are_shared(x, y, x_last, y_last):
                        print("[  INFO  ] Shared plate detected")
                        continue

                x_last = x
                y_last = y

                find_match = False

                if TRACKER_TOP_H_LINE < y < TRACKER_BOTTOM_H_LINE:
                    w = coordinate[2]
                    h = coordinate[3]

                    for ite in range(len(trackers)):
                        xTrackerFirstSeen = trackers[ite][0]
                        yTrackerFirstSeen = trackers[ite][1]
                        xTrackerLastSeen = trackers[ite][7]
                        yTrackerLastSeen = trackers[ite][8]
                        hTrackerLastSeen = trackers[ite][10]
                        tTrackerLastSeen = trackers[ite][2]
                        idTracker = trackers[ite][3]

                        if (car_id - idTracker) <= 2 and \
                                abs(x - xTrackerLastSeen) <= TRACKER_HORIZ_MAX_MOVE and \
                                y > yTrackerLastSeen and \
                                (y - yTrackerFirstSeen) <= TRACKER_TOP_BOTTOM_DISTANCE and \
                                frame_time > tTrackerLastSeen:

                            # Estimate speed
                            tracker_speed = calculate_speed([xTrackerLastSeen, int(yTrackerLastSeen + hTrackerLastSeen / 2)],
                                                            [x, int(y + h / 2)],
                                                            tTrackerLastSeen, frame_time, SPEED_TABLE_INDEX_OFFSET)

                            # coef = 1 + (speed_coefficients[int(y + h / 2)] - h) / 100
                            if tracker_speed >= SPEED_MIN_FOR_MATCH:
                                find_match = True

                                # Append coef to tracker coefs
                                # trackers[ite][22].append(coef)

                                #  Update tracker speed
                                trackers[ite][6] = tracker_speed

                                # Update latest frame time
                                trackers[ite][2] = frame_time

                                # Increase tracker seen counter
                                trackers[ite][4] += 1

                                # Update tracker last seen image
                                trackers[ite][5] = copy.copy(frame)

                                # Update plate coordinates
                                trackers[ite][7] = x
                                trackers[ite][8] = y
                                trackers[ite][9] = w
                                trackers[ite][10] = h

                                # Set matched flag true
                                trackers[ite][12] = 1

                                # update frame side
                                trackers[ite][15] = copy.copy(frame_side)

                                trackers[ite][17] = frame_index
                                trackers[ite][18] = reg_counter

                                print("[  INFO  ] Match found. Car ID: %d" % (trackers[ite][3]))
                                break

                    if not find_match:
                        print("[  INFO  ] New car detected. ID: ", car_id)
                        trackers.append(
                            [x, y, frame_time, car_id, 1, copy.copy(frame), 0, x, y, w, h, 0, 0, time.time(),
                             frame_time, copy.copy(frame_side), frame_index, frame_index, reg_counter, car_type, w, h])
                        car_id += 1

            del frame, frame_side

        for ite in range(len(trackers)):
            tTrackerLastSeen = trackers[ite][13]
            if time.time() - tTrackerLastSeen > TRACKER_QUEUE_TIMEOUT:
                xTrackerFirstSeen = trackers[ite][0]
                yTrackerFirstSeen = trackers[ite][1]
                hTrackerFirstSeen = trackers[ite][21]
                plate_x = trackers[ite][7]
                plate_y = trackers[ite][8]
                plate_w = trackers[ite][9]
                plate_h = trackers[ite][10]
                tracker_id = trackers[ite][3]
                latest_frame = trackers[ite][5]
                latest_frame_time = trackers[ite][2]
                first_frame_time = trackers[ite][14]
                frame_side = trackers[ite][15]
                reg_counter = trackers[ite][18]
                car_type = trackers[ite][19]
                # coefs = trackers[ite][22]

                # Getting plate samples for setting up gain and shutter adaptively according to plate
                plateSample = latest_frame[plate_y:(plate_y + plate_h), plate_x:(plate_x + plate_w)]
                CAM1_AVG_QUEUE.append(cv2.mean(plateSample)[0])
                Z = np.float32(plateSample.reshape((-1)))

                # Define criteria, number of clusters(K) and apply kmeans()
                criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)

                try:
                    ret1, label1, center = cv2.kmeans(Z, 2, None, criteria, 5, cv2.KMEANS_RANDOM_CENTERS)

                    # Convert back into uint8, and make original image
                    center = np.uint8(center)

                    # Add calculations to queue
                    CAM1_MEAN_CENTER_QUEUE.append(center[1][0] / 2 + center[0][0] / 2)

                    if center[1][0] < center[0][0]:
                        CAM1_MEAN_MINUS_QUEUE.append(np.uint(0))
                    else:
                        CAM1_MEAN_MINUS_QUEUE.append(center[1][0] - center[0][0])
                except:
                    print("[  WARN  ] Problem in calculating mean values")
                    pass

                # Calculating speed
                if SPEED_CALC_METHOD == 'R':
                    # Reading speed
                    # Note: If you want consequence speed use this
                    tracker_speed = trackers[ite][6]
                else:
                    # Estimate speed
                    # NOTE: If you want average speed use this
                    tracker_speed = calculate_speed([xTrackerFirstSeen, int(yTrackerFirstSeen + hTrackerFirstSeen / 2)],
                                                    [plate_x, int(plate_y + plate_h / 2)],
                                                    first_frame_time, latest_frame_time, SPEED_TABLE_INDEX_OFFSET,
                                                    trackers[ite][4],
                                                    trackers[ite][16], trackers[ite][17], tracker_id)

                has_side_frame = 1

                if tracker_speed <= SPEED_MIN_FOR_PASS or tracker_speed > SPEED_MAX_FOR_PASS or tracker_speed is None:
                    if len(avg_speed_queue) > 0:
                        if USE_AVERAGE_FOR_SINGLE:
                            tracker_speed = np.mean(avg_speed_queue)
                        else:
                            tracker_speed = -19
                    else:
                        if USE_AVERAGE_FOR_SINGLE:
                            tracker_speed = SPEED_AVG_FOR_BYPASS_EXCEPTIONS
                        else:
                            tracker_speed = -19

                # tracker_speed = int(round((tracker_speed * np.mean(coefs))))
                tracker_speed = int(tracker_speed)
                avg_speed_queue.append(tracker_speed)

                # Writing frames into disk
                file_name = "tracker_{}.jpg".format(tracker_id)
                try:
                    cv2.imwrite(OUT_TRACKER_FRONT + file_name, latest_frame)
                except:
                    print("[  EROR  ] Problem in writing front frame into disk")

                if frame_side is not None:
                    try:
                        cv2.imwrite(OUT_TRACKER_SIDE + file_name, frame_side)
                    except:
                        print("[  EROR  ] Problem in writing side frame into disk")
                else:
                    print("[  WARN  ] Side camera frame not exists")
                    has_side_frame = 0

                # Sending message to OCR
                try:
                    message = "{}|{}|{:.0f}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}".format(OUT_TRACKER_FRONT,
                                                                                     file_name,
                                                                                     tracker_speed,
                                                                                     tracker_id,
                                                                                     plate_x,
                                                                                     plate_y,
                                                                                     plate_w,
                                                                                     plate_h,
                                                                                     latest_frame_time,
                                                                                     OUT_TRACKER_SIDE,
                                                                                     1,
                                                                                     reg_counter,
                                                                                     has_side_frame,
                                                                                     car_type)

                    anpr_channel.basic_publish(exchange='',
                                               routing_key='anpr',
                                               body=message.encode('utf8'),
                                               properties=pika.BasicProperties(expiration='60000', )
                                               )

                    # Sending message to the frontend
                    if SEND2FRONT:
                        message = "{}|{}|{}|{}|{}|{}".format("trk",
                                                             tracker_id,
                                                             len(CAM1_QUEUE),
                                                             camera_gain,
                                                             camera_exposure,
                                                             ir_panel_status)

                        front_channel.basic_publish(exchange='',
                                                    routing_key='frontend',
                                                    body=message.encode('utf8'),
                                                    properties=pika.BasicProperties(expiration='5000', )
                                                    )
                except:
                    print("[  EROR  ] Problem in sending data to OCR")

                trackers[ite][11] = 1

                print("[  SEND  ] Frame sent for OCR. Car ID: ", tracker_id)

        new_trackers = [s for s in trackers if s[11] == 0]
        trackers = new_trackers

        # new_trackers = [s for s in trackers if s[11] == 0]
        # del trackers
        # trackers = new_trackers
        # del new_trackers

    print("[  WARN  ] Unwanted return from process_stream")
    return


def set_priority(pid=None, priority=1):
    """ Set The Priority of a Windows Process.  Priority is a value between 0-5 where
        2 is normal priority.  Default sets the priority of the current
        python process but can take any valid process ID. """

    priorities = [win32process.IDLE_PRIORITY_CLASS,
                  win32process.BELOW_NORMAL_PRIORITY_CLASS,
                  win32process.NORMAL_PRIORITY_CLASS,
                  win32process.ABOVE_NORMAL_PRIORITY_CLASS,
                  win32process.HIGH_PRIORITY_CLASS,
                  win32process.REALTIME_PRIORITY_CLASS]

    if pid is None:
        pid = win32api.GetCurrentProcessId()

    print("[  INFO  ] Process started with ID: ", pid)

    handle = win32api.OpenProcess(win32con.PROCESS_ALL_ACCESS, True, pid)
    win32process.SetPriorityClass(handle, priorities[priority])


if __name__ == '__main__':

    try:
        if not os.path.exists(OUT_TRACKER):
            os.mkdir(OUT_TRACKER)

        if not os.path.exists(OUT_TRACKER_FRONT):
            os.mkdir(OUT_TRACKER_FRONT)

        if not os.path.exists(OUT_TRACKER_SIDE):
            os.mkdir(OUT_TRACKER_SIDE)
    except PermissionError as e:
        print("[  EROR  ]", e)
        time.sleep(10)
        sys.exit()

    set_priority(priority=PROCESS_PRIORITY)

    try:
        front_camera_grabber_thread = threading.Thread(target=grab_front1_direct_side1_direct)
        motion_process_thread = threading.Thread(target=tracker1)

        motion_process_thread.start()
        front_camera_grabber_thread.start()

        # ToDo: Use CAM1_QUEUE length to detect thread problem. Further information in issue #9
        #
        while True:
            if front_camera_grabber_thread.is_alive() is False:
                time.sleep(10)
                front_camera_grabber_thread = threading.Thread(target=grab_front1_direct_side1_direct)
                front_camera_grabber_thread.start()
                print("[  WARN  ] Camera thread started after it has been killed")

            if motion_process_thread.is_alive() is False:
                time.sleep(10)
                motion_process_thread = threading.Thread(target=tracker1)
                motion_process_thread.start()
                print("[  WARN  ] Tracker thread started after it has been killed")

            print("[  INFO  ] Camera and Tracker workers checked for aliveness")
            time.sleep(10)
    except:
        print("[  INFO  ] Error in tracker")
        time.sleep(10)
