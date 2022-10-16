"""
	This module contains the UE, Packet Flow, Packet, PcktQueue, Bearer and RadioLink clases.
	This clases are oriented to describe UE traffic profile, and UE relative concepts
"""

import random
from collections import deque
import numpy as np
from regex import F
from Results import (
	printResults, getKPIs, makePlotsIntra, getKPIsInter, makePlotsInter
)

DEEPMIMO_DATAFILE_PREFIX = 'Data_'
DEEPMIMO_DATAFILE_SUFFIX = '.npz'
DEEPMIMO_DATAFILE_ARR_NAME_SNR = 'arr_0'
DEEPMIMO_DATAFILE_ARR_NAME_RANK = 'arr_1'
DEEPMIMO_DATAFILE_ARR_NAME_DEGREE = 'arr_2'


def initialSinrGenerator(n_ues, refValue):
    """
        Auxiliary method for SINR generation. This method is used to generate initial 
        UE SINR. Later, during the simulation SINR will have small variations with time.
    """
    genSINRs = []
    sameSINR = refValue[0] == 'S'
    value = float(refValue[1:])
    delta = float(value - 5.0)/n_ues
    for i in range(n_ues):
        if sameSINR:
            genSINRs.append(value)
        else:
            genSINRs.append(value-delta*i)
    return genSINRs


class UEgroup:
    """
        This class is used to describe traffic profile and requirements of group of UE which
        the simulation will run for. It is assumed that all UEs shares the same traffic profile
        and service requirements, and will be served by the same slice.
    """
    def __init__(
        self, nuDL, nuUL, pszDL, pszUL, parrDL, parrUL, label, dly, avlty, schedulerType, mmMd,
        lyrs, cell, t_sim, measInterv, env, sinr, init_ues=True
    ):
        self.num_usersDL = nuDL
        self.num_usersUL = nuUL
        self.p_sizeDL = pszDL
        self.p_sizeUL = pszUL
        self.p_arr_rateDL = parrDL
        self.p_arr_rateUL = parrUL
        self.sinr_0DL = 0
        """Initial sinr value for DL"""
        self.sinr_0UL = 0
        """Initial sinr value for UL"""
        self.sch = schedulerType
        """Intra Slice scheduler algorithm"""
        self.label = label
        """Slice label"""
        self.req = {}
        """Dictionary with services requirements"""
        self.mmMd = mmMd
        self.lyrs = lyrs
        self.gr = cell.interSliceSched.granularity
        """Inter Slice scheduler time granularity"""
        self.mgr = measInterv
        """Meassurement time granularity"""
        self.setReq(dly,avlty)
        self.schIn = cell.sch
        
        if init_ues:
            self.setInitialSINR(sinr)
            """Inter Slice scheduler algorithm"""
            if self.num_usersDL>0:
                self.usersDL,self.flowsDL = self.initializeUEs('DL',self.num_usersDL,self.p_sizeDL,self.p_arr_rateDL,self.sinr_0DL,cell,t_sim,measInterv,env)
            if self.num_usersUL>0:
                self.usersUL,self.flowsUL = self.initializeUEs('UL',self.num_usersUL,self.p_sizeUL,self.p_arr_rateUL,self.sinr_0UL,cell,t_sim,measInterv,env)

    def setReq(self,delay,avl):
        """
            This method sets the service requirements depending on the UE group traffic profile and required delay
        """
        self.req['reqDelay'] = delay
        self.req['reqThroughputDL'] = 8*self.p_sizeDL*self.p_arr_rateDL
        self.req['reqThroughputUL'] = 8*self.p_sizeUL*self.p_arr_rateUL
        self.req['reqAvailability'] = avl

    def setInitialSINR(self,sinr):
        """This method sets the initial SINR value"""
        if self.num_usersDL>0:
            self.sinr_0DL = initialSinrGenerator(self.num_usersDL,sinr)
        if self.num_usersUL>0:
            self.sinr_0UL = initialSinrGenerator(self.num_usersUL,sinr)
    

    def initializeUEs(
        self, dir, num_users, p_size, p_arr_rate, sinr_0, cell, t_sim, measInterv, env, update_rl=True
    ):
        """
            This method creates the UEs with its traffic flows, and initializes the asociated PEM methods
        """
        users = []
        flows = []
        procFlow = []
        procUE = []
        procRL = []
        for j in range (num_users):
            ue_name = 'ue'+str(j+1)#+'-'+self.label
            users.append(UE(ue_name,float(sinr_0[j]),0,20))
            flows.append(PacketFlow(1,p_size,p_arr_rate,ue_name,dir,self.label))
            users[j].addPacketFlow(flows[j])
            users[j].packetFlows[0].setQosFId(1)
            # Flow, UE and RL PEM activation
            procFlow.append(env.process(users[j].packetFlows[0].queueAppPckt(env,tSim=t_sim)))
            procUE.append(env.process(users[j].receivePckt(env,c=cell)))
            if update_rl:
                procRL.append(env.process(users[j].radioLinks.updateLQ(env,udIntrv=measInterv,tSim=t_sim,fl=False,u=num_users,r='')))
        return users,flows

    def activateSliceScheds(self,interSliceSche,env):
        """This method activates PEM methods from the intra Slice schedulers"""
        if self.num_usersDL>0:
            procSchDL = env.process(interSliceSche.slices[self.label].schedulerDL.queuesOut(env))
        if self.num_usersUL>0:
            procSchUL = env.process(interSliceSche.slices[self.label].schedulerUL.queuesOut(env))

    def printSliceResults(self,interSliceSche,t_sim,bw,measInterv):
        """This method prints main simulation results on the terminal, gets the considered kpi from the statistic files, and builds kpi plots"""
        if self.num_usersDL>0:
            printResults('DL',self.usersDL,self.num_usersDL,interSliceSche.slices[self.label].schedulerDL,t_sim,True,False,self.sinr_0DL)
            # print('Configured Signalling Load: '+str(interSliceSche.slices[self.label].signLoad))
            # print('Using Robust MCS: '+str(interSliceSche.slices[self.label].robustMCS))
            [SINR_DL,times_DL,mcs_DL,rU_DL,plr_DL,th_DL] = getKPIs('DL','Statistics/dlStsts'+'_'+self.label+'.txt',self.usersDL,self.num_usersDL,self.sinr_0DL,measInterv,t_sim)
            makePlotsIntra('DL',times_DL,SINR_DL,mcs_DL,rU_DL,plr_DL,th_DL,self.label,bw,self.sch,self.mgr)
            [times_DL,rU_DL,plr_DL,th_DL,cnx_DL,buf_DL,met] = getKPIsInter('DL','Statistics/dlStsts_InterSlice.txt',list(interSliceSche.slices.keys()),len(list(interSliceSche.slices.keys())))
            makePlotsInter('DL',times_DL,rU_DL,plr_DL,th_DL,cnx_DL,buf_DL,met,bw,self.schIn,self.gr)

        if self.num_usersUL>0:
            printResults('UL',self.usersUL,self.num_usersUL,interSliceSche.slices[self.label].schedulerUL,t_sim,True,False,self.sinr_0UL)
            # print('Configured Signalling Load: '+str(interSliceSche.slices[self.label].signLoad))
            # print('Using Robust MCS: '+str(interSliceSche.slices[self.label].robustMCS))
            [SINR_UL,times_UL,mcs_UL,rU_UL,plr_UL,th_UL] = getKPIs('UL','Statistics/ulStsts'+'_'+self.label+'.txt',self.usersUL,self.num_usersUL,self.sinr_0UL,measInterv,t_sim)
            makePlotsIntra('UL',times_UL,SINR_UL,mcs_UL,rU_UL,plr_UL,th_UL,self.label,bw,self.sch,self.mgr)
            [times_UL,rU_UL,plr_UL,th_UL,cnx_UL,buf_UL,met] = getKPIsInter('UL','Statistics/ulStsts_InterSlice.txt',list(interSliceSche.slices.keys()),len(list(interSliceSche.slices.keys())))
            makePlotsInter('UL',times_UL,rU_UL,plr_UL,th_UL,cnx_UL,buf_UL,met,bw,self.schIn,self.gr)


class UeGroupDeepMimo(UEgroup):
    def __init__(
        self, nuDL, nuUL, pszDL, pszUL, parrDL, parrUL, label, dly, avlty, schedulerType, mmMd, lyrs,
        cell, t_sim, measInterv, env, ueg_dir, is_dynamic, scene_duration
    ):
        super(UeGroupDeepMimo, self).__init__(
            nuDL, nuUL, pszDL, pszUL, parrDL, parrUL, label, dly, avlty, schedulerType, mmMd, lyrs,
            cell, t_sim, measInterv, env, init_ues=False
        )
        self.ue_group_dir = ueg_dir.strip('/')
        self.id_ant = cell.id_ant  # TODO: Borrar cuando Mateo haga el cambio.
        self.current_scene = 1
        self.is_dynamic = is_dynamic
        self.scene_duration = scene_duration

        self.set_initial_snr()

        if self.num_usersDL>0:
            self.usersDL,self.flowsDL = self.initializeUEs(
				'DL', self.num_usersDL, self.p_sizeDL, self.p_arr_rateDL, self.sinr_0DL, cell,
				t_sim, measInterv, env
			)
        if self.num_usersUL>0:
            self.usersUL,self.flowsUL = self.initializeUEs(
				'UL', self.num_usersUL, self.p_sizeUL, self.p_arr_rateUL, self.sinr_0UL, cell,
				t_sim, measInterv, env
			)
    
    def initializeUEs(
        self, dir, num_users, p_size, p_arr_rate, sinr_0, cell, t_sim, measInterv, env
    ):
        users, flows = super(UeGroupDeepMimo, self).initializeUEs(
            dir, num_users, p_size, p_arr_rate, sinr_0, cell, t_sim, measInterv, env, update_rl=False
        )
        if self.is_dynamic:
            env.process(self.pem_update_ue_group_rl(env, t_sim))
        return users,flows
    
    def set_initial_snr(self,sinr):
        """
            This method sets the initial SNR value
        """
        # TODO: estamos usando solo un snr en vez de todos los del prb
        self.update_ue_group_rl()
    
    def read_ues_channel_status(self, cant_ue, time=0):
        """
            This method returns a list containing SINRs of UEgroup at moment=time
        """
        file_name = DEEPMIMO_DATAFILE_PREFIX + str(time) + DEEPMIMO_DATAFILE_SUFFIX
        file_path = self.ue_group_dir + '/' + file_name
        ueg_channel_status = np.load(file_path)

        snrs = ueg_channel_status[DEEPMIMO_DATAFILE_ARR_NAME_SNR][0:cant_ue,:,0]  # TODO: Se va a sacar la dim de la BS
        ranks = ueg_channel_status[DEEPMIMO_DATAFILE_ARR_NAME_RANK][0:cant_ue,:,0]  # TODO: Se va a sacar la dim de la BS
        degrees = ueg_channel_status[DEEPMIMO_DATAFILE_ARR_NAME_DEGREE][0:cant_ue,:,0]  # TODO: Se va a sacar la dim de la BS

        return snrs, ranks, degrees
    
    def pem_update_ue_group_rl(self, env, tSim):
        """
            This PEM method updates all UE's radio link quality in the group
        """
        # TODO: Cambiar para actualizar un modelo de canal mas razonable.
        while env.now<(tSim*0.83):
            yield env.timeout(self.scene_duration)
            self.update_ue_group_rl()
            self.current_scene += 1
    
    def update_ue_group_rl(self):
        cant_users = max(self.num_usersDL, self.num_usersUL)
        snrs, _, _ = self.read_ues_channel_status(cant_ue=cant_users, time=self.current_scene)
        if self.num_usersDL > 0:
            for i, usr in enumerate(self.usersDL):
                usr.radioLinks.updateLQ(snrs[i,0])
        if self.num_usersUL > 0:
            for i, usr in enumerate(self.usersUL):
                usr.radioLinks.updateLQ(snrs[i,0])



# UE class: terminal description

class UE():
	""" This class is used to model UE behabiour and relative properties """
	def __init__(self, i,ue_sinr0,p,npM):
		self.id = i
		self.state = 'RRC-IDLE'
		self.packetFlows = []
		self.bearers = []
		self.radioLinks = RadioLink(1,ue_sinr0,self.id)
		self.TBid = 1
		self.pendingPckts = {}
		self.prbs = p
		self.resUse = 0
		self.pendingTB = []
		self.bler = 0
		self.tbsz = 1
		self.MCS = 0
		self.pfFactor = 1 # PF Scheduler
		self.pastTbsz = deque([1]) # PF Scheduler
		self.lastDen = 0.001 # PF Scheduler
		self.num = 0 # PF Scheduler
		self.BWPs = npM
		self.TXedTB = 1
		self.lostTB = 0
		self.symb = 0

	def addPacketFlow(self,pckFl):
		self.packetFlows.append(pckFl)

	def addBearer(self,br):
		self.bearers.append(br)

	def receivePckt(self,env,c): # PEM -------------------------------------------
		"""This method takes packets on the application buffers and leave them on the bearer buffers. This is a PEM method."""
		while True:
			if len(self.packetFlows[0].appBuff.pckts)>0:
				if self.state == 'RRC-IDLE': # Not connected
					self.connect(c)
					nextPackTime = c.tUdQueue
					yield env.timeout(nextPackTime)
					if nextPackTime > c.inactTimer:
						self.releaseConnection(c)
				else: # Already connecter user
					self.queueDataPckt(c)
					nextPackTime = c.tUdQueue
					yield env.timeout(nextPackTime)
					if nextPackTime > c.inactTimer:
						self.releaseConnection(c)
			else:
				nextPackTime = c.tUdQueue
				yield env.timeout(nextPackTime)

	def connect(self,cl):
		"""This method creates bearers and bearers buffers."""
		bD = Bearer(1,9,self.packetFlows[0].type)
		self.addBearer(bD)
		self.queueDataPckt(cl)
		if self.packetFlows[0].type == 'DL':
			if (list(cl.interSliceSched.slices[self.packetFlows[0].sliceName].schedulerDL.ues.keys()).count(self.id))<1:
				cl.interSliceSched.slices[self.packetFlows[0].sliceName].schedulerDL.ues[self.id] = self
		else:
			if (list(cl.interSliceSched.slices[self.packetFlows[0].sliceName].schedulerUL.ues.keys()).count(self.id))<1:
				cl.interSliceSched.slices[self.packetFlows[0].sliceName].schedulerUL.ues[self.id] = self
		self.state = 'RRC-CONNECTED'


	def queueDataPckt(self,cell):
		"""This method queues the packets taken from the application buffer in the bearer buffers."""
		pD = self.packetFlows[0].appBuff.removePckt()
		buffSizeAllUEs = 0
		buffSizeThisUE = 0
		if self.packetFlows[0].type == 'DL':
			for ue in list(cell.interSliceSched.slices[self.packetFlows[0].sliceName].schedulerDL.ues.keys()):
				buffSizeUE = 0
				for p in cell.interSliceSched.slices[self.packetFlows[0].sliceName].schedulerDL.ues[ue].bearers[0].buffer.pckts:
					buffSizeUE = buffSizeUE + p.size
				if self.id == ue:
					buffSizeThisUE = buffSizeUE
				buffSizeAllUEs = buffSizeAllUEs + buffSizeUE
		else:
			for ue in list(cell.interSliceSched.slices[self.packetFlows[0].sliceName].schedulerUL.ues.keys()):
				buffSizeUE = 0
				for p in cell.interSliceSched.slices[self.packetFlows[0].sliceName].schedulerUL.ues[ue].bearers[0].buffer.pckts:
					buffSizeUE = buffSizeUE + p.size
				if self.id == ue:
					buffSizeThisUE = buffSizeUE
				buffSizeAllUEs = buffSizeAllUEs + buffSizeUE

		if buffSizeThisUE<cell.maxBuffUE:#len(self.bearers[1].buffer.pckts)<cell.maxBuffUE:
			self.bearers[0].buffer.insertPckt(pD)
		else:
			pcktN = pD.secNum
			#print (Format.CRED+Format.CBOLD+self.id,'packet ',pcktN,' lost .....',str(pD.tIn)+Format.CEND)
			if self.packetFlows[0].type == 'DL':
				cell.interSliceSched.slices[self.packetFlows[0].sliceName].schedulerDL.printDebDataDM('<p style="color:red"><b>'+str(self.id)+' packet '+str(pcktN)+' lost .....'+str(pD.tIn)+'</b></p>')
			else:
				cell.interSliceSched.slices[self.packetFlows[0].sliceName].schedulerUL.printDebDataDM('<p style="color:red"><b>'+str(self.id)+' packet '+str(pcktN)+' lost .....'+str(pD.tIn)+'</b></p>')
			self.packetFlows[0].lostPackets = self.packetFlows[0].lostPackets + 1

	def releaseConnection(self,cl):
		self.state = 'RRC-IDLE'
		self.bearers = []

# ------------------------------------------------
# PacketFlow class: PacketFlow description
class PacketFlow():
	""" This class is used to describe UE traffic profile for the simulation."""
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
		"""This method creates packets according to the packet flow traffic profile and stores them in the application buffer. """
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
	"""This class is used to model packets properties and behabiour."""
	def __init__(self,sn,s,qfi,u):
		self.secNum = sn
		self.size = s
		self.qosFlowId = qfi
		self.ue = u
		self.tIn = 0

	def printPacket(self):
		print (Format.CYELLOW + Format.CBOLD + self.ue+ '+packet '+str(self.secNum)+' arrives at t ='+str(now()) + Format.CEND)

class Bearer:
	"""This class is used to model Bearers properties and behabiour."""
	def __init__(self,i,q,tp):
		self.id = i
		self.qci = q
		self.type = tp
		self.buffer = PcktQueue()

class PcktQueue:
	"""This class is used to model application and bearer buffers."""
	def __init__(self):
		self.pckts = deque([])

	def insertPckt(self,p):
		self.pckts.append(p)

	def insertPcktLeft(self,p):
		self.pckts.appendleft(p)

	def removePckt(self):
		if len(self.pckts)>0:
			return self.pckts.popleft()

class RadioLink():
	"""This class is used to model radio link properties and behabiour."""
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

	# def updateLQ(self,lq):
	# 	"""This method updates UE link quality in terms of SINR during the simulation"""
	# 	self.linkQuality = lq

class Format:
    CEND      = '\33[0m'
    CBOLD     = '\33[1m'
    CITALIC   = '\33[3m'
    CURL      = '\33[4m'
    CBLINK    = '\33[5m'
    CBLINK2   = '\33[6m'
    CSELECTED = '\33[7m'
    CBLACK  = '\33[30m'
    CRED    = '\33[31m'
    CGREEN  = '\33[32m'
    CYELLOW = '\33[33m'
    CBLUE   = '\33[34m'
    CVIOLET = '\33[35m'
    CBEIGE  = '\33[36m'
    CWHITE  = '\33[37m'
    CGREENBG  = '\33[42m'
    CBLUEBG   = '\33[44m'
