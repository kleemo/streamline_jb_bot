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
        self.previous_pattern_strength = 0
        self.previous_rotation = 0
        self.parameters = { #new parameters
            "shape": "none",
            "diameter": (0,0),
            "growth_direction": (0, 0),
            "pattern": "none",
            "pattern_spacing":3,
            "pattern_strength":3,
            "rotation": 0
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
    
    def apply_transformations(self, points):
        # apply transformations to the shape 

        points = self.scale(points, self.params_toolpath["scale"])

        return points

    def create_test(self, factor = 4):
        # this function returns an array containing points
        # the shape is a circle with 'factor' number of corners

        # growth_factor = 0.3
        # if (self.params_toolpath["dia_goal"] > self.params_toolpath["diameter"]):
        #     self.params_toolpath["diameter"] = self.params_toolpath["diameter"] + growth_factor
        # elif (self.params_toolpath["dia_goal"] < self.params_toolpath["diameter"]):
        #     self.params_toolpath["diameter"] = self.params_toolpath["diameter"] - growth_factor

        number_of_points = factor
        center = pc.point(0, 0, 0) # use this center for the Delta configuration with the home position in the center
        # center = pc.point(100, 100, 0) # use this center for cartesian printers with the home position at the corner
        radius = math.sqrt(pow(self.params_toolpath["diameter"], 2) + pow(self.params_toolpath["diameter"], 2)) / 2

        points = []

        i = 0
        while i < number_of_points:
            x = center[0] + radius * math.cos(2 * math.pi * i / number_of_points)
            y = center[1] + radius * math.sin(2 * math.pi * i / number_of_points)
            z = 0
            points.append(pc.point(round(x, 5), round(y, 5), round(z, 5)))
            i += 1

        return points
    
    def generate_spiral(self, num_circumnavigations=10, number_of_points=100, diameter=10, num_centerpoints=3):
        spirals = []
        # Define fixed center points for each spiral
        center_points = [(0, 50), (50, -50), (-50, -50)]

        for i in range(num_centerpoints):
            # Randomly adjust the center point within a -5 to +5 range
            center_x_ind = center_points[i][0] + random.randint(-2, 2)
            center_y_ind = center_points[i][1] + random.randint(-2, 2)
            
            points = []
            theta = np.linspace(0, num_circumnavigations * 2 * np.pi, number_of_points)
            r = np.linspace(0, diameter, number_of_points)
            x = center_x_ind + r * np.cos(theta)
            y = center_y_ind + r * np.sin(theta)
            z = 0  # z remains constant

            for idx in range(len(x)):
                x_rounded = np.around(x[idx], decimals=5)
                y_rounded = np.around(y[idx], decimals=5)
                z_rounded = np.around(z, decimals=5)
                points.append(pc.point(x_rounded, y_rounded, z_rounded))
            
            spirals.append(points)
        flattened_points = [point for spiral in spirals for point in spiral]
        return flattened_points
    
    def generate_snail_shape(self, num_lines=4, line_length=40, radius=8, pattern="straight", center_points=4, rotation_degree=0, grow="center"):
        if center_points is 4:
            center_points = [(25, 25), (-25, 25), (-25, -25), (25, -25)]  # Default center points
        elif center_points is 3:
            center_points = [(25, 25), (-25, 25), (-25, -25)]
        elif center_points is 2:
            center_points = [(25, 25), (-25, 25)]
        elif center_points is 1:
            center_points = [(25, 25)]

        self.update_transformations()

        all_points = []

        for cx, cy in center_points:
            current_x, current_y = cx - line_length / 2, cy + (num_lines - 1) * radius
            initial_x, initial_y = current_x, current_y

            if grow == "left":
                current_x = initial_x - line_length / 2
            elif grow == "right":
                current_x = initial_x + line_length / 2

            # if grow == "center":
                # current_x, current_y = cx - line_length / 2, cy + (num_lines - 1) * radius
            # elif grow == "left":
                # current_x, current_y = cx, cy + (num_lines - 1) * radius
            # elif grow == "right":
                # current_x, current_y = cx - line_length, cy + (num_lines - 1) * radius

            direction = 1  # 1 for right, -1 for left

            points = []

            for i in range(num_lines):
                # Add the straight line with optional pattern
                if pattern == "wave":
                    self.add_wave_line(points, current_x, current_y, direction, line_length)
                elif pattern == "jagged":
                    self.add_jagged_line(points, current_x, current_y, direction, line_length)
                elif pattern == "loop":
                    self.add_loop_line(points, current_x, current_y, direction, line_length)
                elif pattern == "rectangle":
                    self.add_rectangle_line(points, current_x, current_y, direction, line_length)
                elif pattern == "cross_stitch":
                    self.add_cross_stitch_line(points, current_x, current_y, direction, line_length)
                else:
                    points.append(pc.point(current_x, current_y, 0))
                    current_x += direction * line_length - direction * (radius*2)
                    points.append(pc.point(current_x, current_y, 0))

                # Add the end points for the line segment
                if pattern in ["wave", "jagged", "loop", "rectangle", "cross_stitch"]:
                    current_x += direction * line_length - direction * (radius*2)
                    points.append(pc.point(current_x, current_y, 0))

                # Add the half circle (if not the last line)
                if i < num_lines - 1:
                    theta = np.linspace(0, np.pi, radius*2)
                    for angle in theta:
                        if direction == -1:
                            x = (current_x - radius) + radius * (1 - np.sin(angle))
                            y = current_y + direction * radius * (1 - np.cos(angle))
                            points.append(pc.point(x, y, 0))
                        elif direction == 1:
                            x = current_x + radius * np.sin(angle)
                            y = current_y + (direction*-1) * radius * (1 - np.cos(angle))
                            points.append(pc.point(x, y, 0))
                        # x = current_x + radius * np.sin(angle)
                        # y = current_y + direction * radius * (1 - np.cos(angle))
                    
                        # points.append(pc.point(x, y, 0))
                    
                    if direction == -1:
                        current_y += direction * 2 * radius
                        points.append(pc.point(current_x, current_y, 0))
                    elif direction == 1:
                        current_y += direction * 2 * -radius
                        points.append(pc.point(current_x, current_y, 0))
                    # Reverse the direction for the next line
                    direction *= -1
            # Apply rotation to points incrementally
            # while abs(rotation_degree) < abs(rotation_goal):
                # points = self.rotate(points, np.array([cx, cy, 0]), rotation_increment if rotation_goal > 0 else -rotation_increment)
                # rotation_degree += rotation_increment if rotation_goal > 0 else -rotation_increment

            # Apply rotation to points
            # if rotation_degree != 0:
                # points = self.rotate(points, np.array([cx, cy, 0]), rotation_degree)
            points = self.rotate(points, np.array([cx, cy, 0]))

            all_points.extend(points)

        return all_points
    
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


    def toolpath(self, points, shape = "NONE", angle = 0):
        # ths function creates a toolpath from an array of points and returns a new array

        self.update_transformations()
        points = self.apply_transformations(points)

        points = self.rotate(points, np.array([100, 100, 0]), angle)

        step_length = self.params_toolpath["wave_lenght"] / self.params_toolpath["rasterisation"]
        rotation = 360 / self.params_toolpath["rasterisation"]

        global_count = 0
        
        new_points = []

        for i in range(len(points) - 1):

            point = points[i]
            point_next = points[(i + 1) % (len(points))]
            distance = pc.distance(point, point_next)
            direction = pc.normalize(pc.vector(point, point_next))
            perpendicular_direction = pc.normalize(pc.perpendicular_2d(direction))

            scope_count = 0
            while (scope_count * step_length) <= distance:
                new_point = None

                # define the different wave shapes
                if (shape == "NONE"):
                    new_point = point + scope_count * step_length * direction
                elif (shape == "SINE"):
                    new_point = point + scope_count * step_length * direction + perpendicular_direction * math.sin(global_count) * self.params_toolpath["magnitude"]
                elif (shape == "SQUARE"):
                    sign = lambda a: 1 if a>0 else -1 if a<0 else 0
                    new_point = point + scope_count * step_length * direction + perpendicular_direction * sign(math.sin(global_count)) * self.params_toolpath["magnitude"]
                elif (shape == "SAW"):
                    saw_wave = lambda a: (1 / math.pi) * (a%(2*math.pi)) - 1
                    new_point = point + scope_count * step_length * direction + perpendicular_direction * saw_wave(global_count) * self.params_toolpath["magnitude"]
                # experimental saw wave function
                elif (shape == "EXPERIMENTAL"):
                    k = np.arange(1, 100)
                    factor = np.sum(np.sin(2 * np.pi * k * global_count)/k)
                    new_point = point + scope_count * step_length * direction + perpendicular_direction * factor * self.params_toolpath["magnitude"]

                new_points.append(new_point)
                global_count = global_count + math.radians(rotation)
                scope_count = scope_count + 1
        
        return new_points
    
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

    def pyramide(self, layer, pattern): 
        # pyramide shape
        size = self.params_toolpath["linelength"]
        shrinking_factor = layer*0.5
        points = []

        if pattern == "rectangle":
            #self.params_toolpath["magnitude"] = 4
            self.add_line_fill(points, 0+shrinking_factor, 0+shrinking_factor, 1, size-2*shrinking_factor)

        elif pattern == "loop":
            loop_radius = self.params_toolpath["magnitude"] * 0.5
            num_lines = int((size-2*shrinking_factor) // (2 * loop_radius))
            if num_lines > 0:
                loop_radius = (size-2*shrinking_factor) / (2 * num_lines)
                #num_lines = int((size-2*shrinking_factor) // (2 * loop_radius))
            
            for i in range(int(num_lines)):
                direction = 1
                x_start = 0+shrinking_factor + loop_radius
                if i % 2 == 1:
                    x_start = size-shrinking_factor - loop_radius
                    direction = -1

                y_start = 0+shrinking_factor + i * 2 * loop_radius
                self.add_loop_line(points, x_start, y_start, direction, size-2*shrinking_factor)
            
        elif pattern == "jagged":
            line_height = self.params_toolpath["magnitude"]
            num_lines = int((size-2*shrinking_factor) // line_height)
            if num_lines > 0:
                line_height = (size-2*shrinking_factor) / num_lines
                #num_lines = int((size-2*shrinking_factor) // line_height)
            for i in range(int(num_lines)):
                direction = 1
                x_start = 0+shrinking_factor
                if i % 2 == 1:
                    x_start = size-shrinking_factor
                    direction = -1

                y_start = 0+shrinking_factor + line_height*0.5 + i * line_height
                self.add_jagged_fill(points, x_start, y_start, direction, size-2*shrinking_factor)
        else:
            points.append(pc.point(0+shrinking_factor, 0+shrinking_factor, 0))
            points.append(pc.point(size-shrinking_factor, 0+shrinking_factor, 0))
            points.append(pc.point(size-shrinking_factor, size-shrinking_factor, 0))
            points.append(pc.point(0+shrinking_factor, size-shrinking_factor, 0))
            points.append(pc.point(0+shrinking_factor, 0+shrinking_factor, 0))
        
        

        #self.params_toolpath["rotation_degree"] = layer
        print("rotation degree: ", self.params_toolpath["rotation_degree"])
        self.rotate(points, np.array([(size-2*shrinking_factor)/2, (size-2*shrinking_factor)/2, 0]))
        
        return points
    
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
        print("Updated parameters: ", self.parameters)

    def generate_next_layer(self):
        guide_points = []
        pattern_line = []
        center_distance = pc.distance(self.center,self.parameters["growth_direction"])

        if self.parameters["shape"] == "rectangle":
            length = self.parameters["diameter"][0]
            heigth = self.parameters["diameter"][1]
            if center_distance > 0.4:
                direction = pc.normalize(pc.vector(np.array(self.center), np.array(self.parameters["growth_direction"])))
                self.center += (direction * 0.3)

            guide_points.append(pc.point(self.center[0]-length/2, self.center[1] -heigth/2, 0))
            guide_points.append(pc.point(self.center[0]+length/2, self.center[1] -heigth/2, 0))
            guide_points.append(pc.point(self.center[0]+length/2, self.center[1]+heigth/2, 0))
            guide_points.append(pc.point(self.center[0]-length/2, self.center[1]+heigth/2, 0))
            guide_points.append(pc.point(self.center[0]-length/2, self.center[1]-heigth/2, 0))
            #add pattern line
            if self.parameters["pattern"] == "jagged" or self.previous_pattern_strength > 0:
                if self.previous_pattern_strength < self.parameters["pattern_strength"] and self.parameters["pattern"] == "jagged":
                    self.previous_pattern_strength += 0.4
                elif self.parameters["pattern"] != "jagged":
                    self.previous_pattern_strength -= 0.4

                for i in range(len(guide_points)-1):
                    start = guide_points[i]
                    end = guide_points[i+1]
                    # Calculate the direction vector
                    direction = pc.normalize(pc.vector(start, end))
                    distance = pc.distance(start, end)
                    num_segments = int(distance // self.parameters["pattern_spacing"])
                    segment_length = distance / num_segments
                    
                    for j in range(num_segments):
                        new_point = start + j * segment_length * direction
                        perpendicular = np.array([-direction[1], direction[0], 0]) * self.previous_pattern_strength
                        if j % 2 == 0:
                            new_point += perpendicular
                        else:    
                            new_point -= perpendicular
                        pattern_line.append(new_point)
                    pattern_line.append(end)
                   
             
                    

        if self.parameters["shape"] == "circle":
            radius_x = self.parameters["diameter"][0] / 2
            radius_y = self.parameters["diameter"][1] / 2
            num_points = 102  # Number of points to generate for the circle
            if center_distance > 0.4:
                print("distance to center: " + str(center_distance))
                direction = pc.normalize(pc.vector(np.array(self.center), np.array(self.parameters["growth_direction"])))
                self.center += (direction * 0.3)

            for i in range(num_points):
                angle = 2 * np.pi * i / num_points
                x = self.center[0] + radius_x * np.cos(angle)
                y = self.center[1] + radius_y * np.sin(angle)
                guide_points.append(pc.point(x, y, 0))
                if i == num_points - 1:
                    guide_points.append(pc.point(self.center[0]+radius_x*np.cos(0), self.center[1]+radius_y*np.sin(0), 0))
            #add pattern line
            if self.parameters["pattern"] == "jagged" or self.previous_pattern_strength > 0:
                if self.previous_pattern_strength < self.parameters["pattern_strength"] and self.parameters["pattern"] == "jagged":
                    self.previous_pattern_strength += 0.4
                elif self.parameters["pattern"] != "jagged":
                    self.previous_pattern_strength -= 0.4
                for i in range(len(guide_points)):
                    if i % self.parameters["pattern_spacing"] == 0 or i == len(guide_points)-1:
                        point = guide_points[i]
                        direction = pc.normalize(pc.vector(pc.point(self.center[0],self.center[1],0), point))
                        if i % 2 == 0:
                            point += (direction*self.previous_pattern_strength)
                        else:
                            point -= (direction*self.previous_pattern_strength)
                        pattern_line.append(point)

        self.previous_guides = guide_points

        if self.parameters["rotation"] > self.previous_rotation:
            self.previous_rotation += 0.5

        if self.parameters["pattern"] == "jagged" or self.previous_pattern_strength > 0:
            for i in range(len(pattern_line)):
                pattern_line[i] = pc.rotate(pattern_line[i],pc.point(self.center[0],self.center[1],0) , self.previous_rotation)
            return pattern_line
        
        for i in range(len(guide_points)):
            guide_points[i] = pc.rotate(guide_points[i],pc.point(self.center[0],self.center[1],0) , self.previous_rotation)
        return guide_points