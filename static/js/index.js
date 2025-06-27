var socket = io();

socket.on('connect', function() {
    socket.emit('hello');
    socket.emit('shape_options',vm.shape_options);
    socket.emit('line_options',vm.line_options);
    socket.emit('z_plane',vm.z_plane);
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
    // Direct assignments and conversions as needed
    if (data.transition_rate !== undefined) vm.shape_options.transition_rate = Number(data.transition_rate);
    if (data.repetitions !== undefined) vm.shape_options.repetitions = Number(data.repetitions);
    if (data.base_shape !== undefined) vm.shape_options.base_shape = data.base_shape;
    if (data.num_center_points !== undefined) vm.shape_options.num_center_points = Number(data.num_center_points);
    if (data.rotation !== undefined) vm.shape_options.rotation = Number(data.rotation);
    if (data.free_hand_form !== undefined) vm.shape_options.free_hand_form = data.free_hand_form;

    // Convert Python tuples to JS arrays for points/growth_directions
    if (data.center_points !== undefined) vm.shape_options.points = data.center_points.map(arr => Array.from(arr));
    if (data.growth_directions !== undefined) vm.shape_options.growth_directions = data.growth_directions.map(arr => Array.from(arr));

    // If diameter is a list of [x, y] pairs, split into diameter_x and diameter_y
    if (Array.isArray(data.diameter) && data.diameter.length > 0 && Array.isArray(data.diameter[0])) {
        vm.shape_options.diameter_x = data.diameter.map(pair => Number(pair[0]));
        vm.shape_options.diameter_y = data.diameter.map(pair => Number(pair[1]));
    }
});

socket.on('update_line_options', (data) => {
    Object.assign(vm.line_options, data);
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
socket.on('z_plane_preview', (data) => {
    vm.z_plane_displacement = data["displacement"]
});
socket.on('webhook_url', (data) => {
    vm.webhookUrl = data.url
});

// Listen for the trigger_print event and call the print function
socket.on('trigger_print', function() {
    vm.print();
});
//Resume print
socket.on('printer_pause_resume', function() {
    socket.emit('printer_pause_resume');
});