#!/usr/bin/python2.6
from arg.args import *
from apdu.apduExecuter import Executer
from apdu.apdu import ApduDefault

class iso7816_4APDUBuilder(object):

    def getDataCA(self,P1,P2):
        return ApduDefault(cla=0xFF,ins=0xCA,p1=P1,p2=P2)
        
    def getDataCB(self,P1,P2,Data):
        return ApduDefault(cla=0xFF,ins=0xCA,p1=P1,p2=P2, data=Data)
