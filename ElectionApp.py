##############################################################
#   ElectionApp.py                                           #
#   Created by: Alton Zheng & Yun Park                       #
#   Updated in Spring 2020 by Leon Ming, ASUC CTO            #
##############################################################

import wx
from ElectionWindow import *

# Start the Elections Tabulator
app = wx.App()
ElectionFrame(None, title='ASUC Tabulator v4.0')
app.MainLoop()
