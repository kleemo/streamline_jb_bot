var socket = io();
const FLIP_Y = -1

const vm = new Vue({ // Again, vm is our Vue instance's name for consistency.
    el: '#vm',
    delimiters: ['[[', ']]'],
    components: {
        VueRangeSlider
    },
    data: {
        // UI elements
        printLable: "Print",
        pauseLable: "Pause",
        layer: 0,
        printing: false,
        connected: false,
        port: 'COM3',
        baud: '115200',
        slicer_options: {
            extrusion_rate: 0,
            feed_rate: 0,
            layer_hight: 0.75,
            update_rate: 3,
        },
        shape_options: {
            transition_rate: 1,
            repetitions: 1,
            base_shape: "circle",
            diameter_x: 60,
            diameter_y: 60,
            num_center_points: 4,
            growth_directions:[[-40,50], [40,5],[-40,-30],[-30,20],[-10,-30]],
            points: [[-40,50], [40,5],[-40,-30],[-30,20],[-10,-30]],
            filling: 0,
            clip_start:0,
            clip_end:0,
            rotation:0
        },
        current_shape: {
            center_points: [[-40,50], [40,5],[-40,-30],[-30,20],[-10,-30]],
            diameter_x: 60,
            diameter_y: 60,
        },
        infill: [],
        line_options: {
            pattern_range:60,
            transition_rate:0.5,
            amplitude: 20,
            frequency: 1,
            pattern: "rect",
            guides: {
                tri: [[-1, -0.5,0], [0, 0.5,0], [0, 0.5,0],[1, -0.5,0]],
                rect: [[-0.5, -0.5,0], [-0.5, 0.5,0], [0.5, 0.5,0],[0.5, -0.5,0]],
                circ: [[0, -0.5,0], [-1, 0,1], [1, 0,-1],[0, -0.5,-1]],
                sin: [[-0.5, 0,1], [-0.5, 0,0], [0.5, 0,1],[0.5, 0,0]],
                str: [[0, 0,0], [0, 0,0], [0, 0,0],[0, 0,0]],
            }
        },
        draggedGrowthIndex: null,
        selected_index : 0,
        dragOffset: { x: 0, y: 0 },
    },
    mounted() {
    this.drawCenterPoints();
    this.draw_line_preview();
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
        line_options: {
            handler: function (newValue, oldValue) {
                socket.emit('line_options', this.line_options);
                this.draw_line_preview();
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
                const direction_y = this.shape_options.growth_directions[i][1]*2 * FLIP_Y;
                const handleX = centerX + direction_x;
                const handleY = centerY + direction_y;
            // Check if mouse is near the handle
                if (Math.hypot(mouseX - handleX, mouseY - handleY) < 12) {
                    this.draggedGrowthIndex = i;
                    this.selected_index = i;
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
            this.shape_options.growth_directions[i][1] = (mouseY - cy - this.dragOffset.y)/2*FLIP_Y;
            if (!this.printing) {
                // Update starting location of center points only when not printing
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
            const canvas = document.getElementById('centerPointsCanvas');
            if (!canvas) return;
            const ctx = canvas.getContext('2d');
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            this.draw_helper(ctx);
            this.draw_grid(ctx);
            this.draw_infill(ctx);
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
            const cy = centerY + points[i][1] * 2*FLIP_Y;
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
            direction_y = this.shape_options.growth_directions[i][1]*2*FLIP_Y;
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
        draw_line_preview: function () {
            const canvas = document.getElementById('linePreviewCanvas');
            if (!canvas) return;
            const ctx = canvas.getContext('2d');
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            this.draw_grid(ctx);
            const resolution = 11;
            guides = this.line_options.guides[this.line_options.pattern];
            const d = canvas.width / resolution /2;

            ctx.beginPath();
            for (let i =0; i < resolution - 1; i++) {
                if (i % this.line_options.frequency == 0){
                    var cx = (i+1) * (canvas.width / resolution);
                    var cy = canvas.height / 2;
                    for (let j = 0; j < guides.length; j++) {
                        var x = cx + guides[j][0] * d * this.line_options.frequency;
                        var y = cy + guides[j][1] * (this.line_options.amplitude*4);
                        if (j == 0 && i == 0) {
                            ctx.moveTo(x, y);
                        } else {
                            var r = guides[j][2];
                            if (r == 0) {
                                ctx.lineTo(x, y);
                            }else if ( r==1 ) {
                                ctx.moveTo(cx+d*this.line_options.frequency,cy)
                                ctx.ellipse(cx,cy,d*this.line_options.frequency,this.line_options.amplitude*2,0,0,Math.PI*2);
                            }else {
                                ctx.moveTo(x,y);
                            }
                            }
                    }
                }
                
            }

            ctx.strokeStyle = "#000000";
            ctx.lineWidth = 2;
            ctx.stroke();

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
        draw_helper: function(ctx) {
            const canvas = ctx.canvas;
            ctx.save();
            ctx.strokeStyle = "blue";
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.moveTo(20, canvas.height - 20);
            ctx.lineTo(20,canvas.height - 60);
            ctx.moveTo(20, canvas.height - 20);
            ctx.lineTo(60,canvas.height - 20);
            ctx.stroke();
            
            ctx.beginPath()
            ctx.lineWidth = 0;
            ctx.fillStyle = "#eaeaea";
            ctx.ellipse(canvas.width/2,canvas.height/2,200,200,0,0,Math.PI*2);
            ctx.fill()
            

            ctx.restore();
        },
        draw_infill: function(ctx) {
            console.log("draw infill" + this.infill);
            console.log("draw infill l" + this.infill.length);
            if (this.infill.length == 0){
                return;
            }
            const canvas = ctx.canvas;
            ctx.save();
            ctx.strokeStyle = "blue";
            ctx.lineWidth = 2;
            ctx.beginPath();
            for (let i = 0; i< this.infill.length;i++){
                x = this.infill[i][0]*2 + this.shape_options.center_points[0][0]*2;
                y = this.infill[i][1]*2*FLIP_Y + this.shape_options.center_points[0][1]*2*FLIP_Y;
                if (i== 0){
                    console.log("draw infill points " + x + " " + y);
                    ctx.moveTo(x,y);
                }
                ctx.lineTo(x,y);
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
            socket.emit('start_print');
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