"""
    This module contains channel status related classes.
"""

import random
import numpy as np


SUB_CARRIER_SPACING_LIST = ['15khz', '30khz', '60khz', '120khz']
SUB_CARRIER_SPACING_LIST_FR1 = ['15khz', '30khz', '60khz']
SUB_CARRIER_SPACING_LIST_FR2 = ['60khz', '120khz']
FREQUENCY_RANGE_LIST = ['FR1', 'FR2']
CANT_BASE_PRB_IN_PRB_BY_SCS = {
    '15khz': 1,
    '30khz': 2,
    '60khz': 4,
    '120khz': 8
}


class RadioLink():
	"""
        This class is used to model radio link properties and behabiour.
    """
	def __init__(self,i,lq_0,u):
		self.id = i
		state = 'ON'
		self.linkQuality = lq_0
		self.ue = u
		self.totCount = 0
		self.maxVar = 0.1

	def updateLQ(self,env,udIntrv,tSim,fl,u,r):
		"""
			This method updates UE link quality in terms of SINR during the simulation. This is a PEM method.
			During the simulation it is assumed that UE SINR varies following a normal distribution with mean
			value equal to initial SINR value, and a small variance.
		"""

		while env.now<(tSim*0.83):
			yield env.timeout(udIntrv)
			deltaSINR = random.normalvariate(0, self.maxVar)
			while deltaSINR > self.maxVar or deltaSINR<(0-self.maxVar):
				deltaSINR = random.normalvariate(0, self.maxVar)
			self.linkQuality = self.linkQuality + deltaSINR

	def update_link_quality_from_value(self, lq):
		"""
            This method updates UE link quality in terms of SINR during the simulation.
        """
		self.linkQuality = lq


class RadioLinkDeepMimo:
    """
        This class is used to model radio link properties and behabiour for DeepMIMO scenarios.
    """
    def __init__(self, ue, cell):
        self.ue = ue
        self.cell = cell
        self.snr = []
        self.rank = []
        self.degree = []
        self.linkQuality = 0  # TODO: ver si hay que dejarlo
    
    def update_link_status(self, snr, rank, degree):
        self.snr = snr
        self.rank = rank
        self.degree = degree
        self.linkQuality = np.mean(snr)



class DeepMimoChannel():
    """
        This class holds PRBs asignations between differnt slices.
    """
    def __init__(self):
        pass


class BasePrb:
    """
        This class represents a PRB of 15KHz for both FR1 and FR2.
    """
    def __init__(self, id):
        self.id = id
        self.prb = None
    
    def assign_to_ue(self, ue):
        self.ue = ue


class Prb:
    """
        This class holds a group of BasePrb to represent a PRB in different
        SCS configurations.
    """
    def __init__(self, frequency_range, scs, list_of_base_prbs, ue=None):
        if frequency_range not in FREQUENCY_RANGE_LIST:
            raise Exception(f"frequency_range must be one of the following choices: {FREQUENCY_RANGE_LIST}")
        
        if frequency_range == 'FR1' and scs not in SUB_CARRIER_SPACING_LIST_FR1:
            raise Exception(f"For FR1 SCS must be one of the following choices: {SUB_CARRIER_SPACING_LIST_FR1}")
        
        if frequency_range == 'FR2' and scs not in SUB_CARRIER_SPACING_LIST_FR2:
            raise Exception(f"For FR2 SCS must be one of the following choices: {SUB_CARRIER_SPACING_LIST_FR2}")

        cant_base_prb = len(list_of_base_prbs)

        if cant_base_prb != CANT_BASE_PRB_IN_PRB_BY_SCS.get(scs):
            raise Exception(f"For SCS {scs} must give {CANT_BASE_PRB_IN_PRB_BY_SCS.get(scs)} base PRBs")

        self.base_prbs = list_of_base_prbs
        self.ue = ue
    
    def assign_to_ue(self, ue):
        self.ue = ue
    
    def get_base_prbs_id_list(self):
        return [base_prb.id for base_prb in self.base_prbs]

