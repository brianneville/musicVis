import requests
import time
import numpy as np
import json
import base64
import socket
from queue import Queue
from pydub import AudioSegment

np.set_printoptions(threshold=np.inf)

def test():
    time.sleep(3)
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


def finddelay_sethw(h, w):
    obj = {'h': h, 'w': w}
    t0 = time.time()
    client_return_time = requests.get(f'http://localhost:3000/p/{json.dumps(obj)}', verify=False)
    rtt_total = (time.time() - t0)
    return (rtt_total - float(client_return_time.text)/1000)/2


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

        section_len = len(data)//(self.bars_rate*duration)      # number of data samples per section (bar)
        section_count = len(data)//section_len      # number of sections
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
        return outputs/ovr_max


    def send_periodic(self, waveform):
        width = height = 30
        disp_arr = np.zeros((width*height,), dtype=int).reshape((width, height))
        parsing_and_travel = finddelay_sethw(height, width)
        # scale all the max values to fit in this height
        section_right = 0

        # ------------ draw song
        start = time.time()
        sync_substract = None  # subtract time that the script is working so that song doesnt go out of sync
        while section_right < len(waveform) + width:
            # get the next bar to add to the disp_array and shift all bars left to accomodate
            next_wval = 0
            if section_right < len(waveform):
                next_wval = waveform[section_right]

            stop_bar = round(next_wval*height)  # draw bar up to this height
            disp_arr = np.roll(disp_arr, -1, axis=0)        # shift all items in array to the index ahead of them

            disp_arr[width-1][0:int(stop_bar)] = 1  # insert new row
            disp_arr[width-1][int(stop_bar):] = 0

            send_arr = np.rot90(disp_arr)
            control_flags = requests.get(f"http://localhost:3000/q/{(send_arr.flatten()).tolist()}", verify=False)

            section_right += 1
            if sync_substract is None:
                sync_substract = time.time() - start
            time.sleep((1 / self.bars_rate) + sync_substract - 0.0805 - parsing_and_travel)
            # this 0.08 is a bit arbitrary but seems to work great
            if control_flags.text == "stop":
                print("stopped stream")
                break

if __name__ == '__main__':
    shared_q = Queue()
    while 1:
        m = MusicDisp(shared_q)
        m.listen()

        if not shared_q.empty():
            item = shared_q.get().decode()
            item = item[item.rfind('\r\n') + len('\r\n'):] # remove http header
            if item:
                print('song received')

                item = item[item.find(',')+1:]
                item = base64.b64decode(item)
                with open("out.mp3", 'wb+') as f:
                    f.write(item)
                waveform = m.create_waveform()
                print("stream started")
                m.send_periodic(waveform)

                with shared_q.mutex:
                    shared_q.queue.clear()


