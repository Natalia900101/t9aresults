class AttributeDict(dict):
    _slots_ = ()
    _getattr_ = dict.__getitem__
    _setattr_ = dict.__setitem__


class Ranking:
    def __init__(self, class_name):
        self.r = {}
        self.class_name = class_name
        self._stats = False
        self.object = None

    def add(self, id, result, score):
        if not id in self.r:
            self.r[id] = AttributeDict()
            self.r[id].result = []
            self.r[id].score = []
        self.r[id].result.append(result)
        self.r[id].score.append(score)
        return self

    def stats(self):
        if self._stats:
            return self

        for id in self.r:
            self.r[id].games = len(self.r[id].result)
            self.r[id].win = 0
            self.r[id].draw = 0
            self.r[id].loose = 0
            for r in self.r[id].result:
                self.r[id].win += 1 if r == 1 else 0
                self.r[id].draw += 1 if r == 0 else 0
                self.r[id].loose += 1 if r == -1 else 0
            self.r[id].sum = 0
            for s in self.r[id].score:
                self.r[id].sum += s
            self.r[id].avg = self.r[id].sum / self.r[id].games if self.r[id].games > 0 else 1

        self._stats = True
        return self

    def get_list(self):
        self.stats()
        all = self.class_name.objects.all()
        all_map = {}
        for a in all:
            all_map[a.id] = a
        all_list = []
        for id in self.r:
            self.r[id].object = all_map[id]
            all_list.append(self.r[id])
        return all_list

    def __str__(self):
        self.stats()
        output = ''
        for id in self.r:
            o = self.class_name.objects.get(id=id)
            output += f"{o} {self.r[id].games} {self.r[id].win}, {self.r[id].result}\n"
        return output
