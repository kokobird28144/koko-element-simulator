from attack import Attack
import dendro_core
import target
import numpy as np
from const import ELEMENT_REACTION_DICT_REV, decrease_speed, swirl_element_mass
import matplotlib.pyplot as plt

class Monitor:

    def __init__(self, main):  # bs short for basic setting
        bs = main.basic_setting
        self.atk_set = main.attack_setting
        self.log_place = main.log_place
        self.info_place = main.info_place

        self.time = 0
        self.dt = bs.dt
        self.max_time = bs.max_time
        self.attack_num = bs.attack_num

        self.flag_log_apply = bs.log_apply
        self.flag_log_quicken = bs.log_quicken
        self.flag_log_burning = bs.log_burning
        self.log = ''
        self.nilou = bs.nilou
        self.dcm = dendro_core.DCManager(self)
        self.flag_froze = bs.flag_froze
        self.single_target = bs.single_target

        self.steps = int(bs.max_time / self.dt)
        self.attack_list: list[Attack] = []
        if self.single_target:
            self.target_list = [target.Target(self, i) for i in range(1)]
        else:
            self.target_list = [target.Target(self, i) for i in range(2)]

    def simulate(self):
        sim_flag = False
        for atk_s in self.atk_set:
            if atk_s.is_active:
                sim_flag = True
                break
        if not sim_flag:
            return False

        for tgt in self.target_list:
            for a in range(self.attack_num):
                tgt.stat_attack.append([0 for _ in range(27)])
                if self.atk_set[a].attack_mode == '草神协同':
                    tgt.coordinate_nahida_list.append(a)
                elif self.atk_set[a].attack_mode == '雷神协同':
                    tgt.coordinate_shogun_list.append(a)
                elif self.atk_set[a].attack_mode == '阿贝多协同':
                    tgt.coordinate_albedo_list.append(a)

        self.log_basic('---模拟过程---\n')

        for _ in range(self.steps):
            # deal with each attack
            for atk_s in self.atk_set:
                if atk_s.attack_mode == '定时触发':
                    atk = atk_s.generate_attack(self.time)
                    if atk is not None:
                        self.attack_list.append(atk)
                        self.process_attack()

            # element decrease
            for tgt in self.target_list:
                tgt.time_advance(self.dt)

            # cd decrease
            for a in self.atk_set:
                a.time_advance(self.dt)

            # dendro-core life
            self.dcm.time_advance(self.dt)

            self.process_attack()  # 处理协同
            # 协同之后可能还需要继续check，比如产生了新的草原核？

            # time advance
            self.time += self.dt

        if not self.single_target:
            self.log_basic(self.target_list[1].stat(), prev=True)
        self.log_basic(self.target_list[0].stat(), prev=True)
        self.log_basic('---结果统计---\n', prev=True)

        self.log_place.SetLabel(self.log)

        return True

    def process_attack(self):
        while len(self.attack_list) > 0:
            atk = self.attack_list.pop(0)
            atk_elem = atk.element_mass  # 暂存一下，后续atk.element_mass会变

            # 对atk的每个tgt id判断一次
            tgt_list = [0]
            if atk.target == 1:
                tgt_list = [1]
            elif atk.target == 2:
                tgt_list = [0, 1]

            for tgt_id in tgt_list:
                if self.single_target and tgt_id == 1:
                    continue
                tgt = self.target_list[tgt_id]
                atk.element_mass = atk_elem

                if atk.tag == '剧变':  # 剧变额外攻击记录
                    tgt.stat_attack[atk.id][ELEMENT_REACTION_DICT_REV[atk.name]] += 1

                # 岩击碎冰，目前没有剧变可以造成岩攻击，可以先放着
                if atk.element == '岩' and tgt.element[5] > 0:
                    tgt.element[5] = 0
                    self.log_action("%s使得%s碎冰，%s" % (atk.name, tgt.name, self.target_list[0].log_element_change()))
                    self.attack_list.append(Attack('碎冰', id=atk.id, target=tgt_id, tag='剧变'))
                    tgt.coordinate('nahida')  # 碎冰可以触发草神吗？

                if atk.element_mass > 0:
                    # 如果带元素
                    self.reaction(tgt, atk)
                    if atk.tag == '角色':
                        tgt.stat_attack[atk.id][1] += 1  # 记录一次元素攻击

                if atk.tag == '角色':
                    tgt.stat_attack[atk.id][0] += 1  # 记录一次攻击
                    # 超烈绽放
                    if atk.element == '火' or atk.element == '雷':
                        self.dcm.core_reaction(self.target_list[0], atk)

                # 除了感电和燃烧都能触发雷神协同
                if atk.name != '感电' and atk.name != '燃烧':
                    tgt.coordinate('shogun')

                # 所有类型伤害都能触发的阿贝多受击协同
                tgt.coordinate('albedo')
            pass  # for t in tgt_list
        pass

    def plot(self):
        # fig = plt.gcf() or plt.figure()
        t = np.linspace(0, self.max_time, self.steps + 1)

        fig_num_list = plt.get_fignums()
        # 判断是否存在fig对象
        if fig_num_list:
            # 如果存在，则获取当前的fig对象
            fig = plt.figure(fig_num_list[0])
        else:
            # 如果不存在，则创建一个新的fig对象
            fig = plt.figure()

        if self.single_target:
            ax = plt.subplot()
            self.target_list[0].print_element_hist(t, ax)
        else:
            ax1 = plt.subplot(2, 1, 1)
            ax2 = plt.subplot(2, 1, 2)
            self.target_list[0].print_element_hist(t, ax1)
            self.target_list[1].print_element_hist(t, ax2)
            plt.subplots_adjust(hspace=0.4)

        # ax = fig.gca()

        plt.show()
    def log_basic(self, info, prev=False):
        # self.log_place.SetLabel(self.log_place.GetLabel()+info)
        if prev:
            self.log = info + self.log
        else:
            self.log += info

    def log_action(self, info):
        self.log_basic("(%.2fs)%s\n" % (self.time, info))

    def log_apply(self, info):
        if self.flag_log_apply:
            self.log_action(info)

    def log_quicken(self, info):
        if self.flag_log_quicken:
            self.log_action(info)

    def log_burning(self, info):
        if self.flag_log_burning:
            self.log_action(info)

    def reaction(self, tgt, atk):
        reaction_flag = True

        if atk.element == '水':  # 水攻击
            if tgt.element[1] > 0 or tgt.element[7] > 0:  # 目标有火元素附着
                self.reaction_vaporize(tgt, atk)
                if atk.element_mass > 0.01 and (tgt.element[4] > 0 or tgt.element[6] > 0):  # 草元素或激元素
                    self.reaction_bloom(tgt, atk)
            elif tgt.element[2] > 0:  # 目标有冰元素附着，冻结
                self.reaction_froze(tgt, atk)
                if (tgt.element[4] > 0 or tgt.element[6] > 0) and atk.element_mass > 0.01:  # 水过量，且有激草
                    self.reaction_bloom(tgt, atk)

            elif tgt.element[4] > 0 or tgt.element[6] > 0:  # 草元素或激元素
                self.reaction_bloom(tgt, atk)

                if atk.element_mass > 0.01 and tgt.element[3] > 0:  # 水过量，强制触发一次感电，不进行附着
                    if tgt.electro_charged_cd == 0:
                        self.log_action("%s特殊感电，由%s触发。" % (tgt.name, atk.name))
                        # tgt.stat_attack[atk.id][6] += 1
                        self.attack_list.append(Attack('感电', '雷', id=atk.id, tag='剧变'))
                        tgt.electro_charged_cd = 1

            elif tgt.element[0] > 0:  # 目标有水附着
                if atk.element_mass * 0.8 > tgt.element[0]:
                    tgt.element[0] = atk.element_mass * 0.8
                    tgt.electro_charged_source = atk
                    self.log_apply("%s刷新%s的水元素量，%s" % (atk.name, tgt.name, tgt.log_element_change()))
                reaction_flag = False

            else:  # 目标无附着，造成水元素附着，计算衰减速度
                tgt.element[0] = atk.element_mass * 0.8
                tgt.decrease_spd[0] = decrease_speed(atk.element, atk.element_mass)
                tgt.electro_charged_source = atk  # 刷新感电精通来源
                self.log_apply("%s对%s造成水元素附着，%s" % (atk.name, tgt.name, tgt.log_element_change()))
                reaction_flag = False
                # tgt.electro_charge()  # 可能产生感电

            if reaction_flag:
                tgt.coordinate('nahida')

        elif atk.element == '火':  # 火
            if tgt.element[3] > 0:  # 目标有雷附着，超载
                self.reaction_overload(tgt, atk)
                if atk.element_mass > 0.01:  # 过量火
                    if tgt.element[0] > 0:  # 过量火继续蒸发
                        self.reaction_vaporize(tgt, atk)
                    elif tgt.element[6] > 0:  #激雷共存，过量火启动燃烧，之前肯定没有燃
                        self.reaction_burning(tgt, atk)

            elif tgt.element[2] > 0 or tgt.element[5] > 0:  # 目标有冰或冻附着，融化
                self.reaction_melt(tgt, atk)
                if atk.element_mass > 0 and (tgt.element[4] or tgt.element[6]) > 0:  # 过量火燃烧
                    self.reaction_burning(tgt, atk)

            elif tgt.element[0] > 0:  # 目标有水附着
                self.reaction_vaporize(tgt, atk)

            elif tgt.element[1] > 0:  # 目标有火附着
                if atk.element_mass * 0.8 > tgt.element[1]:
                    tgt.element[1] = atk.element_mass * 0.8
                    tgt.decrease_spd[1] = decrease_speed(atk.element, atk.element_mass)  # 3.0后衰减速度也覆盖
                    if atk.name != '燃烧' or atk.tag != '剧变':
                        tgt.burning_source = atk  # 刷新来源
                    self.log_apply("%s刷新%s的火元素量，%s" % (atk.name, tgt.name, tgt.log_element_change()))
                reaction_flag = False

            else:  # 目标无附着，造成火元素附着，计算衰减速度
                tgt.element[1] = atk.element_mass * 0.8
                tgt.decrease_spd[1] = decrease_speed(atk.element, atk.element_mass)
                tgt.burning_source = atk  # 刷新来源
                self.log_apply("%s对%s造成火元素附着，%s" % (atk.name, tgt.name, tgt.log_element_change()))
                reaction_flag = False

            if tgt.element[1] > 0 and (tgt.element[4] > 0 or tgt.element[6] > 0):  # 目标有草或者激附着
                if tgt.element[7] == 0:  # 启动燃烧
                    self.reaction_burning(tgt, atk)
                    reaction_flag = True

            if reaction_flag:
                tgt.coordinate('nahida')

        elif atk.element == '风':  # 风
            self.reaction_swirl(tgt, atk)

        elif atk.element == '雷':  # 雷
            quicken_flag = False
            if tgt.element[6] > 0:  # 超激化
                tgt.stat_attack[atk.id][14] += 1
                self.log_quicken("%s在%s触发超激化" % (atk.name, tgt.name))
                quicken_flag = True

            if tgt.element[1] > 0 or tgt.element[7] > 0:  # 目标有火附着，超载
                self.reaction_overload(tgt, atk)
                if atk.element_mass > 0.01 and tgt.element[4] > 0:
                    self.reaction_quicken(tgt, atk)

            elif tgt.element[2] > 0 or tgt.element[5] > 0:  # 目标有冰附着或冻附着，超导，先消耗藏冰
                self.reaction_superconduct(tgt, atk)
                if tgt.element[4] > 0 and atk.element_mass > 0.01:  # 过量雷和草激化
                    self.reaction_quicken(tgt, atk)

            elif tgt.element[4] > 0:  # 原激化
                self.reaction_quicken(tgt, atk)

            elif tgt.element[3] > 0:  # 目标有雷附着
                if atk.element_mass * 0.8 > tgt.element[3]:
                    tgt.element[3] = atk.element_mass * 0.8
                    tgt.electro_charged_source = atk
                    self.log_apply("%s刷新%s的雷元素量，%s" % (atk.name, tgt.name, tgt.log_element_change()))
                reaction_flag = False

            else:  # 目标无附着或水附着，造成雷元素附着，计算衰减速度
                tgt.element[3] = atk.element_mass * 0.8
                tgt.decrease_spd[3] = decrease_speed(atk.element, atk.element_mass)
                tgt.electro_charged_source = atk
                self.log_apply("%s对%s造成雷元素附着，%s" % (atk.name, tgt.name, tgt.log_element_change()))
                # tgt.electro_charge()
                reaction_flag = False

            if quicken_flag or reaction_flag:
                tgt.coordinate('nahida')
            pass

        elif atk.element == '草':  # 草
            quicken_flag = False
            if tgt.element[6] > 0:  # 蔓激化
                tgt.stat_attack[atk.id][15] += 1
                self.log_quicken("%s在%s触发蔓激化" % (atk.name, tgt.name))
                quicken_flag = True

            if tgt.element[3] > 0:  # 原激化
                self.reaction_quicken(tgt, atk)

                if atk.element_mass > 0.01 and tgt.element[0] > 0:  # 草过量，继续和水反应
                    self.reaction_bloom(tgt, atk)

                if tgt.element[0] > 0:  # 激元素和多余的水反应，将激元素量作为攻击的元素量，代入这一次的草攻击计算
                    atk.element_mass = tgt.element[6]
                    self.reaction_bloom(tgt, atk, self_reaction=True)

            elif tgt.element[0] > 0:  # 绽放
                self.reaction_bloom(tgt, atk)

            elif tgt.element[4] > 0:  # 刷新草量
                if atk.element_mass * 0.8 > tgt.element[4]:
                    tgt.element[4] = atk.element_mass * 0.8
                    self.log_apply("%s刷新%s的草元素量，%s" % (atk.name, tgt.name, tgt.log_element_change()))
                    tgt.burning_source = atk
                reaction_flag = False

            else:  # 草附着
                tgt.element[4] = atk.element_mass * 0.8
                if tgt.element[7] == 0:
                    tgt.decrease_spd[4] = decrease_speed(atk.element, atk.element_mass)
                else:  # 燃烧时衰减速度先存到8号位
                    tgt.decrease_spd[8] = decrease_speed(atk.element, atk.element_mass)
                tgt.burning_source = atk
                self.log_apply("%s对%s造成草元素附着，%s" % (atk.name, tgt.name, tgt.log_element_change()))
                reaction_flag = False

            if (tgt.element[4] > 0 or tgt.element[6] > 0) and tgt.element[1] > 0:  # 目标有火附着
                if tgt.element[7] == 0:  # 启动燃烧
                    self.reaction_burning(tgt, atk)
                    reaction_flag = True

            if quicken_flag or reaction_flag:
                tgt.coordinate('nahida')

        elif atk.element == '冰':  # 冰
            if tgt.element[3] > 0:  # 目标有雷附着，超导
                self.reaction_superconduct(tgt, atk)

                if atk.element_mass > 0 and tgt.element[0] > 0:  # 过量冰继续冻结
                    self.reaction_froze(tgt, atk)

            elif tgt.element[1] > 0 or tgt.element[7] > 0:  # 目标有火附着，融化
                self.reaction_melt(tgt, atk)

            elif tgt.element[0] > 0:  # 目标有水附着，冻结
                self.reaction_froze(tgt, atk)

            elif tgt.element[2] > 0:  # 目标有冰附着，判断是否覆盖
                if atk.element_mass * 0.8 > tgt.element[2]:
                    tgt.element[2] = atk.element_mass * 0.8
                    self.log_apply("%s刷新%s的冰元素量，%s" % (atk.name, tgt.name, tgt.log_element_change()))
                reaction_flag = False
            else:  # 目标无附着，造成冰元素附着，计算衰减速度
                tgt.element[2] = atk.element_mass * 0.8
                tgt.decrease_spd[2] = decrease_speed(atk.element, atk.element_mass)
                self.log_apply("%s对%s造成冰元素附着，%s" % (atk.name, tgt.name, tgt.log_element_change()))
                reaction_flag = False

            if reaction_flag:
                tgt.coordinate('nahida')
            pass

        elif atk.element == '岩':  # 岩
            self.reaction_crystallize(tgt, atk)

    def reaction_froze(self, tgt, atk):
        quant = 0
        if atk.element == '冰':
            quant = min(tgt.element[0], atk.element_mass)  # 反应量是两元素中较少的
            tgt.element[0] = max(0, tgt.element[0] - quant)
        if atk.element == '水':
            quant = min(tgt.element[2], atk.element_mass)  # 反应量是两元素中较少的
            tgt.element[2] = max(0, tgt.element[2] - quant)

        atk.element_mass -= quant
        if self.flag_froze:
            tgt.element[5] = max(tgt.element[5], 2 * quant)

        tgt.stat_attack[atk.id][3] += 1
        self.log_action("%s对%s造成冻结，%s" % (atk.name, tgt.name, tgt.log_element_change()))
        return quant

    def reaction_quicken(self, tgt, atk):
        quant = 0
        if atk.element == '雷':
            quant = min(tgt.element[4], atk.element_mass)
            tgt.element[4] = max(0, tgt.element[4] - quant)
        elif atk.element == '草':
            quant = min(tgt.element[3], atk.element_mass)
            tgt.element[3] = max(0, tgt.element[3] - quant)

        atk.element_mass -= quant
        if quant > tgt.element[6]:  # 覆盖，速度一同覆盖
            tgt.element[6] = quant
            tgt.decrease_spd[6] = decrease_speed('激', quant)

        tgt.stat_attack[atk.id][13] += 1
        self.log_action("%s在%s触发原激化，%s" % (atk.name, tgt.name, tgt.log_element_change()))

    def reaction_bloom(self, tgt, atk, self_reaction=False):
        quant = 0
        if atk.element == '水':
            quant = min(atk.element_mass, max(tgt.element[4], tgt.element[6]) * 2)
            tgt.element[4] = max(0, tgt.element[4] - atk.element_mass / 2)
            tgt.element[6] = max(0, tgt.element[6] - atk.element_mass / 2)
        elif atk.element == '草':
            quant = min(atk.element_mass, tgt.element[0] / 2)
            tgt.element[0] = max(0, tgt.element[0] - atk.element_mass * 2)

        atk.element_mass -= quant
        if self_reaction:
            tgt.element[6] = atk.element_mass  # 仅在草+水雷中使用

        tgt.stat_attack[atk.id][16] += 1
        self.log_action("%s在%s触发绽放产生草核%d，%s" % (atk.name, tgt.name, self.dcm.dc_count+1, tgt.log_element_change()))
        self.dcm.new_dc(atk, tgt)

    def reaction_melt(self, tgt, atk):
        if atk.element == '冰':
            tgt.element[1] = max(0, tgt.element[1] - atk.element_mass / 2)
            tgt.element[7] = max(0, tgt.element[7] - atk.element_mass / 2)
        elif atk.element == '火':
            tgt.element[2] = max(0, tgt.element[2] - atk.element_mass * 2)
            tgt.element[5] = max(0, tgt.element[5] - atk.element_mass * 2)

        tgt.stat_attack[atk.id][4] += 1
        self.log_action("%s在%s发生融化，%s" % (atk.name, tgt.name, tgt.log_element_change()))
        if tgt.is_burning and tgt.element[7] == 0:
            tgt.burning_finalize()

    def reaction_vaporize(self, tgt, atk):
        quant = 0
        if atk.element == '水':
            if tgt.element[1] > tgt.element[7]:
                quant = min(atk.element_mass, tgt.element[1] / 2)
                tgt.element[1] = max(0, tgt.element[1] - atk.element_mass * 2)
                tgt.element[7] = max(0, tgt.element[7] - quant * 2)
            else:
                quant = min(atk.element_mass, tgt.element[7] / 2)
                tgt.element[1] = max(0, tgt.element[1] - quant * 2)
                tgt.element[7] = max(0, tgt.element[7] - atk.element_mass * 2)
        if atk.element == '火':
            quant = min(atk.element_mass, tgt.element[0] * 2)
            tgt.element[0] = max(0, tgt.element[0] - atk.element_mass / 2)

        atk.element_mass -= quant
        tgt.stat_attack[atk.id][2] += 1
        self.log_action("%s在%s发生蒸发，%s" % (atk.name, tgt.name, tgt.log_element_change()))
        if tgt.is_burning and tgt.element[7] == 0:
            tgt.burning_finalize()

    def reaction_overload(self, tgt, atk):
        quant = 0
        if atk.element == '雷':
            if tgt.element[1] > tgt.element[7]:
                quant = min(atk.element_mass, tgt.element[1])
                tgt.element[1] = max(0, tgt.element[1] - atk.element_mass)
                tgt.element[7] = max(0, tgt.element[7] - quant)
            else:
                quant = min(atk.element_mass, tgt.element[7])
                tgt.element[1] = max(0, tgt.element[1] - quant)
                tgt.element[7] = max(0, tgt.element[7] - atk.element_mass)
        elif atk.element == '火':
            quant = min(atk.element_mass, tgt.element[3])
            tgt.element[3] = max(0, tgt.element[3] - atk.element_mass)

        atk.element_mass -= quant
        self.attack_list.append(Attack(name='超载', element='火', target=2, id=atk.id, tag='剧变'))
        # tgt.stat_attack[atk.id][7] += 1
        self.log_action("%s在%s触发超载，%s" % (atk.name, tgt.name, tgt.log_element_change()))
        if tgt.is_burning and tgt.element[7] == 0:
            tgt.burning_finalize()

    def reaction_superconduct(self, tgt, atk):
        quant = 0
        if atk.element == '雷':
            if tgt.element[5] > 0:  # 冻冰
                if tgt.element[2] > atk.element_mass:  # 藏冰足量
                    quant = atk.element_mass
                    tgt.element[2] -= atk.element_mass
                else:
                    quant = min(atk.element_mass, tgt.element[2] + tgt.element[5])
                    tgt.element[5] = max(0, tgt.element[5] - (atk.element_mass - tgt.element[2]))
                    tgt.element[2] = 0
            else:  # 冰
                quant = min(tgt.element[2], atk.element_mass)
                tgt.element[2] = max(0, tgt.element[2] - atk.element_mass)

        elif atk.element == '冰':
            quant = min(atk.element_mass, tgt.element[3])
            tgt.element[3] = max(0, tgt.element[3] - atk.element_mass)

        atk.element_mass -= quant
        self.attack_list.append(Attack(name='超导', element='冰', target=2, id=atk.id, tag='剧变'))
        # tgt.stat_attack[atk.id][5] += 1
        self.log_action("%s在%s触发超导，%s" % (atk.name, tgt.name, tgt.log_element_change()))

    def reaction_burning(self, tgt, atk):
        tgt.element[7] = 2  # 产生2单位燃元素
        tgt.burning_cd = 0.35  # 首次启动时加0.1秒
        tgt.decrease_spd[8] = tgt.decrease_spd[4]  # 8号暂存草消耗速度
        tgt.decrease_spd[9] = tgt.decrease_spd[6]  # 9号暂存激消耗速度
        tgt.decrease_spd[4] = 0.4  # 草元素固定消耗速度
        tgt.decrease_spd[6] = 0.4
        tgt.burning_source = atk
        tgt.is_burning = True
        self.log_action("%s在%s启动燃烧，%s" % (atk.name, tgt.name, tgt.log_element_change()))
        # tgt.coordinate('nahida')

    def reaction_swirl(self, tgt, atk):
        reaction_flag = False
        em = 0
        if tgt.element[3] > 0:
            reaction_flag = True
            em = swirl_element_mass(atk.element_mass, tgt.element[3])
            quant = min(atk.element_mass, tgt.element[3] * 2)
            tgt.element[3] = max(0, tgt.element[3] - quant / 2)
            atk.element_mass -= quant
            self.attack_list.append(Attack(name='雷扩散', element='雷', element_mass=em, target=1-tgt.tgt_id, id=atk.id, tag='剧变'))
            self.attack_list.append(Attack(name='雷扩散', element='雷', target=tgt.tgt_id, id=atk.id, tag='剧变'))
            self.log_action("%s在%s触发雷扩散，%s" % (atk.name, tgt.name, tgt.log_element_change()))

        if (tgt.element[1] > 0 or tgt.element[7] > 0) and atk.element_mass > 0.01:
            reaction_flag = True
            major = max(tgt.element[1], tgt.element[7])
            em = swirl_element_mass(atk.element_mass, major)
            quant = min(atk.element_mass, major * 2)
            tgt.element[1] = max(0, tgt.element[1] - quant / 2)
            tgt.element[7] = max(0, tgt.element[7] - quant / 2)
            atk.element_mass -= quant
            self.attack_list.append(Attack(name='火扩散', element='火', element_mass=em, target=1-tgt.tgt_id, id=atk.id, tag='剧变'))
            self.attack_list.append(Attack(name='火扩散', element='火', target=tgt.tgt_id, id=atk.id, tag='剧变'))
            self.log_action("%s在%s触发火扩散，%s" % (atk.name, tgt.name, tgt.log_element_change()))
            if tgt.is_burning and tgt.element[7] == 0:
                tgt.burning_finalize()

        if tgt.element[0] > 0 and atk.element_mass > 0.01:
            reaction_flag = True
            em = swirl_element_mass(atk.element_mass, tgt.element[0])
            quant = min(atk.element_mass, tgt.element[0] * 2)
            tgt.element[0] = max(0, tgt.element[0] - quant / 2)
            atk.element_mass -= quant
            self.attack_list.append(Attack(name='水扩散', element='水', element_mass=em, target=1-tgt.tgt_id, id=atk.id, tag='剧变'))
            self.attack_list.append(Attack(name='水扩散', element='水', target=tgt.tgt_id, id=atk.id, tag='剧变'))
            self.log_action("%s在%s触发水扩散，%s" % (atk.name, tgt.name, tgt.log_element_change()))

        if tgt.element[2] > 0 and atk.element_mass > 0.01:
            reaction_flag = True
            em = swirl_element_mass(atk.element_mass, tgt.element[2])
            quant = min(atk.element_mass, tgt.element[2] * 2)
            tgt.element[2] = max(0, tgt.element[2] - quant / 2)
            atk.element_mass -= quant
            self.attack_list.append(Attack(name='冰扩散', element='冰', element_mass=em, target=1-tgt.tgt_id, id=atk.id, tag='剧变'))
            self.attack_list.append(Attack(name='冰扩散', element='冰', target=tgt.tgt_id, id=atk.id, tag='剧变'))
            self.log_action("%s在%s触发冰扩散，%s" % (atk.name, tgt.name, tgt.log_element_change()))

        if tgt.element[5] > 0 and atk.element_mass > 0.01:
            reaction_flag = True
            em = swirl_element_mass(atk.element_mass, tgt.element[5])
            quant = min(atk.element_mass, tgt.element[5] * 2)
            tgt.element[5] = max(0, tgt.element[5] - quant / 2)
            atk.element_mass -= quant
            self.attack_list.append(Attack(name='冻扩散', element='冰', element_mass=em, target=1-tgt.tgt_id, id=atk.id, tag='剧变'))
            self.attack_list.append(Attack(name='冻扩散', element='冰', target=tgt.tgt_id, id=atk.id, tag='剧变'))
            self.log_action("%s在%s触发冻扩散，%s" % (atk.name, tgt.name, tgt.log_element_change()))

        if reaction_flag:
            tgt.coordinate('nahida')

    def reaction_crystallize(self, tgt, atk):
        reaction_flag = False
        if tgt.geo_cd > 0:
            return

        if tgt.element[3] > 0:
            reaction_flag = True
            quant = min(atk.element_mass, tgt.element[3] * 2)
            tgt.element[3] = max(0, tgt.element[3] - quant / 2)
            atk.element_mass -= quant
            tgt.stat_attack[atk.id][23] += 1
            self.log_action("%s在%s触发雷结晶，%s" % (atk.name, tgt.name, tgt.log_element_change()))

        elif (tgt.element[1] > 0 or tgt.element[7] > 0) and atk.element_mass > 0.01:
            reaction_flag = True
            major = max(tgt.element[1], tgt.element[7])
            quant = min(atk.element_mass, major * 2)
            tgt.element[1] = max(0, tgt.element[1] - quant / 2)
            tgt.element[7] = max(0, tgt.element[7] - quant / 2)
            atk.element_mass -= quant
            tgt.stat_attack[atk.id][22] += 1
            self.log_action("%s在%s触发火结晶，%s" % (atk.name, tgt.name, tgt.log_element_change()))
            if tgt.is_burning and tgt.element[7] == 0:
                tgt.burning_finalize()

        elif tgt.element[0] > 0 and atk.element_mass > 0.01:
            reaction_flag = True
            quant = min(atk.element_mass, tgt.element[0] * 2)
            tgt.element[0] = max(0, tgt.element[0] - quant / 2)
            atk.element_mass -= quant
            tgt.stat_attack[atk.id][21] += 1
            self.log_action("%s在%s触发水结晶，%s" % (atk.name, tgt.name, tgt.log_element_change()))

        elif tgt.element[2] > 0 and atk.element_mass > 0.01:
            reaction_flag = True
            quant = min(atk.element_mass, tgt.element[2] * 2)
            tgt.element[2] = max(0, tgt.element[2] - quant / 2)
            atk.element_mass -= quant
            tgt.stat_attack[atk.id][24] += 1
            self.log_action("%s在%s触发冰结晶，%s" % (atk.name, tgt.name, tgt.log_element_change()))

        elif tgt.element[5] > 0 and atk.element_mass > 0.01:
            reaction_flag = True
            quant = min(atk.element_mass, tgt.element[5] * 2)
            tgt.element[5] = max(0, tgt.element[5] - quant / 2)
            atk.element_mass -= quant
            tgt.stat_attack[atk.id][25] += 1
            self.log_action("%s在%s触发冻结晶，%s" % (atk.name, tgt.name, tgt.log_element_change()))

        if reaction_flag:
            tgt.geo_cd = 1
            tgt.coordinate('nahida')