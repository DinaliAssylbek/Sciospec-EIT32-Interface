import time
import os
import traceback
import serial
import struct
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import shared_functions as sf

from typing import Union, List
from multiprocessing import Process, Queue, Event
from queue import Empty
from measurment_setup import set_measurement_setup, get_measurement_setup
from output_configs import set_output_config, get_output_config
from datetime import datetime


params = {
  "Burst Count" : 1000,
  "Frame Rate" : 50,
  "Excitation Frequencies" : {"Fmin" : 50000, "Fmax": 50000, "Ftype": 0},
  "Excitation Amplitude" : 0.001,
  "Excitation Switch Type" : 2,
  "Excitation Sequence" : [(1,3), (2,4), (3,5), (4,6), (5,7), (6,8), (7,1), (8,2)],
  "ADC Range" : 2,
  "Single Ended": {"Mode": 1, "Boundary": 1}
}

configurations = {
  "Excitation Setting" : 1,
  "Current row in the frequency stack" : 0,
  "Timestamp" : 1
}

sequence_display = {
  "Excitation Sequence" : [(1,3), (4,6)]
}

    
def read_from_serial(q, stop_event, ser):
  while True:
    buffer = ser.read()
    if buffer:
      q.put(buffer)
      continue
    stop_event.set()
    break

def process_data(q, stop_event, configs, dataset_name, directory_path, live_data_queue, live_timestamp_queue, sequence):
  items = []
  frames = []
  current_frame = []
  frame_started = False
  frame_length = 0
  frame_count = 0
  file_output = ['18'],
  the_first = [],
  curr_sequence = -1
  file_num = 0
  while not stop_event.is_set() or not q.empty():
    try:
      item = q.get(timeout=1)
      num = int.from_bytes(item, byteorder='big')
      items.append(num)
       # Check for the start of a frame
      if num == 180 and not frame_started:
        frame_started = True
        current_frame = [num]
        frame_length = 0
        continue
      
      # If a frame has started, add to the current frame
      if frame_started:
          current_frame.append(num)
          if len(current_frame) == 2:  # second byte indicates the frame length
            frame_length = num + 1

          # Check for the end of the frame
          if len(current_frame) > 2 and len(current_frame) == frame_length + 2:
            frames.append(current_frame)
            frame_count += 1
            if frame_count == 1:
              the_first = [str(current_frame[3]), str(current_frame[4])]

            if [str(current_frame[3]), str(current_frame[4])] == the_first:
              if current_frame[2] == 1:
                if frame_count != 1:
                  file_num += 1
                  file_path = os.path.join(directory_path, f'{dataset_name}_{file_num}.txt')
                  with open(file_path, 'w') as file:
                    for line in file_output:
                      file.write(line + '\n')
                now = datetime.now()
                file_output = ['18', str(frame_count), dataset_name, now.strftime("%Y.%m.%d. %H:%M:%S.%f")[:-3]] + configs + [str(current_frame[4]) + " " + str(current_frame[3])]
              else:
                all_data = frames[-1][9:-1] + current_frame[9:-1]
                floats = []
                for i in range(0, len(all_data), 4):
                  byte_chunk = all_data[i:i+4]
                  if len(byte_chunk) == 4:
                    float_number = struct.unpack('>f', bytes(byte_chunk))[0]
                    floats.append(float_number)
                curr_sequence = (curr_sequence + 1) % len(sequence)
                for index in range(len(live_data_queue[0])):
                  live_data_queue[0][index].put(floats[index * 2])
                live_timestamp_queue[0].put(time.time())
                file_output += [' '.join(map(str, floats))]
            else:
              if current_frame[2] == 1:
                file_output += [str(current_frame[4]) + " " + str(current_frame[3])]
              else:
                all_data = frames[-1][9:-1] + current_frame[9:-1]
                floats = []
                for i in range(0, len(all_data), 4):
                  byte_chunk = all_data[i:i+4]
                  if len(byte_chunk) == 4:
                    float_number = struct.unpack('>f', bytes(byte_chunk))[0]
                    floats.append(float_number)
                curr_sequence = (curr_sequence + 1) % len(sequence)
                for index in range(len(live_data_queue[0])):
                  live_data_queue[curr_sequence][index].put(floats[index * 2])
                live_timestamp_queue[curr_sequence].put(time.time())
                file_output += [' '.join(map(str, floats))]
            frame_started = False
    except Empty:
      continue
    except Exception as e:
      tb = traceback.format_exc()
      print(f"An error occurred: {e}")
      print("Traceback details:")
      print(tb)
  file_num += 1
  file_path = os.path.join(directory_path, f'{dataset_name}_{file_num}.txt')
  with open(file_path, 'w') as file:
    for line in file_output:
        file.write(line + '\n')
    
def StartStopMeasurement(q, stop_event) -> list:
    ser = sf.init_serial()
    print("Starting measurement.")
    ser.write(bytearray([0xB4, 0x01, 0x01, 0xB4]))
    measurement_data_hex = read_from_serial(q, stop_event, ser)
    print("Stopping measurement.")
    ser.write(bytearray([0xB4, 0x01, 0x00, 0xB4]))
    return measurement_data_hex

def measurment(dataset_name, directory_path, live_data_queue, live_timestamp_queue, configs):
  # configs = get_measurement_setup()
  # for i in range(len(configs[-1])):
  #   live_data_queue.append([Queue() for j in range(8)])
  #   live_timestamp_queue.append(Queue())
  q = Queue()
  stop_event = Event()
  read_process = Process(target=StartStopMeasurement, args=(q, stop_event))
  process_process = Process(target=process_data, args=(q, stop_event, configs[:-2], dataset_name, directory_path, live_data_queue, live_timestamp_queue, configs[-1]))
  read_process.start()
  process_process.start()
  
def update_graph(frame, x_data, y_data, live_data_queue, lines, live_timestamp_queue):
    try:
      while True:
        for i in range(len(y_data)):
          y_data[i].append(live_data_queue[i].get_nowait())
        x_data.append(live_timestamp_queue.get_nowait())
    except Empty:
      pass

    if x_data:
      for i, line in enumerate(lines):
        line.set_data(x_data, y_data[i])
        ax = line.axes
        ax.set_xlim(x_data[0], x_data[-1])
        ax.set_ylim(min(y_data[i]), max(y_data[i]))
    return lines

def measure():
  configs = get_measurement_setup()
  print(configs[-1])
  live_data_queue = [[Queue() for i in range(8)] for j in range(len(configs[-1]))]
  live_timestamp_queue = [Queue() for i in range(len(configs[-1]))]
  measurment('hello', 'D:/Sciospec-EIT32-Interface/test_output', live_data_queue, live_timestamp_queue, configs)
  figs, axes, lines, anis = [], [], [], []
  for i in range(len(configs[-1])):
    fig, ax = plt.subplots(8,1, sharex=True)
    figs.append(fig)
    axes.append(ax)
    
    x_data, y_data = [], [[] for _ in range(8)]
    line = [a.plot([], [])[0] for a in ax]
    lines.append(line)

    ani = animation.FuncAnimation(fig, update_graph, fargs=(x_data, y_data, live_data_queue[i], line, live_timestamp_queue[i]), interval=1000)
    anis.append(ani)
  plt.show()


if __name__ == '__main__':
  set_measurement_setup(params)
  set_output_config(configurations)
  measure()
  # live_data_queue = [[Queue() for i in range(8)] for j in range(1)]
  # live_timestamp_queue = [Queue()]
  # measurment('hello', '//chips.eng.utah.edu/home/u1462232/.win_desktop/Sciospec-EIT32-Interface/test_output', live_data_queue, live_timestamp_queue)
  # figs, axes, lines, anis = [], [], [], []
  # for i in range(2):
  #   fig, ax = plt.subplots(8,1, sharex=True)
  #   figs.append(fig)
  #   axes.append(ax)
    
  #   x_data, y_data = [], [[] for _ in range(8)]
  #   line = [a.plot([], [])[0] for a in ax]
  #   lines.append(line)

  #   ani = animation.FuncAnimation(fig, update_graph, fargs=(x_data, y_data, live_data_queue[i], line, live_timestamp_queue), interval=1000)
  #   anis.append(ani)
  # plt.show()