import winreg


def set_reg(name, value):
    registry_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                  "Software\VB and VBA Program Settings\SPEED_CONTROL\CAPTURE_MAIN", 0,
                                  winreg.KEY_WRITE)
    winreg.SetValueEx(registry_key, name, 0, winreg.REG_SZ, value)
    winreg.CloseKey(registry_key)


def get_reg(name):
    try:
        registry_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                      "Software\VB and VBA Program Settings\SPEED_CONTROL\CAPTURE_MAIN", 0,
                                      winreg.KEY_READ)
        value, regtype = winreg.QueryValueEx(registry_key, name)
        winreg.CloseKey(registry_key)
        return value
    except WindowsError:
        return None


def set_ir_value(value):
    if value == 0:
        set_reg("RelayControl1", "0")
        # set_reg("PWM_On", "0")
        print("[  INFO  ] IR status: OFF")
    else:
        set_reg("RelayControl1", "1")
        # set_reg("PWM_On", str(int(value)))
        print("[  INFO  ] IR value: ", value)