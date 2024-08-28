import struct
import shared_functions as sf

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
  print(output)
  sequence = []
  for i in range(0, len(output), 4):
    curr = output[i:i+4]
    print(curr)
    sequence.append(({((curr[2]<< 8) | curr[3])},{((curr[0] << 8) | curr[1])}))
  configs += [sequence]
  ser.close()
  return configs