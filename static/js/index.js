var socket = io();

socket.on('connect', function() {
    socket.emit('hello');
    socket.emit('shape_options',vm.shape_options);
    socket.emit('line_options',vm.line_options);
});

socket.on('layer', (data) => {
    vm.layer = data.layer
});
socket.on('start_print', () => {
    vm.printing = true;
});

socket.on('update_ai_scores', (data) => {
    vm.ai_scores = data
});

socket.on('slicer_options', (data) => {
    vm.slicer_options = data
});

socket.on('update_shape_options', (data) => {
    vm.shape_options.diameter_x = data["diameter"][0]
    vm.shape_options.diameter_y = data["diameter"][1]
});
socket.on('update_line_options', (data) => {
    vm.line_options.frequency= data["frequency"]
    vm.line_options.amplitude = data["amplitude"]
    vm.line_options.pattern_start = data["pattern_start"]
    vm.line_options.pattern_range = data["pattern_range"]
});

socket.on('connected', (data) => {
    vm.connected = data.connected
});
socket.on('update_current_shape', (data) => {
    vm.current_shape = data
});
socket.on('line_preview', (data) => {
    vm.line_displacement = data["line_displacement"]
});
socket.on('webhook_url', (data) => {
    vm.webhookUrl = data.url
});
socket.on('visualize_infill', (data) => {
    vm.infill = data["infill"]
    console.log("infill rec " + vm.infill[0])
    console.log("infill rec l " + vm.infill.length)
});

// Listen for the trigger_print event and call the print function
socket.on('trigger_print', function() {
    vm.print();
});
//Resume print
socket.on('printer_pause_resume', function() {
    socket.emit('printer_pause_resume');
});