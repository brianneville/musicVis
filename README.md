# musicVis
A web client and backend pipeline that stream a waveform of the music you upload.

order of operations:

1. start node.js server (install dependancies if needed)
```
node backend.js
```

2. run python backend script
```
python pybackend.py
```
3. connect to http://localhost:3000/

4. select a song and watch the stream!



*note: pydub is used, which requires downloading ffmpeg and adding path\to\ffmpeg\bin\ to the system Path

## Video 
[Click here and download the video](https://github.com/brianneville/musicVis/blob/master/demo/musicVis_demo.mp4 "github.com/brianneville/musicVis...")
(hosted in this repo)

Recorded with Xbox Game bar, which for some reason ommits a portion of the visualiser on the left hand side. See screenshots for the actual visuals

## Screencaps

![Screencap 0][0]
![Screencap 2][2]
![Screencap 3][3]
![Screencap 5][5]

[0]: https://github.com/brianneville/musicVis/blob/master/demo/screencap/0.png
[2]: https://github.com/brianneville/musicVis/blob/master/demo/screencap/2.png
[3]: https://github.com/brianneville/musicVis/blob/master/demo/screencap/3.png
[5]: https://github.com/brianneville/musicVis/blob/master/demo/screencap/5.png
