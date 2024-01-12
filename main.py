import json

import wx
# import win32api
import sys, os

import pyperclip
import monitor
import setting
import random as rand
from const import APP_TITLE, SETTING_TITLE, SETTING_VERSION, ACCEPTABLE_SETTING_VERSION, PRESET_NAME, PRESET_DICT
# from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wx import NavigationToolbar2Wx
# from matplotlib.figure import Figure
from numpy import arange, sin, pi
import matplotlib

matplotlib.use('WXAgg')

# class CanvasPanel(wx.Panel):
#     def __init__(self, parent):
#         wx.Panel.__init__(self, parent)
#         self.figure = Figure(figsize=(4, 4))
#         self.axes = self.figure.add_subplot(111)
#         self.canvas = FigureCanvas(self, -1, self.figure)
#         self.sizer = wx.BoxSizer(wx.VERTICAL)
#         self.sizer.Add(self.canvas, 1, wx.LEFT | wx.TOP | wx.GROW)
#         self.SetSizer(self.sizer)
#         self.Fit()

    # def draw(self):
    #     t = arange(0.0, 3.0, 0.01)
    #     s = sin(2 * pi * t)
    #     self.axes.plot(t, s)


class infoLogger:
    def __init__(self, log_place):
        self.log_place = log_place
    def log_basic(self, info):
        txt = self.log_place.GetLabel()
        if len(txt) > 80:
            self.log_place.SetLabel('....'+txt[-20:]+"\n"+info)
        else:
            self.log_place.SetLabel(txt+"\n"+info)
        self.log_place.ShowPosition(self.log_place.GetLastPosition())

class MainFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, -1, title=APP_TITLE)

        self.SetBackgroundColour(wx.Colour(224, 224, 224))
        self.SetSize((1400, 600))
        self.Center()
        self.make_menu_bar()
        # self.CreateStatusBar()
        # self.SetStatusText("就绪")

        splitter = wx.SplitterWindow(self)
        self.panel_setting = wx.Panel(splitter)
        panel_info = wx.Panel(splitter)

        # 先建立右侧的消息区
        bs_info = wx.BoxSizer(wx.VERTICAL)
        self.info_place = wx.TextCtrl(panel_info, value='----消息区----\n 就绪。', size=(-1, 50),
                                      style=wx.TE_READONLY | wx.TE_MULTILINE | wx.EXPAND | wx.ALL)
        self.log_place = wx.TextCtrl(panel_info, value='----日志----',
                                     style=wx.TE_READONLY | wx.TE_MULTILINE | wx.EXPAND | wx.ALL)
        static_line = wx.StaticLine(panel_info, style=wx.LI_HORIZONTAL)

        bs_info.Add(self.info_place, 0, wx.EXPAND | wx.ALL, 5)
        bs_info.Add(static_line, flag=wx.ALL | wx.EXPAND, border=5)
        bs_info.Add(self.log_place, 9, wx.EXPAND | wx.ALL, 5)

        self.info_logger = infoLogger(self.info_place)
        # 左侧的由上到下，1. 按钮

        bs_buttons = wx.BoxSizer()
        self.init_buttons(bs_buttons, self.panel_setting)

        # 2. 基本设置

        bs_basic_setting = wx.BoxSizer()
        self.basic_setting = setting.BasicSetting(self.panel_setting, bs_basic_setting, self.info_logger)

        # 3. 攻击设置
        self.gs_atk_set = wx.FlexGridSizer(rows=11, cols=11, hgap=5, vgap=5)
        # 3.1 标题
        for i in range(0, 11):
            prop = 2
            if i < 2:
                prop = 1
            self.gs_atk_set.Add(wx.StaticText(self.panel_setting, style=wx.ALIGN_CENTER, label=SETTING_TITLE[i]),
                           flag=wx.EXPAND | wx.ALL, border=5)

        # 3.2 攻击列表
        self.setting_num = 0
        self.attack_setting = []
        for i in range(5):
            self.add_setting(self.panel_setting, self.gs_atk_set)

        # self.canvas = CanvasPanel(self.panel_setting)

        # 加入整体sizer
        self.bs_setting = wx.BoxSizer(wx.VERTICAL)
        self.bs_setting.Add(bs_buttons, flag=wx.EXPAND | wx.ALL, border=5)
        self.bs_setting.Add(bs_basic_setting, border=5)
        self.bs_setting.Add(self.gs_atk_set, flag=wx.EXPAND | wx.ALL, border=5)

        self.panel_setting.SetSizer(self.bs_setting)

        panel_info.SetSizer(bs_info)
        splitter.SplitVertically(self.panel_setting, panel_info)
        splitter.SetMinimumPaneSize(800)
        self.SetSizer(wx.BoxSizer(wx.VERTICAL))
        self.GetSizer().Add(splitter, 1, wx.EXPAND)

        self.m = None
        self.flag_simulation = False

    def start_simulation(self, event):
        self.basic_setting.attack_num = self.setting_num

        if not self.basic_setting.get_inputs():
            self.info_logger.log_basic('基础参数设置错误')
            return False

        for i in range(self.setting_num):
            if not self.attack_setting[i].get_inputs():
                self.info_logger.log_basic('第%d个攻击设置参数设置错误' % (i + 1))
                return False

        self.m = monitor.Monitor(self)
        if self.m.simulate():
            self.info_logger.log_basic("模拟完成！")
            self.flag_simulation = True
            if self.basic_setting.auto_plot:
                self.m.plot()
        else:
            self.info_logger.log_basic("未进行模拟！")

    def init_buttons(self, sizer, parent):
        # Buttons
        runButton = wx.Button(parent, label="开始模拟")
        runButton.Bind(wx.EVT_BUTTON, self.start_simulation)
        plotButton = wx.Button(parent, label="绘制图线")
        plotButton.Bind(wx.EVT_BUTTON, self.on_plot)
        addButton = wx.Button(parent, label="添加一行")
        addButton.Bind(wx.EVT_BUTTON, self.on_add_setting)
        applyButton = wx.Button(parent, label="加载配置\n从剪贴板\n")
        applyButton.Bind(wx.EVT_BUTTON, self.on_apply_setting)
        saveSetButton = wx.Button(parent, label="保存配置\n到剪贴板")
        saveSetButton.Bind(wx.EVT_BUTTON, self.on_copy_setting)
        presetButton = wx.Button(parent, label="加载预设")
        presetButton.Bind(wx.EVT_BUTTON, self.on_preset_select)
        randomButton = wx.Button(parent, label="随机\n起始时刻")
        randomButton.Bind(wx.EVT_BUTTON, self.on_random)
        saveButton = wx.Button(parent, label="保存结果")
        saveButton.Bind(wx.EVT_BUTTON, self.on_save)
        exitButton = wx.Button(parent, label="退出")
        exitButton.Bind(wx.EVT_BUTTON, self.on_exit)

        sizer.Add(runButton, flag=wx.EXPAND, border=5)
        sizer.Add(plotButton, flag=wx.EXPAND, border=5)
        sizer.Add(addButton, flag=wx.EXPAND, border=5)
        sizer.Add(applyButton, flag=wx.EXPAND, border=5)
        sizer.Add(saveSetButton, flag=wx.EXPAND, border=5)
        sizer.Add(presetButton, flag=wx.EXPAND, border=5)
        sizer.Add(randomButton, flag=wx.EXPAND, border=5)
        sizer.Add(saveButton, flag=wx.EXPAND, border=5)
        sizer.Add(exitButton, flag=wx.EXPAND, border=5)

    def apply_setting(self, text):
        try:
            sets = json.loads(text)
            if sets.pop(0) not in ACCEPTABLE_SETTING_VERSION:
                raise VersionException("配置版本不匹配。")
            self.basic_setting.set_inputs(sets.pop(0))

            # 如果配置比当前多，就添加
            if len(sets) > len(self.attack_setting):
                while len(sets) > len(self.attack_setting):
                    self.add_setting(self.panel_setting, self.gs_atk_set)
                self.bs_setting.Layout()

            for i in range(len(self.attack_setting)):
                if i > len(sets) - 1:
                    self.attack_setting[i].input_is_active.SetValue(False)
                else:
                    self.attack_setting[i].set_inputs(sets[i])
        except VersionException as e:
            self.info_logger.log_basic(str(e))
            return False
        except:
            self.info_logger.log_basic("配置应用错误，请检查剪贴板内容。")
            return False
        return True

    def add_setting(self, parent, sizer):
        self.setting_num += 1
        new_as = setting.AttackSetting(parent, self.setting_num, sizer, self.info_logger)
        self.attack_setting.append(new_as)
        # self.bs_setting.Add(new_as.bs, flag=wx.EXPAND | wx.ALL, border=5)

    def copy_setting(self):
        sets = [SETTING_VERSION, self.basic_setting.get_string()]
        for atk in self.attack_setting:
            if atk.input_name.GetValue() == '':
                continue
            sets.append(atk.get_string())
        return json.dumps(sets)

    def remove_setting(self):
        pass

    def make_menu_bar(self):
        file_menu = wx.Menu()
        help_menu = wx.Menu()
        link_menu = wx.Menu()

        run_item = wx.MenuItem(file_menu, wx.ID_ANY, text="开始模拟", helpString="进行元素反应模拟", kind=wx.ITEM_NORMAL)
        save_item = wx.MenuItem(file_menu, wx.ID_ANY, text="保存日志", helpString="", kind=wx.ITEM_NORMAL)
        exit_item = wx.MenuItem(file_menu, wx.ID_ANY, text="退出", helpString="", kind=wx.ITEM_NORMAL)
        help_item = wx.MenuItem(help_menu, wx.ID_ANY, text="帮助", helpString="", kind=wx.ITEM_NORMAL)
        tip_item = wx.MenuItem(help_menu, wx.ID_ANY, text="提示", helpString="", kind=wx.ITEM_NORMAL)
        update_item = wx.MenuItem(help_menu, wx.ID_ANY, text="更新记录", helpString="", kind=wx.ITEM_NORMAL)
        about_item = wx.MenuItem(help_menu, wx.ID_ANY, text="关于", helpString="", kind=wx.ITEM_NORMAL)
        link_names = ["高等元素论 by Shallow夢", "高等元素论（草反应） by 佳佳妹妹。", "反应优先级 by tesiacoil", '元素附着论 by tesiacoil', '冻结反应机制 by Shallow夢', '项目Github', '本项目NGA页']
        link_addresses = ['https://bbs.nga.cn/read.php?tid=24400590',
                          'https://bbs.nga.cn/read.php?tid=33231790',
                          'https://bbs.nga.cn/read.php?tid=32876825',
                          'https://bbs.nga.cn/read.php?tid=31217959',
                          'https://bbs.nga.cn/read.php?tid=29632439',
                          'https://github.com/hfdxmy/koko-element-simulator',
                          'https://bbs.nga.cn/read.php?tid=35483754']
        link_items = [wx.MenuItem(help_menu, wx.ID_ANY, text=name, helpString="", kind=wx.ITEM_NORMAL) for name in link_names]

        file_menu.Append(run_item)
        file_menu.Append(save_item)
        file_menu.Append(exit_item)
        help_menu.Append(help_item)
        help_menu.Append(tip_item)
        help_menu.Append(update_item)
        help_menu.Append(about_item)

        for item in link_items:
            link_menu.Append(item)

        menu_bar = wx.MenuBar()
        menu_bar.Append(file_menu, "文件(&F)")
        menu_bar.Append(help_menu, "帮助(&H)")
        menu_bar.Append(link_menu, "常用链接(&L)")

        self.SetMenuBar(menu_bar)

        self.Bind(wx.EVT_MENU, self.start_simulation, run_item)
        self.Bind(wx.EVT_MENU, self.on_save, save_item)
        self.Bind(wx.EVT_MENU, self.on_exit, exit_item)
        self.Bind(wx.EVT_MENU, self.on_help, help_item)
        self.Bind(wx.EVT_MENU, self.on_tip, tip_item)
        self.Bind(wx.EVT_MENU, self.on_update, update_item)
        self.Bind(wx.EVT_MENU, self.on_about, about_item)

        link_funcs = [lambda event, i=i: wx.LaunchDefaultBrowser(link_addresses[i]) for i in range(len(link_items))]
        for i in range(len(link_items)):
            self.Bind(wx.EVT_MENU, link_funcs[i], link_items[i])

    def on_preset_select(self, event):
        dlg = wx.SingleChoiceDialog(self, "请选择预设", "加载预设", PRESET_NAME)
        if dlg.ShowModal() == wx.ID_OK:
            selection = dlg.GetStringSelection()
            set_string = PRESET_DICT[selection]
            self.apply_setting(set_string)
            self.info_logger.log_basic("成功加载预设："+selection)
            if selection == '草行久+水草雷前台' or selection == '心雷妲+水冰后台':
                self.info_logger.log_basic("请注意0.5s内单目标最多受到2次超绽放伤害")
        dlg.Destroy()

    def on_about(self, event):
        wx.MessageBox(APP_TITLE+"，仅供研究学习使用。\n NGA@kokobird，2023年2月",
                      "关于",
                      wx.OK | wx.ICON_INFORMATION)
    def on_update(self, event):
        wx.MessageBox("V0.91:\n"
                      "-修复燃烧持续伤害会触发草神协同和雷神协同的bug。\n"
                      "-修复燃烧挂火会将燃烧触发者改为‘燃烧’的bug。\n"
                      "-添加更新记录。\n"
                      "V0.90:\n"
                      "-首次发布。",
                      "更新记录",
                      wx.OK | wx.ICON_INFORMATION)

    def on_help(self, event):
        wx.MessageBox(""
                      # "目前已经实现的功能：\n"
                      # "·指定技能参数，计算元素量衰减、所有种类的元素反应，记录元素变化情况并作图。\n"
                      "1. “模拟时长”最长不超过40秒。“妮绽放”选项不要求水草，仅调整绽放间隔。“不可冻结”生效时，不产生冻元素。"
                      "“忽略目标2”生效时，所有计算均为单目标。”记录附着“等生效时，日志将输出相应信息。\n"
                      "2. 对于每条技能，”启用“关闭时则不进行计算。”名称”可自定义。“元素量”不超过4。"
                      "”起始时间“和”冷却时间“表示生效时间段。”攻击冷却“表示至少经过多少时间才能触发一次攻击，不小于0.5秒。”附着冷却“表示至少经过多少时间，下一次攻击才能上元素。\n"
                      "3. “攻击方式”中，“定时触发”表示冷却时间一到就产生一次攻击，”草神协同“表示目标触发元素反应或受到草原核伤害后触发，”雷神协同“表示目标受到除感电、燃烧以外的攻击后触发，"
                      "”阿贝多协同“表示目标受到任何伤害后触发。名称仅代表触发形式，不要求具体角色。\n"
                      "\n"
                      "特殊处理：\n"
                      "1. 超载、超导、原绽放、烈绽放反应视为对双目标（全体）的伤害。扩散反应为对自身无元素的伤害，对其余目标带有相应元素的伤害。由于本模拟器不关注伤害，故水扩散无影响。\n"
                      "2. 草原核与目标绑定，即草原核由哪个目标产生，超绽放、烈绽放的触发判断也基于哪个目标。草核超绽放的伤害目标也为产生该草核的目标。\n"
                      "3. 同时刻的攻击，按照序号顺序进行计算。如果触发协同，则协同会紧跟其后计算。\n"
                      "4. 水火雷冰草的衰减时间采用2.5*元素量+7计算，当元素量不为1，1.5，2等常见数时。\n"
                      "5. 感电由于延迟扣除元素量的机制，设定为触发感电的下一时间步扣除元素量。\n"
                      "6. 燃烧挂火CD在燃烧结束后不重置，这个不是很清楚具体情况。"
                      "\n"
                      "目前已知问题：\n"
                      "1. 超绽放从触发到命中的延迟没有考虑，目前为零。\n"
                      "2. 对于双目标，目前按照共用计时器处理，即无法分别计算附着CD。\n"
                      "3. 目标受到元素反应伤害的CD未考虑，例如0.5秒内至多只能受到同一个触发来源的两次超绽放伤害。\n"
                      "4. 对于同一时刻的反应，先后顺序可能不准确。能够确定的是草神协同先于雷神协同，其余多元素扩散情况，或是其他特殊情况，可能存在与游戏内现象不符合的问题。请以游戏内为准。",
                      "帮助",
                      wx.OK | wx.ICON_INFORMATION)

    def on_tip(self, event):
        wx.MessageBox("1. 如果只想让攻击触发一次，可以把持续时间设为0。\n"
                      "2. 研究燃烧反应时，推荐将精度设为0.01s，0.05s或0.25s，因为燃烧攻击的cd是0.25s。\n"
                      "3. 如果加了太多空行，复制配置时不想包括，可以将空行的技能名删除，使其为空。\n"
                      "4. 目前没有设计减行的功能，如果需要请重启程序。",
                      "小技巧",
                      wx.OK | wx.ICON_INFORMATION)

    def on_save(self, event):
        string_to_save = "---模拟配置代码---\n"
        string_to_save += self.copy_setting()
        string_to_save += "\n---------------\n"
        string_to_save += self.log_place.GetValue()

        # Bring up the system's native file save dialog
        dialog = wx.FileDialog(self, "保存结果", "", "", "Text files (*.txt)|*.txt",
                               wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        if dialog.ShowModal() == wx.ID_OK:
            # User clicked OK, get the selected filename
            filename = dialog.GetPath()
            # Save the string to the file
            with open(filename, 'w') as f:
                f.write(string_to_save)
            self.info_logger.log_basic("保存到%s" % filename)
        # Destroy the file dialog
        dialog.Destroy()

    def on_exit(self, event):
        self.Close(True)

    def on_add_setting(self, event):
        if len(self.attack_setting) == 10:
            self.info_logger.log_basic("已到达上限，无法添加更多行。")
            return
        self.add_setting(self.panel_setting, self.gs_atk_set)
        self.bs_setting.Layout()

    def on_copy_setting(self, event):
        pyperclip.copy(self.copy_setting())
        self.info_logger.log_basic("已将当前配置保存到剪贴板。")

    def on_apply_setting(self, event):
        text = pyperclip.paste()
        if self.apply_setting(text):
            self.info_logger.log_basic("成功加载配置。")

    def on_plot(self, event):
        if self.flag_simulation:
            self.m.plot()
        else:
            self.info_logger.log_basic("请先执行模拟！")

    def on_random(self, event):
        for atk_set in self.attack_setting:
            if atk_set.input_is_active.GetValue():
                atk_set.input_time_start.SetValue(str(rand.randint(0, 50) / 10))
                # atk_set.input_attack_cd.SetValue(str(rand.randint(10, 20) / 10))


class MainApp(wx.App):

    def OnInit(self):
        self.SetAppName(APP_TITLE)
        self.Frame = MainFrame()
        self.Frame.Show()
        return True


class VersionException(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class MyException(Exception):
        def __init__(self, message):
            self.message = message

        def __str__(self):
            return self.message


if __name__ == '__main__':
    app = MainApp()
    app.MainLoop()


