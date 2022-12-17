import itertools
import numpy as np
import math

class UE: 

    def __init__(self, UE_group, position, is_dynamic = False, speed = 0, type_of_movement = 'vertical', antenas = 1):
        self.i_position = position
        self.position = position
        self.is_dynamic = is_dynamic
        self.speed = speed
        self.UE_group = UE_group
        self.type_of_movement = type_of_movement
        self.antenas = antenas


    def is_dynamic_UE(self):
        # returns true if the UE is part of the dynamic UEs
        return self.is_dynamic

    def switch_position(self, scene, scenario_columns_size, scenario_rows_size, refresh_rate, ue_separation):

        size_scenario_m_1 = (scenario_rows_size-1)*scenario_columns_size

        # Updates the position a dynamic UE moves to
        if (self.type_of_movement == 'vertical'):
            steps_to_move = math.floor(self.convert_speed_to_steps_per_scene(refresh_rate, ue_separation)*scene)*scenario_rows_size
            self.position = (size_scenario_m_1+self.get_column(scenario_columns_size)) - (steps_to_move%size_scenario_m_1)%scenario_rows_size if(steps_to_move > size_scenario_m_1 + self.get_column(scenario_columns_size)) else self.i_position + steps_to_move

        if (self.type_of_movement == 'horizontal'):
            steps_to_move = math.floor(self.convert_speed_to_steps_per_scene(refresh_rate, ue_separation)*scene)
            if (self.i_position%scenario_rows_size + steps_to_move > scenario_rows_size):
                if (math.floor((self.i_position%scenario_rows_size + steps_to_move)/scenario_rows_size)%2 != 0 ):
                    self.position = self.get_row(scenario_rows_size)*scenario_rows_size - (self.i_position%scenario_rows_size + steps_to_move%scenario_rows_size)%scenario_rows_size
                else:
                    self.position = (self.get_row(scenario_rows_size) - 1)*scenario_rows_size + (self.i_position%scenario_rows_size + steps_to_move%scenario_rows_size)%scenario_rows_size
            else: 
                self.position = self.i_position + steps_to_move%scenario_rows_size
            

    def convert_speed_to_steps_per_scene(self, refresh_rate, ue_separation):

        # Returns the steps per scene a dynamic UE moves

        steps_per_scene = self.speed * refresh_rate / ue_separation

        return steps_per_scene


    def get_row(self, scenario_row_size):
        row = math.ceil(self.i_position/scenario_row_size) if(self.i_position%scenario_row_size != 0) else math.ceil(self.i_position/scenario_row_size) + 1
        return row

    def get_column(self, scenario_column_size):
        column = math.ceil(self.i_position/scenario_column_size) if (self.i_position > 0) else 1
        return column

    def user_rank(self, channel_matrix, threshold):
        average_matrix = np.mean(channel_matrix, axis = 2)
        s,v,d = np.linalg.svd(average_matrix)
        max_element = np.max(v)
        rank = self.matrix_rank(v, max_element, threshold)

        return rank

    def best_rank(self, channel_matrix, threshold, ue_antennas):
        rank = 1
        comb_best_rank = []
        for comb in itertools.combinations(range(channel_matrix.shape[1]), ue_antennas):
            rank = self.user_rank(channel_matrix[:, comb, :], threshold) if self.user_rank(channel_matrix[:, comb, :], threshold) > 1 else 1
            comb_best_rank = comb
            if rank > 1:
                break
        
        return rank, comb_best_rank
            

    def matrix_rank(self , v, max_element, threshold):
        rank = 0
        for element in v:
            if element >= max_element/threshold:
                rank = rank + 1
        
        return rank


    def has_at_least_one_prb_with_rank_2(self, ranks):

        has_rank_2 = False

        for i in range(0, len(ranks)):
            has_rank_2 = ranks[i] == 2

        return has_rank_2