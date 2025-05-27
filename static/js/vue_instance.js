var socket = io();

const vm = new Vue({ // Again, vm is our Vue instance's name for consistency.
    el: '#vm',
    delimiters: ['[[', ']]'],
    components: {
        VueRangeSlider
    },
    data: {
        eth: {
            current: 0,
            last: 0,
        },
        // Canvas Magic
        points: [],
        draggedElement: null,
        shapeOpen: true,
        windowWidth: window.innerWidth,
        // UI elements
        printLable: "Print",
        pauseLable: "Pause",
        synced_to_bot: false,
        sentiment: 0,
        lenght: 0,
        polling: null,
        layer: 0,
        printing: false,
        connected: false,
        port: 'COM3',
        baud: '115200',
        log_text: "some random text and even more",
        value: 1,
        slicer_options: {
            extrusion_rate: 0,
            feed_rate: 0,
            layer_hight: 0.75
        },
        toolpath_options: {
            linelength: 50
        },
        shape_options: {
            repetitions: 1,
            base_shape: "circle",
            diameter_x: 60,
            diameter_y: 60,
            pattern_range:60,
            pattern_amplitude: 8,
            num_center_points: 4,
            growth_directions:[[-40,50], [40,5],[-40,-30],[-30,20],[-10,-30]],
            points: [[-40,50], [40,5],[-40,-30],[-30,20],[-10,-30]],
            filling: 0,
        },
        current_shape: {
            center_points: [[-40,50], [40,5],[-40,-30],[-30,20],[-10,-30]],
            diameter_x: 60,
            diameter_y: 60,
        },
        toolpath_type: "straight",
        plate_center_x: 100,
        plate_center_y: 100,
        draggedGrowthIndex: null,
        dragOffset: { x: 0, y: 0 },
    },
    mounted() {
    this.drawCenterPoints();
    const canvas = document.getElementById('centerPointsCanvas');
    canvas.addEventListener('mousedown', this.onCanvasMouseDown);
    canvas.addEventListener('mousemove', this.onCanvasMouseMove);
    canvas.addEventListener('mouseup', this.onCanvasMouseUp);
    canvas.addEventListener('mouseleave', this.onCanvasMouseUp);
    },
    watch: {
        // whenever question changes, this function will run
        layer: function (newValue, oldValue) {
            socket.emit('layer', {'layer': newValue});
        },
        slicer_options: {
            handler: function (newValue, oldValue) {
                socket.emit('slicer_options', this.slicer_options);
            },
            deep: true
        },
        current_shape: {
            handler: function (newValue, oldValue) {
                this.drawCenterPoints();
            },
            deep: true
        },
        shape_options: {
            handler: function (newValue, oldValue) {
                socket.emit('shape_options', this.shape_options);
            },
            deep: true
        },
        'shape_options.diameter_x': function(newValue, oldValue) {
            this.drawCenterPoints();
        },
        'shape_options.diameter_y': function(newValue, oldValue) {
            this.drawCenterPoints();
        },
        'shape_options.num_center_points': function(newValue, oldValue) {
            this.drawCenterPoints();
        },
        'shape_options.base_shape': function(newValue, oldValue) {
            this.drawCenterPoints();
        },
        toolpath_type: function (newValue, oldValue) {
            socket.emit('toolpath_type', {'toolpath_type': newValue});
        },
    },
    computed: { 
        isPrinting: function () {
          return this.polling != null
        },
        stringPoints: function () {
            output = "";
            this.points.forEach(function (point, index) {
                output = output + point[0] + "," + point[1] + " ";
            });
            return output;
        },
        svgFactor: function () {
            return 150 / this.windowWidth;
        },
    },
    methods: {
        onCanvasMouseDown: function(e) {
            const canvas = document.getElementById('centerPointsCanvas');
            const rect = canvas.getBoundingClientRect();
            const mouseX = e.clientX - rect.left;
            const mouseY = e.clientY - rect.top;

            const num_points = this.shape_options.num_center_points;
            const centerX = canvas.width / 2;
            const centerY = canvas.height / 2;

            for (let i = 0; i < num_points; i++) {
                const direction_x = this.shape_options.growth_directions[i][0]*2;
                const direction_y = this.shape_options.growth_directions[i][1]*2;
                const handleX = centerX + direction_x;
                const handleY = centerY + direction_y;
            // Check if mouse is near the handle
                if (Math.hypot(mouseX - handleX, mouseY - handleY) < 12) {
                    this.draggedGrowthIndex = i;
                    this.dragOffset.x = mouseX - handleX;
                    this.dragOffset.y = mouseY - handleY;
                    return;
                }
            }
        },
        onCanvasMouseMove: function(e) {
            if (this.draggedGrowthIndex === null) return;
            const canvas = document.getElementById('centerPointsCanvas');
            const rect = canvas.getBoundingClientRect();
            const mouseX = e.clientX - rect.left;
            const mouseY = e.clientY - rect.top;

            const i = this.draggedGrowthIndex;
            const cx = canvas.width / 2 ;
            const cy = canvas.height / 2 ;

            // Update growth direction relative to center point
            this.shape_options.growth_directions[i][0] = (mouseX - cx - this.dragOffset.x)/2;
            this.shape_options.growth_directions[i][1] = (mouseY - cy - this.dragOffset.y)/2;
            if (!this.printing) {
                // Update starting location of center points only when not printing
                console.log("Updating center points for growth direction index: " + i);
                this.shape_options.points[i][0] = this.shape_options.growth_directions[i];
                this.current_shape.center_points[i] = this.shape_options.growth_directions[i];
            }
            this.drawCenterPoints();
        },
        onCanvasMouseUp: function(e) {
            this.draggedGrowthIndex = null;
            // Emit the updated growth_directions to the server
            socket.emit('shape_options', this.shape_options);
        },
        // draw center points on the canvas
        drawCenterPoints: function () {
            console.log("Drawing center points");
            const canvas = document.getElementById('centerPointsCanvas');
            if (!canvas) return;
            const ctx = canvas.getContext('2d');
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            this.draw_grid(ctx);
            const points = this.shape_options.points;
            const num_points = this.shape_options.num_center_points;
            const rx = this.shape_options.diameter_x / 2;
            const ry = this.shape_options.diameter_y / 2;
            const centerX = canvas.width / 2;
            const centerY = canvas.height / 2;
            
            for (let i = 0; i < num_points; i++) {
            if (i <= this.current_shape.center_points.length) {
                points[i][0] = this.current_shape.center_points[i][0];
                points[i][1] = this.current_shape.center_points[i][1];
            }
            const cx = centerX + points[i][0] * 2;
            const cy = centerY + points[i][1] * 2;
            // draw outline of ellipse
            ctx.beginPath();
            if (this.shape_options.base_shape === "rectangle") {
            // Draw rectangle centered at (cx, cy)
                ctx.rect(cx - rx * 2, cy - ry * 2, rx * 4, ry * 4);
            } else if (this.shape_options.base_shape === "circle") {
            // Draw ellipse
                ctx.ellipse(cx, cy, rx * 2, ry * 2, 0, 0, 2 * Math.PI);
            } else if (this.shape_options.base_shape === "triangle") {
            // Draw triangle centered at (cx, cy)
                ctx.moveTo(cx, cy - ry * 2); // Top vertex
                ctx.lineTo(cx - rx * 2, cy + ry * 2); // Bottom left vertex
                ctx.lineTo(cx + rx * 2, cy + ry * 2); // Bottom right vertex
                ctx.closePath();
            }
            ctx.strokeStyle = "#000000";
            ctx.lineWidth = 2;
            ctx.stroke();
            // draw current diameter
            const crx = this.current_shape.diameter_x / 2;
            const cry = this.current_shape.diameter_y / 2;
            ctx.beginPath();
            if (this.shape_options.base_shape === "rectangle" && this.layer > 0) {
            // Draw rectangle centered at (cx, cy)
                ctx.rect(cx - crx * 2, cy - cry * 2, crx * 4, cry * 4);
            } else if (this.layer > 0 && this.shape_options.base_shape === "circle") {
            // Draw ellipse
                ctx.ellipse(cx, cy, crx * 2, cry * 2, 0, 0, 2 * Math.PI);
            } else if (this.shape_options.base_shape === "triangle" && this.layer > 0) {
            // Draw triangle centered at (cx, cy)
                ctx.moveTo(cx, cy - cry * 2); // Top vertex
                ctx.lineTo(cx - crx * 2, cy + cry * 2); // Bottom left vertex
                ctx.lineTo(cx + crx * 2, cy + cry * 2); // Bottom right vertex
                ctx.closePath();
            }
            ctx.strokeStyle = "#757575";
            ctx.lineWidth = 2;
            ctx.stroke();
            // Draw the center
            ctx.beginPath();
            ctx.arc(cx, cy, 10, 0, 2 * Math.PI); 
            ctx.fillStyle = "#757575"; 
            ctx.fill();
            //draw growth direction
            direction_x = this.shape_options.growth_directions[i][0]*2;
            direction_y = this.shape_options.growth_directions[i][1]*2;
            ctx.beginPath();
            ctx.arc(centerX + direction_x,  centerY + direction_y, 8, 0, 2 * Math.PI); 
            ctx.fillStyle = "#000"; 
            ctx.fill();
            // Draw arrow line
            ctx.beginPath();
            ctx.moveTo(cx, cy);
            ctx.lineTo(centerX + direction_x, centerY + direction_y);
            ctx.strokeStyle = "#000";
            ctx.lineWidth = 2;
            ctx.stroke();
            }
        },
        draw_grid: function (ctx) {
            const canvas = ctx.canvas;
            ctx.save();
            ctx.strokeStyle = "pink";
            ctx.lineWidth = 1;

            // Draw vertical lines
            for (let x = 0; x <= canvas.width; x += 20) {
                ctx.beginPath();
                ctx.moveTo(x, 0);
                ctx.lineTo(x, canvas.height);
                ctx.stroke();
            }

            // Draw horizontal lines
            for (let y = 0; y <= canvas.height; y += 20) {
                ctx.beginPath();
                ctx.moveTo(0, y);
                ctx.lineTo(canvas.width, y);
                ctx.stroke();
            }
            ctx.restore();

        },
        move_up: function (event) {
            socket.emit('move_up');
        },
        move_down: function (event) {
            socket.emit('move_down');
        },
        connect: function (event) {
            if( !this.connected ) {
                socket.emit('printer_connect', this.port, this.baud);
            } else {
                socket.emit('printer_disconnect');
            }
        },
        setup: function(event) {
            socket.emit('printer_setup');
        },
        print: function(event) {
            // send the points and append the first one if the shape is closed
            var print_points = [] // = this.points.slice();
            // bring all points to 0,0
            for (const element of this.points) {
                print_points.push([element[0] - 75 + parseInt(this.plate_center_x), element[1] - 75 + parseInt(this.plate_center_y)])
            }
            console.log(print_points);
            if (!this.shapeOpen) {
                var last_point =  print_points[0];
                print_points = print_points.concat([last_point]);
            }
            socket.emit('start_print', print_points, 0);
            if (this.printLable == "Print") {
                this.printLable = "Home / Park"
            } else {
                this.printLable = "Print"
            }
        },
        pause: function(event) {
            console.log("Pause button clicked. Current label: " + this.pauseLable);
            socket.emit('printer_pause_resume');
            if (this.pauseLable == "Pause") {
                this.pauseLable = "Resume";
                console.log("Printer paused");
            } else {
                this.pauseLable = "Pause";
                console.log("Printer resumed");
            }
        }
    },
})