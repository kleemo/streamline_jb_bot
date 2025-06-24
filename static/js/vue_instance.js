var socket = io();
const FLIP_Y = -1
const DRAWING_SCALING = 2

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
        webhookUrl: '',
        ai_scores:{
            motivation_score: 0,
            complexity_score: 0,
            coherence_score: 0,
        },
        slicer_options: {
            extrusion_rate: 0,
            feed_rate: 0,
            layer_hight: 0.75,
            update_rate: 1,
            simulation_time: 2,
        },
        shape_options: {
            transition_rate: 1,
            repetitions: 1,
            base_shape: "circle",
            diameter_x: [60,60,60,60],
            diameter_y: [60,60,60,60],
            num_center_points: 4, //should be same as lenght of points arrays
            growth_directions:[[-40,50], [40,5],[-40,-30],[-30,20]],
            points: [[-40,50], [40,5],[-40,-30],[-30,20]],
            filling: 0,
            clip_start:0,
            clip_end:0,
            rotation:0,
            free_hand_form:[],
            non_planar: "no"
        },
        current_shape: {
            center_points: [[-40,50], [40,5],[-40,-30],[-30,20]],
            diameter_x: [60,60,60,60],
            diameter_y: [60,60,60,60],
        },
        infill: [],
        outline:true,
        line_displacement: [],
        line_options: {
            pattern_range:40,
            pattern_start:30,
            transition_rate:0.5,
            amplitude: 20,
            frequency: 1,
            pattern: "rect",
            irregularity: 0,
            glitch: "none"
        },
        draggedGrowthIndex: null,
        selected_index : 0,
        dragOffset: { x: 0, y: 0 },
    },
    mounted() {
    this.drawCenterPoints();
    this.draw_line_preview();
    this.drawFreeHandShape();
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
        line_displacement: function(newValue, oldValue){
            this.draw_line_preview();
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
                const direction_x = this.shape_options.growth_directions[i][0]*DRAWING_SCALING;
                const direction_y = this.shape_options.growth_directions[i][1]*DRAWING_SCALING * FLIP_Y;
                const handleX = centerX + direction_x;
                const handleY = centerY + direction_y;
            // Check if mouse is near the handle for growth direction
                if (Math.hypot(mouseX - handleX, mouseY - handleY) < 12) {
                    this.draggedGrowthIndex = i;
                    this.dragOffset.x = mouseX - handleX;
                    this.dragOffset.y = mouseY - handleY;
                }
                const center_x = this.shape_options.points[i][0]*DRAWING_SCALING;
                const center_y = this.shape_options.points[i][1]*DRAWING_SCALING * FLIP_Y;
                const handleX_c = centerX + center_x;
                const handleY_c = centerY + center_y;
            // Check if mouse is near center point for individual shape selection
                if (Math.hypot(mouseX - handleX_c, mouseY - handleY_c) < 12) {
                    if(this.selected_index != i){
                        this.selected_index = i;
                        this.drawCenterPoints();
                    }
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
            this.shape_options.growth_directions[i][0] = (mouseX - cx - this.dragOffset.x)/DRAWING_SCALING;
            this.shape_options.growth_directions[i][1] = (mouseY - cy - this.dragOffset.y)/DRAWING_SCALING*FLIP_Y;
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
            const points = this.shape_options.points;
            const num_points = this.shape_options.num_center_points;
            const centerX = canvas.width / 2;
            const centerY = canvas.height / 2;
            
            for (let i = 0; i < num_points; i++) {
                const rx = this.shape_options.diameter_x[i] * DRAWING_SCALING/ 2;
                const ry = this.shape_options.diameter_y[i] * DRAWING_SCALING/ 2;
            if (i <= this.current_shape.center_points.length) {
                points[i][0] = this.current_shape.center_points[i][0];
                points[i][1] = this.current_shape.center_points[i][1];
                
                const cx = centerX + points[i][0] * DRAWING_SCALING;
                const cy = centerY + points[i][1] * DRAWING_SCALING*FLIP_Y;
                // draw outline of ellipse
                ctx.beginPath();
                if (this.shape_options.base_shape === "rectangle") {
                // Draw rectangle centered at (cx, cy)
                    ctx.rect(cx - rx , cy - ry , rx * 2, ry * 2);
                } else if (this.shape_options.base_shape === "circle") {
                // Draw ellipse
                    ctx.ellipse(cx, cy, rx , ry , 0, 0, 2 * Math.PI);
                } else if (this.shape_options.base_shape === "triangle") {
                // Draw triangle centered at (cx, cy)
                    ctx.moveTo(cx, cy - ry); // Top vertex
                    ctx.lineTo(cx - rx, cy + ry); // Bottom left vertex
                    ctx.lineTo(cx + rx, cy + ry); // Bottom right vertex
                    ctx.closePath();
                } else if (this.shape_options.base_shape === "freehand"){
                // Draw freehand form as base shape
                    if (this.shape_options.free_hand_form == []) return;
                    pts = this.shape_options.free_hand_form;
                    ctx.moveTo(cx+pts[0][0]*rx*2,cy+pts[0][1]*ry*2);
                    for(let j=1; j< pts.length;j++){
                        ctx.lineTo(cx+pts[j][0]*rx*2,cy+pts[j][1]*ry*2);
                    }
                }
                ctx.strokeStyle = "#000000";
                ctx.lineWidth = 2;
                ctx.stroke();
                // draw current diameter
                const crx = this.current_shape.diameter_x[i] * DRAWING_SCALING/ 2;
                const cry = this.current_shape.diameter_y[i] * DRAWING_SCALING/ 2;
                ctx.beginPath();
                if (this.shape_options.base_shape === "rectangle" && this.layer > 0) {
                // Draw rectangle centered at (cx, cy)
                    ctx.rect(cx - crx, cy - cry, crx * 2, cry * 2);
                } else if (this.layer > 0 && this.shape_options.base_shape === "circle") {
                // Draw ellipse
                    ctx.ellipse(cx, cy, crx, cry, 0, 0, 2 * Math.PI);
                } else if (this.shape_options.base_shape === "triangle" && this.layer > 0) {
                // Draw triangle centered at (cx, cy)
                    ctx.moveTo(cx, cy - cry); // Top vertex
                    ctx.lineTo(cx - crx, cy + cry); // Bottom left vertex
                    ctx.lineTo(cx + crx, cy + cry); // Bottom right vertex
                    ctx.closePath();
                } else if (this.shape_options.base_shape === "freehand" && this.layer > 0) {
                    if (this.shape_options.free_hand_form == []) return;
                    pts = this.shape_options.free_hand_form;
                    ctx.moveTo(cx+pts[0][0]*crx*2,cy+pts[0][1]*cry*2);
                    for(let j=1; j< pts.length;j++){
                        ctx.lineTo(cx+pts[j][0]*crx*2,cy+pts[j][1]*cry*2);
                    }
                }
                ctx.strokeStyle = "#757575";
                ctx.lineWidth = 2;
                ctx.stroke();
                // Draw the center
                ctx.beginPath();
                ctx.arc(cx, cy, 10, 0, 2 * Math.PI); 
                if (i == this.selected_index){
                    ctx.fillStyle = "#ff3333";
                } else {
                    ctx.fillStyle = "#757575"; 
                }
                ctx.fill();
                //draw growth direction
                direction_x = this.shape_options.growth_directions[i][0]*DRAWING_SCALING;
                direction_y = this.shape_options.growth_directions[i][1]*DRAWING_SCALING*FLIP_Y;
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
            }
        },
        draw_line_preview: function () {
            const canvas = document.getElementById('linePreviewCanvas');
            if (!canvas) return;
            if (this.line_displacement == []) return;
            const ctx = canvas.getContext('2d');
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            this.draw_grid(ctx);
            const resolution = this.line_displacement.length;
            const spacing = canvas.width / resolution

            ctx.beginPath();
            for (let i =0; i < resolution; i++) {
                x = i*spacing + this.line_displacement[i][0] * DRAWING_SCALING * 2; //manual adjustment to compensate inacurate spacing
                y = canvas.height/2 + (this.line_displacement[i][1] * DRAWING_SCALING * FLIP_Y);
                if (i== 0){
                    ctx.moveTo(x,y);
                }else{
                    ctx.lineTo(x,y);
                }
            }

            ctx.strokeStyle = "#000000";
            ctx.lineWidth = 2;
            ctx.stroke();

        },
        addVertex(event) {
            const canvas = document.getElementById('freeHandShapeCanvas');
            const rect = canvas.getBoundingClientRect();
            const x = event.clientX - rect.left;
            const y = event.clientY - rect.top;
            // Normalize: -1 to 1, with (0,0) at center
            const normX = (x - canvas.width / 2) / (canvas.width / 2);
            const normY = (y - canvas.height / 2) / (canvas.height / 2);
            this.shape_options.free_hand_form.push([normX, normY]);
            this.drawFreeHandShape();
        },
        drawFreeHandShape() {
            const canvas = document.getElementById('freeHandShapeCanvas');
            if (!canvas) return;
            const ctx = canvas.getContext('2d');
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            this.draw_grid(ctx);
            //draw center
            ctx.beginPath();
            ctx.arc(canvas.width/2,canvas.height/2,5,0,2*Math.PI);
            ctx.fillStyle = "#757575"; 
            ctx.fill();

            const points = this.shape_options.free_hand_form;
            if (points.length === 0) return;
            ctx.beginPath();
            ctx.moveTo(
                points[0][0] * (canvas.width / 2) + canvas.width / 2,
                points[0][1] * (canvas.height / 2) + canvas.height / 2
            );
            ctx.arc(points[0][0] * (canvas.width / 2) + canvas.width / 2,
                    points[0][1] * (canvas.height / 2) + canvas.height / 2, 
                    4, 0, 2 * Math.PI
            );
            ctx.fillStyle = "#000";
            ctx.fill();
            for (let i = 1; i < points.length; i++) {
                ctx.lineTo( points[i][0] * (canvas.width / 2) + canvas.width / 2,
                            points[i][1] * (canvas.height / 2) + canvas.height / 2
                );
            }
            ctx.strokeStyle = "#000";
            ctx.lineWidth = 2;
            ctx.stroke();
        },
        clearFreeHandShape() {
            this.shape_options.free_hand_form = [];
            this.drawFreeHandShape();
        },
        draw_grid: function (ctx) {
            const canvas = ctx.canvas;
            ctx.save();
            ctx.strokeStyle = "pink";
            ctx.lineWidth = 1;

            // Draw vertical lines
            for (let x = 0; x <= canvas.width; x += (10*DRAWING_SCALING)) {
                ctx.beginPath();
                ctx.moveTo(x, 0);
                ctx.lineTo(x, canvas.height);
                ctx.stroke();
            }

            // Draw horizontal lines
            for (let y = 0; y <= canvas.height; y += (10*DRAWING_SCALING)) {
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
            ctx.moveTo(10*DRAWING_SCALING, canvas.height - 10*DRAWING_SCALING);
            ctx.lineTo(10*DRAWING_SCALING,canvas.height - 30*DRAWING_SCALING);
            ctx.moveTo(10*DRAWING_SCALING, canvas.height - 10*DRAWING_SCALING);
            ctx.lineTo(30*DRAWING_SCALING,canvas.height - 10*DRAWING_SCALING);
            ctx.stroke();
            
            ctx.beginPath()
            ctx.lineWidth = 0;
            ctx.fillStyle = "#eaeaea";
            ctx.ellipse(canvas.width/2,canvas.height/2,100*DRAWING_SCALING,100*DRAWING_SCALING,0,0,Math.PI*2); //max printing radius 100mm given by machine model
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
        remove_center_point: function(event) {
            prev_value = this.shape_options.num_center_points;
            this.shape_options.num_center_points = Math.max(1, this.shape_options.num_center_points - 1);
            if (this.shape_options.num_center_points < prev_value){
                this.shape_options.points.splice(this.selected_index,1);
                this.current_shape.center_points.splice(this.selected_index,1);
                this.shape_options.growth_directions.splice(this.selected_index,1);
                this.shape_options.diameter_x.splice(this.selected_index,1);
                this.shape_options.diameter_y.splice(this.selected_index,1);
                this.current_shape.diameter_x.splice(this.selected_index,1);
                this.current_shape.diameter_y.splice(this.selected_index,1);
                socket.emit("remove_center_point",{index:this.selected_index})
                this.selected_index = 0;
            }
            
        },
        add_center_point: function(event) {
            prev_value = this.shape_options.num_center_points;
            this.shape_options.num_center_points = Math.min(4, this.shape_options.num_center_points + 1);
            if (this.shape_options.num_center_points > prev_value){
                this.shape_options.points.push([0,0]);
                this.current_shape.center_points.push([0,0]);
                this.shape_options.growth_directions.push([0,0]);
                this.shape_options.diameter_x.push(60);
                this.shape_options.diameter_y.push(60);
                this.current_shape.diameter_x.push(60);
                this.current_shape.diameter_y.push(60);
            }
        },
        outline_toggle:function(event) {
            this.outline = !this.outline;
            socket.emit("set_outline",{outline:this.outline})

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
        },
        exposeWebhook: function(event) {
            socket.emit('expose_webhook');
        }
    },
})