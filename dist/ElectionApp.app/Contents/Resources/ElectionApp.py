#############################################################
#					    ElectionApp.py						#
#			  Created by: Alton Zheng & Yun Park			#
#			   Copyright Elections Council 2014				#
#############################################################

import wx
from ElectionWindow import *

# Start the Elections Tabulator
app = wx.App()
ElectionFrame(None, title='ASUC Tabulator v4.0')
app.MainLoop()