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

from telegram_bot.handlers import send_message_to_telegram, fetch_file, get_openai_response, download_file, get_openai_img_response, TELEGRAM_API_URL, get_audio_response
from pyngrok import ngrok
import requests
import telegram_bot.parametershandler
import threading

port = 'COM3' # use this port for Windows
# port = '/dev/tty.usbmodem14101' # use this port value for Aurelian
baud = 115200 # baud rate as defined in the streamline-delta-arduino firmware
# baud = 250000 # use this baud rate for the ZhDK Makerbot printer
# connect to printer
print_handler = DefaultUSBHandler(port, baud)
slicer_handler = slicerhandler.Slicerhandler()
shape_handler = shapehandler.Shapehandler()
chat_activity = 0
webhook_exposed = False
last_chat_id = 0

parameter_handler = telegram_bot.parametershandler.ParametersHandler("straight")

layer = 0
height = 0
height_max = 5000 #set the maximum height of the object to print (includes starting height)
printing = False
toggle_state = False
simulation_time = 2
outline = True

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
    global parameter_handler
    global layer
    global chat_activity
    global last_chat_id
    
    if 'message' in update:
        chat_id = update['message']['chat']['id']
        last_chat_id = chat_id
        parameter_handler.increase_input()
        chat_activity = 1

        if "text" in update["message"]:
            text = update['message']['text']
            if text == "/start":
                if random.random() > 0.3: #only start conversation sometimes
                    ai_response = get_openai_response("initiate the conversation with the user")
                    send_message_to_telegram(chat_id, ai_response)
                return '', 200 

            ai_response = get_openai_response(text)
            parameter_handler.set_parameters_textInput(user_text=text)
            parameter_handler.add_text(text, ai_response)
            send_message_to_telegram(chat_id, ai_response)

        if "photo" in update["message"]:
            print("photo received")
            photo_sizes = update["message"]["photo"]  # List of photo sizes
            file_id = photo_sizes[-1]["file_id"]
            image_url = fetch_file(file_id)
            ai_response = get_openai_img_response(image_url)
            parameter_handler.set_parameters_imgInput(image_url=image_url)
            parameter_handler.add_text("user send image.",ai_response)
            send_message_to_telegram(chat_id,ai_response)

        if "location" in update["message"]:
            location = update["message"]["location"]
            location_string = str(location["latitude"]) + " " + str(location["longitude"])
            parameter_handler.set_parameters_locationInput(location)
            ai_response = get_openai_response("user send location at " + location_string)
            parameter_handler.set_parameters_locationInput(location)
            parameter_handler.add_text("user send a location.",ai_response)
            send_message_to_telegram(chat_id, ai_response)

        if "voice" in update["message"]:
            voice = update["message"]["voice"]
            file_id = voice["file_id"]
            file_url = fetch_file(file_id)
            voice_file_path = download_file(file_url, "voice.ogg")
            transcript = get_audio_response(voice_file_path)
            parameter_handler.set_parameters_audioInput(auid_file=voice_file_path)
            
            send_message_to_telegram(chat_id, transcript)
        #send updated parameters to the frontend to show on the interface
        shape_parameters , line_parameters, z_plane_parameters = parameter_handler.get_parameters()
        socketio.emit('update_shape_options',shape_parameters)
        socketio.emit('update_line_options',line_parameters)
        socketio.emit('update_z_plane_options',z_plane_parameters)
        socketio.emit('update_ai_scores',parameter_handler.ai_scores)

        

    return '', 200  # Respond with a 200 status to acknowledge the update

@socketio.on('hello')
def hello():
    print("hello socket")
    emit('layer', { 'layer': layer })
    global simulation_time
    emit('slicer_options', {
        'extrusion_rate': slicer_handler.params['extrusion_rate'],
        'feed_rate': slicer_handler.params['feed_rate'],
        'layer_hight': slicer_handler.params['layer_hight'],
        'simulation_time': simulation_time,
    })

def inactivity_checker():
    global chat_activity, webhook_exposed, parameter_handler, last_chat_id
    while True:
        time.sleep(60)  # Check every 60 seconds
        chat_activity -= 1
        random_probality = random.random()
        if webhook_exposed and chat_activity < 0 and random_probality < 0.7:
            # Get the last chat_id
            if last_chat_id > 0:
                ai_response = get_openai_response("Send a message to re-engage the user after inactivity.")
                send_message_to_telegram(last_chat_id, ai_response)
                chat_activity = 0
        

@socketio.on('expose_webhook')
def expose_webhook():
    """Expose Flask server via ngrok and send URL to client."""
    global webhook_exposed
    try:
        public_url = ngrok.connect(5000).public_url
        emit('webhook_url', {'url': public_url})
        try:
            requests.get(f"{TELEGRAM_API_URL}/deleteWebhook", params={'drop_pending_updates': True})
            requests.get(f"{TELEGRAM_API_URL}/setWebhook", params={'url': public_url + "/webhook"})
            webhook_exposed = True
        except Exception as e:
            print(f"Failed to set Telegram webhook: {e}")
    except Exception as e:
        print(f"ngrok error: {e}")

@socketio.on('slicer_options')
def slicer_options(data):
    print("slicer_options socket")
    slicer_handler.params['extrusion_rate'] = data["extrusion_rate"]
    slicer_handler.params['feed_rate'] = data["feed_rate"]
    slicer_handler.params['layer_hight'] = data["layer_hight"]
    global simulation_time
    simulation_time = data['simulation_time']


@socketio.on('layer')
def setLayer(data):
    print("layer socket")
    global layer
    layer = int(data["layer"])
@socketio.on('remove_center_point')
def removeCenterPoint(data):
    global layer
    shape_handler.remove_center_point(int(data["index"]),layer)

@socketio.on('set_outline')
def set_outline(data):
    global outline
    outline = data["outline"]

@socketio.on('shape_options')
def shape_options(data):
    print("shape_options socket")
    shape_handler.shape_options['repetitions'] = data["repetitions"]
    parameter_handler.shape_options["diameter"] = list(zip(data["diameter_x"], data["diameter_y"]))
    parameter_handler.shape_options["num_center_points"] = data["num_center_points"]
    parameter_handler.shape_options["growth_directions"] = data["growth_directions"]
    parameter_handler.shape_options["base_shape"] = data["base_shape"]
    parameter_handler.shape_options["center_points"] = data["points"]
    parameter_handler.shape_options["transition_rate"] = data["transition_rate"]
    parameter_handler.shape_options["rotation"] = data["rotation"]
    parameter_handler.shape_options["free_hand_form"] = data["free_hand_form"]

    parameter_handler.filling = data["filling"]
    parameter_handler.clip_fill_start = data["clip_start"]
    parameter_handler.clip_fill_end = data["clip_end"]
    #if data["filling"] > 0:
        #shape_handler.update_parameters(parameter_handler.get_parameters())
        #infill = shape_handler.simulate_infill(spacing = data["filling"])
        #infill2 = [list(pt) for pt in infill]
        #emit("visualize_infill",{"infill":infill})
    print("shape_options", data)

@socketio.on('line_options')
def line_options(data):
    parameter_handler.line_options["amplitude"] = data["amplitude"]
    parameter_handler.line_options["frequency"] = data["frequency"]
    parameter_handler.line_options["pattern"] = data["pattern"]
    parameter_handler.line_options["transition_rate"] = data["transition_rate"]  
    parameter_handler.line_options["pattern_range"] = data["pattern_range"]
    parameter_handler.line_options["pattern_start"] = data["pattern_start"]
    parameter_handler.line_options["irregularity"] = data["irregularity"]
    parameter_handler.line_options["glitch"] = data["glitch"]

    shape_param, line_param, z_plane_parameters = parameter_handler.get_parameters()
    global layer
    shape_handler.update_parameters(shape_param,line_param, z_plane_parameters,layer)
    displacement = [list(pt) for pt in shape_handler.simulate_line_pattern()]
    emit('line_preview',{'line_displacement':displacement})
    print("line_options: ", data)   

@socketio.on('z_plane')
def z_plane(data):
    parameter_handler.z_plane = data
    shape_param, line_param, z_plane_parameters = parameter_handler.get_parameters()
    global layer
    shape_handler.update_parameters(shape_param,line_param, z_plane_parameters,layer)
    displacement = shape_handler.simulate_z_displacement()
    emit('z_plane_preview',{'displacement':displacement})
    print("z_plane: ", data)  


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
def start_print():
    print("start_print socket")
    global printing
    global toggle_state
    global parameter_handler

    if(printing):
        print("Already printing. Cannot start a new print job.")
        printing = False
        return
    # test the excrusion
    #print("test extrusion start")
    #print_handler.send(slicer_handler.test_extrusion())
    #print("test extrusion end")
    
    #while parameter_handler.shape == "none":
     #   print("waiting for shape")
      #  time.sleep(3)

    
    printing = True
    emit('start_print', {'printing': printing})
    toggle_state = False

    emit('printer_status', {'status': 'printing'})
    print("Print job started.")

    print_handler.send(slicer_handler.start())

    while (print_handler.is_printing()):
        print("waiting for printer to finish setup")
        time.sleep(1)

    global layer
    global height
    global height_max
    global simulation_time
    
    global shape_handler
    

    while printing:

        #check conditions for continouing to print
        while(height >= height_max ):
            print("height reached max at: " + str(height))
            time.sleep(5)
        while len(shape_handler.current_diameter) <=0:
            print("all center points removed")
            time.sleep(5)
        # create the shape points
        #fetch parameters
        shape_parameter, line_parameters, z_plane_parameters = parameter_handler.get_parameters()
        shape_handler.update_parameters(shape_parameter, line_parameters, z_plane_parameters, layer)
        shapes = shape_handler.generate_next_layer(layer)#shape_handler.simpple_rectangle()#shape_handler.simple_circle()#shape_handler.simpple_rectangle()#shape_handler.generate_next_layer(layer)

        # print outline and infill of each shape
        global outline
        for i, points in enumerate(shapes):
            if len(points) > 0:
                #print outline of the shape
                if outline:
                    points.append(points[0])#trace over the start of the outline again
                    gcode = slicer_handler.create(height, points, max_distance=200)
                    print_handler.send(gcode)
                    while (print_handler.is_printing() or print_handler.is_paused()):
                        time.sleep(2)
                        print("print status :",print_handler.status())
                # generate and print infill of the shapes
                if parameter_handler.filling > 0:
                    infill = shape_handler.generate_infill(index=i, spacing=parameter_handler.filling, clip_end=parameter_handler.clip_fill_end, clip_start=parameter_handler.clip_fill_start)
                    if len(infill) == 0:
                        print("no infill generated")
                        continue
                    gcode = slicer_handler.create(height, infill, max_distance=500)
                    print_handler.send(gcode)
                    while (print_handler.is_printing() or print_handler.is_paused()):
                        time.sleep(2)
                        print("print status :",print_handler.status())
        # update layer height
        layer = layer + 1
        height = height + slicer_handler.params['layer_hight']
        emit('layer', {'layer': layer}) #"We are on Layer" – Output
        #update ui view
        center_points = [list(pt) for pt in shape_handler.shape_options["center_points"]]
        unzipped_x, unzipped_y = map(list, zip(*shape_handler.current_diameter))
        emit('update_current_shape',{'center_points':center_points,'diameter_x': unzipped_x, 'diameter_y': unzipped_y})
        time.sleep(simulation_time)  # Wait 10 seconds for simulation

        #check and remove any center point that is too narrow
        for i in reversed(range(len(shape_handler.current_diameter))):
            diameter = shape_handler.current_diameter[i]
            if diameter[0] <= 2 or diameter[1] <= 2:
                emit('remove_center_point', {'index': i})
                time.sleep(5)
            
        print("height = " + str(height))
        print("layer = " + str(layer))
        while len(shape_handler.current_diameter) <=0:
            print("all diameters too narrow")
            time.sleep(5)
    #print_handler.send(slicer_handler.end())

# Start the inactivity checker thread
threading.Thread(target=inactivity_checker, daemon=True).start()

# entry point when running the app. Must be called at the end of the script
if __name__ == '__main__':
    socketio.run(app)

