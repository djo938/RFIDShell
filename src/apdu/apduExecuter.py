#!/usr/bin/python2.6

from arg.args import CommandExecuter
from smartcard.sw.SWExceptions import CheckingErrorException,SWException
from smartcard.util import toHexString

class APDUExecuter(CommandExecuter):
    def executeAPDU(self,apdu):
        if "connection" not in self.envi or self.envi["connection"] == None:
            self.printOnShell("no connection available")
            
        try:
            data, sw1, sw2 = self.envi["connection"].transmit(apdu.toHexArray())
        except SWException as ex:
            self.printOnShell("%x %x : " % (ex.sw1, ex.sw2)+ex.message)
        except Exception as e:
            self.printOnShell(str(e))
        
    def executeAPDUAndConvertDataToString(self,apdu):
        if "connection" not in self.envi or self.envi["connection"] == None:
            self.printOnShell("no connection available")
            
        try:
            data, sw1, sw2 = self.envi["connection"].transmit(apdu.toHexArray())
            s = ""
            for c in data:
                s += chr(c)
            self.printOnShell("data = "+s)
        except SWException as ex:
            self.printOnShell("%x %x : " % (ex.sw1, ex.sw2)+ex.message)
        except Exception as e:
            self.printOnShell(str(e))
        
    def executeAPDUAndPrintData(self,apdu):
        if "connection" not in self.envi or self.envi["connection"] == None:
            self.printOnShell("no connection available")
            
        try:
            data, sw1, sw2 = self.envi["connection"].transmit(apdu.toHexArray())
            self.printOnShell(toHexString(data))
        except SWException as ex:
            self.printOnShell( "%x %x : " % (ex.sw1, ex.sw2)+ex.message)
        except Exception as e:
            self.printOnShell(str(e))
            
    def executeAPDUAndPrintDataAndSW(self,apdu):
        if "connection" not in self.envi or self.envi["connection"] == None:
            self.printOnShell("no connection available")
            
        try:
            data, sw1, sw2 = self.envi["connection"].transmit(apdu.toHexArray())
            self.printOnShell("%x %x : " % (sw1, sw2)+toHexString(data))
        except SWException as ex:
            self.printOnShell( "%x %x : " % (ex.sw1, ex.sw2)+ex.message)
        except Exception as e:
            self.printOnShell(str(e))

#def executeAPDU(con,apdu):
    #TODO

        
#def executeAPDUAndConvertDataToString(con,apdu):
    #TODO

#def executeAPDUAndPrintData(con,apdu):
    #TODO
    
Executer = APDUExecuter()
