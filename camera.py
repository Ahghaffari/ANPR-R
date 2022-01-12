import time
import numpy as np
import cv2

from settings import *
from registery import get_reg, set_ir_value

import pypylon
from pypylon import pylon
from pypylon import genicam
from pypylon import _genicam
from pypylon import _pylon

# Frame list initialization
CAM1_QUEUE = []


#
# Read image stream from camera
#
# ToDo: Remove this function
def get_gm_frame(camera):
    frame = np.zeros(2)
    try:
        grabResult = camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
        if grabResult.GrabSucceeded():
            frame = grabResult.Array
    except grabResult.ErrorCode:
        print("[  EROR  ] Front camera Grab problem happened: ", grabResult.ErrorCode)

    return frame


#
# Get side frame directly
#
# ToDo: remove this function
def get_gc_frame(camera):
    frame = np.zeros(2)

    try:
        grabResult = camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
        frame = cv2.cvtColor(grabResult.Array, cv2.COLOR_BAYER_RG2RGB)
    except grabResult.ErrorCode:
        print("[  EROR  ] Side camera Grab problem happened: ", grabResult.ErrorCode)

    return frame


#
# Setting gain and shutter function
#
def gain_shutter_auto(gain, shutter, brightness):
    if brightness <= 85:
        if gain <= 350:
            gain = gain + 6

        if shutter < 1500:
            shutter = shutter + 9
    elif brightness > 115:
        if gain > 10:
            gain = gain - 6

        if shutter > 100:
            shutter = shutter - 9

    return gain, shutter


#
# Read frames from 2 camera
#
def grab_front1_direct_side1_direct():
    frame_counter = 0
    last_plate_mean = -1
    gain = CAM1_GAIN
    shutter = CAM1_SHUTTER
    ir = 0

    # Get the transport layer factory
    tlFactory = pylon.TlFactory.GetInstance()

    # Get all attached devices and exit application if no device is found.
    devices = tlFactory.EnumerateDevices()
    while len(devices) not in [1, 2]:
        print("[  INFO  ] Enumerate camera devices ...")
        devices = tlFactory.EnumerateDevices()
        time.sleep(1)

    if len(devices) == 0:
        raise SystemExit("[  EROR  ] No camera present")

    if len(devices) == 1:
        print("[  WARN  ] Camera 2 not found!!!")

    cameras = pylon.InstantCameraArray(min(len(devices), CAMERA_NUMBERS))

    # Create and attach all Pylon Devices
    for i, cam in enumerate(cameras):
        cam.Attach(tlFactory.CreateDevice(devices[i]))

        cam.Open()

        print('[  INFO  ] Camera ' + str(i) + ' model name: ' + cam.GetDeviceInfo().GetModelName(), "-",
              cam.GetDeviceInfo().GetSerialNumber())

        try:
            # cam.PixelFormat.SetValue(c_pixel_format)
            cam.GainAuto.SetValue(CAM1_GAIN)
            cam.ExposureAuto.SetValue(CAM1_SHUTTER)
            cam.ExposureTimeRaw.SetValue(CAM1_INIT_SHUTTER)
            cam.GainRaw.SetValue(CAM1_INIT_GAIN)
            cam.AcquisitionFrameRateEnable.SetValue(True)
            cam.AcquisitionFrameRateAbs.SetValue(CAM1_FRAME_RATE)
            cam.MaxNumBuffer.SetValue(CAM1_BUFF_SIZE)
            cam.GevIEEE1588.SetValue(True)
            cam.AutoGainRawLowerLimit.SetValue(CAM2_GAIN_LOWER_LIMIT)
            cam.AutoGainRawUpperLimit.SetValue(CAM2_GAIN_UPPER_LIMIT)
            cam.AutoExposureTimeAbsLowerLimit.SetValue(CAM2_EXPOSURE_LOWER_LIMIT)
            cam.AutoExposureTimeAbsUpperLimit.SetValue(CAM2_EXPOSURE_UPPER_LIMIT)
            cam.AutoFunctionProfile.SetValue(CAM2_AUTO_FUNCTION_PROFILE)
        except:
            pass

    camera = cameras[CAM1_ID]

    if CAMERA_NUMBERS > 1:
        camera3 = cameras[CAM2_ID]

        try:
            camera3.GainAuto.SetValue(CAM2_GAIN)
            camera3.ExposureAuto.SetValue(CAM2_SHUTTER)
            camera3.PixelFormat.SetValue(CAM2_PIXEL_FORMAT)
        except:
            pass
    else:
        camera3 = None

    # Starts grabbing for all cameras starting with index 0. The grabbing is started for one camera after the other.
    # That's why the images of all cameras are not taken at the same time. However, a hardware trigger setup can be
    # used to cause all cameras to grab images synchronously. According to their default configuration, the cameras
    # are set up for free-running continuous acquisition.
    cameras.StartGrabbing()
    last_start = time.time()

    # for count in range(10):
    #     camera3.GevIEEE1588DataSetLatch.Execute()

    while camera.IsGrabbing():
        if frame_counter == CAM1_CONFIG_RATE:
            plate_mean = np.mean(CAM1_AVG_QUEUE)
            plate_meanCenter = np.mean(CAM1_MEAN_CENTER_QUEUE)
            plate_minusCenter = np.mean(CAM1_MEAN_MINUS_QUEUE)

            if last_plate_mean != plate_mean:
                camera.GainRaw.Value, camera.ExposureTimeRaw.Value = gain, shutter = gain_shutter_auto(
                    camera.GainRaw.Value,
                    camera.ExposureTimeRaw.Value,
                    plate_mean)
                if (camera.GainRaw.Value > 30 and plate_minusCenter < 60) or plate_meanCenter < 70:
                    ir = 1
                    set_ir_value(1)
                elif camera.GainRaw.Value < 10 or plate_meanCenter > 190:
                    ir = 0
                    set_ir_value(0)

            try:
                camera3.GevIEEE1588DataSetLatch.Execute()
                offset = camera3.GevIEEE1588OffsetFromMaster.GetValue()
                camera3FrameRate = int(camera3.ResultingFrameRateAbs.GetValue())
            except:
                offset = None
                camera3FrameRate = None

            # clock_id = camera3.GevIEEE1588ClockId.GetValue()
            # parent_clock_id = camera3.GevIEEE1588ParentClockId.GetValue()
            # print("[  INFO  ] Camera 2 clock ID:", clock_id)
            # print("[  INFO  ] Camera 2 master clock ID:", parent_clock_id)
            print("[  INFO  ] Camera 1 frame rate: ", int(camera.ResultingFrameRateAbs.GetValue()))
            print("[  INFO  ] Camera 2 frame rate: ", camera3FrameRate)
            print("[  INFO  ] Camera 2 offset from master:", offset)
            print("[  INFO  ] Plate PM: {:.2f}, PMC: {:.2f}".format(plate_meanCenter, plate_minusCenter))
            print("[  INFO  ] Camera 1 Gain: {}, Shutter: {}, IR: {}".format(camera.GainRaw.Value,
                                                                             camera.ExposureTimeRaw.Value,
                                                                             ir))
            last_plate_mean = plate_mean
            frame_counter = 0

        # Read frame
        grabResult = camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
        frame = grabResult.GetArray()

        try:
            grabResult = camera3.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)

            try:
                side_frame = cv2.cvtColor(grabResult.GetArray(), cv2.COLOR_BAYER_RG2RGB)
            except:
                side_frame = grabResult.GetArray()
        except:
            side_frame = frame

        cap_time = time.time()

        frame_counter += 1

        reg_counter = get_reg("ShareCameraID")

        # Add frame to queue
        if frame is not None:
            CAM1_QUEUE.append([frame, cap_time, side_frame, frame_counter, reg_counter, gain, shutter, ir])
        else:
            continue

        if cap_time - last_start > CAM1_RESTART_TIMEOUT:
            cameras.StopGrabbing()
            time.sleep(1)
            cameras.StartGrabbing()

            last_start = time.time()
