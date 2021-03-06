#!/usr/bin/python2.6

#Copyright (C) 2012  Jonathan Delvaux <jonathan.delvaux@uclouvain.be>

#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#any later version.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.

#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>.


from exception import argException,argExecutionException
from tries.exception import triesException
from tries.multiLevelTries import multiLevelTries
from command import *

import readline
import os
import sys
import traceback

histfile = os.path.join(os.path.expanduser("~"), ".rfidShell")
try:
    readline.read_history_file(histfile)
except IOError:
    pass

import atexit
atexit.register(readline.write_history_file, histfile)
del os, histfile      

class MultiOutput(list):
    pass

class InputManager(object):
    def __init__(self,processCount = 1):
        self.inputList = []
        self.processCount = processCount
        self.work = 0
        for i in range(0,(processCount*2)+1):
            self.inputList.append([])
    
    def hasStillWorkToDo(self):
        return self.work != 0
    
    ### GENERIC ###
    def hasInput(self,indice):
        return len(self.inputList[indice]) > 0
        
    def getNextInput(self,indice):
        self.work -=1
        ret = self.inputList[indice][0]
        self.inputList[indice] = self.inputList[indice][1:]
        return ret
    
    def addOutput(self,indice,output):
        #manage multioutput
        if isinstance(output,MultiOutput):
            for o in output:
                self.inputList[indice].append(o)
                self.work +=1
        else:
            self.inputList[indice].append(output)
            self.work +=1
    
    ### PRE ###
    def getNextPreProcess(self):
        for i in range(0,self.processCount):
            if len(self.inputList[i]) != 0:
                return i

        return -1
        
    def hasPreProcessInput(self,indice):
        return self.hasInput(indice)
    
    def getNextPreProcessInput(self,indice):
        return self.getNextInput(indice)
        
    def addOutputToNextPreProcess(self,indice,output):
        self.addOutput(indice+1,output)
        
    def getPreProcessInputBuffer(self,indice):
        return self.inputList[indice]
    
    ### PROCESS ###
    def hasProcessInput(self):
        return self.hasInput(self.processCount)
    
    def getNextProcessInput(self):
        return self.getNextInput(self.processCount)
        
    def addProcessOutput(self,output):
        self.addOutput(self.processCount+1,output)
    
    def getProcessInputBuffer(self):
        return self.inputList[self.processCount+1]
    
    ### POST ###
    def getNextPostProcess(self):
        for i in range(0,self.processCount):
            if len(self.inputList[i + self.processCount + 1]) != 0:
                return i

        return -1

    def hasPostProcessInput(self,indice):
        return self.hasInput(self.processCount+1+indice)
        
    def getNextPostProcessInput(self,indice):
        return self.getNextInput(self.processCount+1+indice)
        
    def addOutputToNextPostProcess(self,indice,output):
        if (self.processCount+1+indice+1) < len(self.inputList):
            self.addOutput(self.processCount+1+indice+1,output)
    
    def getPostProcessInputBuffer(self,indice):
        return self.inputList[self.processCount+1+indice]
    
    def __str__(self):
        return str(self.inputList)

class CommandExecuter():
    def __init__(self):
        self.envi = {}
        self.envi["prompt"] = ":>"
        self.levelTries = multiLevelTries()
        self.envi["levelTries"] = self.levelTries
        
        #def __init__(self,name,helpMessage,envi,preProcess=None,process=None,argChecker=None,postProcess=None,showInHelp=True):
    def addCommand(self,CommandStrings,preProcess=None,process=None,argChecker=None,postProcess=None,showInHelp=True):
        name = ""
        for s in CommandStrings:
            name += s+" "
        
        c = UniCommand(name,preProcess.__doc__,preProcess,process,argChecker,postProcess,showInHelp)
        
        try:
            self.levelTries.addEntry(CommandStrings,c)
            return c
        except triesException as e:
            print self.printOnShell(str(e))
            return None
            
    def addMultiCommand(self,CommandStrings,helpMessage,showInHelp=True):
        name = ""
        for s in CommandStrings:
            name += s+" "
            
        c = MultiCommand(name,helpMessage,showInHelp)
        
        try:
            self.levelTries.addEntry(CommandStrings,c)
            return c
        except triesException as e:
            print self.printOnShell(str(e))
            return None
            
    def addAlias(self,CommandStrings,AliasCommandStrings):
        #pas aussi simple
            #on doit pouvoir gerer des alias avec des arguments fixe
        
        pass #TODO
    
    #
    #
    # @return, true if no severe error or correct process, false if severe error
    #
    def executeCommand(self,cmd):
        #command string split and parse with "|" and " "
        cmd = cmd.split("|")
        if len(cmd) < 0 :
            print "   split command error"
            return False
        
        CommandStringsList = []    
        for inner in cmd:
            inner = inner.strip(' \t\n\r')
            if len(inner) > 0:
                inner = inner.split(" ")
                if len(inner) < 0 :
                    print "   split command error"
                    CommandStringsList = []
                    break
                
                finalCmd = []
                for cmd in inner:
                    cmd = cmd.strip(' \t\n\r')
                    if len(cmd) > 0 :
                        finalCmd.append(cmd)
                    
                if len(finalCmd) > 0:
                    CommandStringsList.append(finalCmd)
                    #TODO faire la recherche des commandes ici (?)
        
        if len(CommandStringsList) < 1:
            return False
        
        #look after all the command into the tries
        rawCommandList = []
        for CommandStrings in CommandStringsList:
            #look after the command
            try:
                triesNode,args = self.levelTries.searchEntryFromMultiplePrefix(CommandStrings) #args est une liste
                rawCommandList.append((triesNode.value,args))
            except triesException as e:
                self.printOnShell(str(e))
                return True
        
        #manage and prepare the multicommand
        commandList = []
        MultiCommandList = [commandList]
        for rawCommand,args in rawCommandList:
            if isinstance(rawCommand,UniCommand):
                for commandList in MultiCommandList:
                    commandList.append((rawCommand,args))
                    
            elif isinstance(rawCommand,list):#on doit tout duppliquer
                
                newMultiCommandList = []
                for commandList in MultiCommandList:
                    for c in rawCommand:
                        tmp = list(commandList)
                        tmp.append((c,args))
                        newMultiCommandList.append(tmp)
                MultiCommandList = newMultiCommandList
                
            else:
                self.printOnShell("ERROR : a non command is into the tries : "+str(type(rawCommand)))
                return False 
        
        ### EXECUTION ###
        for commandList in MultiCommandList: #Multicommand
            inputManager = InputManager(len(commandList))
            
            #set the buffer to the command
            for i in range(0,len(commandList)-1):
                c,a = commandList[i]
                c.setBuffer(inputManager.getPreProcessInputBuffer(i),None,inputManager.getPostProcessInputBuffer(i))
            
            c,a = commandList[-1]
            c.setBuffer(inputManager.getPreProcessInputBuffer(len(commandList)-1),inputManager.getProcessInputBuffer(),inputManager.getPostProcessInputBuffer(len(commandList)-1))
            
            #set the starting point
            inputManager.addOutput(0,None)
            #print "init : "+str(inputManager)
            
            indice = 0
            while inputManager.hasStillWorkToDo(): #the buffer are not empty
                try: #critical section
                    ### PREPROCESS ###
                    for indice in range(inputManager.getNextPreProcess(),len(commandList)):
                        if inputManager.hasPreProcessInput(indice):
                            commandToExecute,args = commandList[indice]
                        
                            args_tmp = list(args)
                            #append the previous value to the args
                            commandInput = inputManager.getNextPreProcessInput(indice)
                            if commandInput != None:
                                if isinstance(commandInput,list):
                                    for item in commandInput:
                                        args_tmp.append(item)
                                else:
                                    args_tmp.append(commandInput)

                            inputManager.addOutputToNextPreProcess(indice,commandToExecute.preProcessExecution(args_tmp,self,self.envi) )
                            #print "pre "+str(indice)+" : "+str(inputManager)

                    ### PROCESS ###
                    indice = len(commandList)-1
                    if inputManager.hasProcessInput():
                        command,args = commandList[len(commandList)-1]
                        inputManager.addProcessOutput(command.ProcessExecution(inputManager.getNextProcessInput(),self,self.envi))
                        #print "pro : "+str(inputManager)

                    ### POSTPROCESS ###
                    for indice in range(inputManager.getNextPostProcess(),len(commandList)):
                        if inputManager.hasPostProcessInput(indice):
                            command,args = commandList[len(commandList)-1-indice]
                            inputManager.addOutputToNextPostProcess(indice,command.postProcessExecution(inputManager.getNextPostProcessInput(indice),self,self.envi))

                            #print "post "+str(indice)+" : "+str(inputManager)
                except argExecutionException as aee:
                    c,a = commandList[indice]
                    
                    self.printOnShell(""+str(aee)+" at "+c.name)
                    return True
                except argException as aee:
                    c,a = commandList[indice]
                    self.printOnShell(str(aee)+" at "+c.name)
                    self.printOnShell("USAGE : "+c.name+" "+aee.usage)
                    return True
                except argPostExecutionException as aee:
                    c,a = commandList[indice]
                    self.printOnShell(""+str(aee)+" at "+c.name)
                    return True
                except Exception as ex:
                    c,a = commandList[indice]
                    self.printOnShell("SEVERE : "+str(ex)+" at "+c.name)
                    traceback.print_exc() #TODO remove after debug
                    return False
                
        return True
        
    def mainLoop(self):
        while True:
            #readline.parse_and_bind("tab: complete")
            if(sys.platform == 'darwin'):
                import rlcompleter
                readline.parse_and_bind ("bind ^I rl_complete")
            else:
                readline.parse_and_bind("tab: complete")
            
            readline.set_completer(Executer.complete)
            
            try:
                cmd = raw_input(self.envi["prompt"])
            except SyntaxError:
                print "   syntax error"
                continue
            except EOFError:
                print "\n   end of stream"
                break
                
            self.executeCommand(cmd)        
    
    ###############################################################################################
    ##### Readline REPL ###########################################################################
    ###############################################################################################
    def printAsynchronousOnShell(self,EventToPrint):
        print ""
        print "   "+EventToPrint

        #this is needed because after an input, the readline buffer isn't always empty
        if len(readline.get_line_buffer()) == 0 or readline.get_line_buffer()[-1] == '\n':
            sys.stdout.write(self.envi["prompt"])
        else:
            sys.stdout.write(self.envi["prompt"] + readline.get_line_buffer())

        sys.stdout.flush()
    
    #TODO convert into write function from output
    def printOnShell(self,toPrint):
        print "   "+str(toPrint)
        
    def complete(self,prefix,index):
        #TODO pas encore au point
        
        args = prefix.split(" ")
        if len(args) < 0 :
            print "   split command error"
            return None
        StartNode = None
        if len(args) > 0:
            try:
                #TODO, la methode searchEntryFromMultiplePrefix ne semble pas adaptee pour ici
                
                StartNode,args = self.envi["levelTries"].searchEntryFromMultiplePrefix(args,True)
                print StartNode.getCompleteName()
            except triesException as e:
                print "   "+str(e)
                return None
        if StartNode == None:
            StartNode = envi["levelTries"].levelOneTries
    
        key = StartNode.getAllPossibilities().keys()
        #print key
        try:
            return key[index]
        except IndexError:
            return None
    def executeFile(self,filename):
        f = open(filename, "r")
        exitOnEnd = True
        for line in f:
            print self.envi["prompt"]+line.strip('\n\r')
            if line.startswith("noexit"):
                exitOnEnd = False
            elif not self.executeCommand(line):
                break
                
        return exitOnEnd

###############################################################################################
##### anything   ##############################################################################
###############################################################################################
                
Executer = CommandExecuter()

