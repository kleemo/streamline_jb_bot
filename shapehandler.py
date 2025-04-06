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
        self.center = (0,0)
        self.pattern_height = 0
        self.pattern_width = 0
        self.current_rotation = 0
        self.current_diameter = (0,0)
        self.previous_vector = []
        self.parameters = { #new parameters
            "shape": "none",
            "diameter": (0,0),
            "growth_direction": (0, 0),
            "pattern": "none",
            "pattern_spacing":5, #between 3 and 6
            "pattern_strength":3, #between 2 and 5
            "pattern_width":4, #between 2 and 5
            "rotation": 0,
            "bugs": 0,
            "inactive": False,
            "feature_vector": [],
        }
    
    
    
    def scale(self, points, factor):
        # scale an entire shape
        for i in range(len(points)):
            points[i] =  points[i] * factor

        return points
    
    
    def update_parameters(self, data):
        self.parameters["shape"] = data["shape"]
        self.parameters["diameter"] = data["diameter"]
        self.parameters["growth_direction"] = data["growth_direction"]
        self.parameters["pattern"] = data["pattern"]
        self.parameters["rotation"] = data["rotation"]
        self.parameters["bugs"] = data["bugs"]
        self.parameters["pattern_strength"] = data["pattern_height"]
        self.parameters["pattern_width"] = data["pattern_width"]
        self.parameters["inactive"] = data["inactive"]
        self.parameters["feature_vector"] = data["feature_vector"]
        pattern_spacing = int(data["pattern_spacing"])
        if pattern_spacing > self.parameters["pattern_spacing"]:
            self.parameters["pattern_spacing"]+=1
        if pattern_spacing < self.parameters["pattern_spacing"]:
            self.parameters["pattern_spacing"]-=1
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
        if self.parameters["pattern"] == "rectangular" and self.pattern_width < self.parameters["pattern_width"]:
                self.pattern_width += 0.4
                print("Pattern width: ", self.pattern_width)
    
    def generate_rectangle(self,y_displacement):
        points = []
        guide_points = []
        length = self.current_diameter[0]
        heigth = self.current_diameter[1]

        guide_points.append(pc.point(self.center[0]-length/2, self.center[1] -heigth/2, 0))
        guide_points.append(pc.point(self.center[0]+length/2, self.center[1] -heigth/2, 0))
        guide_points.append(pc.point(self.center[0]+length/2, self.center[1]+heigth/2, 0))
        guide_points.append(pc.point(self.center[0]-length/2, self.center[1]+heigth/2, 0))
        guide_points.append(pc.point(self.center[0]-length/2, self.center[1]-heigth/2, 0))

        for i in range(len(guide_points)-1):
            start = guide_points[i]
            end = guide_points[i+1]
            # Calculate the direction vector
            direction = pc.normalize(pc.vector(start, end))
            distance = pc.distance(start, end)
            num_points = int(len(y_displacement)/4)  # Number of points to generate for the line
            segment_length = distance / num_points 
            for j in range(num_points):
                new_point = start + j * segment_length * direction
                perpendicular = np.array([-direction[1], direction[0], 0])
                points.append(new_point + (perpendicular * y_displacement[(i*num_points)+j]))

        return points
    
    def generate_circle(self,y_displacement):
        points = []	
        radius_x = self.current_diameter[0] / 2
        radius_y = self.current_diameter[1] / 2
        num_points = len(y_displacement)  # Number of points to generate for the circle

        for i in range(num_points):
            angle = 2 * np.pi * i / num_points
            x = self.center[0] + radius_x * np.cos(angle)
            y = self.center[1] + radius_y * np.sin(angle)
            new_point = pc.point(x, y, 0)
            direction = pc.normalize(pc.vector(pc.point(self.center[0],self.center[1],0), new_point))
            points.append(new_point + (direction * y_displacement[i]))
            if i == num_points - 1:
                points.append(points[0])
        return points
    
    def generate_path(self):
         y_displacement = []
         smooth_factor = self.parameters["pattern_spacing"]
         if len(self.parameters["feature_vector"]) < 1:
            return
         # generate path from feature vector
         if self.previous_vector == []:
            self.previous_vector = self.parameters["feature_vector"]
         
         for i in range(smooth_factor*len(self.parameters["feature_vector"])): #add 0 in between feautures
            j = int(i/smooth_factor)
            dy = (self.parameters["feature_vector"][j] - self.previous_vector[j])*0.1
            y = self.previous_vector[j] + dy
            y_displacement.append(y)
            self.previous_vector[j] = y
         return y_displacement
    
    def generate_next_layer(self):
        points = []
        y_displacement = self.generate_path()
        # gradually update shape parameters
        center_distance = pc.distance(self.center,self.parameters["growth_direction"])
        if center_distance > 0.4:
            direction = pc.normalize(pc.vector(np.array(self.center), np.array(self.parameters["growth_direction"])))
            self.center += (direction * 0.3)
        diameter_distance = pc.distance(self.current_diameter,self.parameters["diameter"])
        if diameter_distance > 1:
            direction = pc.normalize(pc.vector(np.array(self.current_diameter), np.array(self.parameters["diameter"])))
            self.current_diameter += direction 
            print("current_diameter: ", self.current_diameter)

        if self.parameters["shape"] == "rectangle":
            points = self.generate_rectangle(y_displacement)
        elif self.parameters["shape"] == "circle":
            points = self.generate_circle(y_displacement)
            
        return points

    def generate_next_layer_old(self):
        guide_points = []
        pattern_line = []
        spacial_index = -1
        if self.parameters["inactive"]:
            spacial_index = self.parameters["pattern_spacing"] * 2
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
                    per_mult = 1
                    for j in range(num_points):
                        if j == random_index: # generate buggy line
                            new_point = start + j * segment_length * direction
                            pattern_line.append(new_point)
                            perpendicular = np.array([-direction[1],direction[0], 0]) * 15
                            pattern_line.append(new_point - perpendicular)
                            pattern_line.append(new_point + direction *2 - perpendicular)
                            pattern_line.append(new_point)
                            print("Buggy line")
                        if j!= spacial_index and (j % self.parameters["pattern_spacing"] == 0 or j == num_points-1):
                            new_point = start + j * segment_length * direction
                            perpendicular = np.array([-direction[1], direction[0], 0]) * self.pattern_height
                            
                            new_point += (perpendicular* per_mult)
                            per_mult *= -1
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
                per_mult = 1
                for i in range(len(guide_points)):
                    if i == random_index: # generate buggy line
                            new_point = guide_points[i]
                            pattern_line.append(new_point)
                            direction = pc.normalize(pc.vector(pc.point(self.center[0],self.center[1],0), new_point))
                            perpendicular = np.array([-direction[1], direction[0], 0])
                            pattern_line.append(new_point + 13*direction)
                            pattern_line.append(new_point + direction *13 - 5*perpendicular)
                            pattern_line.append(new_point)
                            print("Buggy line")
                    if i!=spacial_index and (i % self.parameters["pattern_spacing"] == 0 or i == len(guide_points)-1):
                        point = guide_points[i]
                        direction = pc.normalize(pc.vector(pc.point(self.center[0],self.center[1],0), point))
                        perpendicular = np.array([-direction[1], direction[0], 0])
                        point += (direction*self.pattern_height * per_mult)
                        per_mult *= -1
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