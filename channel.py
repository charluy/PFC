"""
    This module contains channel status related classes.
"""

import random
import numpy as np


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
        
