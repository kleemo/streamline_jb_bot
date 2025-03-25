# -*- coding: utf-8 -*-
"""
Name: Shape Handler
Description: is responsible to deal with the creation and adaption of the shapes
"""

import time
import getopt
import sys
import getopt
import random

import math

# import custom classes
import point_calc as pc
import matplotlib.pyplot as plt
import numpy as np

class Shapehandler:
    def __init__(self):
        self.params_toolpath = { #previous parameters
            "transformation_factor": 0.3,
            "growth_factor": 0.5,
            "growth_rotation_factor": 1,
            "magnitude": 5,
            "mag_goal": 5,
            "wave_lenght": 8,
            "rasterisation": 15,
            "diameter": 10,
            "dia_goal": 10,
            "linelength": 50,
            "linelength_goal": 50,
            "numlines": 4,
            "numlines_goal": 4,
            "center_points": 4,
            "centerpoints_goal": 4,
            "scale": 1,
            "scale_goal": 1,
            "rotation_degree": 0,
            "rotation_goal": 0,
            "grow": 'center',
        }
        self.center = (0,0)
        self.pattern_height = 0
        self.pattern_width = 0
        self.current_rotation = 0
        self.current_diameter = (0,0)
        self.parameters = { #new parameters
            "shape": "none",
            "diameter": (0,0),
            "growth_direction": (0, 0),
            "pattern": "none",
            "pattern_spacing":3,
            "pattern_strength":3,
            "rotation": 0,
            "bugs": 0
        }

    def update_transformations(self):
        # update transformations set in the frontend  
        if (self.params_toolpath["dia_goal"] > self.params_toolpath["diameter"]):
            self.params_toolpath["diameter"] = self.params_toolpath["diameter"] + self.params_toolpath["transformation_factor"]
        elif (self.params_toolpath["dia_goal"] < self.params_toolpath["diameter"]):
            self.params_toolpath["diameter"] = self.params_toolpath["diameter"] - self.params_toolpath["transformation_factor"]

        if (self.params_toolpath["scale_goal"] > self.params_toolpath["scale"]):
            self.params_toolpath["scale"] = self.params_toolpath["scale"] + self.params_toolpath["transformation_factor"]
        elif (self.params_toolpath["scale_goal"] < self.params_toolpath["scale"]):
            self.params_toolpath["scale"] = self.params_toolpath["scale"] - self.params_toolpath["transformation_factor"]

        if (self.params_toolpath["linelength_goal"] > self.params_toolpath["linelength"]):
            self.params_toolpath["linelength"] = self.params_toolpath["linelength"] + self.params_toolpath["transformation_factor"]
        elif (self.params_toolpath["linelength_goal"] < self.params_toolpath["linelength"]):
            self.params_toolpath["linelength"] = self.params_toolpath["linelength"] - self.params_toolpath["transformation_factor"]
        
        if (self.params_toolpath["numlines_goal"] > self.params_toolpath["numlines"]):
            self.params_toolpath["numlines"] = self.params_toolpath["numlines"] + self.params_toolpath["transformation_factor"]
        elif (self.params_toolpath["numlines_goal"] < self.params_toolpath["numlines"]):
            self.params_toolpath["numlines"] = self.params_toolpath["numlines"] - self.params_toolpath["transformation_factor"]

        growth_factor = 0.5
        if (self.params_toolpath["mag_goal"] > self.params_toolpath["magnitude"]):
            self.params_toolpath["magnitude"] = self.params_toolpath["magnitude"] + growth_factor
        elif (self.params_toolpath["mag_goal"] < self.params_toolpath["magnitude"]):
            self.params_toolpath["magnitude"] = self.params_toolpath["magnitude"] - growth_factor

        growth_rotation_factor = 1
        if (self.params_toolpath["rotation_goal"] > self.params_toolpath["rotation_degree"]):
            self.params_toolpath["rotation_degree"] = self.params_toolpath["rotation_degree"] + growth_rotation_factor
        elif (self.params_toolpath["rotation_goal"] < self.params_toolpath["rotation_degree"]):
            self.params_toolpath["rotation_degree"] = self.params_toolpath["rotation_degree"] - growth_rotation_factor

        return 0
    
    def rotate(self, points, center):
        rotation_degree = self.params_toolpath['rotation_degree']
        # rotate an entire shape
        for i in range(len(points)):
            points[i] = pc.rotate(points[i], center, rotation_degree)

        return points
    
    def add_wave_line(self, points, start_x, start_y, direction, length):
        magnitude = self.params_toolpath['magnitude']
        for x in np.linspace(start_x, start_x + direction * length, 100):
            y = start_y + magnitude * np.sin(((magnitude*1.5)/3) * (x - start_x) / length * 2 * np.pi)
            points.append(pc.point(x, y, 0))

    def add_jagged_line(self, points, start_x, start_y, direction, length):
        segments = 10
        segment_length = length / segments
        magnitude = self.params_toolpath['magnitude']
        for i in range(segments + 1):
            x = start_x + i * direction * segment_length
            y = start_y + (magnitude if i % 2 == 0 else -magnitude)
            points.append(pc.point(x, y, 0))
        points.append(pc.point(start_x + direction * length, start_y, 0))  # Ensure end point is aligned

    def add_loop_line(self, points, start_x, start_y, direction, length):
        loop_radius = self.params_toolpath['magnitude'] * 0.5
        loops = int(length // (2 * loop_radius))
        if loops > 0:
            loop_radius = length / (2 * loops)
            #loops = int(length // (2 * loop_radius))
        for i in range(int(loops)):
            theta = np.linspace(0, 2 * np.pi, 20)
            for angle in theta:
                x = start_x + direction * (i * 2 * loop_radius + loop_radius * np.sin(angle))
                y = start_y + loop_radius * (1 - np.cos(angle))
                points.append(pc.point(x, y, 0))
        points.append(pc.point(start_x + direction * length, start_y, 0))  # Ensure end point is aligned

    def add_rectangle_line(self, points, start_x, start_y, direction, length):
        magnitude = self.params_toolpath['magnitude']
        segments = 10
        segment_length = length / segments
        
        for i in range(segments):
            x = start_x + i * direction * segment_length
            points.append(pc.point(x, start_y, 0))
            points.append(pc.point(x, start_y + magnitude, 0))
            points.append(pc.point(x + direction * segment_length, start_y + magnitude, 0))
            points.append(pc.point(x + direction * segment_length, start_y, 0))
        
        points.append(pc.point(start_x + direction * length, start_y, 0))  # Ensure end point is aligned
    
    def add_cross_stitch_line(self, points, start_x, start_y, direction, length, stitch_size=10):
        num_stitches = length // stitch_size
        for i in range(int(num_stitches)):
            # Calculate the start position for each "X" shape
            x_base = start_x + direction * i * stitch_size
            y_base = start_y

            # Define the four points of the "X"
            points.append(pc.point(x_base, y_base, 0))
            points.append(pc.point(x_base + direction * stitch_size / 2, y_base + stitch_size / 2, 0))

            points.append(pc.point(x_base + direction * stitch_size / 2, y_base + stitch_size / 2, 0))
            points.append(pc.point(x_base + direction * stitch_size, y_base, 0))

            points.append(pc.point(x_base + direction * stitch_size, y_base, 0))
            points.append(pc.point(x_base + direction * stitch_size / 2, y_base - stitch_size / 2, 0))

            points.append(pc.point(x_base + direction * stitch_size / 2, y_base - stitch_size / 2, 0))
            points.append(pc.point(x_base, y_base, 0))

        # Ensure the end point aligns with the overall line length
        points.append(pc.point(start_x + direction * length, start_y, 0))
    
    def create_stepover(self, angle = 0, stepover_parameter = 10):
        # stepover test shape

        diameter = 50
        center = pc.point(100, 100, 0)

        points = []

        # first line
        x = center[0] - diameter / 2
        y = center[1] - diameter / 2
        z = 0
        points.append(pc.point(round(x, 5), round(y, 5), round(z, 5)))

        x = points[-1][0] + diameter
        y = points[-1][1]
        z = 0
        points.append(pc.point(round(x, 5), round(y, 5), round(z, 5)))

        for i in range(stepover_parameter):
            x = points[-1][0]
            y = points[-1][1] + (diameter/stepover_parameter)
            z = 0
            points.append(pc.point(round(x, 5), round(y, 5), round(z, 5)))

            if (i % 2) == 0:
                x = points[-1][0] - diameter
                y = points[-1][1]
                z = 0
                points.append(pc.point(round(x, 5), round(y, 5), round(z, 5)))
            else:
                x = points[-1][0] + diameter
                y = points[-1][1]
                z = 0
                points.append(pc.point(round(x, 5), round(y, 5), round(z, 5)))

        for i in range(len(points)):
            points[i] = pc.rotate(points[i], center, angle)

        return points
        # return points
    
    def scale(self, points, factor):
        # scale an entire shape
        for i in range(len(points)):
            points[i] =  points[i] * factor

        return points


    
    
    def add_line_fill(self, points, start_x, start_y, direction, length):
        densitiy = self.params_toolpath['magnitude']
        segments = int(length // densitiy)
        if segments > 0:
            densitiy = length / segments
            #segments = int(length // densitiy)
        
        for i in range(0,int(segments),2):
            x = start_x + i * direction * densitiy
            points.append(pc.point(x, start_y, 0))
            points.append(pc.point(x, start_y + length, 0))
            points.append(pc.point(x + direction * densitiy, start_y + length, 0))
            points.append(pc.point(x + direction * densitiy, start_y, 0))
        
        points.append(pc.point(start_x + direction * length, start_y, 0))
        points.append(pc.point(start_x + direction * length, start_y + length, 0))  # Ensure end point is aligned

    def add_jagged_fill(self, points, start_x, start_y, direction, length):
        density = self.params_toolpath['magnitude']
        segments = int(length // density)
        if segments > 0:
            density = length / segments
            #segments = int(length // density)

        for i in range(int(segments)):
            x = start_x + i * direction * density
            y = start_y + (density/2 if i % 2 == 0 else -density/2)
            points.append(pc.point(x, y, 0))
        points.append(pc.point(start_x + direction * length, start_y, 0))  # Ensure end point is aligned

    
    
    def surface_distortion(self,layer):
        size = self.params_toolpath["linelength"]
        points = []

        points.append(pc.point(0, 0, 0))
        points.append(pc.point(size, 0, 0))
        points.append(pc.point(size, size, 0))

        random_y = -1
        if layer / 10 > 1:
            random_y = 1
        if layer / 15 > 2:
            random_y = -1
        self.previous_guides[0] += random_y
        points.append(pc.point(size/4*3, size*0.9 + self.previous_guides[0], 0))
        self.previous_guides[1] += random_y
        points.append(pc.point(size/4*2, size*1.1 - self.previous_guides[1], 0))
        if layer / 7 > 1:
            random_y = 1
        if layer / 10 > 2:
            random_y = -1
        if layer / 9 > 3:
            random_y = 1
        if layer / 10 > 4:
            random_y = -1
        self.previous_guides[2] += random_y
        points.append(pc.point(size/4, size*0.8 - self.previous_guides[2], 0))

        points.append(pc.point(0, size, 0))
        points.append(pc.point(0, 0, 0))

        return points
    
    def update_parameters(self, data):
        self.parameters["shape"] = data["shape"]
        self.parameters["diameter"] = data["diameter"]
        self.parameters["growth_direction"] = data["growth_direction"]
        self.parameters["pattern"] = data["pattern"]
        self.parameters["rotation"] = data["rotation"]
        self.parameters["bugs"] = data["bugs"]
        if set(self.current_diameter) == {0}:
            self.current_diameter = self.parameters["diameter"]
        print("Updated parameters: ", self.parameters)

    def update_pattern_parameters(self):
        if self.pattern_height < self.parameters["pattern_strength"] and self.parameters["pattern"] != "straight":
                self.pattern_height += 0.4
        if self.parameters["pattern"] == "straight":
                if self.pattern_height >= 0.4:
                    self.pattern_height -= 0.4
                else:
                    self.pattern_height = 0
                if self.pattern_width >= 0.4:
                    self.pattern_width -= 0.4
                else:
                    self.pattern_width = 0
        if self.parameters["pattern"] == "jagged" and self.pattern_width > 0:
                if self.pattern_width >= 0.4:
                    self.pattern_width -= 0.4
                else:
                    self.pattern_width = 0
        if self.parameters["pattern"] == "rectangular" and self.pattern_width < self.parameters["pattern_spacing"]:
                self.pattern_width += 0.4
                print("Pattern width: ", self.pattern_width)

    def generate_next_layer(self):
        guide_points = []
        pattern_line = []
        center_distance = pc.distance(self.center,self.parameters["growth_direction"])
        if center_distance > 0.4:
                direction = pc.normalize(pc.vector(np.array(self.center), np.array(self.parameters["growth_direction"])))
                self.center += (direction * 0.3)
        diameter_distance = pc.distance(self.current_diameter,self.parameters["diameter"])
        if diameter_distance > 1:
                direction = pc.normalize(pc.vector(np.array(self.current_diameter), np.array(self.parameters["diameter"])))
                self.current_diameter += direction 
                print("current_diameter: ", self.current_diameter)
# rectangle shape
        if self.parameters["shape"] == "rectangle":
            length = self.current_diameter[0]
            heigth = self.current_diameter[1]

            guide_points.append(pc.point(self.center[0]-length/2, self.center[1] -heigth/2, 0))
            guide_points.append(pc.point(self.center[0]+length/2, self.center[1] -heigth/2, 0))
            guide_points.append(pc.point(self.center[0]+length/2, self.center[1]+heigth/2, 0))
            guide_points.append(pc.point(self.center[0]-length/2, self.center[1]+heigth/2, 0))
            guide_points.append(pc.point(self.center[0]-length/2, self.center[1]-heigth/2, 0))
        #add pattern line
            if True: #self.parameters["pattern"] != "straight" or self.pattern_height > 0
                self.update_pattern_parameters()
                for i in range(len(guide_points)-1):
                    start = guide_points[i]
                    end = guide_points[i+1]
                    # Calculate the direction vector
                    direction = pc.normalize(pc.vector(start, end))
                    distance = pc.distance(start, end)
                    num_points = 36  # Number of points to generate for the line
                    segment_length = distance / num_points 
                    #parameter for buggy line
                    random_index = -1
                    if self.parameters["bugs"] > 0:
                        self.parameters["bugs"] -= 1
                        random_index = random.randint(0, num_points-1) 

                    for j in range(num_points):
                        if j == random_index: # generate buggy line
                            new_point = start + j * segment_length * direction
                            pattern_line.append(new_point)
                            perpendicular = np.array([-direction[1],direction[0], 0]) * 10
                            pattern_line.append(new_point - perpendicular)
                            pattern_line.append(new_point + direction *2 - perpendicular)
                            pattern_line.append(new_point)
                            print("Buggy line")
                        if j % self.parameters["pattern_spacing"] == 0 or j == num_points-1:
                            new_point = start + j * segment_length * direction
                            perpendicular = np.array([-direction[1], direction[0], 0]) * self.pattern_height
                            if j % 2 == 0:
                                new_point += perpendicular
                            else:    
                                new_point -= perpendicular
                            if self.pattern_width > 0:
                                pattern_line.append(new_point - (direction * (self.pattern_width*0.5)))
                                pattern_line.append(new_point + (direction * (self.pattern_width*0.5)))
                            else:
                                pattern_line.append(new_point)
                    pattern_line.append(end) 
# circle shape                    
        if self.parameters["shape"] == "circle":
            radius_x = self.current_diameter[0] / 2
            radius_y = self.current_diameter[1] / 2
            num_points = 102  # Number of points to generate for the circle

            for i in range(num_points):
                angle = 2 * np.pi * i / num_points
                x = self.center[0] + radius_x * np.cos(angle)
                y = self.center[1] + radius_y * np.sin(angle)
                guide_points.append(pc.point(x, y, 0))
                if i == num_points - 1:
                    guide_points.append(pc.point(self.center[0]+radius_x*np.cos(0), self.center[1]+radius_y*np.sin(0), 0))
        #add pattern line
            if True: #self.parameters["pattern"] != "straight" or self.pattern_height > 0
                self.update_pattern_parameters()
                #parameter for buggy line
                random_index = -1
                if self.parameters["bugs"] > 0:
                    self.parameters["bugs"] -= 1
                    random_index = random.randint(0, len(guide_points)-1) 

                for i in range(len(guide_points)):
                    if i == random_index: # generate buggy line
                            new_point = guide_points[i]
                            pattern_line.append(new_point)
                            direction = pc.normalize(pc.vector(pc.point(self.center[0],self.center[1],0), new_point))
                            perpendicular = np.array([-direction[1], direction[0], 0])
                            pattern_line.append(new_point - 10*perpendicular)
                            pattern_line.append(new_point + direction *2 - 10*perpendicular)
                            pattern_line.append(new_point)
                            print("Buggy line")
                    if i % self.parameters["pattern_spacing"] == 0 or i == len(guide_points)-1:
                        point = guide_points[i]
                        direction = pc.normalize(pc.vector(pc.point(self.center[0],self.center[1],0), point))
                        perpendicular = np.array([-direction[1], direction[0], 0])
                        if i % 2 == 0:
                            point += (direction*self.pattern_height)
                        else:
                            point -= (direction*self.pattern_height)
                        if self.pattern_width > 0:
                            pattern_line.append(point - (perpendicular * (self.pattern_width*0.5)))
                            pattern_line.append(point + (perpendicular * (self.pattern_width*0.5)))
                        else:   
                            pattern_line.append(point)

        self.previous_guides = guide_points

        if self.parameters["rotation"] > self.current_rotation:
            self.current_rotation += 0.5
            #apply rotation to pattern line
        for i in range(len(pattern_line)):
            pattern_line[i] = pc.rotate(pattern_line[i],pc.point(self.center[0],self.center[1],0) , self.current_rotation)
        return pattern_line