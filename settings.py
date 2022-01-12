import os
import collections
import math
from numpy import ones, vstack
from numpy.linalg import lstsq

from configparser import ConfigParser

# Reading configuration file
configuration = ConfigParser()
WORKING_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE_PATH = os.path.join(WORKING_DIR, 'config.ini')
configuration.read(CONFIG_FILE_PATH)

# Deployment configuration
DEPLOY = configuration.getboolean('DEPLOY', 'deployment')
LOCATION = configuration.get('DEPLOY', 'location')
CPD_GPU = configuration.getboolean('DEPLOY', 'cpd_gpu')
VERBOSE = configuration.getboolean('DEPLOY', 'verbose')
SHOW_LINES = configuration.getboolean('DEPLOY', 'show_lines')
PROCESS_PRIORITY = configuration.getint('DEPLOY', 'priority')
SEND2FRONT = configuration.getboolean('DEPLOY', 'sendfront')
SEND2WIM = configuration.getboolean('DEPLOY', 'sendwim')

# Output configuration
OUT_DIR = configuration.get('OUTPUT', 'out_dir')
OUT_TRACKER = configuration.get('OUTPUT', 'out_tracker')
OUT_TRACKER_FRONT = configuration.get('OUTPUT', 'out_tracker_front')
OUT_TRACKER_SIDE = configuration.get('OUTPUT', 'out_tracker_side')
OUT_SIDE = configuration.get('OUTPUT', 'side_out')
OUT_MOTION = configuration.get('OUTPUT', 'motion_out')
OUT_OCR = configuration.get('OUTPUT', 'ocr_out')

# Database configurations
DB_TYPE = configuration.get('DATABASE', 'database')
MYSQL_SERVER = configuration.get('MYSQL', 'address')
MYSQL_PORT = configuration.getint('MYSQL', 'port')
MYSQL_USER = configuration.get('MYSQL', 'username')
MYSQL_PASSWORD = configuration.get('MYSQL', 'password')
MYSQL_DATABASE = configuration.get('MYSQL', 'database')

# RabbitMQ configurations
RABBIT_ADDRESS = configuration.get('RABBITMQ', 'address')
RABBIT_USER = configuration.get('RABBITMQ', 'username')
RABBIT_PASSWORD = configuration.get('RABBITMQ', 'password')
RABBIT_HEARTBEAT = configuration.getint('RABBITMQ', 'heartbeat')
ANPR_CHANNEL = configuration.get('RABBITMQ', 'channel')

# Road configurations
ROAD_THREE_LANE = configuration.getboolean('ROAD', 'three_line')
ROAD_V_SEPARATOR1 = configuration.getint('ROAD', 'vertical_1')
ROAD_V_SEPARATOR2 = configuration.getint('ROAD', 'vertical_2')
ROAD_V_SEPARATOR3 = configuration.getint('ROAD', 'vertical_3')
ROAD_USE_REGRESSION = configuration.getboolean('ROAD', 'regression')

if ROAD_THREE_LANE:
    if ROAD_USE_REGRESSION:
        ROAD_L1P1_X = configuration.getint('ROAD', 'L1P1_x')
        ROAD_L1P1_Y = configuration.getint('ROAD', 'L1P1_y')
        ROAD_L1P2_X = configuration.getint('ROAD', 'L1P2_x')
        ROAD_L1P2_Y = configuration.getint('ROAD', 'L1P2_y')

        points = [(ROAD_L1P1_X, ROAD_L1P1_Y), (ROAD_L1P2_X, ROAD_L1P2_Y)]
        x_coords, y_coords = zip(*points)
        A = vstack([x_coords, ones(len(x_coords))]).T
        ROAD_L1_A, ROAD_L1_B = lstsq(A, y_coords, rcond=None)[0]

        ROAD_L2P1_X = configuration.getint('ROAD', 'L2P1_x')
        ROAD_L2P1_Y = configuration.getint('ROAD', 'L2P1_y')
        ROAD_L2P2_X = configuration.getint('ROAD', 'L2P2_x')
        ROAD_L2P2_Y = configuration.getint('ROAD', 'L2P2_y')

        points = [(ROAD_L2P1_X, ROAD_L2P1_Y), (ROAD_L2P2_X, ROAD_L2P2_Y)]
        x_coords, y_coords = zip(*points)
        A = vstack([x_coords, ones(len(x_coords))]).T
        ROAD_L2_A, ROAD_L2_B = lstsq(A, y_coords, rcond=None)[0]

        ROAD_L3P1_X = configuration.getint('ROAD', 'L3P1_x')
        ROAD_L3P1_Y = configuration.getint('ROAD', 'L3P1_y')
        ROAD_L3P2_X = configuration.getint('ROAD', 'L3P2_x')
        ROAD_L3P2_Y = configuration.getint('ROAD', 'L3P2_y')

        points = [(ROAD_L3P1_X, ROAD_L3P1_Y), (ROAD_L3P2_X, ROAD_L3P2_Y)]
        x_coords, y_coords = zip(*points)
        A = vstack([x_coords, ones(len(x_coords))]).T
        ROAD_L3_A, ROAD_L3_B = lstsq(A, y_coords, rcond=None)[0]

        ROAD_L4P1_X = configuration.getint('ROAD', 'L4P1_x')
        ROAD_L4P1_Y = configuration.getint('ROAD', 'L4P1_y')
        ROAD_L4P2_X = configuration.getint('ROAD', 'L4P2_x')
        ROAD_L4P2_Y = configuration.getint('ROAD', 'L4P2_y')

        points = [(ROAD_L4P1_X, ROAD_L4P1_Y), (ROAD_L4P2_X, ROAD_L4P2_Y)]
        x_coords, y_coords = zip(*points)
        A = vstack([x_coords, ones(len(x_coords))]).T
        ROAD_L4_A, ROAD_L4_B = lstsq(A, y_coords, rcond=None)[0]

        ROAD_C1P1_X = configuration.getint('ROAD', 'C1P1_x')
        ROAD_C1P1_Y = configuration.getint('ROAD', 'C1P1_y')
        ROAD_C1P2_X = configuration.getint('ROAD', 'C1P2_x')
        ROAD_C1P2_Y = configuration.getint('ROAD', 'C1P2_y')

        points = [(ROAD_C1P1_X, ROAD_C1P1_Y), (ROAD_C1P2_X, ROAD_C1P2_Y)]
        x_coords, y_coords = zip(*points)
        A = vstack([x_coords, ones(len(x_coords))]).T
        ROAD_C1_A, ROAD_C1_B = lstsq(A, y_coords, rcond=None)[0]

        ROAD_C2P1_X = configuration.getint('ROAD', 'C2P1_x')
        ROAD_C2P1_Y = configuration.getint('ROAD', 'C2P1_y')
        ROAD_C2P2_X = configuration.getint('ROAD', 'C2P2_x')
        ROAD_C2P2_Y = configuration.getint('ROAD', 'C2P2_y')

        points = [(ROAD_C2P1_X, ROAD_C2P1_Y), (ROAD_C2P2_X, ROAD_C2P2_Y)]
        x_coords, y_coords = zip(*points)
        A = vstack([x_coords, ones(len(x_coords))]).T
        ROAD_C2_A, ROAD_C2_B = lstsq(A, y_coords, rcond=None)[0]

    else:
        ROAD_L1_A = configuration.getfloat('ROAD', 'A1')
        ROAD_L1_B = configuration.getfloat('ROAD', 'B1')
        ROAD_L2_A = configuration.getfloat('ROAD', 'A2')
        ROAD_L2_B = configuration.getfloat('ROAD', 'B2')
        ROAD_L3_A = configuration.getfloat('ROAD', 'A3')
        ROAD_L3_B = configuration.getfloat('ROAD', 'B3')
        ROAD_L4_A = configuration.getfloat('ROAD', 'A4')
        ROAD_L4_B = configuration.getfloat('ROAD', 'B4')
        ROAD_C1_A = configuration.getfloat('ROAD', 'AC1')
        ROAD_C1_B = configuration.getfloat('ROAD', 'BC1')
        ROAD_C2_A = configuration.getfloat('ROAD', 'AC2')
        ROAD_C2_B = configuration.getfloat('ROAD', 'BC2')

# Camera 1 configuration
CAMERA_NUMBERS = configuration.getint('CAMERA1', 'camera_numbers')
CAM1_GAIN = configuration.get('CAMERA1', 'gain_auto')
CAM1_SHUTTER = configuration.get('CAMERA1', 'shutter_auto')
CAM1_INIT_GAIN = configuration.getint('CAMERA1', 'init_gain')
CAM1_INIT_SHUTTER = configuration.getint('CAMERA1', 'init_shutter')
CAM1_NIGHT_GAIN = configuration.getint('CAMERA1', 'night_gain')
CAM1_NIGHT_SHUTTER = configuration.getint('CAMERA1', 'night_shutter')
CAM1_BUFF_SIZE = configuration.getint('CAMERA1', 'buffer_size')
CAM1_FRAME_RATE = configuration.getint('CAMERA1', 'frame_rate')
CAM1_ID = configuration.getint('CAMERA1', 'camera_id')
CAM1_AVG_QUEUE_SIZE = configuration.getint('CAMERA1', 'cam1_avg_queue_size')
CAM1_MeanCenter_QUEUE_SIZE = configuration.getint('CAMERA1', 'cam1_meancenter_queue_size')
CAM1_MeanM_QUEUE_SIZE = configuration.getint('CAMERA1', 'cam1_minuscenter_queue_size')
CAM1_AVG_QUEUE = collections.deque(maxlen=CAM1_AVG_QUEUE_SIZE)
CAM1_MEAN_CENTER_QUEUE = collections.deque(maxlen=CAM1_MeanCenter_QUEUE_SIZE)
CAM1_MEAN_MINUS_QUEUE = collections.deque(maxlen=CAM1_MeanM_QUEUE_SIZE)
CAM1_CONFIG_RATE = configuration.getint('CAMERA1', 'reconfiguration_rate')
CAM1_RESTART_TIMEOUT = configuration.getint('CAMERA1', 'restart_timeout')

# Camera 2 configuration
CAM2_GAIN = configuration.get('CAMERA2', 'gain_auto')
CAM2_SHUTTER = configuration.get('CAMERA2', 'shutter_auto')
CAM2_BUFF_SIZE = configuration.getint('CAMERA2', 'buffer_size')
CAM2_FRAME_RATE = configuration.getint('CAMERA2', 'frame_rate')
CAM2_ID = configuration.getint('CAMERA2', 'camera_id')
CAM2_GAIN_LOWER_LIMIT = configuration.getint('CAMERA2', 'auto_gain_raw_lower_limit')
CAM2_GAIN_UPPER_LIMIT = configuration.getint('CAMERA2', 'auto_gain_raw_upper_limit')
CAM2_EXPOSURE_LOWER_LIMIT = configuration.getfloat('CAMERA2', 'auto_exposure_time_abs_lower_limit')
CAM2_EXPOSURE_UPPER_LIMIT = configuration.getfloat('CAMERA2', 'auto_exposure_time_abs_upper_limit')
CAM2_AUTO_FUNCTION_PROFILE = configuration.get('CAMERA2', 'auto_function_profile')
CAM2_PIXEL_FORMAT = configuration.get('CAMERA2', 'pixel_format')

# Tracker configuration
TRACKER_SLEEP = configuration.getfloat('TRACKER', 'wait_time')
TRACKER_TOP_H_LINE = configuration.getint('TRACKER', 'top_h_line')
TRACKER_BOTTOM_H_LINE = configuration.getint('TRACKER', 'bottom_h_line')
TRACKER_TOP_BOTTOM_DISTANCE = TRACKER_BOTTOM_H_LINE - TRACKER_TOP_H_LINE
TRACKER_HORIZ_MAX_MOVE = configuration.getint('TRACKER', 'horiz_max_move')
TRACKER_QUEUE_TIMEOUT = configuration.getfloat('TRACKER', 'queue_lifetime')
TRACKER_AVG_SPEED_QUEUE_LEN = configuration.getint('TRACKER', 'avg_speed_q_len')
SPEED_MIN_FOR_PASS = configuration.getint('TRACKER', 'speed_min_for_pass')
SPEED_MAX_FOR_PASS = configuration.getint('TRACKER', 'speed_max_for_pass')
SPEED_AVG_FOR_BYPASS_EXCEPTIONS = configuration.getint('TRACKER', 'speed_avg_for_bypass_exceptions')
SPEED_CALC_METHOD = configuration.get('TRACKER', 'speed_calculation_method')
SPEED_MIN_FOR_MATCH = configuration.getint('TRACKER', 'speed_min_for_match')
SPEED_TABLE_INDEX_OFFSET = configuration.getint('TRACKER', 'speed_table_index_offset')
TRACKER_MASK1 = configuration.get('TRACKER', 'mask1')
TRACKER_MASK2 = configuration.get('TRACKER', 'mask2')
TRACKER_LOG_RATE = configuration.getint('TRACKER', 'log_rate')
TRACKER_PD_APPROACH = configuration.getint('TRACKER', 'tracker_pd_approach')

# OCR configuration
SEGMENTATION_CONFIG = configuration.get('OCR', 'segmentation_config')
SEGMENTATION_WEIGHTS = configuration.get('OCR', 'segmentation_weights')
CHAR_MODEL_WEIGHT_PATH = configuration.get('OCR', 'char_weights')
NUM_MODEL_WEIGHT_PATH = configuration.get('OCR', 'num_weights')
OCR_SIMILARITY_RATIO = configuration.getfloat('OCR', 'similarity_ratio')
OCR_POST_PROCESS_PLATE = configuration.getboolean('OCR', 'post_process_plate')
OCR_CAR_TYPE_DETECTION = configuration.getboolean('OCR', 'car_type_detection')
USE_AVERAGE_FOR_SINGLE = configuration.getboolean('OCR', 'use_average_for_single')
SPEED_OFFSET_L1 = configuration.getint('OCR', 'speed_offset_l1')
SPEED_OFFSET_L2 = configuration.getint('OCR', 'speed_offset_l2')
SPEED_OFFSET_L3 = configuration.getint('OCR', 'speed_offset_l3')
SPEED_OFFSET_L12 = configuration.getint('OCR', 'speed_offset_l12')
SPEED_OFFSET_L23 = configuration.getint('OCR', 'speed_offset_l23')
SPEED_OFFSET_HEAVY_L1 = configuration.getint('OCR', 'speed_offset_heavy_l1')
SPEED_OFFSET_HEAVY_L2 = configuration.getint('OCR', 'speed_offset_heavy_l2')
SPEED_OFFSET_HEAVY_L3 = configuration.getint('OCR', 'speed_offset_heavy_l3')
SPEED_OFFSET_HEAVY_L12 = configuration.getint('OCR', 'speed_offset_heavy_l12')
SPEED_OFFSET_HEAVY_L23 = configuration.getint('OCR', 'speed_offset_heavy_l23')

# Plate configuration
CASCADE_MODEL_PATH = configuration.get('PLATE', 'cascade_model')
CASCADE_THR = configuration.getfloat('PLATE', 'cascade_thr')
CASCADE_NEIGHBOUR = configuration.getint('PLATE', 'cascade_neighbour')
CASCADE_MIN_SIZE_W = configuration.getint('PLATE', 'cascade_min_size_w')
CASCADE_MIN_SIZE_H = configuration.getint('PLATE', 'cascade_min_size_h')
CASCADE_MAX_SIZE_W = configuration.getint('PLATE', 'cascade_max_size_w')
CASCADE_MAX_SIZE_H = configuration.getint('PLATE', 'cascade_max_size_h')
CAR_PLATE_DETECTION_WEIGHT_PATH = configuration.get('PLATE', 'car_plate_detection_weight_path')
CAR_PLATE_DETECTION_CFG_PATH = configuration.get('PLATE', 'car_plate_detection_config_path')
CAR_PLATE_DETECTION_THR = configuration.getfloat('PLATE', 'car_plate_detection_thr')
CAR_DETECTION_WEIGHT_PATH = configuration.get('PLATE', 'car_detection_weight_path')
CAR_DETECTION_CFG_PATH = configuration.get('PLATE', 'car_detection_config_path')
CAR_DETECTION_THR = configuration.getfloat('PLATE', 'car_detection_thr')

# Other
BAD_PLATE_TEMPLATE_PATH = "assets/bad_plate.jpg"
WIM_ID = 0
CHAR_DIC = [
    "A",
    "B",
    "P",
    "W",
    "X",
    "J",
    "D",
    "C",
    "S",
    "T",
    "E",
    "G",
    "L",
    "M",
    "N",
    "V",
    "H",
    "Y",
    "%",
]
