import wx

class MyFrame(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, title="SplitterWindow Example")

        # 创建SplitterWindow
        splitter = wx.SplitterWindow(self)

        # 创建左侧面板和右侧面板
        panel1 = wx.Panel(splitter)
        panel2 = wx.Panel(splitter)

        # 在左侧面板中添加一个文本控件
        text1 = wx.StaticText(panel1, label="This is panel 1")
        vbox1 = wx.BoxSizer(wx.VERTICAL)
        vbox1.Add(text1, 0, wx.ALL, 5)
        panel1.SetSizer(vbox1)

        # 在右侧面板中添加一个文本控件
        text2 = wx.StaticText(panel2, label="This is panel 2")
        vbox2 = wx.BoxSizer(wx.VERTICAL)
        vbox2.Add(text2, 0, wx.ALL, 5)
        panel2.SetSizer(vbox2)

        # 设置SplitterWindow的最小尺寸
        splitter.SetMinimumPaneSize(20)

        # 设置SplitterWindow的左右两个面板
        splitter.SplitVertically(panel1, panel2)

        # 将SplitterWindow作为窗口的主面板
        self.SetSizer(wx.BoxSizer(wx.VERTICAL))
        self.GetSizer().Add(splitter, 1, wx.EXPAND)

if __name__ == "__main__":
    app = wx.App()
    frame = MyFrame(None)
    frame.Show()
    app.MainLoop()
