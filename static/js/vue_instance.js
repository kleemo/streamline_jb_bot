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
        connected: false,
        port: '/dev/tty.usbmodem2101',
        baud: '115200',
        log_text: "some random text and even more",
        value: 1,
        slicer_options: {
            extrusion_rate: 0,
            feed_rate: 0,
            layer_hight: 1.5
        },
        toolpath_options: {
            linelength: 50
        },
        toolpath_type: "straight",
        plate_center_x: 100,
        plate_center_y: 100
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
        toolpath_options: {
            handler: function (newValue, oldValue) {
                socket.emit('toolpath_options', this.toolpath_options);
            },
            deep: true
        },
        toolpath_type: function (newValue, oldValue) {
            socket.emit('toolpath_type', {'toolpath_type': newValue});
        },
        synced_to_bot: function (newValue, oldValue) {
            if (newValue == false) {
                this.unpoll()
            }
            else {
                this.poll()
            }
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
        },
        // functionality for the drawing thingy
        draw(e) {
            var pt = svg.createSVGPoint();  // Created once for document

            pt.x = e.clientX;
            pt.y = e.clientY;

            // The cursor point, translated into svg coordinates
            var cursorpt =  pt.matrixTransform(svg.getScreenCTM().inverse());
            // console.log("(" + cursorpt.x + ", " + cursorpt.y + ")");

            this.points.push([cursorpt.x, cursorpt.y]);
            // this.points.push([e.offsetX, e.offsetY]);
            // this.drawPoints();
        },
        loadCircle(e, points = 10, radius = 50, center = [75,75]) {
            this.points = [];
            var slice = 2 * Math.PI / points;
            for (var i = 0; i < points; i++)
            {
                var angle = slice * i;
                var newX = Math.floor(center[0] + radius * Math.cos(angle));
                var newY = Math.floor(center[1] + radius * Math.sin(angle));
                var p = [newX, newY];
                this.points.push(p);
            }
        },
        shapeCloseOpen(e) {
            this.shapeOpen = !this.shapeOpen;
        },
        startDrag(e) {
            this.draggedElement = e.target;
        },
        drag(e) {
            var pt = svg.createSVGPoint();  // Created once for document

            pt.x = e.clientX;
            pt.y = e.clientY;

            // The cursor point, translated into svg coordinates
            var cursorpt =  pt.matrixTransform(svg.getScreenCTM().inverse());
            // console.log("(" + cursorpt.x + ", " + cursorpt.y + ")");

            if(this.draggedElement != null) {
                this.points[this.draggedElement.id][0] = cursorpt.x;
                this.points[this.draggedElement.id][1] = cursorpt.y;
                // array needs to be destroyed and copied to triger the reactivity from vue
                this.points = this.points.slice();
            }
        },
        endDrag(e) {
            this.draggedElement = null;
        },
        emptyPoints(e) {
            this.points = [];
        }
    },
    mounted() {
        var svg = document.getElementById("svg");
        window.addEventListener('resize', () => {
            this.windowWidth = window.innerWidth
        })
    }
})