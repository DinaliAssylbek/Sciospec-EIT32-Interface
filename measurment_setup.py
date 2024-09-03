import struct
import shared_functions as sf

class MeasurmentSetup:

  def __init__(self):
    self.ser = sf.init_serial()
  
  def set_measurment_setup(self, parameters):
    # First Reset Parameters to default
    self.ser.write(bytearray([0xB0, 0x01, 0x01, 0xB0]))

    # Set Burst Count
    if "Burst Count" in parameters:
      self.ser.write(bytearray([0xB0, 0x03, 0x02] + [int(bt) for bt in struct.pack(">H", parameters["Burst Count"])] + [0xB0]))
    
    # Set Frame Rate
    if "Frame Rate" in parameters:
      value = bytearray([0xB0, 0x05, 0x03] + [int(bt) for bt in struct.pack(">f", parameters["Frame Rate"])] + [0xB0])
      self.ser.write(value)

    # Set Excitation Frequencies
    if "Excitation Frequencies" in parameters:
      frequencies = []
      if "Fmin" in parameters["Excitation Frequencies"]:
        frequencies.append([int(bt) for bt in struct.pack(">f", parameters["Excitation Frequencies"]["Fmin"])])
      else:
        frequencies.append([int(bt) for bt in struct.pack(">f", 100000)])
      
      if "Fmax" in parameters["Excitation Frequencies"]:
        frequencies.append([int(bt) for bt in struct.pack(">f", parameters["Excitation Frequencies"]["Fmax"])])
      else:
        frequencies.append([int(bt) for bt in struct.pack(">f", 100000)])
      
      if "Fcount" in parameters["Excitation Frequencies"]:
        frequencies.append([int(bt) for bt in struct.pack(">H", parameters["Excitation Frequencies"]["Fcount"])])
      else:
        frequencies.append([int(bt) for bt in struct.pack(">H", 1)])

      if "Ftype" in parameters["Excitation Frequencies"]:
        frequencies.append([parameters["Excitation Frequencies"]["Ftype"]])
      else:
        frequencies.append([1])

      value = bytearray([0xB0, 0x0C, 0x04] + frequencies[0] + frequencies[1] + frequencies[2] + frequencies[3] + [0xB0])
      self.ser.write(value)

    # Set Excitation Amplitude
    if "Excitation Amplitude" in parameters:
      self.ser.write(bytearray([0xB0, 0x09, 0x05] + [int(bt) for bt in struct.pack(">d", parameters["Excitation Amplitude"])] + [0xB0]))

    # Set Single-Ended or Differential Measure Mode
    if "Single-Ended" in parameters:
      self.ser.write(bytearray([0xB0, 0x03, 0x08, 0x01, 0x01, 0xB0]))
      # sf.valid_argument("Single-Ended", 3, ser)
    if "Differential Measure Mode" in parameters:
      self.ser.write(bytearray([0xB0, 0x03, 0x08, parameters["Differential Measure Mode"]["Mode"], parameters["Differential Measure Mode"]["Boundary"], 0xB0]))

    # Set Excitation Sequence
    if "Excitation Sequence" in parameters:
      for sequence in parameters["Excitation Sequence"]:
        Cin, Cout = sequence
        # self.ser.readline()
        self.ser.write(bytearray([0xB0, 0x05, 0x06] + [int(bt) for bt in struct.pack(">H", Cout)] + [int(bt) for bt in struct.pack(">H", Cin)] + [0xB0]))

    # Set Excitation Switch Type
    if "Excitation Switch Type" in parameters and parameters["Excitation Switch Type"] == 2:
      self.ser.write(bytearray([0xB0, 0x02, 0x0C, 0x02, 0xB0]))
    
    if "ADC Range" in parameters:
      self.ser.write(bytearray([0xB0, 0x02, 0x0D, parameters["ADC Range"], 0xB0]))

  def get_measurement_setup(self):
    configs = []
    self.ser.readline()
    
    # Commands to retrieve parameters
    self.ser.write(bytearray([0xB1, 0x01, 0x04, 0xB1]))
    self.ser.write(bytearray([0xB1, 0x01, 0x05, 0xB1]))
    self.ser.write(bytearray([0xB1, 0x01, 0x03, 0xB1]))
    self.ser.write(bytearray([0xB1, 0x01, 0x0D, 0xB1]))
    self.ser.write(bytearray([0xB1, 0x01, 0x08, 0xB1]))
    self.ser.write(bytearray([0xB1, 0x01, 0x0C, 0xB1]))
    self.ser.write(bytearray([0xB1, 0x01, 0x06, 0xB1]))
    output = self.ser.readline()

    # Get Excitation Frequencies
    configs.append(str(round(struct.unpack(">f", bytearray(output[3:7]))[0], 8))) # Min Frequency
    configs.append(str(round(struct.unpack(">f", bytearray(output[7:11]))[0], 8))) # Max Frequency
    configs.append("0" if output[13] == 0 else "1") # Frequency Scale
    configs.append(str(((output[11] << 8) | output[12]))) # Frequency Count

    # Get Excitation Amplitude
    configs.append(str(round(struct.unpack(">f", bytearray(output[22:26]))[0], 8)))

    # Get Frame Rate
    configs.append(str(struct.unpack('>f', bytes(list(output[34:38])))[0]))

    # Get ADC Range
    configs.append(str(output[46]))

    # Get Single-Ended or Differential Measure Mode
    configs.append(str(output[55]))
    if (output[55] == 2 or output[55] == 3 or output[55] == 4) and output[56] == 1:
      configs.append("1") # Internal Boundary
    elif (output[55] == 2 or output[55] == 3 or output[55] == 4) and output[56] == 2:
      configs.append("2") # External Boundary
    
    # Get Excitation Switch Type
    configs.append(output[65])

    # Get Excitation Sequence
    if len(output[71:114]) < 33:
      output = output[74:-6]
    else:
      output = output[74:102] + output[106:-5]
    sequence = []
    for i in range(0, len(output), 4):
      curr = output[i:i+4]
      sequence.append(({((curr[2]<< 8) | curr[3])},{((curr[0] << 8) | curr[1])}))
    configs += [sequence]
    return configs
  
  def set_output_config(self, configs):
    # Set Excitation Setting
    if "Excitation Setting" in configs:
      self.ser.write(bytearray([0xB2, 0x02, 0x01, configs["Excitation Setting"], 0xB2]))
    
    # Set Current row in the frequency stack
    if "Current row in the frequency stack" in configs:
      self.ser.write(bytearray([0xB2, 0x02, 0x02, configs["Current row in the frequency stack"], 0xB2]))
    
    # Set Timestamp
    if "Timestamp" in configs:
      self.ser.write(bytearray([0xB2, 0x02, 0x03, configs["Timestamp"], 0xB2]))
    # self.ser.write(bytearray([0xB2, 0x02, 0x01, configs["Excitation Setting"], 0xB2, 0xB2, 0x02, 0x02, configs["Current row in the frequency stack"], 0xB2, 0xB2, 0x02, 0x03, configs["Timestamp"], 0xB2]))

  def close_connection(self):
      self.ser.close()
  
  def get_output_configs(self):
    self.ser.write(bytearray([0xB3, 0x01, 0x01, 0xB3]))
    self.ser.readline()
    print("Excitation Setting: " + ("True" if output[3] == 1 else "False"))

    # Get Current row in the frequency stack
    self.ser.write(bytearray([0xB3, 0x01, 0x02, 0xB3]))
    output = list(self.ser.readline())
    print("Current row in the frequency stack: " + ("True" if output[3] == 1 else "False"))

    # Get Timestamp
    self.ser.write(bytearray([0xB3, 0x01, 0x03, 0xB3]))
    output = list(self.ser.readline())
    print("Timestamp: " + ("True" if output[3] == 1 else "False"))

def set_measurement_setup(parameters):
  '''
    matlab_struct = struct();
    matlab_struct.('Burst Count') = (int) 0 - 65535 [Defualt : 0];
    matlab_struct.('Frame Rate') = (float) 0.1 - 100 [Default : 1];
    matlab_struct.('Excitation Frequency') = 
    [
      frequency_struct = struct();
      frequency_struct.('Fmin') = (float) 100 Hz - 10 MHz [Default : 100 kHz];
      frequency_struct.('Fmax') = (float) 100 Hz - 10 MHz [Defualt : 100 kHz];
      frequency_struct.('Fcount') = (int) 1 - 128 [Defualt : 1];
      frequency_struct.('Ftype') = (int) 0 - linear frequency distribution | 1 - logarithmic frequency distribution [Default : 0];
    ]
    matlab_struct.('Excitation Amplitude') = (float) 100 nA - 10 mA [Default : 0.01 A];
    matlab_struct.('Excitation Sequence') = (array) [(CDout, CDin), ];
    matlab_struct.('Single Ended') = ;
    matlab_struct.('Differential Measure Mode') = ;
    
      

    struct(
        'Burst Count', (int) 0 - 65535 [Defualt : 0], 
        'Frame Rate', 0 - Off : 1 - On, 
        'Excitation Frequency', 0 - Off : 1 - On,
        'Excitation Amplitude', ,
        'Single Ended', ,
        'Differential Measure Mode', ,
        'Excitation Sequence', ,
        'Excitation Switch Type', ,()
        'ADC Range', ,
    );
  '''
  ser = sf.init_serial()

  # First Reset Parameters to default
  ser.write(bytearray([0xB0, 0x01, 0x01, 0xB0]))

  # Set Burst Count
  if "Burst Count" in parameters:
    ser.write(bytearray([0xB0, 0x03, 0x02] + [int(bt) for bt in struct.pack(">H", parameters["Burst Count"])] + [0xB0]))
  
  # Set Frame Rate
  if "Frame Rate" in parameters:
    value = bytearray([0xB0, 0x05, 0x03] + [int(bt) for bt in struct.pack(">f", parameters["Frame Rate"])] + [0xB0])
    ser.write(value)

  # Set Excitation Frequencies
  if "Excitation Frequencies" in parameters:
    frequencies = []
    if "Fmin" in parameters["Excitation Frequencies"]:
      frequencies.append([int(bt) for bt in struct.pack(">f", parameters["Excitation Frequencies"]["Fmin"])])
    else:
      frequencies.append([int(bt) for bt in struct.pack(">f", 100000)])
    
    if "Fmax" in parameters["Excitation Frequencies"]:
      frequencies.append([int(bt) for bt in struct.pack(">f", parameters["Excitation Frequencies"]["Fmax"])])
    else:
      frequencies.append([int(bt) for bt in struct.pack(">f", 100000)])
    
    if "Fcount" in parameters["Excitation Frequencies"]:
      frequencies.append([int(bt) for bt in struct.pack(">H", parameters["Excitation Frequencies"]["Fcount"])])
    else:
      frequencies.append([int(bt) for bt in struct.pack(">H", 1)])

    if "Ftype" in parameters["Excitation Frequencies"]:
      frequencies.append([parameters["Excitation Frequencies"]["Ftype"]])
    else:
      frequencies.append([1])

    value = bytearray([0xB0, 0x0C, 0x04] + frequencies[0] + frequencies[1] + frequencies[2] + frequencies[3] + [0xB0])
    ser.write(value)

  # Set Excitation Amplitude
  if "Excitation Amplitude" in parameters:
    ser.write(bytearray([0xB0, 0x09, 0x05] + [int(bt) for bt in struct.pack(">d", parameters["Excitation Amplitude"])] + [0xB0]))

  # Set Single-Ended or Differential Measure Mode
  if "Single-Ended" in parameters:
    ser.write(bytearray([0xB0, 0x03, 0x08, 0x01, 0x01, 0xB0]))
    # sf.valid_argument("Single-Ended", 3, ser)
  if "Differential Measure Mode" in parameters:
    ser.write(bytearray([0xB0, 0x03, 0x08, parameters["Differential Measure Mode"]["Mode"], parameters["Differential Measure Mode"]["Boundary"], 0xB0]))

  # Set Excitation Sequence
  if "Excitation Sequence" in parameters:
    for sequence in parameters["Excitation Sequence"]:
      Cin, Cout = sequence
      ser.readline()
      ser.write(bytearray([0xB0, 0x05, 0x06] + [int(bt) for bt in struct.pack(">H", Cout)] + [int(bt) for bt in struct.pack(">H", Cin)] + [0xB0]))

  # Set Excitation Switch Type
  if "Excitation Switch Type" in parameters and parameters["Excitation Switch Type"] == 2:
    ser.write(bytearray([0xB0, 0x02, 0x0C, 0x02, 0xB0]))
  
  if "ADC Range" in parameters:
    ser.write(bytearray([0xB0, 0x02, 0x0D, parameters["ADC Range"], 0xB0]))
  ser.close()


def get_measurement_setup():
  ser = sf.init_serial()
  configs = []
  ser.readline()
  # Get Excitation Frequencies
  ser.write(bytearray([0xB1, 0x01, 0x04, 0xB1]))
  output = sf.read_measurment(ser)
  configs.append(str(round(struct.unpack(">f", bytearray(output[3:7]))[0], 8))) # Min Frequency
  configs.append(str(round(struct.unpack(">f", bytearray(output[7:11]))[0], 8))) # Max Frequency
  configs.append("0" if output[13] == 0 else "1") # Frequency Scale
  configs.append(str(((output[11] << 8) | output[12]))) # Frequency Count

  # Get Excitation Amplitude
  ser.write(bytearray([0xB1, 0x01, 0x05, 0xB1]))
  output = sf.read_measurment(ser)
  configs.append(str(round(struct.unpack(">f", bytearray(output[3:7]))[0], 8))) # Excitation Amplitude

  # Get Frame Rate
  ser.write(bytearray([0xB1, 0x01, 0x03, 0xB1]))
  output = sf.read_measurment(ser)
  configs.append(str(struct.unpack('>f', bytes(list(output[3:7])))[0]))

  # Get ADC Range
  ser.write(bytearray([0xB1, 0x01, 0x0D, 0xB1]))
  output = sf.read_measurment(ser)
  configs.append(str(output[3])) # ADC Range

  # Get Single-Ended or Differential Measure Mode
  ser.write(bytearray([0xB1, 0x01, 0x08, 0xB1]))
  output = sf.read_measurment(ser)
  configs.append(str(output[3])) 
  if (output[3] == 2 or output[3] == 3 or output[3] == 4) and output[4] == 1:
    configs.append("1") # Internal Boundary
  elif (output[3] == 2 or output[3] == 3 or output[3] == 4) and output[4] == 2:
    configs.append("2") # External Boundary

  # Get Excitation Switch Type
  ser.write(bytearray([0xB1, 0x01, 0x0C, 0xB1]))
  output = sf.read_measurment(ser)
  output.append(output[3])

  # Get Excitation Sequence
  ser.write(bytearray([0xB1, 0x01, 0x06, 0xB1]))
  output = sf.read_measurment(ser)
  print(output)
  if len(output) < 33:
    output = output[3:-2]
  else:
    output = output[3:31] + output[35:-1]
  sequence = []
  for i in range(0, len(output), 4):
    curr = output[i:i+4]
    sequence.append(({((curr[2]<< 8) | curr[3])},{((curr[0] << 8) | curr[1])}))
  configs += [sequence]
  ser.close()
  return configs