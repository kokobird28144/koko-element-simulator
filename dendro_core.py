from attack import Attack


class DendroCore:
    
    def __init__(self, count, source, tgt, dcm):
        self.name = dcm.dc_prefix + str(count)
        self.life = dcm.dc_life
        self.parent = tgt
        self.source = source


class DCManager:

    def __init__(self, monitor):
        self.dc_count = 0
        self.dc_list: list[DendroCore] = []
        self.monitor = monitor
        self.dc_life = 6.0
        self.dc_prefix = '草原核'
        if monitor.nilou:
            self.dc_life = 0.85
            self.dc_prefix = '丰穰之核'

    def clear(self):
        self.dc_count = 0
        self.dc_list = []

    def new_dc(self, source, tgt):
        self.dc_count += 1
        self.dc_list.append(DendroCore(self.dc_count, source, tgt, dcm=self))
        if len(self.dc_list) > 5:
            self.core_bloom(0, 0)

    def time_advance(self, dt):
        if len(self.dc_list) == 0:
            return
        for dc in self.dc_list:
            dc.life -= dt
        self.check_life()

    def check_life(self):
        if len(self.dc_list) == 0:
            return
        while self.dc_list[0].life < 0:
            self.core_bloom(0, 0)
            if len(self.dc_list) == 0:
                break

    def core_reaction(self, tgt, atk):
        if len(self.dc_list) == 0:
            return
        if self.monitor.nilou:
            return
        for i in range(len(self.dc_list)).__reversed__():
            if self.dc_list[i].parent == tgt:
                if atk.element == '雷':
                    self.core_bloom(i, 1, atk)
                elif atk.element == '火':
                    self.core_bloom(i, 2, atk)

    def core_bloom(self, core_id, method, trigger=None):
        core = self.dc_list.pop(core_id)
        if method == 0:  # 普通绽放
            self.monitor.log_action("由%s产生的%s绽放" % (core.source.name, core.name))
            self.monitor.attack_list.append(Attack('绽放', '草', id=core.source.id, target=2, tag='剧变'))
        elif method == 1:  # 超绽放
            self.monitor.log_action("%s超绽放，由%s触发，目标为%s" % (core.name, trigger.name, core.parent.name))
            self.monitor.attack_list.append(Attack('超绽放', '草', id=trigger.id, target=core.parent.tgt_id, tag='剧变'))
        elif method == 2:  # 烈绽放
            self.monitor.log_action("%s烈绽放，由%s触发" % (core.name, trigger.name))
            self.monitor.attack_list.append(Attack('烈绽放', '草', id=trigger.id, target=2, tag='剧变'))
        core.parent.coordinate('nahida')

