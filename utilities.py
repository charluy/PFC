"""
    This module contains auxiliary functions and classes.
"""

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

