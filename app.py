from flask import Flask, render_template, request
import time
import getopt
import random

from flask_socketio import SocketIO, emit
from flaskwebgui import FlaskUI # import FlaskUI

from options import *
from printhandler import DefaultUSBHandler

import shapehandler
import slicerhandler
import point_calc as pc

from telegram_bot.handlers import send_message_to_telegram, fetch_image, check_location

port = 'COM3'
# port = '/dev/tty.usbmodem14101' # use this port value for Aurelian
baud = 115200 # baud rate as defined in the streamline-delta-arduino firmware
# baud = 250000 # use this baud rate for the ZhDK Makerbot printer
# connect to printer
print_handler = DefaultUSBHandler(port, baud)
slicer_handler = slicerhandler.Slicerhandler()
shape_handler = shapehandler.Shapehandler()

layer = 0
height = 0
tooplpath_type = "straight"
grow =  "center"
printing = False
toggle_state = False

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

@app.route("/")
def index():
    return render_template('index.html')

@app.route('/webhook', methods=['POST'])
def telegram_webhook():
    #Endpoint to receive updates from Telegram.
    update = request.json  # Get the JSON payload from Telegram
    if 'message' in update:
        chat_id = update['message']['chat']['id']

        if "text" in update["message"]:
            text = update['message']['text']
            print(f"Received message from {chat_id}: {text}")
            send_message_to_telegram(chat_id, f"You said: {text}")

        if "photo" in update["message"]:
            print("photo received")
            photo_sizes = update["message"]["photo"]  # List of photo sizes
            file_id = photo_sizes[-1]["file_id"]
            encoded_file = fetch_image(file_id)
            
            arr_str = "\n".join(map(str, encoded_file))
            send_message_to_telegram(chat_id,"you send a photo: " + arr_str )

        if "location" in update["message"]:
            location = update["message"]["location"]
            longitude = location["longitude"]
            position = check_location(longitude)
            print(f"Received location from {chat_id}: ({position})")
            send_message_to_telegram(chat_id, f"Received your location: ({position}) from toni")
            shape_handler.params_toolpath['grow'] = position
            socketio.emit('toolpath_options',shape_handler.params_toolpath)
        

    return '', 200  # Respond with a 200 status to acknowledge the update

@socketio.on('hello')
def hello():
    print("hello socket")
    emit('layer', { 'layer': layer })
    emit('slicer_options', {
        'extrusion_rate': slicer_handler.params['extrusion_rate'],
        'feed_rate': slicer_handler.params['feed_rate'],
        'layer_hight': slicer_handler.params['layer_hight'],
    })
    emit('toolpath_type', { 'toolpath_type': tooplpath_type })
    emit('toolpath_options', {
        'transformation_factor': shape_handler.params_toolpath['transformation_factor'],
        'magnitude': shape_handler.params_toolpath['magnitude'],
        'wave_lenght': shape_handler.params_toolpath['wave_lenght'],
        'rasterisation': shape_handler.params_toolpath['rasterisation'],
        'diameter': shape_handler.params_toolpath['diameter'],
        'numlines': shape_handler.params_toolpath['numlines'],
        'center_points': shape_handler.params_toolpath['center_points'],
        'linelength': shape_handler.params_toolpath['linelength'],
        'rotation_degree': shape_handler.params_toolpath['rotation_degree'],
        'grow': shape_handler.params_toolpath['grow'],
    })

@socketio.on('slicer_options')
def slicer_options(data):
    print("slicer_options socket")
    slicer_handler.params['extrusion_rate'] = data["extrusion_rate"]
    slicer_handler.params['feed_rate'] = data["feed_rate"]
    slicer_handler.params['layer_hight'] = data["layer_hight"]

@socketio.on('toolpath_options')
def toolpath_options(data):
    print("toolpath_options socket")
    global magnitude, diameter, numlines, linelength, rotation_goal, rotation_increment, rotation_degree, center_points, grow

    shape_handler.params_toolpath['mag_goal'] = data["magnitude"]
    magnitude = data["magnitude"]

    rotation_goal = data["rotation_degree"]
    rotation_increment = data.get("rotation_increment", 2)

    shape_handler.params_toolpath['rotation_goal'] = data["rotation_degree"]
    rotation_degree = data["rotation_degree"]

    shape_handler.params_toolpath['wave_lenght'] = data["wave_lenght"]
    shape_handler.params_toolpath['rasterisation'] = data["rasterisation"]

    shape_handler.params_toolpath['dia_goal'] = data["diameter"]
    diameter = data["diameter"]

    numlines = data["numlines"]
    linelength = data["linelength"]
    center_points = data["center_points"]
    grow = data["grow"]
    print(shape_handler.params_toolpath, data)

@socketio.on('layer')
def setLayer(data):
    print("layer socket")
    global layer
    layer = int(data["layer"])

@socketio.on('toolpath_type')
def setToolpath(data):
    print("toolpath_type socket")
    global tooplpath_type
    tooplpath_type = data["toolpath_type"]
    print(str(tooplpath_type))

@socketio.on('printer_connect')
def printer_connect(port, baud):
    print("printer_connect socket")
    print("connect")
    if print_handler.connect(port, int(baud)):
        emit('connected', {'connected': True})

@socketio.on('printer_disconnect')
def printer_disconnect():
    print("printer_disconnect socket")
    print_handler.disconnect()
    emit('connected', {'connected': False})

@socketio.event
def layer_to_zero():
    print("layer_to_zero socket")
    global layer
    layer = 0
    emit('layer', {'layer': layer})

#reset printer postition and settings
@socketio.on('printer_setup')
def printer_setup():
    print("printer_setup socket")
    print_handler.send(["G90", "M104 S210", "G28", "G91", "G1 Z10", "G90"])
    global layer
    global height
    layer = 0
    height = 0
    emit('layer', {'layer': layer}) 
    #print_handler.send(["G90", "G28"])
    while print_handler.is_printing():
        time.sleep(0.1)

@socketio.on('move_up')
def printer_up():
    print("move_up socket")
    print_handler.send(["G91", "G1 Z10", "G90"])
    while print_handler.is_printing():
        time.sleep(0.1)

@socketio.on('move_down')
def printer_down():
    print("move_down socket")
    print_handler.send(["G91", "G1 Z-10", "G90"])
    while print_handler.is_printing():
        time.sleep(0.1)

@socketio.on('printer_pause_resume')
def printer_pause_resume():
    print("printer_pause_resume socket")
    global toggle_state
    global printing
    if not toggle_state:  # If currently printing (even count of button clicks)
        printing = False
        toggle_state = True  # Set to paused state
        print_handler.pause()
        print("Printing paused.")
        emit('printer_status', {'status': 'paused'})  # Emit status back to frontend
    else:  # If currently paused (odd count of button clicks)
        printing = True
        toggle_state = False  # Set to printing state
        print_handler.resume()
        print("Printing resumed.")
        emit('printer_status', {'status': 'resumed'})  # Emit status back to frontend

def printer_extrude():
    print_handler.send(["G92 E0", "G1 E2 F100"])
    while print_handler.is_printing():
        time.sleep(0.1)

def zero_layer():
    global layer
    layer = 0
    print("layer set to O")

@socketio.on('start_print')
def start_print(data, wobble):
    print("start_print socket")
    global printing
    global toggle_state

    if(printing):
        print("Already printing. Cannot start a new print job.")
        printing = False
        return

    original_points = []
    for point in data:
        original_points.append(pc.point(point[0], point[1], 0))
    
    printing = True
    toggle_state = False

    emit('printer_status', {'status': 'printing'})
    print("Print job started.")

    shape_handler.params_toolpath['magnitude'] = shape_handler.params_toolpath["mag_goal"]
    shape_handler.params_toolpath['diameter'] = shape_handler.params_toolpath["dia_goal"]
    shape_handler.params_toolpath['rotation_degree'] = shape_handler.params_toolpath["rotation_goal"]

    print_handler.send(slicer_handler.start())

    while print_handler.is_printing():
        time.sleep(0.1)

    global layer
    global height
    global tooplpath_type

    angle = 0

    while printing:

        #Set Machine Height
        if(height > 150):
            printing = False

        wobbler = wobble
        angle = angle + random.randint(-wobbler, wobbler)

        # create the shape points
        # points = shape_handler.generate_spiral(circumnavigations, shape, diameter, centerpoints)
        points = shape_handler.generate_snail_shape(numlines, linelength, diameter, tooplpath_type, center_points, rotation_degree, grow)

        repetitions = 1
        for i in range(repetitions):
            # create gcode from points
            gcode = slicer_handler.create(height, points)
            print_handler.send(gcode)

            while (print_handler.is_printing() or print_handler.is_paused()):
                time.sleep(0.1)
                print(print_handler.status())

            # update layer height
            layer = layer + 1
            height = height + slicer_handler.params['layer_hight']
            emit('layer', {'layer': layer}) #"We are on Layer" – Output

            time.sleep(3)  # Wait 3 seconds

            
        print("height = " + str(height))
    print_handler.send(slicer_handler.end())

# entry point when running the app. Must be called at the end of the script
def test():
    print("test")
    data = {"toolpath_type": "wave"}
    socketio.emit('toolpath_type', data)
if __name__ == '__main__':
    socketio.run(app)

