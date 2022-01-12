from settings import *
from car_detection import detect_car_type

if ROAD_THREE_LANE is False:
    def determine_lane_and_update_speed(x, y, w, h, speed, frame=None):

        plate_width_center = x + w / 2

        car_type = -1
        if OCR_CAR_TYPE_DETECTION:
            car_type = detect_car_type(frame, x, y)

        if plate_width_center <= ROAD_V_SEPARATOR2:
            if plate_width_center <= ROAD_V_SEPARATOR1:
                line_status = "L1"
            else:
                line_status = "C1"

            speed += SPEED_OFFSET_L1

            if car_type == 1:
                speed += SPEED_OFFSET_HEAVY_L1
        else:
            if plate_width_center > ROAD_V_SEPARATOR3:
                line_status = "L2"
            else:
                line_status = "C2"

            speed += SPEED_OFFSET_L2

            if car_type == 1:
                speed += SPEED_OFFSET_HEAVY_L2

        return line_status, speed, car_type
else:
    def determine_lane_and_update_speed(x, y, w, h, speed, frame=None):
        plate_width_center = x + w / 2

        x_line1 = (y - ROAD_L1_B) / ROAD_L1_A
        x_line2 = (y - ROAD_L2_B) / ROAD_L2_A
        x_line3 = (y - ROAD_L3_B) / ROAD_L3_A
        x_line4 = (y - ROAD_L4_B) / ROAD_L4_A

        x_lineC1 = (y - ROAD_C1_B) / ROAD_C1_A
        x_lineC2 = (y - ROAD_C2_B) / ROAD_C2_A

        car_type = -1
        if OCR_CAR_TYPE_DETECTION:
            car_type = detect_car_type(frame, x, y)

        if plate_width_center < x_line1:
            line_status = "L3"
            speed += SPEED_OFFSET_L3

            if car_type == 1:
                speed += SPEED_OFFSET_HEAVY_L3

        elif plate_width_center < x_line2:
            if plate_width_center < x_lineC1:
                line_status = "C233"
            else:
                line_status = "C232"
            speed += SPEED_OFFSET_L23

            if car_type == 1:
                speed += SPEED_OFFSET_HEAVY_L23

        elif plate_width_center < x_line3:
            line_status = "L2"
            speed += SPEED_OFFSET_L2

            if car_type == 1:
                speed += SPEED_OFFSET_HEAVY_L2

        elif plate_width_center < x_line4:
            if plate_width_center < x_lineC2:
                line_status = "C122"
            else:
                line_status = "C121"
            speed += SPEED_OFFSET_L12

            if car_type == 1:
                speed += SPEED_OFFSET_HEAVY_L12

        else:
            line_status = "L1"
            speed += SPEED_OFFSET_L1

            if car_type == 1:
                speed += SPEED_OFFSET_HEAVY_L1

        return line_status, speed, car_type
