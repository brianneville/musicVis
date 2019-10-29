import requests
import time
import numpy as np
import json
import base64
import socket
from queue import Queue
from scipy.io.wavfile import read as read_wavefile
from pydub import AudioSegment

np.set_printoptions(threshold=np.inf)

def test():
    time.sleep(3)
    # http://jamie-wong.com/2016/08/05/webgl-fluid-simulation/
    msg = [0, 0, 0, 0,  # white, white, white, white
           0, 0, 1, 0,  # white, red, green, white
           0, 1, 0, 1,  # white, blue, yellow, white
           0, 0, 0, 0]  # white, white, white, white

    requests.get(f'http://localhost:3000/q/{np.array(msg)}', verify=False)
    time.sleep(2)

    frame = 1/24   # seconds per frame
    width = height = 10

    sethw(height, width)
    arr_len = width*height
    arr = np.zeros(arr_len, dtype=int)

    prev_i = -1
    while 1:
        for i in range(0, arr_len):
            arr[i] = 1
            if 1 + prev_i:
                arr[prev_i] = 0
            prev_i = i
            requests.get(f'http://localhost:3000/q/{arr}', verify=False)
            time.sleep(frame)


def sethw(h, w):
    obj = {'h': h, 'w': w}
    requests.get(f'http://localhost:3000/p/{json.dumps(obj)}', verify=False)


class MusicDisp():

    def __init__(self, q, portnum=3000,addr='127.0.0.1', max_buf=25000000): # max file len = 25Mb
        self.portnum = portnum
        self.q = q
        self.addr = addr
        self.max_buf = max_buf
        self.recent_mp3_fname = 'out.mp3'
        self.bars_rate = 4      # 4 bars/sec

    def listen(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.addr,  self.portnum))
            s.sendall(b"GET /getfile/ HTTP/1.1\r\nHost: localhost:3000\r\n\r\n")
            recv = s.recv(self.max_buf)
            self.q.put(recv)

    def create_waveform(self):

        audio = AudioSegment.from_mp3(self.recent_mp3_fname)
        duration=len(audio)//1000  # duration in seconds
        data = np.fromstring(audio._data, np.int16)

        section_len = len(data)//(self.bars_rate*duration)
        section_count = len(data)//section_len
        print(f"{section_count} sections, each of length {section_len} data items")
        outputs = np.array([], dtype=int)
        ovr_max = 0
        full = 0
        max_val = 0
        for i in range(0, len(data)):
            v = abs(data[i])
            if full == section_len:
                outputs = np.append(outputs, [max_val])  # append max value from that second to the outputs
                full = 0
                max_val = 0
            else:
                if v > max_val:
                    max_val = v
                    if v > ovr_max:
                        ovr_max = v
                full += 1
        return outputs/ovr_max, ovr_max


    def send_periodic(self, waveform, max_val):
        width = height = 30
        disp_arr = np.zeros((width*height,), dtype=int).reshape((width, height))
        sethw(height, width)
        # scale all the max values to fit in this height
        section_right = 0
        # ------------------------- initial
        # create initial waveform of song
        """
        disp_sections = waveform[0:section_right]
        bar_height = disp_sections*height

        # initial population of display array
        for i in range(0, width):
            stop_bar = round(bar_height[i])     # draw bar up to this height
            disp_arr[i][0:int(stop_bar)] = 1

        send_arr = np.rot90(disp_arr)

        requests.get(f'http://localhost:3000/q/{send_arr.flatten()}', verify=False)
        section_right += 1
        """
        # ------------ rest of song
        start = time.time()
        end = None
        sync_substract = 0  # subtract time that the script is working so that song doesnt go out of sync
        while section_right < len(waveform) + width:
            # get the next bar to add to the disp_array and shift all bars left to accomodate
            next_wval = 0
            if section_right < len(waveform):
                next_wval = waveform[section_right]

            stop_bar = round(next_wval*height)  # draw bar up to this height
            disp_arr = np.roll(disp_arr, -1, axis=0)        # shift all items in array to the index ahead of them

            disp_arr[width-1][0:int(stop_bar)] = 1  # insert new row
            disp_arr[width-1][int(stop_bar):] = 0
            # print(next)
            # print(disp_arr[width-1])
            send_arr = np.rot90(disp_arr)

            requests.get(f'http://localhost:3000/q/{send_arr.flatten()}', verify=False)
            section_right += 1
            if end is None:
                end = time.time()
                sync_substract = start - end
            time.sleep((1/self.bars_rate) - sync_substract-0.08)



if __name__ == '__main__':
    shared_q = Queue()
    m = MusicDisp(shared_q)
    m.listen()


    while 1:
        if not shared_q.empty():
            item = shared_q.get().decode()
            item = item[item.rfind('\r\n') + len('\r\n'):] # remove http header
            if item:
                print('song received')
                item = item[item.find(',')+1:]
                item = base64.b64decode(item)
                with open("out.mp3", 'wb+') as f:
                    f.write(item)
                waveform, max_val = m.create_waveform()
                m.send_periodic(waveform, max_val)
                break


















"""
msg = {'r': [
    0xff, 0xff, 0xff, 0xff,  # white, white, white, white
    0xff, 0x00, 0xff, 0xff,  # white, red, green, white
    0xff, 0x00, 0x00, 0xff,  # white, blue, yellow, white
    0xff, 0xff, 0xff, 0xff,  # white, white, white, white
], 'g': [
    0xff, 0xff, 0xff, 0xff,  # white, white, white, white
    0xff, 0x00, 0x00, 0xff,  # white, red, green, white
    0xff, 0x00, 0xff, 0xff,  # white, blue, yellow, white
    0xff, 0xff, 0xff, 0xff,  # white, white, white, white
], 'b': [
    0xff, 0xff, 0xff, 0xff,  # white, white, white, white
    0xff, 0x00, 0x00, 0xff,  # white, red, green, white
    0xff, 0xff, 0x00, 0xff,  # white, blue, yellow, white
    0xff, 0xff, 0xff, 0xff,  # white, white, white, white
]}
"""