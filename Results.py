"""
    This module contains auxiliary simulation classes and methods along with results processing.
"""
import os
import sys
import matplotlib.pyplot as plt
from matplotlib.ticker import (AutoMinorLocator, MultipleLocator)
# from UE import *
from Cell import Format
import numpy as np

def printResults(dir,users,num_users,scheduler,t_sim,singleRunMode,fileSINR,sinr):
    """This method prints main simulation results on the terminal"""
    PDRprom = 0.0
    SINRprom = 0.0
    MCSprom = 0.0
    THprom = 0.0
    # UEresults = open('UEresults'+str(sinr[0])+'.txt','w') # This file is used as an input for the validation script
    # UEresults.write('SINR MCS BLER PLR TH ResUse'+'\n')
    print (Format.CGREEN+'Accumulated '+dir+' indicators by user:'+Format.CEND)
    for i in range (num_users):
        # Count pending packets also as lost
        users[i].packetFlows[0].lostPackets = users[i].packetFlows[0].lostPackets + len(list(scheduler.ues[users[i].id].pendingPckts.keys())) + len(users[i].packetFlows[0].appBuff.pckts) + len(scheduler.ues[users[i].id].bearers[0].buffer.pckts)
        for p in list(scheduler.ues[users[i].id].pendingPckts.keys()):
            for pp in scheduler.ues[users[i].id].bearers[0].buffer.pckts:
                if p == pp.secNum:
                     users[i].packetFlows[0].lostPackets = users[i].packetFlows[0].lostPackets - 1

        users[i].packetFlows[0].setMeassures(t_sim)
        PDRprom = PDRprom + users[i].packetFlows[0].meassuredKPI['PacketLossRate']
        THprom = THprom + users[i].packetFlows[0].meassuredKPI['Throughput']
        if singleRunMode and fileSINR:
            sinrUser = float(users[i].radioLinks.lqAv)/users[i].radioLinks.totCount
        else:
            sinrUser = users[i].radioLinks.linkQuality # not single run, or single run but not taking SINR from file
        SINRprom = SINRprom + sinrUser
        MCSprom = MCSprom + float(users[i].MCS)

        print (users[i].id+'\t'+Format.CYELLOW+ ' Sent Packets:'+Format.CEND+str(users[i].packetFlows[0].sentPackets)+Format.CYELLOW+ ' Lost Packets:'+Format.CEND+str(users[i].packetFlows[0].lostPackets))
        print ('\t'+ 'SINRav: '+str(int(sinrUser))+ ' MCSav: '+str(users[i].MCS)+' PLR: '+str(round(users[i].packetFlows[0].meassuredKPI['PacketLossRate'],2))+' %'+' Throughput: '+str(round(users[i].packetFlows[0].meassuredKPI['Throughput'],2)))

        # UEresults.write(str(sinrUser)+' '+str(users[i].MCS)+' '+str(float(users[i].lostTB)/(users[i].TXedTB+users[i].lostTB))+' '+str(users[i].packetFlows[0].meassuredKPI['PacketLossRate']/100)+' '+str(users[i].packetFlows[0].meassuredKPI['Throughput'])+' '+str(users[i].resUse)+' '+str(int(float(users[i].tbsz)/8))+'\n')

    print (Format.CGREEN+'Average '+dir+' Indicators:'+Format.CEND)
    print ('Packet Loss Rate av: '+'\t'+str(round((PDRprom)/num_users,2))+' %')
    print ('Throughput av: '+'\t'+str(round(THprom/num_users,2))+' Mbps')
    print ('Connections av: '+'\t'+str(num_users))
    print ('Slice Resources: '+'\t'+str(scheduler.nrbUEmax)+ ' PRBs')
    print ('Symbols in slot: '+'\t'+str(scheduler.TDDsmb))
    print ('Slice Numerology: '+'\t'+str(scheduler.ttiByms*15)+ ' kHz')

def getKPIs(dir,stFile,users,num_users,sinr_0,measInterv,tSim):
    """This method gets the intra slice kpi from the statistic files"""
    sent = {}
    lost = {}
    SINR = {}
    BLER = {}
    times = {}
    mcs = {}
    rBytes = {}
    rU = {}
    plr = {}
    th = {}
    allTimes = {}
    for i in range (num_users):
        times[users[i].id] = [0]
        SINR[users[i].id] = [sinr_0[i]]
        mcs[users[i].id] = [users[i].MCS]
        BLER[users[i].id] = [users[i].bler]
        rU[users[i].id] = [0]
        sent[users[i].id] = [0]
        lost[users[i].id] = [0]
        rBytes[users[i].id] = [0]
        plr[users[i].id] = [0]
        th[users[i].id] = [0]

    with open(stFile) as dlStsts:
        lines = dlStsts.readlines()
    for line in lines[1:]:
        columns = line.split(" ",9)
        time = columns[0]
        ue = columns[1]
        sinr_ = columns[2]
        mcs_ = columns[3]
        bler = columns[4]
        resUse = columns[5]
        sntPackets = columns[6]
        lstPackets = columns[7]
        rcvdBytes = columns[8]
        slice = columns[9]

        times[ue].append(float(time))
        SINR[ue].append(float(sinr_))
        mcs[ue].append(int(mcs_))
        BLER[ue].append(float(bler))
        rU[ue].append(int(resUse) - rU[ue][len(rU[ue])-1])
        sent[ue].append(int(sntPackets))
        lost[ue].append(int(lstPackets))
        rBytes[ue].append(int(rcvdBytes))
        if (sent[ue][len(sent[ue])-1] - sent[ue][len(sent[ue])-2])>0:
            plr[ue].append(100*float(lost[ue][len(lost[ue])-1] - lost[ue][len(lost[ue])-2])/(sent[ue][len(sent[ue])-1] - sent[ue][len(sent[ue])-2]))
        else:
            plr[ue].append(0)
        rcvdBytes = rBytes[ue][len(rBytes[ue])-1] - rBytes[ue][len(rBytes[ue])-2]
        deltaT = times[ue][len(times[ue])-1] - times[ue][len(times[ue])-2]
        th[ue].append((float(rcvdBytes)*8000)/(deltaT*1024*1024))

    # update resource Use (rU) to consider %
    for t in range(len(times[users[0].id])):
        resU = 0
        for ue in list(times.keys()):
            resU = resU + rU[ue][t]
        for ue in list(times.keys()):
            if resU>0:
                rU[ue][t] = 100*float(rU[ue][t])/resU
    return SINR,times,mcs,rU,plr,th

def getKPIsInter(dir,stFile,slices,num_slices):
    """This method gets the inter Slice kpi from the statistic files"""
    sent = {}
    lost = {}
    times = {}
    rBytes = {}
    plr = {}
    th = {}
    rU = {}
    cnx = {}
    buf = {}
    met = {}
    for i in range (num_slices):
        times[slices[i]] = [0]
        rU[slices[i]] = [0]
        sent[slices[i]] = [0]
        lost[slices[i]] = [0]
        rBytes[slices[i]] = [0]
        plr[slices[i]] = [0]
        th[slices[i]] = [0]
        cnx[slices[i]] = [0]
        buf[slices[i]] = [0]
        met[slices[i]] = [0]

    with open(stFile) as Ststs:
        lines = Ststs.readlines()
    for line in lines[1:]:
        columns = line.split(" ",9)
        time = columns[0]
        slice = columns[1]
        cnxs = columns[2]
        resUse = columns[3]
        sntPackets = columns[4]
        lstPackets = columns[5]
        rcvdBytes = columns[6]
        buff = columns[7]
        mt = columns[8]

        times[slice].append(float(time))
        cnx[slice].append(float(cnxs))
        rU[slice].append(int(resUse))
        buf[slice].append(int(buff))
        met[slice].append(float(mt))
        sent[slice].append(int(sntPackets))
        lost[slice].append(int(lstPackets))
        rBytes[slice].append(int(rcvdBytes))
        if (sent[slice][len(sent[slice])-1] - sent[slice][len(sent[slice])-2])>0:
            plr[slice].append(100*float(lost[slice][len(lost[slice])-1] - lost[slice][len(lost[slice])-2])/(sent[slice][len(sent[slice])-1] - sent[slice][len(sent[slice])-2]))
        else:
            plr[slice].append(0)
        rcvdBytes = rBytes[slice][len(rBytes[slice])-1] - rBytes[slice][len(rBytes[slice])-2]
        deltaT = times[slice][len(times[slice])-1] - times[slice][len(times[slice])-2]
        th[slice].append((float(rcvdBytes)*8000)/(deltaT*1024*1024))

    return times,rU,plr,th,cnx,buf,met

def makeTimePlot(u,plotName,plotType,xAx,yAx):
    """This method makes basic time plots. Labels deppend on which kpi is being plotted."""
    # if inter=True, u is the slice name
    if plotType=='PLR':
        plt.plot(xAx[u],yAx[u],label='PLR(%) '+u)
    if plotType=='TH':
        plt.plot(xAx[u],yAx[u],label='TH(Mbps) '+u)
    if plotType=='UEresUse':
        plt.plot(xAx[u],yAx[u],label='ResUse(%) '+u)
    if plotType=='sliceResUse':
        plt.plot(xAx[u],yAx[u],label='ResUse(PRBs) '+u)
    if plotType=='SINR':
        plt.plot(xAx[u],yAx[u],label='SINR(dB) '+u)
    if plotType=='MCS':
        plt.scatter(xAx[u],yAx[u],label='MCS '+u)
    if plotType=='Connections':
        plt.plot(xAx[u],yAx[u],label='Connections '+u)
    if plotType=='PBuff':
        plt.plot(xAx[u],yAx[u],label='Packets in Buffer '+u)
    if plotType=='Metric':
        plt.plot(xAx[u],yAx[u],label='Metric '+u)
    plt.legend(loc='upper right')
    plt.xlabel('Time(ms)')
    plt.ylabel(plotName)

def makeIntraSlicePlot(plotName,plotType,xAx,yAx,slcLbl,bw,sch,gran):
    """This method makes and stores any Intra Slice plot"""
    plt.figure(figsize=(15,10))
    for ue in list(xAx.keys()):
        makeTimePlot(ue,plotName,plotType,xAx,yAx)
    ax = plt.gca()
    plt.autoscale()
    ax.xaxis.set_major_locator(MultipleLocator(gran*3))
    ax.grid(which='major', color='#CCCCCC', linestyle='--')
    ind = plotName.find('(')
    if ind != -1:
        fileName = plotName[0:ind]
    else:
        fileName = plotName
    plt.title(plotName+' | BAND='+str(bw)[1:len(str(bw))-1]+' MHz | '+str(len(list(xAx.keys())))+' UEs | '+slcLbl+' slice | '+str(sch)+' scheduler')
    plt.savefig('Figures/'+fileName+'|BW='+str(bw)+'|Slice='+slcLbl+'|IntraSliceSched='+str(sch))
    plt.close()

def makeInterSlicePlot(plotName,plotType,xAx,yAx,bw,sch,gran):
    """This method makes and stores any Inter Slice plot"""
    plt.figure(figsize=(15,10))
    maxusePRB = []
    for slice in list(xAx.keys()):
        makeTimePlot(slice,plotName,plotType,xAx,yAx)
        if plotType=='sliceResUse':
            maxusePRB = maxusePRB + yAx[slice]
    ax = plt.gca()
    plt.autoscale()
    ax.xaxis.set_major_locator(MultipleLocator(gran))
    if plotType=='sliceResUse':
        ax.yaxis.set_minor_locator(MultipleLocator(1))
        ax.yaxis.set_major_locator(MultipleLocator(5))
        plt.yticks(list(set(maxusePRB)))
    ax.grid(which='major',color='#CCCCCC', linestyle='--')
    ax.grid(which='minor',color='#CCCCCC', linestyle=':')
    ind = plotName.find('(')
    if ind != -1:
        fileName = plotName[0:ind]
    else:
        fileName = plotName
    plt.title(plotName+' | BW='+str(bw)[1:len(str(bw))-1]+' MHz | '+str(len(list(xAx.keys())))+' Slices | '+str(sch)+' scheduler')
    plt.savefig('Figures/'+fileName+'|BW='+str(bw)+'|InterSliceSched='+str(sch))
    plt.close()

def makePlotsIntra(dir,times,sinr,mcs,rU,plr,th,slcLbl,bw,sch,gr):
    """This method makes all Intra Slice kpi plots"""
    # Plot results ---------------------------------------------------------
    if not os.path.exists('Figures'):
        os.mkdir('Figures')
    makeIntraSlicePlot('PLR-'+dir,'PLR'               ,times,plr ,slcLbl,bw,sch,gr)
    makeIntraSlicePlot('TH-'+dir+' (Mbps)','TH'       ,times,th  ,slcLbl,bw,sch,gr)
    makeIntraSlicePlot('ResUse-'+dir+' (%)','UEresUse',times,rU  ,slcLbl,bw,sch,gr)
    makeIntraSlicePlot('SINR-'+dir,'SINR'             ,times,sinr,slcLbl,bw,sch,gr)
    makeIntraSlicePlot('MCS-'+dir,'MCS'               ,times,mcs ,slcLbl,bw,sch,gr)

def makePlotsInter(dir,times,res,plr,th,cnx,buf,met,bw,schIn,gr):
    """This method makes all Inter Slice kpi plots"""
    # Plot results ---------------------------------------------------------
    if not os.path.exists('Figures'):
        os.mkdir('Figures')
    # makeInterSlicePlot('PLR-'+dir,'PLR'                 ,times,plr,bw,schIn,gr)
    makeInterSlicePlot('TH-'+dir+' (Mbps)','TH'         ,times,th ,bw,schIn,gr)
    makeInterSlicePlot('ResUse-'+dir,'sliceResUse'      ,times,res,bw,schIn,gr)
    makeInterSlicePlot('Connections-'+dir,'Connections' ,times,cnx,bw,schIn,gr)
    makeInterSlicePlot('Packets in Buffer-'+dir,'PBuff' ,times,buf,bw,schIn,gr)
    makeInterSlicePlot('Metric-'+dir,'Metric'           ,times,met,bw,schIn,gr)
