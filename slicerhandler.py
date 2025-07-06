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

STARTING_HEIGHT = 49.25 #start height with thicker plate

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
        
        gcode.append("G1 Z" + str(height + STARTING_HEIGHT )) 
        gcode.append("G1 X" + str(round(points[0][0],2)) + " Y" + str(round(points[0][1],2)))
        gcode.append("G92 E0")
        gcode.append("G1 E5 F500")
        point = []
        point_next = []
        while i < len(points) - 1:
            point = points[i]
            point_next = points[(i + 1) % (len(points))]
            x = round(point_next[0],2)
            y = round(point_next[1],2)
            z = round(point_next[2],2)
            distance = round(pc.distance(point, point_next),4)
            # Check if the distance is below the threshold
            if distance < max_distance:  # threshold for extruding material between points
                if abs(z) > 0.01:
                    gcode.append("G92 E0")
                    gcode.append(
                        "G1 Z" + str(height + STARTING_HEIGHT + z) +
                        " X" + str(x) +
                        " Y" + str(y) +
                        " E" + str(distance * self.params['extrusion_rate']) +
                        " F" + str(self.params['feed_rate'])
                    )
                else: #drop z coordinate if print is planar
                    gcode.append("G92 E0")
                    gcode.append(
                        "G1" +
                        " X" + str(x) +
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
        #add extra path with no extrusion to avoid sharp turn when printing the next shape
        direction = pc.normalize(pc.vector(point,point_next))
        x = round(point_next[0]+direction[0]*12,2)
        y = round(point_next[1]+direction[1]*12,2)
        gcode.append(
            "G1 X" + str(x) +
            " Y" + str(y) +
            " F" + str(self.params['feed_rate'])
        )
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
        gcode.append("G90 ")
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
        gcode.append("G28")

        # Write last GCode layer to the GCode File
        with open("output_gcode_file.gcode", "a") as file:
            file.write("\n".join(gcode))

        return gcode

