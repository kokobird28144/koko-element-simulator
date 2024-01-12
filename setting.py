import wx
from validator import NumberValidator
from const import ELEMENTS
from main import MyException
from attack import Attack
import random as rand


class AttackSetting:

    def __init__(self, parent, num, sizer, logger):
        self.logger = logger
        # self.bs = wx.BoxSizer()
        self.input_is_active = wx.CheckBox(parent, style=wx.ALIGN_RIGHT)  # 启用
        self.input_name = wx.TextCtrl(parent, size=(80, 20))  # 名称
        self.input_element = wx.Choice(parent, choices=ELEMENTS)  # 元素
        self.input_element_mass = wx.TextCtrl(parent, validator=NumberValidator(), size=(30, 20))  # 元素量
        self.input_attack_mode = wx.Choice(parent, choices=['定时触发', '草神协同', '雷神协同', '阿贝多协同'])  # 攻击方式
        self.input_attack_target = wx.Choice(parent, choices=['目标1', '目标2', '双目标'])  # 目标选择
        self.input_time_start = wx.TextCtrl(parent, validator=NumberValidator(), size=(30, 20))  # 起始时间
        self.input_time_last = wx.TextCtrl(parent, validator=NumberValidator(), size=(30, 20))  # 持续时间
        self.input_attack_cd = wx.TextCtrl(parent, validator=NumberValidator(), size=(30, 20))  # 攻击冷却
        self.input_element_cd = wx.TextCtrl(parent, validator=NumberValidator(), size=(30, 20))  # 附着冷却

        sizer.Add(self.input_is_active, proportion=0, flag=wx.EXPAND | wx.ALL, border=5)  # 启用
        sizer.Add(wx.StaticText(parent, style=wx.ALIGN_CENTER, label=str(num)), flag=wx.EXPAND | wx.ALL, border=5)  # 序号
        sizer.Add(self.input_name, proportion=0, flag=wx.EXPAND | wx.ALL, border=5)  # 名称
        sizer.Add(self.input_element, proportion=0, flag=wx.EXPAND | wx.ALL, border=5)  # 元素
        sizer.Add(self.input_element_mass, proportion=0, flag=wx.EXPAND | wx.ALL, border=5)  # 元素量
        sizer.Add(self.input_attack_mode, proportion=0, flag=wx.EXPAND | wx.ALL, border=5)  # 攻击方式
        sizer.Add(self.input_attack_target, proportion=0, flag=wx.EXPAND | wx.ALL, border=5)
        sizer.Add(self.input_time_start, proportion=0, flag=wx.EXPAND | wx.ALL, border=5)  # 起始时间
        sizer.Add(self.input_time_last, proportion=0, flag=wx.EXPAND | wx.ALL, border=5)  # 持续时间
        sizer.Add(self.input_attack_cd, proportion=0, flag=wx.EXPAND | wx.ALL, border=5)  # 攻击冷却
        sizer.Add(self.input_element_cd, proportion=0, flag=wx.EXPAND | wx.ALL, border=5)  # 附着冷却

        # default value
        if num < 4:
            self.input_is_active.SetValue(True)
        self.input_element.SetSelection((num-1) % 7)
        self.input_name.SetValue(ELEMENTS[(num-1) % 7])
        self.input_element_mass.SetValue('1')
        self.input_attack_mode.SetSelection(0)
        self.input_attack_target.SetSelection(0)
        self.input_time_start.SetValue(str(rand.randint(0, 30) / 10))
        self.input_time_last.SetValue('15')
        self.input_attack_cd.SetValue(str(rand.randint(10, 20) / 10))
        self.input_element_cd.SetValue('0')

        self.setting_id = num
        self.is_active = False
        self.name = 'Default'
        self.element_choice = 0
        self.element = 'Default'
        self.element_mass = 1
        self.attack_mode_choice = 0
        self.attack_mode = 'Default'
        self.attack_target = 0
        self.time_start = 0
        self.time_last = 1
        self.attack_cd = 1
        self.element_cd = 2.5

        self.current_attack_cd = 0
        self.current_element_cd = 0
        pass

    def get_inputs(self):
        try:
            self.is_active = self.input_is_active.GetValue()
            self.name = self.input_name.GetValue()
            self.element_choice = self.input_element.GetSelection()
            self.element = self.input_element.GetString(self.element_choice)
            self.attack_mode_choice = self.input_attack_mode.GetSelection()
            self.attack_mode = self.input_attack_mode.GetString(self.attack_mode_choice)
            self.attack_target = self.input_attack_target.GetSelection()
            self.element_mass = float(self.input_element_mass.GetValue())
            self.time_start = float(self.input_time_start.GetValue())
            self.time_last = float(self.input_time_last.GetValue())
            self.attack_cd = float(self.input_attack_cd.GetValue())
            self.element_cd = float(self.input_element_cd.GetValue())
        except ValueError:
            self.error_log('数值输入错误')
            return False
        except:
            self.error_log('数据格式错误')
            return False

        if self.element_mass > 4:
            self.error_log('元素量过大')
            return False

        if self.attack_cd < 0.5:
            self.error_log('攻击频率过快')
            return False

        # restart simulation reset cd
        self.current_attack_cd = 0
        self.current_element_cd = 0
        return True

    def get_string(self):
        self.get_inputs()
        return [getattr(self, attr) for attr in ["is_active", "name", "element_choice", "element_mass",
                                                 "attack_mode_choice", "attack_target", "time_start",
                                                 "time_last", "attack_cd", "element_cd"]]

    def set_inputs(self, array):
        attr_list = ["is_active", "name", "element_choice", "element_mass",
                     "attack_mode_choice", "attack_target", "time_start",
                     "time_last", "attack_cd", "element_cd"]
        try:
            for i in range(len(attr_list)):
                setattr(self, attr_list[i], array[i])

            self.input_is_active.SetValue(self.is_active)
            self.input_name.SetValue(self.name)
            self.input_element.SetSelection(self.element_choice)
            self.input_element_mass.SetValue(str(self.element_mass))
            self.input_attack_mode.SetSelection(self.attack_mode_choice)
            self.input_attack_target.SetSelection(self.attack_target)
            self.input_time_start.SetValue(str(self.time_start))
            self.input_time_last.SetValue(str(self.time_last))
            self.input_attack_cd.SetValue(str(self.attack_cd))
            self.input_element_cd.SetValue(str(self.element_cd))
        except:
            self.error_log('设置应用失败。')
            return False
        return True

    def error_log(self, info):
        self.logger.log_basic('第%d条设置：“%s” %s' % (self.setting_id, self.name, info))

    def remove(self):
        pass

    def time_advance(self, dt):
        if not self.is_active:
            return None
        # 冷却减少
        if self.current_attack_cd > 0:
            self.current_attack_cd -= dt
            self.current_attack_cd = max(self.current_attack_cd, 0)
        if self.current_element_cd > 0:
            self.current_element_cd -= dt
            self.current_element_cd = max(self.current_element_cd, 0)
        pass

    def generate_attack(self, time):
        if not self.is_active:
            return None
        if time < self.time_start - 0.001 or time > self.time_start + self.time_last + 0.001:
            return None
        if self.current_attack_cd > 0.001:
            return None

        self.current_attack_cd = self.attack_cd
        if self.current_element_cd < 0.001:
            self.current_element_cd = self.element_cd
            return Attack(self.name, self.element, element_mass=self.element_mass, target=self.attack_target,
                          id=self.setting_id - 1, tag='角色')
        else:
            return Attack(self.name, self.element, element_mass=0, target=self.attack_target, id=self.setting_id - 1,
                          tag='角色')


class BasicSetting:

    def __init__(self, parent, sizer, logger):
        self.input_max_time = wx.TextCtrl(parent, validator=NumberValidator(), size=(30, 24))
        self.input_max_time.SetValue('20')
        self.input_dt = wx.Choice(parent, choices=['0.25', '0.2', '0.1', '0.05', '0.02', '0.01'])
        self.input_dt.SetSelection(5)
        self.input_nilou = wx.CheckBox(parent, label='妮绽放')
        self.input_flag_froze = wx.CheckBox(parent, label='不可冻结')
        self.input_single_target = wx.CheckBox(parent, label='忽略目标2')
        self.input_single_target.SetValue(True)
        self.input_log_apply = wx.CheckBox(parent, label='记录附着')
        self.input_log_quicken = wx.CheckBox(parent, label='记录激化')
        self.input_log_burning = wx.CheckBox(parent, label='记录燃烧')
        self.input_auto_plot = wx.CheckBox(parent, label='自动绘图')
        self.input_auto_plot.SetValue(True)

        sizer.Add(wx.StaticText(parent, style=wx.ALIGN_LEFT, label=" 模拟时长(s)"), flag=wx.ALIGN_CENTER_VERTICAL, border=5)
        sizer.Add(self.input_max_time, flag=wx.EXPAND | wx.ALL, border=5)
        sizer.Add(wx.StaticText(parent, style=wx.ALIGN_LEFT, label="精度(s)"), flag=wx.ALIGN_CENTER_VERTICAL, border=5)
        sizer.Add(self.input_dt, flag=wx.EXPAND | wx.ALL, border=5)
        sizer.Add(self.input_nilou, flag=wx.ALIGN_CENTER_VERTICAL)
        sizer.Add(self.input_flag_froze, flag=wx.ALIGN_CENTER_VERTICAL)
        sizer.Add(self.input_single_target, flag=wx.ALIGN_CENTER_VERTICAL)
        sizer.Add(self.input_log_apply, flag=wx.ALIGN_CENTER_VERTICAL)
        sizer.Add(self.input_log_quicken, flag=wx.ALIGN_CENTER_VERTICAL)
        sizer.Add(self.input_log_burning, flag=wx.ALIGN_CENTER_VERTICAL)
        sizer.Add(self.input_auto_plot, flag=wx.ALIGN_CENTER_VERTICAL)

        self.max_time = 0
        self.dt = 0.02
        self.attack_num = 1
        self.dt_choice = 0
        self.log_apply = True
        self.log_quicken = True
        self.log_burning = False
        self.nilou = False
        self.flag_froze = True
        self.single_target = True
        self.auto_plot = True

        self.logger = logger

    def get_inputs(self):
        try:
            max_time = float(self.input_max_time.GetValue())

        except ValueError:
            self.logger.log_basic('模拟时长错误。')
            return False
        if max_time > 40:
            self.logger.log_basic('模拟时长太长。')
            return False

        self.max_time = max_time
        self.dt_choice = self.input_dt.GetSelection()
        self.dt = float(self.input_dt.GetString(self.dt_choice))
        self.log_apply = self.input_log_apply.GetValue()
        self.log_quicken = self.input_log_quicken.GetValue()
        self.log_burning = self.input_log_burning.GetValue()
        self.nilou = self.input_nilou.GetValue()
        self.flag_froze = not (self.input_flag_froze.GetValue())
        self.single_target = self.input_single_target.GetValue()
        self.auto_plot = self.input_auto_plot.GetValue()
        return True

    def set_inputs(self, array):
        attr_list = ["max_time", "dt_choice", "log_apply", "log_quicken",
                     "log_burning", "nilou", "flag_froze", "single_target", "auto_plot"]
        try:
            for i in range(len(attr_list)):
                setattr(self, attr_list[i], array[i])

            self.input_max_time.SetLabel(str(self.max_time))
            self.input_dt.SetSelection(self.dt_choice)
            self.input_log_apply.SetValue(self.log_apply)
            self.input_log_quicken.SetValue(self.log_quicken)
            self.input_log_burning.SetValue(self.log_burning)
            self.input_nilou.SetValue(self.nilou)
            self.input_flag_froze.SetValue(not self.flag_froze)
            self.input_single_target.SetValue(self.single_target)
            self.input_auto_plot.SetValue(self.auto_plot)
        except:
            return False
        return True

    def get_string(self):
        self.get_inputs()
        return [getattr(self, attr) for attr in ["max_time", "dt_choice", "log_apply", "log_quicken",
                                                 "log_burning", "nilou", "flag_froze", "single_target", "auto_plot"]]
