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

from telegram_bot.handlers import send_message_to_telegram, fetch_image, get_openai_response, analyze_image_with_openai
from telegram_bot.utils import image_encoder, map_brightness_to_value
import telegram_bot.locationhandler
import telegram_bot.parametershandler

port = 'COM3'
# port = '/dev/tty.usbmodem14101' # use this port value for Aurelian
baud = 115200 # baud rate as defined in the streamline-delta-arduino firmware
# baud = 250000 # use this baud rate for the ZhDK Makerbot printer
# connect to printer
print_handler = DefaultUSBHandler(port, baud)
slicer_handler = slicerhandler.Slicerhandler()
shape_handler = shapehandler.Shapehandler()

location_handler = telegram_bot.locationhandler.LocationHandler()
parameter_handler = telegram_bot.parametershandler.ParametersHandler("straight")

layer = 0
height = 0
height_max = 0
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
    global height_max
    global toggle_state
    global layer
    if 'message' in update:
        chat_id = update['message']['chat']['id']

        if "text" in update["message"]:
            parameter_handler.count_input += 1
            text = update['message']['text']
            parameter_handler.add_text(text)
            #topic = parameter_handler.map_topic_to_pattern(text)
            ai_response = get_openai_response(text)
            send_message_to_telegram(chat_id, f"OpenAI response: {ai_response}")

        if "photo" in update["message"]:
            parameter_handler.count_input += 1
            print("photo received")
            photo_sizes = update["message"]["photo"]  # List of photo sizes
            file_id = photo_sizes[-1]["file_id"]
            image_url = fetch_image(file_id)
            #ai_response = analyze_image_with_openai(image_url)
            brightnes_level = map_brightness_to_value(image_url, 1, 8) * 0.5
            parameter_handler.density = brightnes_level
            send_message_to_telegram(chat_id,"you send a photo with brightness value: " + str(brightnes_level))
            #send_message_to_telegram(chat_id, f"OpenAI response: {ai_response}")

        if "location" in update["message"]:
            location = update["message"]["location"]
            dist = location_handler.handle_location(location)
            if dist > 0:
                topic_nr, pattern = parameter_handler.map_topic_to_pattern()
                socketio.emit('toolpath_type', { 'toolpath_type': pattern })
                shape_handler.params_toolpath["magnitude"] = parameter_handler.density
                height_max += (dist*1000)
                parameter_handler.set_new_epoch(height_max, layer)
                send_message_to_telegram(chat_id, f"Your text messages during this walking distance belonged to topic : {topic_nr} corresponding to pattern: {pattern}")    
                    #socketio.emit('printer_pause_resume')
            #print("Emitting start_print event")
            #socketio.emit('trigger_print')
            send_message_to_telegram(chat_id, f"Received your location with distance to previous location: ({dist})")
            

        

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
    emit('toolpath_options', {
        'linelength': shape_handler.params_toolpath['linelength']
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
    shape_handler.params_toolpath["linelength"] = data["linelength"]
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

    print_handler.send(slicer_handler.start())

    while print_handler.is_printing():
        time.sleep(0.1)

    global layer
    global height
    global height_max
    global tooplpath_type

    while printing:

        #Set Machine Height
        while(height >= height_max):
            print("loop height = " + str(height))
            time.sleep(2)
            #emit('printer_pause_resume')
            #printing = False


        # create the shape points
        # points = shape_handler.generate_spiral(circumnavigations, shape, diameter, centerpoints)
        shape_handler.params_toolpath["rotation_degree"] += parameter_handler.get_layer_rotation(slicer_handler.params['layer_hight'], layer)
        points = shape_handler.pyramide(layer, tooplpath_type)

        repetitions = 1
        for i in range(repetitions):
            # create gcode from points
            gcode = slicer_handler.create(height, points)
            print_handler.send(gcode)

            
            while (print_handler.is_printing() or print_handler.is_paused()):
                time.sleep(2)
                print(print_handler.status())

            # update layer height
            layer = layer + 1
            height = height + slicer_handler.params['layer_hight']
            emit('layer', {'layer': layer}) #"We are on Layer" – Output

            time.sleep(3)  # Wait 3 seconds
            
            

            
        print("height = " + str(height))
        print("layer = " + str(layer))
    #print_handler.send(slicer_handler.end())

# entry point when running the app. Must be called at the end of the script
if __name__ == '__main__':
    socketio.run(app)

