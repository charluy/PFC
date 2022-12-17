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
    def __init__(self, ue):
        self.ue = ue
        self.snr = []
        self.rank = []
        self.degree = []
        self.linkQuality = 0
    
    def update_link_status(self, snr, rank, degree):
        self.snr = snr
        self.rank = rank
        self.degree = degree
        self.linkQuality = np.mean(snr)
    
    def get_radio_link_quality_over_assigned_prbs(self) -> tuple:
        assigned_prb_list = self.ue.assigned_base_prbs
        cant_base_prb = len(assigned_prb_list)
        snr_value = 0
        
        for prb_index in assigned_prb_list:
            snr_value += self.snr[prb_index]

        if cant_base_prb != 0:
            snr = float(snr_value)/cant_base_prb
            return (snr, self.ue.assigned_layers)
        else:
            return (0, 0)

