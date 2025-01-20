var socket = io();
    socket.on('connect', function() {
        socket.emit('connecting', {data: 'I\'m connected!'});
    });