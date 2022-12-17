"""
    This module containts packet related classes.
"""

import random
from collections import deque
from utilities import Format


class PacketFlow():
	"""
		This class is used to describe UE traffic profile for the simulation.
	"""
	def __init__(self,i,pckSize,pckArrRate,u,tp,slc):
		self.id = i
		self.tMed = 0
		self.sMed = 0
		self.type = tp
		self.sliceName = slc
		self.pckArrivalRate = pckArrRate
		self.qosFlowId = 0
		self.packetSize = pckSize
		self.ue = u
		self.sMax = (float(self.packetSize)/350)*600
		self.tMax = (float(self.pckArrivalRate)/6)*12.5
		self.tStart = 0
		self.appBuff = PcktQueue()
		self.lostPackets = 0
		self.sentPackets = 0
		self.rcvdBytes = 0
		self.pId = 1
		self.header = 30
		self.meassuredKPI = {'Throughput':0,'Delay':0,'PacketLossRate':0}


	def setQosFId(self,q):
		qosFlowId = q

	def queueAppPckt(self,env,tSim): # --- PEM -----
		"""
			This method creates packets according to the packet flow traffic profile and stores them in 
			the application buffer.
		"""
		ueN = int(self.ue[2:]) # number of UEs in simulation
		self.tStart = (random.expovariate(1.0))
		yield env.timeout(self.tStart) 	 # each UE start transmission after tStart
		while env.now<(tSim*0.83):
			self.sentPackets = self.sentPackets + 1
			size = self.getPsize()
			pD = Packet(self.pId,size+self.header,self.qosFlowId,self.ue)
			self.pId = self.pId + 1
			pD.tIn = env.now
			self.appBuff.insertPckt(pD)
			nextPackTime = self.getParrRate()
			yield env.timeout(nextPackTime)

	def getPsize(self):
		pSize = random.paretovariate(1.2)*(self.packetSize*(0.2/1.2))
		while pSize > self.sMax:
			pSize = random.paretovariate(1.2)*(self.packetSize*(0.2/1.2))
		self.sMed = self.sMed + pSize
		return pSize

	def getParrRate(self):
		pArrRate = random.paretovariate(1.2)*(self.pckArrivalRate*(0.2/1.2))
		while pArrRate > self.tMax:
			pArrRate = random.paretovariate(1.2)*(self.pckArrivalRate*(0.2/1.2))
		self.tMed = self.tMed + pArrRate
		return pArrRate

	def setMeassures(self,tsim):
		"""This method calculates average PLR and throughput for the simulation."""
		self.meassuredKPI['PacketLossRate'] = float(100*self.lostPackets)/self.sentPackets
		if tsim>1000:
			self.meassuredKPI['Throughput'] = (float(self.rcvdBytes)*8000)/(0.83*tsim*1024*1024)
		else:
			self.meassuredKPI['Throughput'] = 0

class Packet:
	"""
		This class is used to model packets properties and behabiour.
	"""
	def __init__(self,sn,s,qfi,u):
		self.secNum = sn
		self.size = s
		self.qosFlowId = qfi
		self.ue = u
		self.tIn = 0

	def printPacket(self):
		print (Format.CYELLOW + Format.CBOLD + self.ue+ '+packet '+str(self.secNum)+' arrives at t ='+str(now()) + Format.CEND)

class Bearer:
	"""
		This class is used to model Bearers properties and behabiour.
	"""
	def __init__(self,i,q,tp):
		self.id = i
		self.qci = q
		self.type = tp
		self.buffer = PcktQueue()
	
	def has_packets(self):
		return not self.buffer.is_empty()

class PcktQueue:
	"""
		This class is used to model application and bearer buffers.
	"""
	def __init__(self):
		self.pckts = deque([])

	def insertPckt(self,p):
		self.pckts.append(p)

	def insertPcktLeft(self,p):
		self.pckts.appendleft(p)

	def removePckt(self):
		if len(self.pckts)>0:
			return self.pckts.popleft()
	
	def is_empty(self):
		return len(self.pckts) == 0
