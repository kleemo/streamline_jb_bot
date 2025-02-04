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
            "layer_hight": 1.25
        }

    def create(self, height, points):
        # creates g-code from a list of points and the actual height of the print-layer

        gcode = []

        i = 0
        
        gcode.append("G1 Z" + str(height + self.params['layer_hight']))
        gcode.append("G1 X" + str(points[0][0]) + " Y" + str(points[0][1]))
        gcode.append("G92 E0")
        gcode.append("G1 E5 F500")
        while i < len(points) - 1:
            point = points[i]
            point_next = points[(i + 1) % (len(points))]
            x = point_next[0]
            y = point_next[1]
            gcode.append("G92 E0")
            gcode.append(
                "G1 X" + str(x) + 
                " Y" + str(y) + 
                " E" + str(pc.distance(point, point_next) * self.params['extrusion_rate']) + 
                " F" + str(self.params['feed_rate'])
            )
            i += 1

        gcode.append("G92 E0")
        gcode.append("G1 E-6")

        # Write each GCode layer to the GCode File
        with open("output_gcode_file.gcode", "a") as file:
            file.write("\n".join(gcode))

        return gcode

    def start(self):
        # start sequence to initiate the print

        gcode = []
        gcode.append("G90")
        # the following 2 lines are the likely the brim extrustion commands to get the material flowing
        gcode.append("G1 X0 Y0 Z" + str(self.params['layer_hight']))
        gcode.append("G1 X0 E25")
        gcode.append("G90")
        gcode.append("G92 E0")
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

