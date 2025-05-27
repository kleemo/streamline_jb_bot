# -*- coding: utf-8 -*-
"""
Name: Slicer
Description: creates gcode from a list of points
"""

import time
import getopt
import sys
import getopt

import math
from options import *

# import custom classes for point clculations
import point_calc as pc

class Slicerhandler:
    def __init__(self):
        # makerbot
        # self.params = {
        #    "extrusion_rate": 0.1,
        #    "feed_rate": 850,
        #    "layer_hight": 0.5
        #}
        
        # delta
        self.params = {
            "extrusion_rate": 0.8,
            "feed_rate": 1000,
            "layer_hight": 0.75
        }

    def create(self, height, points, max_distance = 10):
        # creates g-code from a list of points and the actual height of the print-layer

        gcode = []

        i = 0
        
        gcode.append("G1 Z" + str(height + 49.5 )) #+ self.params['layer_hight'] #3 for printing on the extra plate
        gcode.append("G1 X" + str(points[0][0]) + " Y" + str(points[0][1]))
        gcode.append("G92 E0")
        gcode.append("G1 E5 F500")
        while i < len(points) - 1:
            point = points[i]
            point_next = points[(i + 1) % (len(points))]
            x = point_next[0]
            y = point_next[1]
            distance = pc.distance(point, point_next)
            # Check if the distance is below the threshold
            if distance < max_distance:  # Example threshold: 10 units
                gcode.append("G92 E0")
                gcode.append(
                    "G1 X" + str(x) +
                    " Y" + str(y) +
                    " E" + str(distance * self.params['extrusion_rate']) +
                    " F" + str(self.params['feed_rate'])
                )
            else:
                # Move without extrusion
                gcode.append(
                    "G1 X" + str(x) +
                    " Y" + str(y) +
                    " F" + str(self.params['feed_rate'])
                )
            i += 1

        gcode.append("G92 E0")
        gcode.append("G1 E-6")

        # Write each GCode layer to the GCode File
        with open("output_gcode_file.gcode", "a") as file:
            file.write("\n".join(gcode))

        return gcode
    
    def test_extrusion(self):
        gcode = []
        #gcode.append("G90")
        gcode.append("G92 E0")  # Reset the extruder position
        gcode.append(f"G1 E70 F1000")  # Extrude filament
        return gcode

    def start(self):
        # start sequence to initiate the print

        gcode = []
        gcode.append("G90")
        # the following 2 lines are the likely the brim extrustion commands to get the material flowing
            #gcode.append("G1 X0 Y0 Z" + str(3)) #+ self.params['layer_hight']) alternative plate -12 #2.5 for printing on the extra plate
            #gcode.append("G1 X0 E1 F1000")
            #gcode.append("G90")
            #gcode.append("G92 E0")
        # gcode.append("G1 E-4")

        # We are starting a new GCode File for testing
        with open("output_gcode_file.gcode", "w") as file:
            file.write("\n".join(gcode))

        return gcode

    def end(self):
        # end sequence to finish the print
        
        gcode = []

        gcode.append("G92 E0")
        gcode.append("G91")
        gcode.append("G1 Z10 E-15")
        gcode.append("G90")
        # gcode.append("G28 X Y")
        gcode.append("G28")

        # Write last GCode layer to the GCode File
        with open("output_gcode_file.gcode", "a") as file:
            file.write("\n".join(gcode))

        return gcode

