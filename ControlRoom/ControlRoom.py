
"""
MIT License
Copyright (c) 2022 Yihao Liu, Johns Hopkins University
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import logging
import os
import json
import random, qt, time
from ControlRoomLib.UtilConnections import UtilConnections
from ControlRoomLib.UtilSlicerFuncs import setTranslation
from datetime import datetime, timedelta
from ControlRoomLib.UtilConnectionsWtNnBlcRcv import UtilConnectionsWtNnBlcRcv

import vtk

import slicer
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin


#
# ControlRoom
#

class ControlRoom(ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "Control Room"  # TODO: make this more human readable by adding spaces
        self.parent.categories = ["AkTrack"]  # TODO: set categories (folders where the module shows up in the module selector)
        self.parent.dependencies = []  # TODO: add here list of module names that this module requires
        self.parent.contributors = ["Yihao Liu (Johns Hopkins University)"]  # TODO: replace with "Firstname Lastname (Organization)"
        # TODO: update with short description of the module and a link to online module documentation
        self.parent.helpText = """
This is an example of scripted loadable module bundled in an extension.
See more information in <a href="https://github.com/organization/projectname#ControlRoom">module documentation</a>.
"""
        # TODO: replace with organization, grant and thanks
        self.parent.acknowledgementText = """
This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc., Andras Lasso, PerkLab,
and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
"""

#
# ControlRoomWidget
#

class ControlRoomWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
    """Uses ScriptedLoadableModuleWidget base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent=None):
        """
        Called when the user opens the module the first time and the widget is initialized.
        """
        ScriptedLoadableModuleWidget.__init__(self, parent)
        VTKObservationMixin.__init__(self)  # needed for parameter node observation
        self.logic = None
        self._parameterNode = None
        self._updatingGUIFromParameterNode = False

    def setup(self):
        """
        Called when the user opens the module the first time and the widget is initialized.
        """
        ScriptedLoadableModuleWidget.setup(self)

        # Load widget from .ui file (created by Qt Designer).
        # Additional widgets can be instantiated manually and added to self.layout.
        uiWidget = slicer.util.loadUI(self.resourcePath('UI/ControlRoom.ui'))
        self.layout.addWidget(uiWidget)
        self.ui = slicer.util.childWidgetVariables(uiWidget)

        # Set scene in MRML widgets. Make sure that in Qt designer the top-level qMRMLWidget's
        # "mrmlSceneChanged(vtkMRMLScene*)" signal in is connected to each MRML widget's.
        # "setMRMLScene(vtkMRMLScene*)" slot.
        uiWidget.setMRMLScene(slicer.mrmlScene)

        # Create logic class. Logic implements all computations that should be possible to run
        # in batch mode, without a graphical user interface.
        self.logic = ControlRoomLogic(self.resourcePath('Configs/'))
        self.logic.ui = self.ui

        # Connections

        # These connections ensure that we update parameter node when scene is closed
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.StartCloseEvent, self.onSceneStartClose)
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.EndCloseEvent, self.onSceneEndClose)

        # These connections ensure that whenever user changes some settings on the GUI, that is saved in the MRML scene
        # (in the selected parameter node).
        self.ui.comboSubjectAcr.connect("currentIndexChanged(int)", self.onComboSubjectAcr)
        self.ui.comboExpTime.connect("currentIndexChanged(int)", self.onComboExpTime)
        self.ui.comboTargetTrial.connect("currentIndexChanged(int)", self.onComboTargetTrial)

        # Buttons
        self.ui.pushAddSubj.connect('clicked(bool)', self.onPushAddSubj)
        self.ui.pushStartAnExp.connect('clicked(bool)', self.onPushStartAnExp)
        self.ui.pushRandSeq.connect('clicked(bool)', self.onPushRandSeq)
        self.ui.pushRetrieveSeq.connect('clicked(bool)', self.onPushRetrieveSeq)
        self.ui.pushApplySeq.connect('clicked(bool)', self.onPushApplySeq)
        self.ui.pushStartVis.connect('clicked(bool)', self.onPushStartVis)
        self.ui.pushStopVis.connect('clicked(bool)', self.onPushStopVis)
        self.ui.pushPrevTrial.connect('clicked(bool)', self.onPushPrevTrial)
        self.ui.pushStopCurTrial.connect('clicked(bool)', self.onPushStopCurTrial)
        self.ui.pushCurTrial.connect('clicked(bool)', self.onPushCurTrial)
        self.ui.pushTargetTrial.connect('clicked(bool)', self.onPushTargetTrial)

        self.ui.pushConnect.connect('clicked(bool)', self.onPushConnect)

        # Text
        self.ui.textTimer.setPlainText("Trial Duration Timer: 00:00:00.000000") 
        self.ui.textIPPort.connect('textChanged()', self.onTextIPPort)
        self.ui.textSessionSeq.connect('textChanged()', self.onTextSessionSeq)

        # Make sure parameter node is initialized (needed for module reload)
        self.initializeParameterNode()

        for i in self.logic._subjectAcrList:
            self.ui.comboSubjectAcr.addItem(i)

    def cleanup(self):
        """
        Called when the application closes and the module widget is destroyed.
        """
        self.removeObservers()
        if self.logic._connections_screendot:
            self.logic._connections_screendot.clear()
        if self.logic._connections_tracker:
            self.logic._connections_tracker.clear()
        if self.logic._connections_goggle:
            self.logic._connections_goggle.clear()

    def enter(self):
        """
        Called each time the user opens this module.
        """
        # Make sure parameter node exists and observed
        self.initializeParameterNode()

    def exit(self):
        """
        Called each time the user opens a different module.
        """
        # Do not react to parameter node changes (GUI wlil be updated when the user enters into the module)
        self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)

    def onSceneStartClose(self, caller, event):
        """
        Called just before the scene is closed.
        """
        # Parameter node will be reset, do not use it anymore
        self.setParameterNode(None)

    def onSceneEndClose(self, caller, event):
        """
        Called just after the scene is closed.
        """
        # If this module is shown while the scene is closed then recreate a new parameter node immediately
        if self.parent.isEntered:
            self.initializeParameterNode()

    def initializeParameterNode(self):
        """
        Ensure parameter node exists and observed.
        """
        # Parameter node stores all user choices in parameter values, node selections, etc.
        # so that when the scene is saved and reloaded, these settings are restored.

        self.setParameterNode(self.logic.getParameterNode())
        self.ui.textIPPort.setPlainText(self._parameterNode.GetParameter("TerminalIPPort")) 

    def setParameterNode(self, inputParameterNode):
        """
        Set and observe parameter node.
        Observation is needed because when the parameter node is changed then the GUI must be updated immediately.
        """

        if inputParameterNode:
            self.logic.setDefaultParameters(inputParameterNode)

        # Unobserve previously selected parameter node and add an observer to the newly selected.
        # Changes of parameter node are observed so that whenever parameters are changed by a script or any other module
        # those are reflected immediately in the GUI.
        if self._parameterNode is not None:
            self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)
        self._parameterNode = inputParameterNode
        if self._parameterNode is not None:
            self.addObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)

        # Initial GUI update
        self.updateGUIFromParameterNode()

    def updateGUIFromParameterNode(self, caller=None, event=None):
        """
        This method is called whenever parameter node is changed.
        The module GUI is updated to show the current state of the parameter node.
        """
        
        if self._parameterNode is None or self._updatingGUIFromParameterNode:
            return

        # Make sure GUI changes do not call updateParameterNodeFromGUI (it could cause infinite loop)
        self._updatingGUIFromParameterNode = True
        
        # Update buttons states and tooltips

        self.ui.pushRetrieveSeq.toolTip = "Click to retrieve currently applied sequence"

        if self._parameterNode.GetParameter("SessionSeqTempDisplay") == \
            self._parameterNode.GetParameter("SessionSeq"):
                self.ui.pushApplySeq.enabled = False
                self.ui.pushApplySeq.toolTip = "No changes made"
        else:
            self.ui.pushApplySeq.enabled = True
            self.ui.pushApplySeq.toolTip = "Click to set sequence"

        if not self._parameterNode.GetParameter("SessionSeqTempDisplay"):
            self.ui.pushApplySeq.enabled = False
            self.ui.pushApplySeq.toolTip = "Session Sequence is not set"

        if not self._parameterNode.GetParameter("SessionSeq"):
            self.ui.comboTargetTrial.enabled = False
            self.ui.comboTargetTrial.toolTip = "Session Sequence is not set"
        else:
            self.ui.comboTargetTrial.enabled = True
            self.ui.comboTargetTrial.toolTip = "pick a trial"

        if self._parameterNode.GetParameter("Visualization") == "true":
            self.ui.pushStartVis.enabled = False
            self.ui.pushStartVis.toolTip = "Visualization is enabled"
            self.ui.pushStopVis.enabled = True
            self.ui.pushStopVis.toolTip = "Click to stop visualization"
        else:
            self.ui.pushStartVis.enabled = True
            self.ui.pushStartVis.toolTip = "Click to start visualization"
            self.ui.pushStopVis.enabled = False
            self.ui.pushStopVis.toolTip = "Visualization not started"

        if self._parameterNode.GetParameter("RunningATrial") == "true":
            self.ui.pushPrevTrial.enabled = False
            self.ui.pushPrevTrial.toolTip = "Running"
            self.ui.pushStopCurTrial.enabled = True
            self.ui.pushStopCurTrial.toolTip = "Click to stop current trial"
            self.ui.pushCurTrial.enabled = False
            self.ui.pushCurTrial.toolTip = "Running"
            self.ui.pushTargetTrial.enabled = False
            self.ui.pushTargetTrial.toolTip = "Running"
        else:
            self.ui.pushPrevTrial.enabled = True
            self.ui.pushPrevTrial.toolTip = "Click to do previous trial"
            self.ui.pushStopCurTrial.enabled = False
            self.ui.pushStopCurTrial.toolTip = "Not running"
            self.ui.pushCurTrial.enabled = True
            self.ui.pushCurTrial.toolTip = "Do current trial"
            if self._parameterNode.GetParameter("TargetTrial"):
                self.ui.pushTargetTrial.enabled = True
                self.ui.pushTargetTrial.toolTip = "Click to perform target trial"
            else:
                self.ui.pushTargetTrial.enabled = False
                self.ui.pushTargetTrial.toolTip = "Pick a target trial first"
            if not self._parameterNode.GetParameter("CurTrial"):
                self.ui.pushCurTrial.enabled = False
                self.ui.pushCurTrial.toolTip = "Current trial not set"
            else:
                self.ui.pushCurTrial.enabled = True
                self.ui.pushCurTrial.toolTip = "Click to run current trial"
            if not self._parameterNode.GetParameter("PrevTrial"):
                self.ui.pushPrevTrial.enabled = False
                self.ui.pushPrevTrial.toolTip = "Previous trial not set"
            else:
                self.ui.pushPrevTrial.enabled = True
                self.ui.pushPrevTrial.toolTip = "Click to run previous trial"

        if self._parameterNode.GetParameter("CurTrial"):
            self.ui.textCurTrial.setPlainText(self._parameterNode.GetParameter("CurTrial"))
        
        if self._parameterNode.GetParameter("PrevTrial"):
            self.ui.textPrevTrial.setPlainText(self._parameterNode.GetParameter("PrevTrial"))
            
        # All the GUI updates are done
        self._updatingGUIFromParameterNode = False

    def updateParameterNodeFromGUI(self, caller=None, event=None):
        """
        This method is called when the user makes any change in the GUI.
        The changes are saved into the parameter node (so that they are restored when the scene is saved and loaded).
        """
        if self._parameterNode is None or self._updatingGUIFromParameterNode:
            return
        wasModified = self._parameterNode.StartModify()  # Modify all properties in a single batch
        self._parameterNode.SetParameter("SubjectAcr", self.ui.comboSubjectAcr.currentText)
        self._parameterNode.SetParameter("ExperimentTimeStamp", self.ui.comboExpTime.currentText) 
        self._parameterNode.SetParameter("TargetTrial", self.ui.comboTargetTrial.currentText)
        self._parameterNode.EndModify(wasModified)

    def onTextIPPort(self):
        self._parameterNode.SetParameter("TerminalIPPort", self.ui.textIPPort.plainText)

    def onPushConnect(self):
        self.logic.processConnectTerminal()

    def onPushAddSubj(self):
        self.ui.comboSubjectAcr.clear()
        acr = self.ui.textAddSubj.text
        self.logic.processAddSubject(acr)
        for i in self.logic._subjectAcrList:
            self.ui.comboSubjectAcr.addItem(i)
        self.ui.comboSubjectAcr.setCurrentIndex(self.ui.comboSubjectAcr.count-1)

    def onComboSubjectAcr(self, i=None):
        self._parameterNode.SetParameter("SubjectAcr", self.ui.comboSubjectAcr.currentText) 
        self.ui.comboExpTime.clear()
        if self._parameterNode.GetParameter("SubjectAcr"):
            subj = self.logic._subjectConfig[self._parameterNode.GetParameter("SubjectAcr").split("_")[1]]
            exparr = subj["experiments"]
            for e in exparr:
                self.ui.comboExpTime.addItem(e["datetime"])

    def onComboExpTime(self,i=None):
        self._parameterNode.SetParameter("ExperimentTimeStamp", self.ui.comboExpTime.currentText) 
        if self._parameterNode.GetParameter("SubjectAcr"):
            subj = self.logic._subjectConfig[self._parameterNode.GetParameter("SubjectAcr").split("_")[1]]
            exparr = subj["experiments"]
            self.onPushRetrieveSeq()
            self.ui.comboTargetTrial.clear()
            for e in exparr:
                if e["datetime"] == self.ui.comboExpTime.currentText:
                    for ee in e["sequence"]:
                        self.ui.comboTargetTrial.addItem(ee)

    def onPushStartAnExp(self):
        timestamp = datetime.now().strftime("%m%d%Y%H%M%S")
        self.logic.processStartAnExp(timestamp)
        self._parameterNode.SetParameter("ExperimentTimeStamp", timestamp)
        self.onComboSubjectAcr()
        self.ui.comboExpTime.setCurrentIndex(self.ui.comboExpTime.count-1)

    def onPushRandSeq(self):
        # see orders.png for more information

        res = self.logic.processRandSeq()
        res[0].extend(res[1])
        res[0].extend(res[2])
        res = res[0]
        
        sessionSeqTempDisplay = ""
        for i in res:
            sessionSeqTempDisplay = sessionSeqTempDisplay + i + "\n"

        self._parameterNode.SetParameter("SessionSeqTempDisplay", sessionSeqTempDisplay)
        self.ui.textSessionSeq.setPlainText(self._parameterNode.GetParameter("SessionSeqTempDisplay")) 
        
    def onTextSessionSeq(self):
        self._parameterNode.SetParameter("SessionSeqTempDisplay", self.ui.textSessionSeq.plainText)
    
    def onPushRetrieveSeq(self):
        subj = self.logic._subjectConfig[self._parameterNode.GetParameter("SubjectAcr").split("_")[1]]
        exparr = subj["experiments"]
        for e in exparr:
            if e["datetime"] == self.ui.comboExpTime.currentText:
                self.ui.textSessionSeq.setPlainText('\n'.join(e["sequence"])) 
                self._parameterNode.SetParameter("SessionSeq", self._parameterNode.GetParameter("SessionSeqTempDisplay"))

    def onPushApplySeq(self):
        text = self._parameterNode.GetParameter("SessionSeqTempDisplay")
        if self.logic.processSeqTextCheck(text):
            exp = self.logic.processApplySeq(text)
            if exp:
                self._parameterNode.SetParameter("SessionSeq", text)
                self.ui.comboTargetTrial.clear()
                for i in exp:
                    self.ui.comboTargetTrial.addItem(i)
        
    def onPushStartVis(self):

        if not self._parameterNode.GetNodeReference("TrackerIndicatorTr"):
            transformNode = slicer.vtkMRMLTransformNode()
            slicer.mrmlScene.AddNode(transformNode)
            self._parameterNode.SetNodeReferenceID(
                "TrackerIndicatorTr", transformNode.GetID())

        if not self._parameterNode.GetNodeReference("TrackerIndicator"):
            inputModel = slicer.util.loadModel(self.logic._configPath + "BoardModel.STL")
            inputModel = slicer.util.loadModel(self.logic._configPath + "TrackerIndicatorModel.STL")
            self._parameterNode.SetNodeReferenceID(
                "TrackerIndicator", inputModel.GetID())

        modelTransform = self._parameterNode.GetNodeReference("TrackerIndicatorTr")
        modelIndicator = self._parameterNode.GetNodeReference("TrackerIndicator")

        modelTransform.SetMatrixTransformToParent(self.logic._connections_tracker._transformMatrixTrackerIndicator)
        modelIndicator.SetAndObserveTransformNodeID(
            modelTransform.GetID())

        comm_out = "start_visualizat" + ";"
        self.logic._connections_tracker.utilSendCommand(comm_out)
        self._parameterNode.SetParameter("Visualization", "true")

    def onPushStopVis(self):
        comm_out = "stop_visualizati" + ";"
        self.logic._connections_tracker.utilSendCommand(comm_out)
        self._parameterNode.SetParameter("Visualization", "false")
        
    def onPushPrevTrial(self):
        
        if self._parameterNode.GetParameter("PrevTrial"):
            if self._parameterNode.GetParameter("PrevTrial") == "__NONE__":
                return
            else:
                # Notify aktrack-matlab module
                if self._parameterNode.GetParameter("PrevTrial") == "VPB-hfixed":
                    self.logic._connections_goggle.utilSendCommand('1')
                elif self._parameterNode.GetParameter("PrevTrial") == "VPB-hfree":
                    self.logic._connections_goggle.utilSendCommand('2')
                # Notify aktrack-ros module
                comm_out = "start_trialxxxxx" + "_" + \
                    self._parameterNode.GetParameter("ExperimentTimeStamp") + "_" + \
                    self._parameterNode.GetParameter("SubjectAcr").split("_")[1] + "_" + \
                    self._parameterNode.GetParameter("PrevTrial") + ";"
                self.logic._connections_tracker.utilSendCommand(comm_out)
                # Notify aktrack-screen module
                comm = {"commandtype":"trialcommand", \
                    "commandcontent":self._parameterNode.GetParameter("PrevTrial")}
                comm_out = json.dumps(comm)
                self.logic._connections_screendot.utilSendCommand(comm_out)
                self._parameterNode.SetParameter("RunningATrial", "true")
                # Update the "current trial" and "previous trial" identifiers
                sessionSeq = self._parameterNode.GetParameter("SessionSeq").strip().split("\n")
                sessionSeq = ["__NONE__"] + sessionSeq + ["__NONE__"]
                self._parameterNode.SetParameter("TrialIndex", \
                    str(int(self._parameterNode.GetParameter("TrialIndex"))-1))
                self._parameterNode.SetParameter("PrevTrial", \
                    sessionSeq[int(self._parameterNode.GetParameter("TrialIndex"))])
                self._parameterNode.SetParameter("CurTrial", \
                    sessionSeq[int(self._parameterNode.GetParameter("TrialIndex"))+1])
                # Set GUI timer
                self._timer_start = datetime.now()
                qt.QTimer.singleShot(329, self.AccuTimerCallBack)

    def onPushStopCurTrial(self):
        # Notify aktrack-screen module
        comm = {"commandtype":"trialstopcommand", \
            "commandcontent":""}
        comm_out = json.dumps(comm)
        self.logic._connections_screendot.utilSendCommand(comm_out)
        # Notify aktrack-ros module
        comm_out = "stop_trialxxxxxx" + ";"
        self.logic._connections_tracker.utilSendCommand(comm_out)
        # Notify aktrack-matlab module
        if self._parameterNode.GetParameter("CurTrial") == "VPB-hfixed":
            self.logic._connections_goggle.utilSendCommand('3')
        elif self._parameterNode.GetParameter("CurTrial") == "VPB-hfree":
            self.logic._connections_goggle.utilSendCommand('4')
        
    def onPushCurTrial(self):
        
        if self._parameterNode.GetParameter("CurTrial"):
            if self._parameterNode.GetParameter("CurTrial") == "__NONE__":
                return
            else:
                # Notify aktrack-matlab module
                if self._parameterNode.GetParameter("CurTrial") == "VPB-hfixed":
                    self.logic._connections_goggle.utilSendCommand('1')
                elif self._parameterNode.GetParameter("CurTrial") == "VPB-hfree":
                    self.logic._connections_goggle.utilSendCommand('2')
                # Notify aktrack-ros module
                comm_out = "start_trialxxxxx" + "_" + \
                    self._parameterNode.GetParameter("ExperimentTimeStamp") + "_" + \
                    self._parameterNode.GetParameter("SubjectAcr").split("_")[1] + "_" + \
                    self._parameterNode.GetParameter("CurTrial") + ";"
                self.logic._connections_tracker.utilSendCommand(comm_out)
                # Notify aktrack-screen module
                comm = {"commandtype":"trialcommand", \
                    "commandcontent":self._parameterNode.GetParameter("CurTrial")}
                comm_out = json.dumps(comm)
                self.logic._connections_screendot.utilSendCommand(comm_out)
                self._parameterNode.SetParameter("RunningATrial", "true")
                self._timer_start = datetime.now()
                qt.QTimer.singleShot(329, self.AccuTimerCallBack)

    def AccuTimerCallBack(self):
        if self._parameterNode.GetParameter("RunningATrial") == "true":
            duration = (datetime.now() - self._timer_start).total_seconds()
            self.ui.textTimer.setPlainText("Trial Duration Timer: "+str(timedelta(seconds=duration))) 
            qt.QTimer.singleShot(329, self.AccuTimerCallBack)
                
    def onComboTargetTrial(self, i=None):
        self._parameterNode.SetParameter("TargetTrial", self.ui.comboTargetTrial.currentText) 
    
    def onPushTargetTrial(self):
        # Check if the name is valid
        if self._parameterNode.GetParameter("TargetTrial"):
            # Notify aktrack-matlab module
            if self._parameterNode.GetParameter("TargetTrial") == "VPB-hfixed":
                self.logic._connections_goggle.utilSendCommand('1')
            elif self._parameterNode.GetParameter("TargetTrial") == "VPB-hfree":
                self.logic._connections_goggle.utilSendCommand('2')
            # Notify aktrack-ros module
            comm_out = "start_trialxxxxx" + "_" + \
                self._parameterNode.GetParameter("ExperimentTimeStamp") + "_" + \
                self._parameterNode.GetParameter("SubjectAcr").split("_")[1] + "_" + \
                self._parameterNode.GetParameter("TargetTrial") + ";"
            self.logic._connections_tracker.utilSendCommand(comm_out)
            # Notify aktrack-screen module
            # Send trial info to screen dot application
            comm = {"commandtype":"trialcommand", \
                "commandcontent":self._parameterNode.GetParameter("TargetTrial")}
            comm_out = json.dumps(comm)
            self.logic._connections_screendot.utilSendCommand(comm_out)
            # Set the running flag
            self._parameterNode.SetParameter("RunningATrial", "true")
            # Update the "current trial" and "previous trial" identifiers
            sessionSeq = self._parameterNode.GetParameter("SessionSeq").strip().split("\n")
            sessionSeq = ["__NONE__"] + sessionSeq + ["__NONE__"]
            self._parameterNode.SetParameter("TrialIndex", \
                str(self.ui.comboTargetTrial.currentIndex))
            self._parameterNode.SetParameter("PrevTrial", \
                sessionSeq[int(self._parameterNode.GetParameter("TrialIndex"))])
            self._parameterNode.SetParameter("CurTrial", \
                sessionSeq[int(self._parameterNode.GetParameter("TrialIndex"))+1])
            # Set GUI timer
            self._timer_start = datetime.now()
            qt.QTimer.singleShot(329, self.AccuTimerCallBack)


#
# ControlRoomLogic
#

class ControlRoomLogic(ScriptedLoadableModuleLogic):
    """This class should implement all the actual
    computation done by your module.  The interface
    should be such that other python code can import
    this class and make use of the functionality without
    requiring an instance of the Widget.
    Uses ScriptedLoadableModuleLogic base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, configPath):
        """
        Called when the logic class is instantiated. Can be used for initializing member variables.
        """
        ScriptedLoadableModuleLogic.__init__(self)
        self._configPath = configPath
        self.initializeModule()
        self._connections_screendot = None
        self._connections_tracker = None
        self._connections_goggle = None

    def setDefaultParameters(self, parameterNode):
        """
        Initialize parameter node with default settings.
        """
        if not parameterNode.GetParameter("RunningATrial"):
            parameterNode.SetParameter("RunningATrial", "false")
        if not parameterNode.GetParameter("Visualization"):
            parameterNode.SetParameter("Visualization", "false")
        if not parameterNode.GetParameter("SubjectAcr"):
            parameterNode.SetParameter("SubjectAcr", self.ui.comboSubjectAcr.currentText)
        if not parameterNode.GetParameter("ExperimentTimeStamp"):
            parameterNode.SetParameter("ExperimentTimeStamp", self.ui.comboExpTime.currentText) 
        if not parameterNode.GetParameter("TargetTrial"):
            parameterNode.SetParameter("TargetTrial", self.ui.comboTargetTrial.currentText)
        if not parameterNode.GetParameter("TerminalIPPort"):
            parameterNode.SetParameter("TerminalIPPort", \
            "127.0.0.1:8753\n127.0.0.1:8769\n127.0.0.1:8757\n10.17.101.48:8057\n0.0.0.0:8059\n0.0.0.0:8083\n127.0.0.1:8297\n127.0.0.1:8293")
        if not parameterNode.GetParameter("CurTrial"):
            parameterNode.SetParameter("CurTrial", "__NONE__")
        if not parameterNode.GetParameter("PrevTrial"):
            parameterNode.SetParameter("PrevTrial", "__NONE__")

    def processConnectTerminal(self):

        terminalIPPort = self._parameterNode.GetParameter("TerminalIPPort")
        ipPortArr = terminalIPPort.strip().split("\n")
        packetInterval = 8 # wait time of the singleShot function (msec)

        # Screen dot connections
        sock_ip_receive_nnblc, sock_port_receive_nnblc = \
            ipPortArr[2].split(":")[0], int(ipPortArr[2].split(":")[1])
        sock_ip_receive, sock_port_receive = \
            ipPortArr[1].split(":")[0], int(ipPortArr[1].split(":")[1])
        sock_ip_send, sock_port_send = \
            ipPortArr[0].split(":")[0], int(ipPortArr[0].split(":")[1])

        if not self._connections_screendot:
            self._connections_screendot = ControlRoomConnectionsScreenDot(sock_ip_receive_nnblc, sock_port_receive_nnblc, packetInterval, \
                sock_ip_receive, sock_port_receive, sock_ip_send, sock_port_send)
            self._connections_screendot.setup()
            self._connections_screendot._flag_receiving_nnblc = True
            self._connections_screendot.receiveTimerCallBack()
            self._connections_screendot._parameterNode = self._parameterNode

        # Tracker connections
        sock_ip_receive_nnblc, sock_port_receive_nnblc = \
            ipPortArr[5].split(":")[0], int(ipPortArr[5].split(":")[1])
        sock_ip_receive, sock_port_receive = \
            ipPortArr[4].split(":")[0], int(ipPortArr[4].split(":")[1])
        sock_ip_send, sock_port_send = \
            ipPortArr[3].split(":")[0], int(ipPortArr[3].split(":")[1])

        if not self._connections_tracker:
            self._connections_tracker = ControlRoomConnectionsTracker(sock_ip_receive_nnblc, sock_port_receive_nnblc, packetInterval, \
                sock_ip_receive, sock_port_receive, sock_ip_send, sock_port_send)
            self._connections_tracker.setup()
            self._connections_tracker._flag_receiving_nnblc = True
            self._connections_tracker.receiveTimerCallBack()
            self._connections_tracker._parameterNode = self._parameterNode

        self._connections_screendot._connections_tracker = self._connections_tracker

        # Goggle connections
        sock_ip_receive, sock_port_receive = \
            ipPortArr[7].split(":")[0], int(ipPortArr[7].split(":")[1])
        sock_ip_send, sock_port_send = \
            ipPortArr[6].split(":")[0], int(ipPortArr[6].split(":")[1])

        if not self._connections_goggle:
            self._connections_goggle = UtilConnections(sock_ip_receive, sock_port_receive, sock_ip_send, sock_port_send)
            self._connections_goggle.setup()
            self._connections_goggle._sock_receive.settimeout(2.5)

        self._connections_screendot._connections_goggle = self._connections_goggle
            
    def initializeModule(self):
        with open(self._configPath + "SubjectConfig.json") as f:
            self._subjectConfig = json.load(f)
        self._subjectAcrList = []
        self._subjectNumList = []
        for i in self._subjectConfig.keys():
            self._subjectAcrList.append(self._subjectConfig[i]["acronym"]+"_"+i) 
            self._subjectNumList.append(int(i))
        self._parameterNode = self.getParameterNode()
    
    def processAddSubject(self, acr):
        subjectNum = max(self._subjectNumList)+1
        self._subjectAcrList.append(acr + "_" + str(subjectNum))
        self._subjectNumList.append(subjectNum)
        newSubject = {str(subjectNum): {"acronym": acr, "experiments": []}}
        self._subjectConfig.update(newSubject)
        with open(self._configPath + "SubjectConfig.json", "w") as f:
            json.dump(self._subjectConfig, f, indent=4)

    def processStartAnExp(self, timestamp):
        subj = self._subjectConfig[self._parameterNode.GetParameter("SubjectAcr").split("_")[1]]
        exparr = subj["experiments"]
        exparr.append({"datetime": timestamp, "sequence": []})
        subj["experiments"] = exparr
        with open(self._configPath + "SubjectConfig.json", "w") as f:
            json.dump(self._subjectConfig, f, indent=4)
    
    def processRandSeq(self):
        vpb = ["VPB-hfree", "VPB-hfixed"]
        random.shuffle(vpb)

        vpc = ["VPC-L", "VPC-R", "VPC-U", "VPC-D"]
        vpc.extend(random.sample(set(vpc), 2))
        random.shuffle(vpc)

        vpm = ["VPM-2", "VPM-4", "VPM-6", "VPM-8", "VPM-12", "VPM-24"]
        random.shuffle(vpm)
        def randDir(sess):
            arr = [sess+"-L", sess+"-R", sess+"-U", sess+"-D"]
            arr.extend(random.sample(set(arr), 2))
            random.shuffle(arr)
            return arr
        tempvpm = []
        for i in range(len(vpm)):
            tempvpm.extend(randDir(vpm[i]))
        vpm = tempvpm
        
        res = [vpb, vpc, vpm]
        random.shuffle(res)
        return res

    def processSeqTextCheck(self, text):
        res = text.strip().split("\n")
        saved = ['VPM-2-L', 'VPM-2-U', 'VPM-2-R', 'VPM-2-D', \
            'VPM-4-L', 'VPM-4-U', 'VPM-4-R', 'VPM-4-D', \
            'VPM-12-U', 'VPM-12-R', 'VPM-12-L', 'VPM-12-D', \
            'VPM-6-U', 'VPM-6-L', 'VPM-6-D', 'VPM-6-R', \
            'VPM-24-U', 'VPM-24-R', 'VPM-24-D', 'VPM-24-L', \
            'VPM-8-D', 'VPM-8-L', 'VPM-8-R', 'VPM-8-U', \
            'VPC-U', 'VPC-D', 'VPC-R', 'VPC-L', \
            'VPB-hfixed', 'VPB-hfree']
        saved_poped = []
        if len(res) != len(saved) + 14:
            slicer.util.errorDisplay("The sequence does not pass! Number of trials is not valid")
            return
        while res:
            i = res.pop(0)
            if i not in saved and i not in saved_poped:
                slicer.util.errorDisplay("The sequence does not pass: A trial is not valid")
                return
            if i not in saved and i in saved_poped:
                saved_poped.remove(i)
            if i in saved and i not in saved_poped:
                saved.remove(i)
                saved_poped.append(i)
            if i in saved and i in saved_poped:
                slicer.util.errorDisplay("The sequence does not pass: A trial repeated 3 times")
                return
        if len(saved) != 0:
            slicer.util.errorDisplay("The sequence does not pass: A trial is not performed")
            return
        return True

    def processApplySeq(self, text):
        exp = text.strip().split("\n")
        subj = self._subjectConfig[self._parameterNode.GetParameter("SubjectAcr").split("_")[1]]
        exparr = subj["experiments"]
        for i in exparr:
            if self._parameterNode.GetParameter("ExperimentTimeStamp") == i["datetime"]:
                if slicer.util.confirmYesNoDisplay("Override the previous sequence?"):
                    i["sequence"] = exp
                    subj["experiments"] = exparr
                    with open(self._configPath + "SubjectConfig.json", "w") as f:
                        json.dump(self._subjectConfig, f, indent=4)
                    self._parameterNode.SetParameter("CurTrial", exp[0])
                    self._parameterNode.SetParameter("PrevTrial", "__NONE__")
                    self._parameterNode.SetParameter("TrialIndex", "0")
                    return exp
                else:
                    return None
        if not self._parameterNode.GetParameter("ExperimentTimeStamp"):
            return None
        self._parameterNode.SetParameter("CurTrial", exp[0])
        self._parameterNode.SetParameter("PrevTrial", "__NONE__")
        self._parameterNode.SetParameter("TrialIndex", "0")
        exparr.append({"datetime": self._parameterNode.GetParameter("ExperimentTimeStamp"), "sequence": exp})
        subj["experiments"] = exparr
        with open(self._configPath + "SubjectConfig.json", "w") as f:
            json.dump(self._subjectConfig, f, indent=4)
        
        return exp

class ControlRoomConnectionsScreenDot(UtilConnectionsWtNnBlcRcv):

    def __init__(self, sock_ip_receive_nnblc, sock_port_receive_nnblc, packetInterval, \
            sock_ip_receive, sock_port_receive, sock_ip_send, sock_port_send):
        super().__init__(sock_ip_receive_nnblc, sock_port_receive_nnblc, packetInterval, \
            sock_ip_receive, sock_port_receive, sock_ip_send, sock_port_send)

    def setup(self):
        super().setup()
        self._jsondata = None

    def handleReceivedData(self):
        """
        Override the parent class function
        """
        func = self.utilMsgParse()
        func()

    def utilMsgParse(self):
        """
        """
        data = self._data_buff.decode("UTF-8")
        self._jsondata = json.loads(data)
        if self._jsondata["commandtype"] == "test":
            return self.utilTestCallBack
        elif self._jsondata["commandtype"] == "trialStop":
            return self.utilTrialStopped

    def utilTestCallBack(self):
        """
        """
        print("test")

    def utilTrialStopped(self):
        print("Trial stopped")
        self._parameterNode.SetParameter("RunningATrial", "false")
        comm_out = "stop_trialxxxxxx" + ";"
        self._connections_tracker.utilSendCommand(comm_out)
        # Notify aktrack-matlab module
        if self._parameterNode.GetParameter("CurTrial") == "VPB-hfixed":
            self._connections_goggle.utilSendCommand('3')
        elif self._parameterNode.GetParameter("CurTrial") == "VPB-hfree":
            self._connections_goggle.utilSendCommand('4')

        msg = self._jsondata["commandcontent"]
        if msg == "trialcomplete":
            sessionSeq = self._parameterNode.GetParameter("SessionSeq").strip().split("\n")
            sessionSeq = ["__NONE__"] + sessionSeq + ["__NONE__"]
            self._parameterNode.SetParameter("TrialIndex", \
                str(int(self._parameterNode.GetParameter("TrialIndex"))+1))
            self._parameterNode.SetParameter("PrevTrial", \
                sessionSeq[int(self._parameterNode.GetParameter("TrialIndex"))])
            self._parameterNode.SetParameter("CurTrial", \
                sessionSeq[int(self._parameterNode.GetParameter("TrialIndex"))+1])
        elif msg == "trialstop":
            return

class ControlRoomConnectionsTracker(UtilConnectionsWtNnBlcRcv):

    def __init__(self, sock_ip_receive_nnblc, sock_port_receive_nnblc, packetInterval, \
            sock_ip_receive, sock_port_receive, sock_ip_send, sock_port_send):
        super().__init__(sock_ip_receive_nnblc, sock_port_receive_nnblc, packetInterval, \
            sock_ip_receive, sock_port_receive, sock_ip_send, sock_port_send)
        self._transformMatrixTrackerIndicator = None

    def setup(self):
        super().setup()
        self._jsondata = None
        if not self._transformMatrixTrackerIndicator:
            self._transformMatrixTrackerIndicator = vtk.vtkMatrix4x4()

    def handleReceivedData(self):
        """
        Override the parent class function
        """
        func = self.utilMsgParse()
        func()

    def utilMsgParse(self):
        """
        """
        data = self._data_buff.decode("UTF-8")
        if data.startswith("__msg_pose_"):
            msg = data[11:]
            num_str = msg.split("_")
            self._buffvispose = []
            for i in num_str:
                self._buffpose.append(float(i))
            return self.utilVisCallBack
        elif data == "test":
            return self.utilTestCallBack
        
    def utilVisCallBack(self):
        p = [self._buffvispose[0], self._buffvispose[1], 0]
        setTranslation(p, self._transformMatrixTrackerIndicator)
        self._parameterNode.GetNodeReference(
            "TrackerIndicatorTr").SetMatrixTransformToParent(self._transformMatrixTrackerIndicator)
        slicer.app.processEvents()

    def utilTestCallBack(self):
        """
        """
        print("test")