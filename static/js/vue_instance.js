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
        }
    },
})