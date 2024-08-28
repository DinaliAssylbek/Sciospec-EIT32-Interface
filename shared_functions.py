import serial

errors = {
  1 : "Frame-Not-Acknowledge: Incorrect syntax",
  2 : "Timeout: Communication-timeout (less data than expected)",
  4 : "Wake-Up Message: System boot ready",
  17 :  "TCP-Socket: Valid TCP client-socket connection",
  129 : "Not-Acknowledge: Command has not been executed",
  130 : "Not-Acknowledge: Command could not be recognized",
  132 : "System-Ready Message: System is operational and ready to receive data",
  140 : "Data holdup: Measurement data could not be sent via the master interface"
}

def init_serial():
  ser = serial.Serial('COM3', baudrate=9600, timeout=2,parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE,bytesize=serial.EIGHTBITS)
  if ser.is_open:
    return ser
  else:
      return None

def valid_argument(setting, value, ser):
  output = list(ser.readline())
  if output[2] == 131:
    print(f'{setting} Set To: {value}')
  else:
    print(f'Error Setting {setting}: {errors[output[2]]}')

def read_measurment(ser):
  output = list(ser.readline())
  if output[-2] == 131:
    return output[:-4]
  else:
    print(f'Error: {errors[output[-2]]}')
    return []