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
        self.current_rotation = 0
        self.current_diameter = (0,0)
        self.previous_vector = []
        self.parameters = { #new parameters
            "shape": "none",
            "diameter": (0,0),
            "growth_direction": (0, 0),
            "pattern": "none",
            "pattern_spacing":2, #between 3 and 6
            "pattern_height":8, #between 2 and 5
            "pattern_width":4, #between 2 and 5
            "rotation": 0,
            "inactive": False,
            "feature_vector": [],
            "center_points": [(0,0), (30,20)],
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
        #self.parameters["pattern_height"] = data["pattern_height"]
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
        if self.current_diameter[0] < 25 or self.current_diameter[1] < 25:
            self.parameters["pattern_height"] = 6
        if self.current_diameter[0] < 15 or self.current_diameter[1] < 15:
            self.parameters["pattern_height"] = 4
        print("Updated parameters: ", self.parameters)
    
    def generate_rectangle(self,displacement):
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
            num_points = int(len(displacement)/4)  # Number of points to generate for the line
            segment_length = distance / num_points
            for j in range(0,num_points):
                new_point = start + j * segment_length * direction
                perpendicular = np.array([-direction[1], direction[0], 0])
                points.append(new_point + (perpendicular * displacement[(i*num_points)+j][1]) + (direction * displacement[(i*num_points)+j][0]))
                
        points.append(points[0])
        # Add the last point to close the rectangle
        return points
    
    def generate_circle(self,displacement):
        points = []	
        radius_x = self.current_diameter[0] / 2
        radius_y = self.current_diameter[1] / 2
        num_points = len(displacement)  # Number of points to generate for the circle
        num_centers = len(self.parameters["center_points"])

        for j in range(num_centers):
            center = self.parameters["center_points"][j]
            for i in range(num_points):
                angle = 2 * np.pi * i / num_points
                x = center[0] + radius_x * np.cos(angle)
                y = center[1] + radius_y * np.sin(angle)
                new_point = pc.point(x, y, 0)
                direction = pc.normalize(pc.vector(pc.point(center[0],center[1],0), new_point))
                perpendicular = np.array([-direction[1], direction[0], 0])
                points.append(new_point)
                #points.append(new_point + (direction * displacement[i][1]) + (perpendicular * displacement[i][0]))
                
        if num_centers > 1:
            shilouette = []
            for point in points:
                for i in range(num_centers):
                    if not self.is_inside_ellipse(point, self.parameters["center_points"][i], (radius_x, radius_y)):
                        shilouette.append(point)
            points = shilouette
        # Sort points in counterclockwise order around the center
            points = self.sort_points_counterclockwise(points, self.parameters["center_points"][0])
        points.append(points[0])
        # Add the last point to close the circle
        print("points len: ", len(points))
        return points
    
    def generate_path(self):
         displacement = []
         resolution = 120
         
         multiplicator = 1
         for i in range(resolution):
            x = self.parameters["pattern_width"] * 0.5
            y = self.parameters["pattern_height"] * 0.5
            if i % self.parameters["pattern_spacing"] == 0:
                x = -x
                multiplicator *= -1
            goal = (x,y * multiplicator)

            if len(self.previous_vector) < resolution:
                displacement.append(goal)
                self.previous_vector.append(goal)
                
            else:
                vector = (goal[0] - self.previous_vector[i][0], goal[1] - self.previous_vector[i][1])
                # Multiply the vector by a factor (e.g., 0.1)
                scaled_vector = (vector[0] * 0.1, vector[1] * 0.1)
                displacement.append((self.previous_vector[i][0] + scaled_vector[0],self.previous_vector[i][1] + scaled_vector[1]))
                self.previous_vector[i] = displacement[i]
            
         #print("displacement: ", displacement)
         return displacement
    
    def generate_next_layer(self):
        points = []
        displacement = self.generate_path()
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
            points = self.generate_rectangle(displacement)
        elif self.parameters["shape"] == "circle":
            points = self.generate_circle(displacement)

        #appply rotation of layer
        if self.parameters["rotation"] > self.current_rotation:
            self.current_rotation += 0.5
            #apply rotation to pattern line
        for i in range(len(points)):
            points[i] = pc.rotate(points[i],pc.point(self.center[0],self.center[1],0) , self.current_rotation)
            
        return points
    @staticmethod
    def is_inside_ellipse(point, center, radius):
        """
        Check if a point is inside an ellipse.
        """
        x, y = point[0], point[1]
        cx, cy = center[0], center[1]
        rx, ry = radius[0], radius[1]
        # Ellipse equation: ((x - cx)^2 / rx^2) + ((y - cy)^2 / ry^2) <= 1
        return ((x - cx)**2 / rx**2) + ((y - cy)**2 / ry**2) <= 1.1 #add extra tolerance to rounding errors

    @staticmethod
    def sort_points_counterclockwise(points, center):
        """
        Sort points in counterclockwise order around a center.
        """
        cx, cy = center[0], center[1]
        return sorted(points, key=lambda p: np.arctan2(p[1] - cy, p[0] - cx))
    