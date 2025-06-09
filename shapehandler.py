# -*- coding: utf-8 -*-
"""
Name: Shape Handler
Description: is responsible to deal with the creation and adaption of the shapes
"""

# import custom classes
import point_calc as pc
import numpy as np
from shapely.geometry import Polygon, LineString
LINE_CONST = 8

class Shapehandler:
    def __init__(self):
        self.current_rotation = 0
        self.current_diameter = [0,0]
        self.previous_vector = [] #for line pattern transition
        self.previous_shapes = [] #for layer repeat
        self.fixed_thetas = [] #save optimal starting point on circular shape for printing
        self.fixed_closest_ids = [] # save optimal starting point on rectangular shapes for printing
        self.current_layer = 0 
        self.shape_options = { 
            "transition_rate":1,
            "base_shape": "circle",
            "diameter": [0,0],
            "rotation": 0,
            "center_points": [],
            "growth_directions": [],
            "repetitions": 1,
        }
        self.line_options = {
            "pattern_range": 60,
            "pattern_start":50,
            "transition_rate":0.5,
            "pattern": "rect",
            "amplitude": 1,
            "frequency":1,
            "resolution":240
        }


    def update_parameters(self, shape_parameters, line_parameters, layer):
        self.shape_options["base_shape"] = shape_parameters["base_shape"]
        self.shape_options["diameter"] = shape_parameters["diameter"]
        self.shape_options["rotation"] = shape_parameters["rotation"]
        self.shape_options["growth_directions"] = shape_parameters["growth_directions"]
        self.shape_options["transition_rate"] = shape_parameters["transition_rate"]

        self.line_options["pattern"] = line_parameters["pattern"]
        self.line_options["amplitude"] = line_parameters["amplitude"]
        self.line_options["frequency"] = line_parameters["frequency"]
        self.line_options["transition_rate"] = line_parameters["transition_rate"]
        self.line_options["pattern_range"] = line_parameters["pattern_range"]
        self.line_options["pattern_start"] = line_parameters["pattern_start"]
        
        #initialize the current diameter only at the very beginning
        #initialize center points 
        if layer == 0:
            self.shape_options["center_points"] = shape_parameters["center_points"]
            self.current_diameter = shape_parameters["diameter"]
        #reduce number of center points if applicable
        if len(self.shape_options["center_points"]) > shape_parameters["num_center_points"]:
            self.shape_options["center_points"] = shape_parameters["center_points"] #todo prevent reset of points position depending on the layer update rate
        print("Updated shape_options: ", self.shape_options)
        print("Updated line_options: ", self.line_options)
    
    def generate_rectangle(self,displacement, cx, cy, index):
        points = []
        length = self.current_diameter[0]
        heigth = self.current_diameter[1]
        corners = [
        pc.point(cx-length/2, cy-heigth/2, 0),
        pc.point(cx+length/2, cy-heigth/2, 0),
        pc.point(cx+length/2, cy+heigth/2, 0),
        pc.point(cx-length/2, cy+heigth/2, 0)
        ]
        # Find the index of the corner closest to the origin
        closest_idx = min(range(len(corners)), key=lambda i: corners[i][0]**2 + corners[i][1]**2)
        if self.current_layer == 0:
            self.fixed_closest_ids.append(closest_idx)
        closest_idx = self.fixed_closest_ids[index]
        # Reorder so the closest point is first, and preserve order (wrap around)
        ordered_corners = corners[closest_idx:] + corners[:closest_idx]
        # Optionally close the rectangle by repeating the first point
        ordered_corners.append(ordered_corners[0])
        guide_points = corners #todo should be ordered_corners but is not compatible with manual center point removal at the moment
        guide_points.append(corners[0])

        for i in range(len(guide_points)-1):
            start = guide_points[i]
            end = guide_points[i+1]
                # Calculate the direction vector
            direction = pc.normalize(pc.vector(start, end))
            perpendicular = np.array([-direction[1], direction[0], 0])
            distance = pc.distance(start, end)
            num_points = int(len(displacement)/4)  # Number of points to generate for the line
            segment_length = distance / num_points
            new_point = start
            for j in range(0,num_points):
                jdx = (i*num_points) + j
                new_point = start + j * segment_length * direction  # Point along the outline
                patterned_point = (
                    new_point
                    + direction * displacement[jdx][0]      # Tangential offset
                    + perpendicular * displacement[jdx][1]  # Normal offset
                    )
                points.append(patterned_point)
                    
        points.append(points[0])  # Close the rectangle by adding the first point again
        # Add the last point to close the rectangle
        return points
    
    def generate_circle(self,displacement, cx,cy, index):
        points = []	
        radius_x = self.current_diameter[0] / 2
        radius_y = self.current_diameter[1] / 2
        num_points = len(displacement)  # Number of points to generate for the circle
        if self.current_layer == 0:
            self.fixed_thetas.append(np.arctan2(-cy, -cx))
        theta = 0 #self.fixed_thetas[index]
        
        angle = theta
        for i in range(num_points):
            angle = theta +(np.pi*2- ((2 * np.pi * i) / num_points))
            #angle = 2 * np.pi * i / num_points
            x = cx + radius_x * np.cos(angle)
            y = cy + radius_y * np.sin(angle)
            new_point = pc.point(x, y, 0)
            direction = pc.normalize(pc.vector(pc.point(cx,cy,0), new_point))
            perpendicular = np.array([-direction[1], direction[0], 0])
            points.append(new_point + (direction * displacement[i][1]) + (perpendicular * displacement[i][0]))
           
        points.append(points[0])  # Close the circle by adding the first point again
             
        return points
    
    def generate_triangle(self, displacement, cx, cy, index):
        points = []
        # Define the vertices of the triangle
        vertices = [
            pc.point(cx, cy + self.current_diameter[1] / 2, 0),  # Top vertex
            pc.point(cx - self.current_diameter[0] / 2, cy - self.current_diameter[1] / 2, 0),  # Bottom left vertex
            pc.point(cx + self.current_diameter[0] / 2, cy - self.current_diameter[1] / 2, 0)   # Bottom right vertex
        ]
        
        # Find the index of the vertex closest to the origin
        closest_idx = min(range(len(vertices)), key=lambda i: vertices[i][0]**2 + vertices[i][1]**2)
        if self.current_layer == 0:
            self.fixed_closest_ids.append(closest_idx)
        closest_idx = self.fixed_closest_ids[index]
        # Reorder so the closest point is first, and preserve order (wrap around)
        ordered_vertices = vertices[closest_idx:] + vertices[:closest_idx]
        # Optionally close the triangle by repeating the first point
        ordered_vertices.append(ordered_vertices[0])
        guide_points = vertices#ordered_vertices
        guide_points.append(vertices[0])
        for i in range(len(guide_points)-1):
            start = guide_points[i]
            end = guide_points[i+1]
                # Calculate the direction vector
            direction = pc.normalize(pc.vector(start, end))
            distance = pc.distance(start, end)
            num_points = int(len(displacement)/3)  # Number of points to generate for the line
            segment_length = distance / num_points
            new_point = start
            for j in range(0,num_points):
                new_point = start + j * segment_length * direction
                perpendicular = np.array([-direction[1], direction[0], 0])
                points.append(new_point + (perpendicular * displacement[(i*num_points)+j][1]) + (direction * displacement[(i*num_points)+j][0]))
                    
        points.append(points[0])  # Close the rectangle by adding the first point again
        # Add the last point to close the rectangle
        return points
    
    def generate_loop(self,num_points, height):
        points = []
        for i in range(num_points):
            angle =  2*np.pi - ((2 * np.pi * i) / num_points)
            x = height* np.cos(angle)
            y = height* np.sin(angle)
            points.append([x,y])
        return points
    def generate_stairs(self,num_points, height):
        points = []
        corner_points = [[-1,-height/2],[0,-height/2],[0,-height/2],[0,-height/2],[-1,height/2],[0,height/2],[0,height/2],[0,height/2]]
        gidx = -1
        for i in range(num_points):
            if i % (num_points/LINE_CONST) == 0:
                gidx = gidx + 1
            points.append(corner_points[gidx])
        return points
    def generate_zigzag(self,num_points,height):
        points = []
        half = num_points/2
        for i in range(num_points):
            if i < half:
                points.append([0,-height/2 + height *((i+1)*(1/half))])
            else:
                points.append([0,height/2 - height *((i+1-half)*(1/half))])
        return points
    def generate_wave(self,num_points,height):
        points = []
        for i in range(num_points):
            angle =  (2 * np.pi * i) / num_points
            x = 0
            y = height* np.sin(angle)
            points.append([x,y])
        return points
    
    def generate_path(self):
         displacement = []
         resolution = self.line_options["resolution"]
         h = self.line_options["amplitude"]
         pattern = self.line_options["pattern"]
         aplication_range = self.map_parameter_to_range(self.line_options["pattern_range"],0,resolution,0,100)
         pattern_start = self.map_parameter_to_range(self.line_options["pattern_start"],0,resolution-1,1,100)
         guides = []
         for i in range(resolution):
            idx = i
            bundle_size = LINE_CONST*self.line_options["frequency"]
            if i%bundle_size == 0:
                if pattern == "circ":
                    guides = self.generate_loop(bundle_size,h/2)
                if pattern == "rect":
                    guides = self.generate_stairs(bundle_size,h)
                if pattern == "tri":
                    guides = self.generate_zigzag(bundle_size,h)
                if pattern == "wav":
                    guides = self.generate_wave(bundle_size,h)
            goal = (0,0)
            if pattern == "str":
                goal = (0,0)
            elif (i >= pattern_start and i < (pattern_start + aplication_range)) or (i < (aplication_range-(resolution - pattern_start))):
                x = guides[i%bundle_size][0] 
                y = guides[i%bundle_size][1] 
                goal = (x,y)

            if len(self.previous_vector) < resolution:
                displacement.append(goal)
                self.previous_vector.append(goal) 
            else:
                vector = pc.normalize(pc.vector(np.array(self.previous_vector[idx]),np.array(goal)))#(goal[0] - self.previous_vector[i][0], goal[1] - self.previous_vector[i][1])
                # Multiply the vector by a factor (e.g., 0.1)
                scaled_vector = (vector[0] * self.line_options["transition_rate"], vector[1] * self.line_options["transition_rate"])
                new_displacement = (self.previous_vector[idx][0] + scaled_vector[0], self.previous_vector[idx][1] + scaled_vector[1])
                x, y = new_displacement
                if abs(x) < self.line_options["transition_rate"]/2:
                    x = 0
                if abs(y) < self.line_options["transition_rate"]/2:
                    y = 0
                new_displacement = (x, y)
                displacement.append(new_displacement)
                self.previous_vector[idx] = new_displacement
         return displacement
    
    def generate_next_layer(self,layer):
        # draw the same shape for given number of layers (layer reptition)
        self.current_layer = layer
        if layer % self.shape_options["repetitions"] != 0:
            return self.previous_shapes
        
        shapes = []
        displacement = self.generate_path() #distortion of outline depending on line pattern
        
        # gradually update center points shift
        for i in range(len(self.shape_options["center_points"])):
            center = self.shape_options["center_points"][i]
            center_distance = pc.distance(center,self.shape_options["growth_directions"][i])
            if center_distance > 0.05:
                direction = pc.normalize(pc.vector(np.array(center), np.array(self.shape_options["growth_directions"][i])))
                self.shape_options["center_points"][i] += (direction * self.shape_options["transition_rate"])
                
        # gradually update diameter
        diameter_distance = pc.distance(self.current_diameter,self.shape_options["diameter"])
        if diameter_distance > 1:
            direction = pc.normalize(pc.vector(np.array(self.current_diameter), np.array(self.shape_options["diameter"])))
            self.current_diameter += (direction * self.shape_options["transition_rate"]) 

        #generate points of the outlines for each center point
        for i in range(len(self.shape_options["center_points"])):
            center = self.shape_options["center_points"][i]
            cx = center[0]
            cy = center[1]
            points = []
            if self.shape_options["base_shape"] == "rectangle":
                points = self.generate_rectangle(displacement, cx, cy, i)
            elif self.shape_options["base_shape"] == "circle":
                points = self.generate_circle(displacement, cx, cy, i)
            elif self.shape_options["base_shape"] == "triangle":
                points = self.generate_triangle(displacement, cx, cy, i)
            shapes.append(points)

        #apply layer rotation
        self.current_rotation += self.shape_options["rotation"]
        #center_of_mass_x = sum(point[0] for point in self.shape_options["center_points"]) / len(self.shape_options["center_points"])
        #center_of_mass_y = sum(point[1] for point in self.shape_options["center_points"]) / len(self.shape_options["center_points"])
        for i in range(len(shapes)):
            points = shapes[i]
            for j in range(len(points)):
                r = points[j][2]
                points[j][2] = float(0)
                points[j] = pc.rotate(points[j],pc.point(self.shape_options["center_points"][i][0],self.shape_options["center_points"][i][1],0) , self.current_rotation)
                points[j][2] = r
            
        self.previous_shapes = shapes
        return shapes
    
    def generate_infill(self, polygon, spacing=10, angle=0, clip_start = 1, clip_end = 0):
        """
        Generate a simple linear infill for a given outline.
    
        Args:
        points (list): List of points defining the outline.
        spacing (float): Spacing between infill lines.
        angle (float): Angle of the infill lines in degrees (default is 0 for horizontal lines).
    
        Returns:
        list: List of line segments representing the infill.
        """

        # Remove duplicate points
        polygon = [tuple(p) for p in polygon]
        polygon = list(dict.fromkeys(polygon))
        
        # Ensure the polygon is closed
        if polygon[0] != polygon[-1]:
            polygon.append(polygon[0])

        # Create a polygon from the outline points
        outline_polygon = Polygon(polygon)

        # Validate the outline polygon
        if not outline_polygon.is_valid:
            print("Outline polygon is invalid. Attempting to fix...")
            outline_polygon = outline_polygon.buffer(0)
            if not outline_polygon.is_valid:
                print("Failed to fix the outline polygon. Skipping infill generation.")
                return []

        # Get the bounding box of the outline
        min_x, min_y, max_x, max_y = outline_polygon.bounds

        # Generate parallel lines within the bounding box
        infill_lines = []
        y = min_y
        while y <= max_y:
            line = LineString([(min_x, y), (max_x, y)])
            infill_lines.append(line)
            y += spacing

        # Clip the lines to the outline
        clipped_lines = [line.intersection(outline_polygon) for line in infill_lines]

        # Filter out empty or invalid lines
        clipped_lines = [line for line in clipped_lines if not line.is_empty]
        if len(clipped_lines) > clip_end and clip_end > 0:
            clipped_lines = clipped_lines[:(-1*clip_end)]  # Limit to 6 lines
        if len(clipped_lines) > clip_start and clip_start > 0:
            clipped_lines = clipped_lines[clip_start:]

        # Convert the clipped lines to a list of points
        infill_points = []
        for line in clipped_lines:
            if line.geom_type == 'LineString':
                for coord in line.coords:
                    infill_points.append(coord)
            elif line.geom_type == 'MultiLineString':
                for segment in line.geoms:
                    for coord in segment.coords:
                        infill_points.append(coord)
        print("infill_points len: ", len(infill_points))
        #print("infill_points: ", infill_points)
        return infill_points
    
#functions to draw realistic UI preview 

    def simulate_line_pattern(self):
         displacement = []
         resolution = self.line_options["resolution"]
         h = self.line_options["amplitude"]
         pattern = self.line_options["pattern"]
         aplication_range = self.map_parameter_to_range(self.line_options["pattern_range"],0,resolution,0,100)
         pattern_start = self.map_parameter_to_range(self.line_options["pattern_start"],0,resolution-1,1,100)
         guides = []
         for i in range(resolution):
            bundle_size = LINE_CONST*self.line_options["frequency"]
            if i%bundle_size == 0:
                if pattern == "circ":
                    guides = self.generate_loop(bundle_size,h/2)
                if pattern == "rect":
                    guides = self.generate_stairs(bundle_size,h)
                if pattern == "tri":
                    guides = self.generate_zigzag(bundle_size,h)
                if pattern == "wav":
                    guides = self.generate_wave(bundle_size,h)
            goal = (0,0)
            if pattern == "str":
                goal = (0,0)
            elif (i >= pattern_start and i < (pattern_start + aplication_range)) or (i < (aplication_range-(resolution - pattern_start))):
                x = guides[i%bundle_size][0] 
                y = guides[i%bundle_size][1] 
                goal = (x,y)

            displacement.append(goal)
         return displacement
    
    def simulate_infill(self, spacing=10, clip_start = 0, clip_end = 0):
        inflill = []
        points = self.generate_next_layer(layer=0)[0]
        print("points len ", len(points))
        inflill = self.generate_infill(spacing = spacing, clip_end=clip_end, clip_start=clip_start,polygon=points)
        #todo reset to initial state?

        return inflill
    
#helper functions

    @staticmethod
    def map_parameter_to_range(value, min_value, max_value, input_min, input_max):
        """
        Maps a value from one range to another.
        """
        # Ensure the input range is valid
        if input_min >= input_max:
            raise ValueError("Input min must be less than input max")
        
        # Ensure the output range is valid
        if min_value >= max_value:
            raise ValueError("Output min must be less than output max")
        
        # Normalize the value to a 0-1 range based on the input range
        normalized_value = (value - input_min) / (input_max - input_min)
        
        # Map the normalized value to the output range
        mapped_value = min_value + normalized_value * (max_value - min_value)
        
        return mapped_value
    

    
