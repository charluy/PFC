"""
	This module contains the UE, Packet Flow, Packet, PcktQueue, Bearer and RadioLink clases.
	This clases are oriented to describe UE traffic profile, and UE relative concepts
"""

from collections import deque
import numpy as np
from regex import F
from Results import (
	printResults, getKPIs, makePlotsIntra, getKPIsInter, makePlotsInter
)
from utilities import (
    initialSinrGenerator, Format
)
from channel import (
    RadioLink, RadioLinkDeepMimo
)
from packet import (
    PacketFlow, Bearer
)

DEEPMIMO_DATAFILE_PREFIX = 'Data_'
DEEPMIMO_DATAFILE_SUFFIX = '.npz'
DEEPMIMO_DATAFILE_ARR_NAME_SNR = 'arr_0'
DEEPMIMO_DATAFILE_ARR_NAME_RANK = 'arr_1'
DEEPMIMO_DATAFILE_ARR_NAME_DEGREE = 'arr_2'


class UeGroupBase:
    """
        This class is used to describe traffic profile and requirements of group of UE which
        the simulation will run for. It is assumed that all UEs shares the same traffic profile
        and service requirements, and will be served by the same slice.
    """
    def __init__(
        self, nuDL, nuUL, pszDL, pszUL, parrDL, parrUL, label, dly, avlty, schedulerType, mmMd,
        lyrs, cell, t_sim, measInterv, env
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
    
    def setReq(self,delay,avl):
        """
            This method sets the service requirements depending on the UE group traffic profile and required delay
        """
        self.req['reqDelay'] = delay
        self.req['reqThroughputDL'] = 8*self.p_sizeDL*self.p_arr_rateDL
        self.req['reqThroughputUL'] = 8*self.p_sizeUL*self.p_arr_rateUL
        self.req['reqAvailability'] = avl
    
    def initializeUEs(
        self, dir, num_users, p_size, p_arr_rate, sinr_0, cell, t_sim, measInterv, env
    ):
        """
            This method creates the UEs with its traffic flows, and initializes the asociated PEM methods
        """
        users = []
        flows = []

        for j in range (num_users):
            ue_name = 'ue' + str(j+1)
            users.append(UE(ue_name,float(sinr_0[j]),0,20))
            flows.append(PacketFlow(1,p_size,p_arr_rate,ue_name,dir,self.label))
            users[j].addPacketFlow(flows[j])
            users[j].packetFlows[0].setQosFId(1)
            # Flow, UE and RL PEM activation
            env.process(users[j].packetFlows[0].queueAppPckt(env,tSim=t_sim))
            env.process(users[j].receivePckt(env,c=cell))

        return users,flows
    
    def activateSliceScheds(self,interSliceSche,env):
        """
            This method activates PEM methods from the intra Slice schedulers.
        """
        if self.num_usersDL>0:
            procSchDL = env.process(interSliceSche.slices[self.label].schedulerDL.queuesOut(env))
        if self.num_usersUL>0:
            procSchUL = env.process(interSliceSche.slices[self.label].schedulerUL.queuesOut(env))

    def printSliceResults(self,interSliceSche,t_sim,bw,measInterv):
        """
            This method prints main simulation results on the terminal, gets the considered kpi 
            from the statistic files, and builds kpi plots.
        """
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


class UEgroup(UeGroupBase):  # TODO: Cambiar el nombre de la clase a algo mas descriptivo
    """
        Extends UeGroupBase class for simple UE definition
    """
    
    def __init__(
        self, nuDL, nuUL, pszDL, pszUL, parrDL, parrUL, label, dly, avlty, schedulerType, mmMd,
        lyrs, cell, t_sim, measInterv, env, sinr='S40'
    ):
        super(UEgroup, self).__init__(
            nuDL, nuUL, pszDL, pszUL, parrDL, parrUL, label, dly, avlty, schedulerType, mmMd, lyrs,
            cell, t_sim, measInterv, env
        )

        self.setInitialSINR(sinr)

        if self.num_usersDL > 0:
            self.usersDL, self.flowsDL = self.initializeUEs(
                'DL', self.num_usersDL, self.p_sizeDL, self.p_arr_rateDL, self.sinr_0DL, cell, t_sim,measInterv, env
            )
        if self.num_usersUL > 0:
            self.usersUL, self.flowsUL = self.initializeUEs(
                'UL', self.num_usersUL, self.p_sizeUL, self.p_arr_rateUL, self.sinr_0UL, cell, t_sim, measInterv, env
            )

    def setInitialSINR(self,sinr):
        """
            This method generates SINR values from string.
            Example: 'S40' to indicate static value of 40db. # TODO: revisar!
        """
        if self.num_usersDL>0:
            self.sinr_0DL = initialSinrGenerator(self.num_usersDL,sinr)
        if self.num_usersUL>0:
            self.sinr_0UL = initialSinrGenerator(self.num_usersUL,sinr)
    
    def initializeUEs(
        self, dir, num_users, p_size, p_arr_rate, sinr_0, cell, t_sim, measInterv, env
    ):
        """
            Each UE radio link quality is updated in a separate PEM process.
        """
        users, flows = super(UEgroup, self).initializeUEs(
            dir, num_users, p_size, p_arr_rate, sinr_0, cell, t_sim, measInterv, env
        )
        for user in users:
            env.process(
                user.radioLinks.updateLQ(env,udIntrv=measInterv,tSim=t_sim,fl=False,u=num_users,r='')
            )

        return users, flows


class UeGroupDeepMimo(UeGroupBase):
    def __init__(
        self, nuDL, nuUL, pszDL, pszUL, parrDL, parrUL, label, dly, avlty, schedulerType, mmMd, lyrs,
        cell, t_sim, measInterv, env, ueg_dir, is_dynamic, scene_duration
    ):
        super(UeGroupDeepMimo, self).__init__(
            nuDL, nuUL, pszDL, pszUL, parrDL, parrUL, label, dly, avlty, schedulerType, mmMd, lyrs,
            cell, t_sim, measInterv, env
        )
        self.ue_group_dir = ueg_dir.strip('/')
        self.id_ant = cell.id_ant  # TODO: Borrar cuando Mateo haga el cambio.
        self.current_scene = 0
        self.is_dynamic = is_dynamic
        self.scene_duration = scene_duration

        self.sinr_0DL, _, _ = self.read_ues_channel_status(self.num_usersDL)
        self.sinr_0DL = self.sinr_0DL[:,0]

        self.sinr_0UL, _, _ = self.read_ues_channel_status(self.num_usersDL)
        self.sinr_0UL = self.sinr_0UL[:,0]

        if self.num_usersDL>0:
            self.usersDL, self.flowsDL = self.initializeUEs(
				'DL', self.num_usersDL, self.p_sizeDL, self.p_arr_rateDL, self.sinr_0DL, cell,
				t_sim, measInterv, env
			)
        if self.num_usersUL>0:
            self.usersUL, self.flowsUL = self.initializeUEs(
				'UL', self.num_usersUL, self.p_sizeUL, self.p_arr_rateUL, self.sinr_0UL, cell,
				t_sim, measInterv, env
			)
		
        self.set_initial_snr()
    
    def initializeUEs(
        self, dir, num_users, p_size, p_arr_rate, sinr_0, cell, t_sim, measInterv, env
    ):
        users, flows = super(UeGroupDeepMimo, self).initializeUEs(
            dir, num_users, p_size, p_arr_rate, sinr_0, cell, t_sim, measInterv, env
        )
        if self.is_dynamic:
            env.process(self.pem_update_ue_group_rl(env, t_sim))
        return users,flows
    
    def set_initial_snr(self):
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
        """
            This methods read DeepMIMO channel status files and update each UE radio link 
            quality.
        """

        cant_users = max(self.num_usersDL, self.num_usersUL)
        snrs, ranks, degrees = self.read_ues_channel_status(cant_ue=cant_users, time=self.current_scene)

        if self.num_usersDL > 0:
            for i, usr in enumerate(self.usersDL):
                usr.radioLinks.update_link_quality_from_value(snrs[i,0])

        if self.num_usersUL > 0:
            for i, usr in enumerate(self.usersUL):
                usr.radioLinks.update_link_quality_from_value(snrs[i,0])


# UE class: terminal description

class UeBase:
    """
        This class is used to model UE behabiour and relative properties
    """
    def __init__(self, id, ue_initial_sinr):
        self.id = id
        self.state = 'RRC-IDLE'
        self.packetFlows = []
        self.bearers = []

        self.TBid = 1
        self.pendingPckts = {}

        self.resUse = 0
        self.pendingTB = []
        self.bler = 0
        self.tbsz = 1
        self.MCS = 0
        self.pfFactor = 1 # PF Scheduler
        self.pastTbsz = deque([1]) # PF Scheduler
        self.lastDen = 0.001 # PF Scheduler
        self.num = 0 # PF Scheduler

        self.TXedTB = 1
        self.lostTB = 0
        self.symb = 0
    
    def addPacketFlow(self, pckFl):
        self.packetFlows.append(pckFl)

    def addBearer(self, br):
        self.bearers.append(br)
    
    def receivePckt(self,env,c): # PEM -------------------------------------------
        """
            This method takes packets on the application buffers and leave them on the bearer buffers.
            This is a PEM method.
        """
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
        """
            This method creates bearers and bearers buffers.
        """
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
        """
            This method queues the packets taken from the application buffer in the bearer buffers.
        """
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


class UE(UeBase):
    """
        This class is used to model UE behabiour and relative properties
        for a simplified version of channel model.
    """
    def __init__(self, id, ue_initial_sinr, p, npM):
        super(UE, self).__init__(id, ue_initial_sinr)
        self.radioLinks = RadioLink(1, ue_initial_sinr, self.id)
        self.prbs = p
        self.BWPs = npM


class UeDeepMimo(UeBase):
    """
        This class is used to model UE behabiour and relative properties
        for a complex version of channel model given by DeepMIMO framework.
    """
    def __init__(self, id, ue_initial_sinr, ue_initial_rank, ue_initial_degree, cell):
        super(UeDeepMimo, self).__init__(id, ue_initial_sinr)
        self.cell = cell
        self.radioLinks = RadioLinkDeepMimo(self, cell)
        self.update_radio_link_status(ue_initial_sinr, ue_initial_rank, ue_initial_degree)
    
    def update_radio_link_status(self, snr, rank, degree):
        self.radioLinks.update_link_status(snr, rank, degree)
    



