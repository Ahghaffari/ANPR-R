# This Python file uses the following encoding: utf-8
import sys
import os
import psutil
import pika
import threading
import subprocess
import threading
from subprocess import check_output

from PySide2.QtGui import QGuiApplication, QIcon
from PySide2.QtQml import QQmlApplicationEngine
from PySide2.QtCore import *
from PyQt5.QtCore import pyqtSlot as pyQtSlot
from PyQt5 import QtCore, QtGui, QtQml


from settings import *

import contextlib

with contextlib.redirect_stdout(None):
    pass


class Connections(QObject):
    plateChanged = Signal(str, arguments=["plate"])
    laneChanged = Signal(str, arguments=["lane"])
    carChanged = Signal(str, arguments=["car"])
    frameChanged = Signal(str, arguments=["image"])
    queueChanged = Signal(str, arguments=["queue"])
    counterChanged = Signal(str, arguments=["counter"])
    timeChanged = Signal(str, arguments=["time"])
    irChanged = Signal(str, arguments=["ir_status"])
    gainChanged = Signal(str, arguments=["gain"])
    shutterChanged = Signal(str, arguments=["shutter"])
    speedChanged = Signal(str, arguments=["speed"])


# RabbitMQ configurations
try:
    credentials = pika.PlainCredentials(RABBIT_USER, RABBIT_PASSWORD)
    parameters = pika.ConnectionParameters(RABBIT_ADDRESS, credentials=credentials, heartbeat=RABBIT_HEARTBEAT)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    channel.queue_declare(queue='frontend')
except:
    pass


def run_ocr():
    subprocess.Popen(['ocr.exe'],
                     stdout=subprocess.PIPE,
                     stderr=subprocess.PIPE,
                     shell=True).communicate()


def run_tracker():
    subprocess.Popen(['tracker.exe'],
                     stdout=subprocess.PIPE,
                     stderr=subprocess.PIPE,
                     shell=True).communicate()


def onStartButtonActivated(deployment, gpu, log, lines, road, location, fps, offset1, offset2, offset3, offset4, offset5):
    configuration.set('DEPLOY', 'deployment', str(deployment))
    configuration.set('DEPLOY', 'cpd_gpu', str(gpu))
    configuration.set('DEPLOY', 'verbose', str(log))
    configuration.set('DEPLOY', 'show_lines', str(lines))
    configuration.set('DEPLOY', 'three_line', str(road))
    configuration.set('DEPLOY', 'location', location)
    configuration.set('CAMERA1', 'buffer_size', fps)
    configuration.set('CAMERA1', 'frame_rate', fps)
    configuration.set('CAMERA2', 'buffer_size', fps)
    configuration.set('CAMERA2', 'frame_rate', fps)
    configuration.set('TRACKER', 'speed_offset_l1', offset1)
    configuration.set('TRACKER', 'speed_offset_l2', offset2)
    configuration.set('TRACKER', 'speed_offset_l3', offset3)
    configuration.set('TRACKER', 'speed_offset_l4', offset4)
    configuration.set('TRACKER', 'speed_offset_l5', offset5)

    with open('config.ini', 'w') as configfile:  # save
        configuration.write(configfile)

    mWidget = win.findChild(QObject, "deploymentSwitch")
    mWidget.setProperty("enabled", 0)
    mWidget = win.findChild(QObject, "gpuSwitch")
    mWidget.setProperty("enabled", 0)
    mWidget = win.findChild(QObject, "logSwitch")
    mWidget.setProperty("enabled", 0)
    mWidget = win.findChild(QObject, "linesSwitch")
    mWidget.setProperty("enabled", 0)
    mWidget = win.findChild(QObject, "roadTypeSwitch")
    mWidget.setProperty("enabled", 0)
    mWidget = win.findChild(QObject, "fpsTextInput")
    mWidget.setProperty("enabled", 0)
    mWidget = win.findChild(QObject, "offset1TextInput")
    mWidget.setProperty("enabled", 0)
    mWidget = win.findChild(QObject, "offset2TextInput")
    mWidget.setProperty("enabled", 0)
    mWidget = win.findChild(QObject, "offset3TextInput")
    mWidget.setProperty("enabled", 0)
    mWidget = win.findChild(QObject, "offset4TextInput")
    mWidget.setProperty("enabled", 0)
    mWidget = win.findChild(QObject, "offset5TextInput")
    mWidget.setProperty("enabled", 0)

    ocr_thread = threading.Thread(target=run_ocr, args=())
    ocr_thread.start()
    tracker_thread = threading.Thread(target=run_tracker, args=())
    tracker_thread.start()


def onStartButtonDeactivated():
    os.system("taskkill /f /im ocr.exe")
    os.system("taskkill /f /im tracker.exe")

    mWidget = win.findChild(QObject, "deploymentSwitch")
    mWidget.setProperty("enabled", 1)
    mWidget = win.findChild(QObject, "gpuSwitch")
    mWidget.setProperty("enabled", 1)
    mWidget = win.findChild(QObject, "logSwitch")
    mWidget.setProperty("enabled", 1)
    mWidget = win.findChild(QObject, "linesSwitch")
    mWidget.setProperty("enabled", 1)
    mWidget = win.findChild(QObject, "roadTypeSwitch")
    mWidget.setProperty("enabled", 1)
    mWidget = win.findChild(QObject, "fpsTextInput")
    mWidget.setProperty("enabled", 1)
    mWidget = win.findChild(QObject, "offset1TextInput")
    mWidget.setProperty("enabled", 1)
    mWidget = win.findChild(QObject, "offset2TextInput")
    mWidget.setProperty("enabled", 1)
    mWidget = win.findChild(QObject, "offset3TextInput")
    mWidget.setProperty("enabled", 1)
    mWidget = win.findChild(QObject, "offset4TextInput")
    mWidget.setProperty("enabled", 1)
    mWidget = win.findChild(QObject, "offset5TextInput")
    mWidget.setProperty("enabled", 1)


def on_message_received(msg):

    decoded_message = msg.decode('utf-8').split("|")
    source = decoded_message[0]

    if source == "ocr":
        image_file = decoded_message[1]
        licencePlate = decoded_message[2]
        carLane = decoded_message[3]
        carType = decoded_message[4]
        carTime = decoded_message[5]
        carSpeed = decoded_message[6]

        connector.frameChanged.emit("file:///" + image_file)
        if licencePlate[0] != "[":
            connector.plateChanged.emit(licencePlate[0:2] + " " + licencePlate[2] + " " + licencePlate[3:6] + " " + licencePlate[7:9])
        else:
            connector.plateChanged.emit("")

        connector.laneChanged.emit(carLane)
        connector.timeChanged.emit(carTime[:carTime.find(".")].replace("-", "/").replace("T", " "))
        connector.speedChanged.emit(carSpeed + " Km/H")

        if carType == "0":
            connector.carChanged.emit("Small")
        elif carType == "1":
            connector.carChanged.emit("Big")
        else:
            connector.carChanged.emit("Not detected")

    elif source == "trk":
        trackerCounter = decoded_message[1]
        trackerProcessQueueSize = decoded_message[2]
        camera_gain = decoded_message[3]
        camera_exposure = decoded_message[4]
        ir_panel_status = decoded_message[5]

        connector.counterChanged.emit(trackerCounter)
        connector.queueChanged.emit(trackerProcessQueueSize)
        connector.shutterChanged.emit(camera_exposure)
        connector.gainChanged.emit(camera_gain)

        if ir_panel_status == "0":
            connector.irChanged.emit("Off")
        else:
            connector.irChanged.emit("On")


def connection_handler():
    try:
        # Callback function
        def callback(ch, method, properties, body):
            on_message_received(body)

        # Subscribe to the queue
        channel.basic_consume('frontend',
                              callback,
                              auto_ack=True)
        channel.start_consuming()
        connection.close()

    except pika.exceptions.ConnectionClosed:
        print("[  INFO  ] Connection closed")

    except pika.exceptions.AMQPConnectionError:
        print("[  INFO  ] Error in connection")


def kill_process_tree(pid, including_parent=True):
    parent = psutil.Process(pid)
    for child in parent.children(recursive=True):
        child.kill()
    if including_parent:
        parent.kill()


if __name__ == "__main__":

    app = QGuiApplication(sys.argv)
    app.setWindowIcon(QIcon("assets/anpr.ico"))
    engine = QQmlApplicationEngine()
    connector = Connections()

    # Initializing QML file
    context = engine.rootContext()
    context.setContextProperty("connector", connector)
    context.setContextProperty("image_source", "D:/towzin_its/Motion/16/15/2020-11-16-15-35-33-L2-13E266_29-o.jpg")
    context.setContextProperty("trackerCounter", "0")
    context.setContextProperty("trackerProcessQueueSize", "0")
    context.setContextProperty("cameraGain", str(CAM1_INIT_GAIN))
    context.setContextProperty("cameraShutter", str(CAM1_INIT_SHUTTER))
    context.setContextProperty("irValue", "0")
    context.setContextProperty("licencePlate", "")
    context.setContextProperty("carLane", "")
    context.setContextProperty("carType", "")
    context.setContextProperty("deployment", DEPLOY)
    context.setContextProperty("use_gpu", CPD_GPU)
    context.setContextProperty("verbose", VERBOSE)
    context.setContextProperty("show_lines", SHOW_LINES)
    context.setContextProperty("is3line", ROAD_THREE_LANE)
    context.setContextProperty("location", LOCATION)
    context.setContextProperty("fps", str(CAM1_FRAME_RATE))
    context.setContextProperty("offset1", str(SPEED_OFFSET_L1))
    context.setContextProperty("offset2", str(SPEED_OFFSET_L2))
    context.setContextProperty("offset3", str(SPEED_OFFSET_L3))
    context.setContextProperty("offset4", str(SPEED_OFFSET_L12))
    context.setContextProperty("offset5", str(SPEED_OFFSET_L23))

    # Load QML file
    engine.load(os.path.join(os.path.dirname(__file__), "anpr.qml"))

    # Getting window object
    win = engine.rootObjects()[0]

    # Connecting signals and slots
    win.startButtonActivated.connect(onStartButtonActivated)
    win.startButtonDeactivated.connect(onStartButtonDeactivated)
    win.on_message_received.connect(on_message_received)

    process_recent_cars_queue_thread = threading.Thread(target=connection_handler)
    process_recent_cars_queue_thread.start()

    if not engine.rootObjects():
        kill_process_tree(os.getpid())
        sys.exit(-1)

    # sys.exit(app.exec_())
    app.exec_()
    kill_process_tree(os.getpid())


