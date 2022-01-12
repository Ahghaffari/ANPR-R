import pyodbc

from settings import *

if DB_TYPE == "mysql":
    import mysql.connector

    mydb = mysql.connector.connect(
        host=MYSQL_SERVER,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE
    )

    mycursor = mydb.cursor()


    def save_into_database(seen_time, plate, state, line, car_image, plate_image, side_image, speed, wim_id, counter,
                           counter2=None):
        command = "INSERT INTO ocr (plate, state, line, car_image, plate_image, side_image, speed, wim_id, counter, time) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"

        values = (plate, state, line, car_image, plate_image, side_image, speed, wim_id, counter, seen_time)
        mycursor.execute(command, values)

        mydb.commit()

        print("[  INFO  ] Record inserted")

elif DB_TYPE == "sql_server":
    def save_into_database(seen_time, Plate, StatFlag, Line, FullImage, PlateImage, SideImage, Speed, wim_id,
                           Counter1,
                           Counter2, car_type):
        dsn = "Driver={SQL Server};Server=.;Database=WIMDB;Trusted_Connection=no;uid=sa;pwd=1234;"
        conn = pyodbc.connect(dsn)

        if StatFlag == 'O':
            P = Plate[0:-1].replace("0", "5")
            P = P + Plate[-1]
            Plate = P

        if Counter1 == 'ADRegNet Opened' or Counter1 == '' or (Counter1 == 'None') or Counter1 == 'ADRegNet Closed' or Counter1 == 'ADRegNet Created':
            Counter1 = 0

        if Counter2 == 'ADRegNet Opened' or Counter2 == '' or (Counter2 == 'None') or Counter2 == 'ADRegNet Closed' or Counter2 == 'ADRegNet Created':
            Counter2 = 0

        # if Plate[2] != 'E' and car_type == 1:
        #     car_type = 0

        cursor = conn.cursor()
        query = 'EXEC Towzin_ANPR_InsertToDB ' \
                '@MotionTime = \'%s\' ,' \
                '@Plate = \'%s\',' \
                '@StatFlag = \'%s\',' \
                '@Line = \'%s\',' \
                '@FullImage = \'%s\', ' \
                '@PlateImage = \'%s\', ' \
                '@SideImage = \'%s\', ' \
                '@Speed = %d, ' \
                '@WIMID = %d, ' \
                '@Counter1 = %d, ' \
                '@Counter2 = %d, ' \
                '@car_type = %d' % (
                    seen_time, Plate, StatFlag, Line, FullImage, PlateImage, SideImage, int(Speed), int(wim_id),
                    int(Counter1),
                    int(Counter2), int(car_type))

        try:
            cursor.execute(query)
            cursor.commit()

            print("[  INFO  ] Record inserted successfully: ", Plate, Line, car_type)
        except:
            print("[  INFO  ] problem in inserting to database: ", Plate, Line, car_type)