import os
import sys
import time
import pandas as pd

from settings import WORKING_DIR

slut_file_path = os.path.join(WORKING_DIR, 'assets/slut.xlsx')

if os.path.exists(slut_file_path):
    try:
        slut_data = pd.read_excel(slut_file_path, squeeze=True, header=None)
        conversions = slut_data[0]
        # speed_coefficients = slut_data[1]
        print(slut_data)
    except:
        print("[  EROR  ] Could not read speed file!!!")
        time.sleep(30)
        sys.exit()
else:
    print("[  EROR  ] Speed file is not exists!!!")
    time.sleep(30)
    sys.exit()
