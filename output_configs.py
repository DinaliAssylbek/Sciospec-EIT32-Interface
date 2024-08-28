import shared_functions as sf

def set_output_config(configs):
  '''
    struct(
        'Excitation Setting', 0 - Off : 1 - On, 
        'Current row in the frequency stack', 0 - Off : 1 - On, 
        'Timestamp', 0 - Off : 1 - On
    );
  '''
  ser = sf.init_serial()
  # Set Excitation Setting
  if "Excitation Setting" in configs:
    ser.write(bytearray([0xB2, 0x02, 0x01, configs["Excitation Setting"], 0xB2]))
  
  # Set Current row in the frequency stack
  if "Current row in the frequency stack" in configs:
    ser.write(bytearray([0xB2, 0x02, 0x02, configs["Current row in the frequency stack"], 0xB2]))
  
  # Set Timestamp
  if "Timestamp" in configs:
    ser.write(bytearray([0xB2, 0x02, 0x03, configs["Timestamp"], 0xB2]))

def get_output_config():
  ser = sf.init_serial()

  # Get Excitation Setting
  ser.write(bytearray([0xB3, 0x01, 0x01, 0xB3]))
  output = list(ser.readline())
  print("Excitation Setting: " + ("True" if output[3] == 1 else "False"))

  # Get Current row in the frequency stack
  ser.write(bytearray([0xB3, 0x01, 0x02, 0xB3]))
  output = list(ser.readline())
  print("Current row in the frequency stack: " + ("True" if output[3] == 1 else "False"))

  # Get Timestamp
  ser.write(bytearray([0xB3, 0x01, 0x03, 0xB3]))
  output = list(ser.readline())
  print("Timestamp: " + ("True" if output[3] == 1 else "False"))
