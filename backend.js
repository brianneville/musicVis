let fetch = require('node-fetch');
let fs = require('fs');
let app = require('express')();
let http = require('http').Server(app);
let io = require('socket.io')(http);

app.get('/', (req, res) => {
    res.sendFile(__dirname + '/clientUI.html')
});

app.get('/q/:msg/', pythonsays); 

app.get('/p/:hw/', update_hw);

app.get('/getfile/', send_file_back)

app.get('/controlpause/', unpause)

http.listen(3000, () => {
    console.log('Listening on port: 3000');
});
let sock_access = null
var filedata = ''

var most_recent_response = null
var update_hw_response = null
var control_flags = "";
var resume_response = null

io.on('connection', (socket) => {
    sock_access = socket
    console.log("found connection!!")
    
    socket.on('disconnect', () => {
        console.log("A user disconnected");
        sock_access.emit('recv_disconnect');
        //control_flags = '';
    });
    
    socket.on('filedata', (data)=>{
        console.log("updating filedata on server")
        control_flags = "";
        filedata = data;
        console.log(filedata.length)
        if(most_recent_response != null){
            most_recent_response.send(filedata)   
            filedata= '';  
        }
    });
    socket.on("timing_info", (data)=>{
        //return timing info to pybackend
        update_hw_response.send(data)
    });
    socket.on("set_control_flags", (data) =>{
        control_flags = data;
        console.log("set control flags to:" + data);
        if(control_flags == 'resume'){
            resume_response.send('resume')
        }
    });

});

function update_hw(request, response){
    update_hw_response = response
    let data = request.params.hw
    sock_access.emit('update_hw', (data));

}

function pythonsays(request, response){
    //can send information back to python in return value - e.g. stop, pause, skip
    response.send(control_flags)
    let data = request.params.msg;
    sock_access.emit('send_data', (data));
}

function send_file_back(request, response){
    most_recent_response = response
    console.log("sending file back")
    if(filedata != ''){     // account for the multiple different orders in which the .py and the html could occur
        response.send(filedata)
        most_recent_response = null
        filedata = '';
    }else{
        most_recent_response = response
    }
}

function unpause(request, response){
    console.log("unpause func has control flags as:", control_flags);
    if(control_flags != 'pause'){ 
        sock_access.emit('resume');
        
    }else{
        resume_response = response;
    }
}