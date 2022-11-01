"""
    This module contains different implemented intra slice schedulers.
    New schedulers should be implemented here following the current structure.
"""

import math
from IntraSliceSch import (
    IntraSliceScheduler, Format, TbQueueDeepMimo
)
from collections import deque
from utilities import Format


class IntraSliceSchedulerDeepMimo(IntraSliceScheduler):
    def __init__(self, ba, n, debMd, sLod, ttiByms, mmd_, ly_, dir, Smb, robustMCS, slcLbl, sch, slice):
        
        super(IntraSliceSchedulerDeepMimo, self).__init__(
            ba, n, debMd, sLod, ttiByms, mmd_, ly_, dir, Smb, robustMCS, slcLbl, sch
        )
        self.slice = slice
        self.queue = TbQueueDeepMimo()
    
    def resAlloc(self):
        """
            This method allocates cell specifics PRBs to the different connected UEs.
        """

        # TODO: Completar. 
        # Ver de donde saco la lista de prbs base asignados a la slice.
        # Tengo que guardar los resultados en los usuarios:
        #   - assigned_prbs: lista de los prb base asignados a los usuarios, asi despues se puede ver el snr.
        #   - PRBs: por compatibilidad, es la cantidad de PRBs asignados = cant_prbs_base_asignado/factor.
        #   - assigned_layers: la cantidad de layers que se le dio a ese usuario.

        base_prbs_to_assign = self.slice.assigned_base_prbs
        cant_prb_in_a_group = self.ttiByms
        ue_with_bearer_packets = [self.ues[ue_key] for ue_key in list(self.ues.keys()) if self.ues[ue_key].has_packet_in_bearer()]

        # Esto esta mal, pero para probar a cada ue le doy todas los prbs (repito):
        for ue in ue_with_bearer_packets:
            ue.assigned_base_prbs = base_prbs_to_assign  # La asignacion deberia hacerse teniendo en cuenta el scs del prb.
            ue.assigned_layers = 2
            ue.prbs = len(ue.assigned_base_prbs)/cant_prb_in_a_group

        # Print Resource Allocation
        self.printResAlloc()

    def queueUpdate(self):
        """
            This method overrides the one in the parent class. 
            This method fills scheduler TB queue at each TTI with TBs built with UE data/signalling 
            bytes without verify that the resource blocks used match with the assigned ones.
            It makes Resource allocation and insert generated TBs into Scheduler queue in a TTI.
        """

        self.ueLst = list(self.ues.keys())
        self.resAlloc()
        
        # RB limit no va mas, ahora se confia en la asignacion de resAlloc.

        for ue_key in self.ueLst:

            ue = self.ues[ue_key]
            ue_has_packets_in_bearer = ue.has_packet_in_bearer()
            ue_has_prb_assigned = ue.prbs > 0
            ue_has_tb_to_retransmit = len(ue.pendingTB) > 0

            self.printDebDataDM('---------------- '+ue_key+' ------------------<br>') # print more info in debbug mode

            if ue_has_prb_assigned and ue_has_packets_in_bearer:

                if not ue_has_tb_to_retransmit:
                    self.dataPtoTB(ue_key)
                else:
                    self.retransmitTB(ue_key)

                if self.dbMd:
                    self.printQtb() # Print TB queue in debbug mode
    
    def setMod(self,u,nprb):
        """
            This method sets the MCS and TBS for each TB over the specifics PRBs frequencies.
        """
        snr, _ = self.ues[u].radioLinks.get_radio_link_quality_over_assigned_prbs()
        mcs_ = self.findMCS(snr)
        if self.robustMCS and mcs_>2:
            mcs_ = mcs_-2
        mo = self.modTable[mcs_]['mod']
        mcsi = self.modTable[mcs_]['mcsi']
        Qm = self.modTable[mcs_]['bitsPerSymb']
        R = self.modTable[mcs_]['codeRate']
        # Find TBsize
        if self.band == 'n257' or self.band == 'n258' or self.band == 'n260' or self.band == 'n261':
            fr = 'FR2'
        else:
            fr = 'FR1'
        if nprb>0:
            tbls = self.setTBS(R,Qm,self.direction,u,fr,nprb) # bits
        else:
            tbls = 0 # PF Scheduler
        return [tbls, mo, Qm, mcsi]
    
    def setTBS(self, r, qm, uldl, ue, fr, nprb): # TS 38.214 procedure
        OHtable = {'DL':{'FR1':0.14,'FR2':0.18},'UL':{'FR1':0.08,'FR2':0.10}}
        OH = OHtable[uldl][fr]
        Nre__ = min(156,math.floor(12*self.TDDsmb*(1-OH)))

        tbs = Nre__*nprb*r*qm*self.ues[ue].assigned_layers

        return tbs


class PF_Scheduler(IntraSliceScheduler): # PF Sched ---------
    """
        This class implements Proportional Fair intra slice scheduling algorithm.
    """
    def __init__(self,ba,n,debMd,sLod,ttiByms,mmd_,ly_,dir,Smb,robustMCS,slcLbl,sch):
        IntraSliceScheduler.__init__(self,ba,n,debMd,sLod,ttiByms,mmd_,ly_,dir,Smb,robustMCS,slcLbl,sch)
        self.promLen = 30
        """Past Throughput average length considered in PF metric"""

    def resAlloc(self,band):
        """
            This method implements Proportional Fair resource allocation between the different connected UEs.
            This method overwrites the resAlloc method from IntraSliceScheduler class.
            Proportional Fair scheduler allocates all PRBs in the slice to the UE with the biggest metric.
            Metric for each UE is calculated as PossibleUEtbs/AveragePastTbs.
        """
        schd = self.schType[0:2]
        if schd=='PF' and len(list(self.ues.keys()))>0:
            exp_num = float(self.schType[2])
            exp_den = float(self.schType[3])
            self.setUEfactor(exp_num, exp_den)
            maxInd = self.findMaxFactor()
            for ue in list(self.ues.keys()):
                if ue == maxInd:
                    self.ues[ue].prbs = band
                else:
                    self.ues[ue].prbs = 0
                    if len(self.ues[ue].pastTbsz)>self.promLen:
                        self.ues[ue].pastTbsz.popleft()
                    self.ues[ue].pastTbsz.append(self.ues[ue].tbsz)
                    self.ues[ue].tbsz = 1
        # Print Resource Allocation
        self.printResAlloc()

    def setUEfactor(self, exp_n, exp_d):
        """
            This method sets the PF metric for each UE.
        """
        for ue in list(self.ues.keys()):
            sumTBS = 0
            for t in self.ues[ue].pastTbsz:
                sumTBS = sumTBS + t
            actual_den = sumTBS/len(self.ues[ue].pastTbsz)
            [tbs, mod, bi, mcs] = self.setMod(ue,self.nrbUEmax)
            self.ues[ue].pfFactor = math.pow(float(tbs), exp_n)/math.pow(actual_den,exp_d)
            self.ues[ue].lastDen = actual_den
            self.ues[ue].num = tbs

    def findMaxFactor(self):
        """
            This method finds and returns the UE with the highest metric
        """
        factorMax = 0
        factorMaxInd = ''
        for ue in list(self.ues.keys()):
            if len(self.ues[ue].bearers[0].buffer.pckts)>0 and self.ues[ue].pfFactor>factorMax:
                factorMax = self.ues[ue].pfFactor
                factorMaxInd = ue
        if factorMaxInd=='':
            ue = list(self.ues.keys())[self.ind_u]
            q = 0
            while len(self.ues[ue].bearers[0].buffer.pckts)==0 and q<len(self.ues):
                self.updIndUE()
                ue = list(self.ues.keys())[self.ind_u]
                q = q + 1
            factorMaxInd = ue

        return factorMaxInd

    def printResAlloc(self):
        if self.dbMd:
            self.printDebData('+++++++++++ Res Alloc +++++++++++++'+'<br>')
            self.printDebData('PRBs: '+str(self.nrbUEmax)+'<br>')
            resAllocMsg = ''
            for ue in list(self.ues.keys()):
                resAllocMsg = resAllocMsg + ue +' '+ str(self.ues[ue].pfFactor)+' '+str(self.ues[ue].prbs)+ ' '+str(self.ues[ue].num)+' '+ str(self.ues[ue].lastDen)+'<br>'
            self.printDebData(resAllocMsg)
            self.printDebData('+++++++++++++++++++++++++++++++++++'+'<br>')

class TDD_Scheduler(IntraSliceScheduler): # TDD Sched ---------
    """
        This class implements TDD intra slice scheduling.
    """
    def __init__(self,ba,n,debMd,sLod,ttiByms,mmd_,ly_,dir,Smb,robustMCS,slcLbl,sch):
        IntraSliceScheduler.__init__(self,ba,n,debMd,sLod,ttiByms,mmd_,ly_,dir,Smb,robustMCS,slcLbl,sch)
        self.symMax = Smb
        self.queue = TBqueueTDD(self.symMax)
        """
            TDD scheduler TB queue. IntraSliceScheduler class attribute queue is overwriten here by a new type of queue
            which handles symbols. This queue will contain as much TB as a slot can contain. If resource allocation is made
            in terms of slots, it will contain 1 element, else, it will contain as much mini-slots as can be supported in 1 slot.
        """

    def resAlloc(self,band):
        """
            This method implements resource allocation between the different connected UEs in a TDD slice.
            It overwrites the resAlloc method from IntraSliceScheduler class.
            In this Py5cheSim version TDD scheduler allocates all PRBs in the slice to a UE during 1 slot.
            Future Py5cheSim versions could support mini-slot allocation by changing the UE symbol allocation in this method.
            Note that in that case, althoug there is no need to update the queueUpdate method,
            TBS calculation must be adjusted to avoid losing capacity when trunking the Nre__ value.
        """

        if len(list(self.ues.keys()))>0:
            for ue in list(self.ues.keys()):
                self.ues[ue].prbs = band
                self.ues[ue].symb = self.TDDsmb
        # Print Resource Allocation
        self.printResAlloc()

    def queueUpdate(self):
        """
            This method fills scheduler TB queue at each TTI with TBs built with UE data/signalling bytes.
            It overwrites queueUpdate method from IntraSliceScheduler class, making Resource allocation in terms of slot Symbols
            and insert generated TBs into Scheduler queue in a TTI. Althoug in this version Resource allocation is made by slot,
            it is prepared to support mini-slot resource allocation by handling a scheduler TB queue in terms of symbols.
        """
        packts = 1
        self.ueLst = list(self.ues.keys())
        self.resAlloc(self.nrbUEmax)
        sym = 0
        if self.nrbUEmax == 0:
            self.sm_lim = 0
        else:
            if self.mimomd == 'MU':
                self.sm_lim = self.symMax*self.nlayers
            else:
                self.sm_lim = self.symMax

        while len(self.ueLst)>0 and packts>0 and sym < self.sm_lim:
            ue = self.ueLst[self.ind_u]
            self.printDebDataDM('---------------- '+ue+' ------------------<br>') # print more info in debbug mode
            if self.ues[ue].symb>0:
                if len(self.ues[ue].bearers)>0 and sym < self.sm_lim:
                    if len(self.ues[ue].pendingTB)==0: # No TB to reTX
                        sym = sym + self.rrcUncstSigIn(ue)
                        if sym < self.sm_lim and len(self.ues[ue].bearers[0].buffer.pckts)>0:
                            sym = sym + self.dataPtoTB(ue)
                    else: # There are TB to reTX
                        self.printPendTB()
                        sym = sym + self.retransmitTB(ue)
                    if self.dbMd:
                        self.printQtb() # Print TB queue in debbug mode
            self.updIndUE()
            packts = self.updSumPcks()

    def rrcUncstSigIn(self,u):
        ueN = int(self.ues[u].id[2:])
        sfSig = int(float(1)/self.sLoad)
        rrcUESigCond = (self.sbFrNum-ueN)%sfSig == 0
        if rrcUESigCond:
            p_l = []
            p_l.append(self.ues[u].packetFlows[0].pId)
            self.ues[u].packetFlows[0].pId = self.ues[u].packetFlows[0].pId + 1
            ins = self.insertTB(self.ues[u].TBid,'4-QAM',u,'Sig',p_l,self.ues[u].prbs,19)
            r = self.symMax
        else:
            r = 0
        return r

    def retransmitTB(self,u):
        pendingTbl = self.ues[u].pendingTB[0]
        if pendingTbl.reTxNum < 3000: # TB retransmission
            intd = self.queue.insertTB(pendingTbl)
            self.ues[u].pendingTB.pop(0)
            pendingTbl.reTxNum = pendingTbl.reTxNum + 1
            r = self.symMax
        else:
            self.ues[u].pendingTB.pop(0) # Drop!!!
            r = 0
        return r

    def dataPtoTB(self,u):
        """
            This method takes UE data bytes, builds TB and puts them in the scheduler TB queue.
            It overwrites dataPtoTB method from IntraSliceScheduler class. In this case it returns
            the amount of allocated symbols to the UE.
        """
        n = self.ues[u].prbs
        [tbSbits,mod,bits,mcs__] = self.setMod(u,n)
        if self.schType[0:2]=='PF':
            if len(self.ues[u].pastTbsz)>self.promLen:
                self.ues[u].pastTbsz.popleft()
            self.ues[u].pastTbsz.append(self.ues[u].tbsz)

        self.ues[u].tbsz = tbSbits
        self.ues[u].MCS = mcs__
        self.setBLER(u)
        tbSize = int(float(tbSbits)/8) # TB size in bytes
        self.printDebDataDM('TBs: '+str(tbSize)+' nrb: '+str(n)+' FreeSp: '+str(self.queue.getFreeSpace())+'<br>')
        pks_s = 0
        list_p = []
        while pks_s<tbSize and len(self.ues[u].bearers[0].buffer.pckts)>0:
            pacD = self.ues[u].bearers[0].buffer.removePckt()
            pks_s = pks_s + pacD.size
            list_p.append(pacD.secNum)

        insrt = self.insertTB(self.ues[u].TBid,mod,u,'data',list_p,n,min(int(pks_s),tbSize))
        if (pks_s - tbSize)>0:
            pacD.size = pks_s - tbSize
            self.ues[u].bearers[0].buffer.insertPcktLeft(pacD)
        return self.ues[u].symb

    def setTBS(self,r,qm,uldl,u_,fr,nprb): # TS 38.214 procedure
        OHtable = {'DL':{'FR1':0.14,'FR2':0.18},'UL':{'FR1':0.08,'FR2':0.10}}
        OH = OHtable[uldl][fr]
        Nre__ = min(156,math.floor(12*self.ues[u_].symb*(1-OH)))
        if self.mimomd == 'SU':
            Ninfo = Nre__*nprb*r*qm*self.nlayers
            tbs = Ninfo
        else:
            Ninfo = Nre__*nprb*r*qm
            tbs = Ninfo
        return tbs

    def printResAlloc(self):
        if self.dbMd:
            self.printDebData('+++++++++++ Res Alloc +++++++++++++'+'<br>')
            self.printDebData('PRBs: '+str(self.nrbUEmax)+'<br>')
            resAllocMsg = ''
            for ue in list(self.ues.keys()):
                resAllocMsg = resAllocMsg + ue +': '+ str(self.ues[ue].symb)+' symbols'+'<br>'
            self.printDebData(resAllocMsg)
            self.printDebData('+++++++++++++++++++++++++++++++++++'+'<br>')

class TBqueueTDD: # TB queue!!!
    """
        This class is used to model scheduler TB queue in TDD scheduler.
    """
    def __init__(self,symb):
        self.res = deque([])
        self.numRes = symb

    def getFreeSpace(self):
        freeSpace = self.numRes
        if len(self.res)>0:
            for tbl in self.res:
                freeSpace = freeSpace - 1
        return freeSpace

    def insertTB(self,tb):
        succ = False
        freeSpace = self.getFreeSpace()
        if freeSpace>=1:
            self.res.append(tb) # The TB fits the free space
            succ = True
        else:
            succ = False
            print (Format.CRED+'Not enough space!!! : '+str(freeSpace)+'/'+str(tb.numRB)+Format.CEND)
        return succ

    def removeTB(self):
        if len(self.res)>0:
            return self.res.popleft()

    def updateSize(self,newSize):
        self.numRes = newSize
