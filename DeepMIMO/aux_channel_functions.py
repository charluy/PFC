import numpy as np
import math

class UE: 

    def __init__(self, UE_group, position, is_dynamic = False, speed = 0, type_of_movement = 'vertical'):
        self.position = position
        self.is_dynamic = is_dynamic
        self.speed = speed
        self.UE_group = UE_group
        self.type_of_movement = type_of_movement


    def is_dynamic_UE(self):

        # returns true if the UE is part of the dynamic UEs
        return self.is_dynamic

    def switch_position(self, scene, scenario_column_size, scenario_rows_size):

        # Updates the position a dynamic UE moves to
        if (self.type_of_movement == 'vertical'):
            steps_to_move = math.floor(self.convert_speed_to_steps_per_scene(0.001, 0.01)*scene)*scenario_rows_size
            self.position = scenario_column_size - (self.position + steps_to_move)%scenario_column_size if(self.position + steps_to_move > scenario_column_size) else (self.position + steps_to_move)%scenario_column_size

        if (self.type_of_movement == 'horizontal'):
            steps_to_move = math.floor(self.convert_speed_to_steps_per_scene(0.001, 0.01)*scene)
            self.position = scenario_rows_size - (self.position + steps_to_move)%scenario_rows_size if(self.position + steps_to_move > scenario_rows_size) else (self.position + steps_to_move)%scenario_rows_size
            

    def convert_speed_to_steps_per_scene(self, scene_duration, ue_separation):

        # Returns the steps per scene a dynamic UE moves

        steps_per_scene = self.speed * scene_duration / ue_separation

        return steps_per_scene

