import attack
from const import ATTACH_ELEMENT_DICT, ELEMENT_REACTION_DICT
import numpy as np
import matplotlib.pyplot as plt

class Target:

    def __init__(self, monitor, tgt_id):
        self.element = [0, 0, 0, 0, 0, 0, 0, 0]  # 0水 1火 2冰 3雷 4草 5冻 6激 7燃
        self.decrease_spd = [0, 0, 0, 0, 0, 0.4, 0, 0, 0, 0]  # 8和9用于临时存放草激在燃烧时的速度
        self.monitor = monitor
        self.tgt_id = tgt_id
        self.name = '目标' + str(tgt_id + 1)
        self.name_eng = 'Target ' + str(tgt_id + 1)
        self.element_string = "无元素附着"
        self.element_hist = [self.element.copy()]
        self.is_frozen = False  # 冻结
        self.frozen_time = 0
        self.electro_charged_tag = False
        self.electro_charged_source = None  # 感电触发者
        self.electro_charged_cd = 0  # 感电CD
        self.geo_cd = 0  # 结晶CD

        self.is_burning = False
        self.burning_source = None
        self.burning_fire_cd = 0
        self.burning_cd = 0

        self.coordinate_nahida_list = []  # 草神协同
        self.coordinate_shogun_list = []  # 雷神协同
        self.coordinate_albedo_list = []  # 阿贝多/迪协同

        self.stat_frozen = []
        self.stat_attack = []

    def coordinate(self, mode):
        coord_list = []
        if mode == 'nahida':
            coord_list = self.coordinate_nahida_list
        elif mode == 'shogun':
            coord_list = self.coordinate_shogun_list
        elif mode == 'albedo':
            coord_list = self.coordinate_albedo_list
        else:
            self.monitor.log_action("未知协同")

        for i in coord_list:
            atk = self.monitor.atk_set[i].generate_attack(self.monitor.time)
            if atk is not None:
                self.monitor.attack_list.append(atk)

    def time_advance(self, dt):
        # 冻结判断
        if self.element[5] > 0:
            self.decrease_spd[5] += 0.1 * dt
            if not self.is_frozen:
                self.is_frozen = True
                self.frozen_time = self.monitor.time
                self.monitor.log_action("%s冻结" % self.name)
        else:
            if self.decrease_spd[5] > 0.4:
                self.decrease_spd[5] = max(0.4, self.decrease_spd[5] - 0.2 * dt)
            if self.is_frozen:
                self.is_frozen = False
                self.stat_frozen.append([self.frozen_time, self.monitor.time])
                self.monitor.log_action("%s解冻，冻结时长%.2f秒" % (self.name, self.monitor.time-self.frozen_time))

        # 感电CD
        self.electro_charge()
        if self.electro_charged_cd > 0:
            self.electro_charged_cd = max(0, self.electro_charged_cd - dt)

        # 燃烧逻辑
        self.burning()
        if self.burning_cd > 0:
            self.burning_cd = max(0, self.burning_cd - dt)
        if self.burning_fire_cd > 0:
            self.burning_fire_cd = max(0, self.burning_fire_cd - dt)

        # 结晶CD
        if self.geo_cd > 0:
            self.geo_cd = max(0, self.geo_cd - dt)

        # 元素减少
        for i in range(8):
            if self.element[i] > 0:
                self.element[i] -= self.decrease_spd[i] * dt
            if self.element[i] < 0:
                self.element[i] = 0

        self.refresh_element_string()
        self.element_hist.append(self.element.copy())

    def refresh_element_string(self):
        string = ""
        for i in [6, 7, 8, 5, 1, 2, 3, 4]:
            if self.element[i-1] > 0:
                string += ATTACH_ELEMENT_DICT[i]
                string += "%.2f" % (self.element[i-1])
        if string == "":
            string = "无元素附着"
        self.element_string = string
        return string

    def electro_charge(self):
        if self.electro_charged_tag:
            self.element[0] = max(0, self.element[0] - 0.4)
            self.element[3] = max(0, self.element[3] - 0.4)
            self.monitor.log_action("%s感电扣除元素，%s" % (self.name, self.log_element_change()))
            self.electro_charged_tag = False
        if self.element[0] == 0 or self.element[3] == 0:
            return
        if self.electro_charged_cd > 0:
            return

        self.electro_charged_tag = True  # 将
        self.electro_charged_cd = 1  # 感电冷却1秒
        # self.stat_attack[self.electro_charged_source.id][6] += 1
        self.monitor.log_action("%s感电，由%s触发。" % (self.name, self.electro_charged_source.name))
        self.monitor.attack_list.append(attack.Attack('感电', '雷', target=self.tgt_id, id=self.electro_charged_source.id, tag='剧变'))
        self.coordinate('nahida')


    def log_element_change(self):
        # print("%s：(%s)->(%s)" % (self.name, self.element_string, self.refresh_element_string()))
        return "%s：(%s)->(%s)" % (self.name, self.element_string, self.refresh_element_string())

    def print_element_hist(self, t, ax):
        element_hist = np.array(self.element_hist).transpose()

        element_hist_max = [0, 0, 0, 0, 0, 0, 0, 0]
        element_plot_color = {0: "blue", 1: "Red", 2: "lightblue", 3: "mediumpurple", 4: "lightgreen", 5: "deepskyblue", 6: "green", 7: "firebrick"}
        element_plot_name = {0: "Hydro", 1: "Pyro", 2: "Cryo", 3: "Electro", 4: "Dendro", 5: "Frozen", 6: "Quicken", 7: "Burning"}
        # if canvas is not None:
        #     ax = canvas.axes
        #     ax.cla()
        # else:
        #     fig, ax = plt.subplots()

        ax.cla()
        for i in range(8):
            element_hist_max[i] = max(element_hist[i])
            if element_hist_max[i] > 0.1:
                ax.plot(t, element_hist[i], color=element_plot_color[i], label=element_plot_name[i], linewidth=1)

        ax.legend(loc='upper right')
        ax.set_xticks(np.arange(0, t[-1]+1, 1.0))
        if t[-1] < 10.01:
            ax.set_xticks(np.arange(0, t[-1] + 1, 0.5))
        ax.grid()
        ax.set_title(self.name_eng)

        # if canvas is not None:
        #     canvas.canvas.draw()
        # else:
        #     plt.show()
        # ax.plot(t, element_hist[2], color="purple")
        # plt.show()

    # 统计目标受到的攻击
    # 受到xx攻击xx次，带元素的xx次，其中xx反应xx次（蒸发，融化，超激化。。）；xx反应xx次（绽放，超绽放，超载，感电，原激化，冻结）
    # 每个tgt对象，对于每个atk攻击有一个数组，依次记录受到攻击次数，元素次数。。。
    # 剧变反应算谁的精通就记在谁身上
    # 冻结时长序列，总冻结时长
    def stat(self):
        stat = self.name
        stat += '：\n'
        for i in range(self.monitor.attack_num):
            if self.monitor.atk_set[i].is_active:
                stat += self.stat_attack_log(i)
                stat += '\n'
        pass
        return stat

    def stat_attack_log(self, atk_id):
        string_reaction1 = '，该攻击产生'
        for j in [2, 3, 4, 13, 14, 15, 16, 21, 22, 23, 24, 25, 26]:
            if self.stat_attack[atk_id][j] > 0:
                if string_reaction1 != '，该攻击产生':
                    string_reaction1 += '，'
                string_reaction1 += '%s%d次' % (ELEMENT_REACTION_DICT[j], self.stat_attack[atk_id][j])

        string_reaction2 = '，受到由该攻击触发的'
        for j in [5, 6, 7, 8, 9, 10, 11, 12, 17, 18, 19, 20]:
            if self.stat_attack[atk_id][j] > 0:
                if string_reaction2 != '，受到由该攻击触发的':
                    string_reaction2 += '，'
                string_reaction2 += '%s%d次' % (ELEMENT_REACTION_DICT[j], self.stat_attack[atk_id][j])

        if string_reaction1 == '，该攻击产生':
            string_reaction1 = ''
        if string_reaction2 == '，受到由该攻击触发的':
            string_reaction2 = ''
        string = '受到%s攻击%d次，其中%d次上元素%s%s。' % (self.monitor.atk_set[atk_id].name, self.stat_attack[atk_id][0], self.stat_attack[atk_id][1], string_reaction1, string_reaction2)
        return string

    def burning(self):
        if not self.is_burning:
            return
        if self.element[4] == 0 and self.element[6] == 0:  # 草和激都消耗完
            self.element[7] = 0
        if self.element[7] == 0:    # 燃元素消耗完，把草激元素的衰减速度还回去
            self.burning_finalize()
            return
        # 此时存在燃草
        if self.burning_cd == 0:
            self.burning_cd = 0.25 - 0.001
            self.monitor.log_burning("%s燃烧，由%s触发。" % (self.name, self.burning_source.name))
            em = 0
            if self.burning_fire_cd == 0:
                self.burning_fire_cd = 2 - 0.001
                em = 1
            self.monitor.attack_list.append(attack.Attack('燃烧', '火', element_mass=em, target=self.tgt_id, id=self.burning_source.id, tag='剧变'))


    def burning_finalize(self):
        self.decrease_spd[4] = self.decrease_spd[8]
        self.decrease_spd[6] = self.decrease_spd[9]
        self.is_burning = False
        self.monitor.log_action("%s燃烧结束。" % self.name)
