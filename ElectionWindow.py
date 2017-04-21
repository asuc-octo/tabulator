#############################################################
#                     ElectionWindow.py                     #
#             Created by: Alton Zheng & Yun Park            #
#                   Edited by; Lisa Lee                     #
#              Copyright Elections Council 2014             #
#############################################################

import wx
import wx.lib.scrolledpanel as scrolled
import wx.grid as gridlib

from Tabulator import *
from constants import *
from Race import *

import time
import thread, threading
from resignation import PositionRankings

class ElectionFrame(wx.Frame):
  
    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, title=title, size=(900, 680))
        
        self.InitUI()
        self.Centre()
        self.Show()
        
    def InitUI(self):
        # Create Status Bar
        self.CreateStatusBar()

        # Create Menu Bar
        menubar = wx.MenuBar()

        # File Menu
        filemenu = wx.Menu()

        loadb = filemenu.Append(wx.ID_ANY, "Load &Ballots", "Load ballots file")
        self.Bind(wx.EVT_MENU, self.LoadBallots, loadb)
        loadc = filemenu.Append(wx.ID_ANY, "Load &Candidates", "Load candidates file")
        self.Bind(wx.EVT_MENU, self.LoadCandidates, loadc)
        removebc = filemenu.Append(wx.ID_ANY, "Remove Candidates &Before", "Remove candidates from race before tabulation")
        self.Bind(wx.EVT_MENU, self.RemoveCandidatesBefore, removebc)
        removeac = filemenu.Append(wx.ID_ANY, "Remove Candidates &After", "Remove candidates from race after tabulation")
        self.Bind(wx.EVT_MENU, self.RemoveCandidatesAfter, removeac)
        quit = filemenu.Append(wx.ID_ANY, "E&xit", "Terminate the program")
        self.Bind(wx.EVT_MENU, self.OnQuit, quit)
        
        menubar.Append(filemenu, '&File')

        # Help Menu
        helpmenu = wx.Menu()
        about = helpmenu.Append(wx.ID_ANY, "&About", "Information about the program")
        self.Bind(wx.EVT_MENU, self.About, about)
        menubar.Append(helpmenu, '&Help')

        # Set Menu Bar
        self.SetMenuBar(menubar)

        # Variables
        self.ballotsLoaded = False      # Make sure ballots are loaded first before candidates
        self.candidatesLoaded = False   # Make sure candidates are loaded
        self.candidatesRemoved = False  # Check if any candidates have been withdrawn/disqualified
        self.speed = 0.0005             # Speed of tallying votes (seconds per tally)
        self.position = PRESIDENT       # Position of current race
        self.quota = 0                  # Quota of current race
        self.status = CONTINUE          # Status of current race
        self.toCompletion = False

        # Outside Panel
        self.backgroundPanel = wx.Panel(self)
        self.backgroundPanel.SetSizer(wx.BoxSizer(wx.VERTICAL))
        self.backgroundPanel.SetBackgroundColour((200,200,200))

        # Start an Election
        self.election = Election(self)

        # Initialize Candidates Panel (with no candidates since no file has been loaded)
        self.candidatesPanel = wx.Panel(self.backgroundPanel)
        self.candidatesPanel.SetBackgroundColour((220,220,220))
        self.backgroundPanel.GetSizer().Add(self.candidatesPanel, 1, wx.EXPAND | wx.ALL, 5)

        # Load information panel
        self.infoPanel = InfoPanel(self.backgroundPanel, self.quota)
        self.infoPanel.frame = self
        self.infoPanel.SetBackgroundColour((210,210,210))
        self.backgroundPanel.GetSizer().Add(self.infoPanel, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)

    def replaceRace(self):
        # Replace candidates panel with new
        self.candidatesPanel.Destroy()
        self.candidatesPanel = CandidatesPanel(self.backgroundPanel, self.election.candidates[self.position], self)
        self.candidatesPanel.SetBackgroundColour((220,220,220))
        self.backgroundPanel.GetSizer().Insert(0,self.candidatesPanel, 1, wx.EXPAND | wx.ALL, 3)
        self.backgroundPanel.Layout()

        # Reset the scores and ballots of candidates, start race, and update datasource
        self.election.resetRace()
        self.quota = self.election.startRace(self.position)
        self.candidatesPanel.datasource.update()
        self.candidatesPanel.datasource.quota = self.quota

        # Update the quota in info panel
        self.infoPanel.quota = self.quota
        self.infoPanel.resetQuotaLabel()
        self.infoPanel.Layout()

    def RemoveCandidatesBefore(self, evt):
        # Make sure ballots are loaded before candidates
        if not self.candidatesLoaded:
            error = wx.MessageDialog(None, 'Please Load Candidates First!', '', wx.OK | wx.ICON_EXCLAMATION)
            error.ShowModal()
            return
        candidates = self.election.candidates
        allCand = []
        for posList in candidates.values():
            for cand in posList:
                allCand.append(cand.name)
        candRemove = wx.MultiChoiceDialog(self, "Candidates", "Remove Candidates", allCand, wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER | wx.OK | wx.CANCEL | wx.CENTER)

        # If file was not selected
        if candRemove.ShowModal() == wx.ID_CANCEL:
            return
        try: 
            toRemove = []
            toRemoveNum = candRemove.GetSelections()
            for i in toRemoveNum:
                toRemove.append(allCand[i])
            self.election.remove += toRemove
        except:
            error = wx.MessageDialog(None, 'Something went wrong!', '', wx.OK | wx.ICON_EXCLAMATION)
            error.ShowModal()
            return
        loaded = wx.MessageDialog(None, 'Candidates Successfully Removed!', '', wx.OK | wx.ICON_EXCLAMATION)
        loaded.ShowModal()

    def RemoveCandidatesAfter(self, evt):
        if not self.election.finished:
            error = wx.MessageDialog(None, 'Please run the election first!', '', wx.OK | wx.ICON_EXCLAMATION)
            error.ShowModal()
            return

        # Make sure ballots are loaded before candidates
        if not self.candidatesLoaded:
            error = wx.MessageDialog(None, 'Please Load Candidates First!', '', wx.OK | wx.ICON_EXCLAMATION)
            error.ShowModal()
            return
        candidates = self.election.race.winner
        allCand = []
        for cand in candidates:
            allCand.append(cand.name)
        candRemove = wx.MultiChoiceDialog(self, "Candidates", "Remove Candidates", allCand, wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER | wx.OK | wx.CANCEL | wx.CENTER)

        # If file was not selected
        if candRemove.ShowModal() == wx.ID_CANCEL:
            return
        try: 
            toRemove = []
            toRemoveNum = candRemove.GetSelections()
            for i in toRemoveNum:
                toRemove.append(allCand[i])
            self.election.remove += toRemove
            if (self.election.race.position != SENATOR):
                self.election.race.execute_resignation_election_exec(self.election.race.position, toRemove)
            else:
                self.election.race.execute_resignation_election(toRemove)
        except:
            error = wx.MessageDialog(None, 'Something went wrong!', '', wx.OK | wx.ICON_EXCLAMATION)
            error.ShowModal()
            return
        loaded = wx.MessageDialog(None, 'Candidates Successfully Removed!', '', wx.OK | wx.ICON_EXCLAMATION)
        loaded.ShowModal()

    def LoadCandidates(self, evt):
        # Make sure ballots are loaded before candidates
        candFile = wx.FileDialog(self, "", "", "", "", wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)

        # If file was not selected
        if candFile.ShowModal() == wx.ID_CANCEL:
            return
        candFilePath = candFile.GetPath()
        try: 
            self.election.loadCandidatesFromTextFile(candFilePath)
        except:
            error = wx.MessageDialog(None, 'Incorrectly Formatted Candidates File!', '', wx.OK | wx.ICON_EXCLAMATION)
            error.ShowModal()
            return
        loaded = wx.MessageDialog(None, 'Candidates Successfully Loaded!', '', wx.OK | wx.ICON_EXCLAMATION)
        loaded.ShowModal()
        self.candidatesLoaded = True
            
    def LoadBallots(self, evt):
        if not self.candidatesLoaded:
            error = wx.MessageDialog(None, 'Please Load Candidates First!', '', wx.OK | wx.ICON_EXCLAMATION)
            error.ShowModal()
            return
        ballotFile = wx.FileDialog(self, "", "", "", "", wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)

        # If file was not selected
        if ballotFile.ShowModal() == wx.ID_CANCEL:
            return
        ballotFilePath = ballotFile.GetPath()
        try:
             self.election.loadBallotsFromCSVFile(ballotFilePath)
        except:
            error = wx.MessageDialog(None, 'Incorrectly Formatted Ballots File!', '', wx.OK | wx.ICON_EXCLAMATION)
            error.ShowModal()
            return
        loaded = wx.MessageDialog(None, 'Ballots Successfully Loaded!', '', wx.OK | wx.ICON_EXCLAMATION)
        loaded.ShowModal()
        self.ballotsLoaded = True
        self.replaceRace()

    def OnQuit(self, evt):
        # Close the tabulator
        self.Close()

    def About(self, evt):
        # About Dialog
        self.about = wx.MessageDialog(None,
            'This was writting for exclusive use by the Associated Students of the University of California by \
            Yun Park and Alton Zheng-Xie. (ASUC Technical Coordinators 2011-2014) This software is provided \
            \'as is\', and users must recognize that they operate this software at their own risk. In no event \
            shall the producers of this software be liable for any consequential, incidental, or special damage \
            whatsoever arising out of the use of or inability to use this software. Although this program has been \
            thoroughly tested, there is always the change of unresolved issues.',
            'ASUC Elections Tabulator v4.0',
            wx.OK)
        self.about.ShowModal()

    def redistribute(self):
        thread.start_new_thread(self.next, ())

    def next(self):
        status = self.election.iterateRace()

        # Disable changing positions and redistributing again
        self.infoPanel.redistributeButton.Disable()
        self.infoPanel.positionComboBox.Disable()

        while status == CONTINUE:
            time.sleep(self.speed)
            self.candidatesPanel.refresh()
            status = self.election.iterateRace()
            wx.Yield()
        
        self.status = status

        # Enable changing positions and redistributing again
        self.infoPanel.redistributeButton.Enable()
        self.infoPanel.positionComboBox.Enable()

        if status == FINISHED:
            self.electionsCompleted()
            self.toCompletion = False
            self.infoPanel.completeButton.Enable()
        elif (self.toCompletion):
            self.redistribute()

    def complete(self):
        self.toCompletion = True
        self.redistribute()
        self.infoPanel.completeButton.Disable()

    def electionsCompleted(self):
        finished = wx.MessageDialog(None, 'Elections Completed!', '', wx.OK | wx.ICON_EXCLAMATION)
        finished.ShowModal()

class CandidatesPanel(scrolled.ScrolledPanel):
    def __init__(self, parent, candidates, frame):
        scrolled.ScrolledPanel.__init__(self, parent)
        self.parent = parent
        self.candidates = candidates
        self.frame = frame
        self.quota = self.frame.quota
        
        self.SetSizer(wx.BoxSizer(wx.VERTICAL))
        self.initializeGrid()
        self.GetSizer().Add(self.grid, 1, wx.EXPAND)

        self.SetAutoLayout(1)
        self.SetupScrolling()

    def initializeGrid(self):
        self.grid = gridlib.Grid(self)
        self.datasource = CandidatesTable(self, self.candidates, self.grid, BarRenderer)
        self.grid.SetTable(self.datasource)
        self.grid.AutoSize()
        self.grid.SetColSize(0, 35)
        self.grid.SetColSize(1, 200)
        self.grid.SetColSize(2, 100)
        self.grid.SetColSize(3, 200)
        self.grid.SetColSize(4, 500)

        sizeInfo = gridlib.GridSizesInfo(18, [])
        self.grid.SetRowSizes(sizeInfo)

    def refresh(self):
        self.candidates.sort(key=lambda x: -1 * (x.score + x.quotaPlace * self.quota))
        self.grid.Refresh()

class BarRenderer(wx.grid.PyGridCellRenderer):
    def __init__(self, table, color):
        wx.grid.PyGridCellRenderer.__init__(self)
        self.table = table
        self.color = color
        self.rowSize = 50

    def Draw(self, grid, attr, dc, rect, row, col, isSelected):
        self.percentage = self.table.getPercentage(row)
        self.dc = dc
        self.dc.BeginDrawing()
        self.dc.SetPen(wx.Pen("grey",style=wx.TRANSPARENT))
        if self.percentage >= 1:
            self.dc.SetBrush(wx.Brush("yellow", wx.SOLID))
        else:
            self.dc.SetBrush(wx.Brush("blue", wx.SOLID))
        self.length = grid.GetColSize(col)
        self.height = grid.GetRowSize(row)
        self.dc.DrawRectangle(rect.x,rect.y,self.length*self.percentage,self.height)
        self.dc.EndDrawing()
        self.dc.BeginDrawing()
        self.dc.SetPen(wx.Pen("grey",style=wx.TRANSPARENT))
        self.dc.SetBrush(wx.Brush("white", wx.SOLID))
        self.dc.DrawRectangle(rect.x+self.length*self.percentage,rect.y,self.length*(1-self.percentage),self.height)
        self.dc.EndDrawing()

class CandidatesTable(wx.grid.PyGridTableBase):
    def __init__(self, parent, candidates, grid, barRenderer):
        wx.grid.PyGridTableBase.__init__(self)
        self.parent = parent
        self.candidates = candidates
        self.candidates.sort(key=lambda x: x.number)
        self.grid = grid
        self.barRenderer = barRenderer

        self.quota = 1
        self.lastScore = {}

        self.update()

    def GetNumberRows(self):
        """Return the number of rows in the grid"""
        return len(self.candidates)

    def GetNumberCols(self):
        """Return the number of columns in the grid"""
        return 5

    def IsEmptyCell(self, row, col):
        """Return True if the cell is empty"""
        return False

    def GetColLabelValue(self, col):
        """Return the label of column"""
        if col == 0:
            return "Num"
        elif col == 1:
            return "Name"
        elif col == 2:
            return "Party"
        elif col == 3:
            return "Score"
        elif col == 4:
            return "Percentage of Quota"

    def GetTypeName(self, row, col):
        """Return the name of the data type of the value in the cell"""
        return None

    def GetValue(self, row, col):
        """Return the value of a cell"""
        try:
            if col == 0:
                return self.candidates[row].number
            elif col == 1:
                return self.candidates[row].name
            elif col == 2:
                return self.candidates[row].party
            elif col == 3:
                # Display quota if candidate quota'd
                return self.round(self.candidates[row].score,4)
            elif col == 4:
                return ""
        except:
            pass

    def SetValue(self, row, col, value):
        """Set the value of a cell"""
        pass

    def getPercentage(self,row):
        try:
            self.lastScore[row] = self.candidates[row].score/self.quota
            return self.lastScore[row]
        except:
            return self.lastScore[row]

    def round(self, num, places):
        return int(num * (10 ** places))/float(10 ** places)

    def update(self):
        attr = wx.grid.GridCellAttr()
        renderer = self.barRenderer(self, "blue")
        attr.SetReadOnly(True)
        attr.SetRenderer(renderer)
        self.grid.SetColAttr(4, attr)

        for i in range(0,4):
            attr = wx.grid.GridCellAttr()
            font = wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False)
            attr.SetFont(font)
            self.grid.SetColAttr(i, attr)

class InfoPanel(wx.Panel):
    def __init__(self, parent, quota):
        wx.Panel.__init__(self, parent)
        self.parent = parent
        self.quota = quota
        self.SetSizer(wx.BoxSizer(wx.HORIZONTAL))

        font = wx.Font(14, wx.DECORATIVE, wx.NORMAL, wx.BOLD)

        self.quotaText = wx.StaticText(self, label='QUOTA: ' + str(self.quota))
        self.quotaText.SetFont(font)
        self.GetSizer().Add(self.quotaText, 1, wx.TOP | wx.LEFT | wx.RIGHT, 15)

        self.speedSlider = wx.Slider(self, value=10, minValue=1, maxValue=100, style=wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS, size=(150,-1))
        self.GetSizer().Add(self.speedSlider, 0, wx.BOTTOM, 5)
        self.Bind(wx.EVT_SCROLL, self.changeSpeed, self.speedSlider)

        positions = ['President', 'Executive VP', 'External Affairs VP', 'Academic Affairs VP', 'Student Advocate', 'Senator']
        self.positionComboBox = wx.ComboBox(self, choices=positions, style=wx.CB_READONLY, size=(150,25))
        self.GetSizer().Add(self.positionComboBox, 0, wx.TOP | wx.LEFT, 15)
        self.Bind(wx.EVT_COMBOBOX, self.changeRace)

        self.redistributeButton = wx.Button(self, wx.ID_ANY, label='Redistribute', size=(100,25))
        self.GetSizer().Add(self.redistributeButton, 0, wx.TOP | wx.LEFT, 15)
        self.Bind(wx.EVT_BUTTON, self.redistribute, self.redistributeButton)

        self.completeButton = wx.Button(self, wx.ID_ANY, label='Complete', size=(100,25))
        self.GetSizer().Add(self.completeButton, 0, wx.TOP | wx.LEFT, 15)
        self.Bind(wx.EVT_BUTTON, self.complete, self.completeButton)

    def changeSpeed(self, evt):
        self.frame.speed = evt.GetEventObject().GetValue() * 0.0001

    def changeRace(self, evt):
        position = evt.GetString()
        if position == 'President':
            self.frame.position = PRESIDENT
        elif position == 'Executive VP':
            self.frame.position = EXECUTIVE_VP
        elif position == 'External Affairs VP':
            self.frame.position = EXTERNAL_VP
        elif position == 'Academic Affairs VP':
            self.frame.position = ACADEMIC_VP
        elif position == 'Student Advocate':
            self.frame.position = STUDENT_ADVOCATE
        elif position == 'Senator':
            self.frame.position = SENATOR
        if self.frame.candidatesLoaded:
            self.frame.replaceRace()

    def redistribute(self, evt):
        self.frame.redistribute()

    def complete(self, evt):
        self.frame.complete()
        pass

    def resetQuotaLabel(self):
        self.quotaText.SetLabel('QUOTA (Score to WIN): ' + str(self.quota))

