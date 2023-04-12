import re

from django.core.mail import send_mail

from t9a.models import ListsUnits, UnitsPoints


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
        self.class_as_string = class_name._meta.model_name

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
            self.r[id].pk = f'{self.class_as_string}:{id}'

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
        all_list.sort(key=lambda x: (x.win, x.draw, -x.loose), reverse=True)
        return all_list

    def __str__(self):
        self.stats()
        output = ''
        for id in self.r:
            o = self.class_name.objects.get(id=id)
            output += f"{o} {self.r[id].games} {self.r[id].win}, {self.r[id].result}\n"
        return output


class ListParser:
    def parser(self, list):
        regex = re.finditer('^\s*(\d+)\s+-\s+(.+?)\s*$', list, re.MULTILINE)
        list_group = []
        sum = 0
        for r in regex:
            dupa = {}
            dupa['points'] = int(r.group(1))
            dupa['unit'] = r.group(2)
            dupa['special'] = 200 if re.search('general|battle standard bearer', r.group(2), re.IGNORECASE) else 0
            sum += dupa['points']
            list_group.append(dupa)
        last_regex = re.search('^\s*(\d+)\s*$', list, re.MULTILINE)
        if last_regex:
            if int(last_regex.group(1)) == sum:
                return list_group
            else:
                return []
        else:
            return list_group


class HelpFunctions:
    def count_score(self, points, my, op, scenario):  # function to count score used in Result
        difference = my - op
        fraction = abs(difference / points)
        score = 0
        if fraction <= 0.05:
            score += 10
        elif fraction <= 0.10:
            score += 11
        elif fraction <= 0.20:
            score += 12
        elif fraction <= 0.30:
            score += 13
        elif fraction <= 0.40:
            score += 14
        elif fraction <= 0.50:
            score += 15
        elif fraction <= 0.70:
            score += 16
        else:
            score += 17

        if difference < 0:
            score = 20 - score
        score += 3 * scenario
        return score

    def create_unit_points(self, request, prefix, list_id, result_id):
        unit_point = {}
        for v in request.POST:
            if re.match(f'{prefix}pp-(\d*)', v):
                list_unit_id = int(re.match(f'{prefix}pp-(\d*)', v)[1])
                if not list_unit_id in unit_point:
                    unit_point[list_unit_id] = {}
                unit_point[list_unit_id]['unit_id'] = ListsUnits.objects.get(id=list_unit_id).unit_id
                unit_point[list_unit_id]['points_percentage'] = request.POST[v]
                unit_point[list_unit_id]['points_special'] = False

        for v in request.POST:
            if re.match(f'{prefix}ps-(\d*)', v):
                list_unit_id = int(re.match(f'{prefix}ps-(\d*)', v)[1])
                unit_point[list_unit_id]['points_special'] = True

        for list_unit_id in unit_point:
            UnitsPoints.objects.create(
                points_percentage=unit_point[list_unit_id]['points_percentage'],
                points_special=unit_point[list_unit_id]['points_special'],
                list_unit_id=list_unit_id,
                unit_id=unit_point[list_unit_id]['unit_id'],
                list_id=list_id,
                result_id=result_id,
            )


class SendEmail:
    def send_approval_email(self, recipient, link, recipient_name):
        subject = 'Result for approval in t9a'
        message = f'Hello {recipient_name}!\n\n' \
                  f'You have result to complete follow {link} and do it.\n\n' \
                  f'-- \nTeam t9a.wyniki'
        from_email = 'from@yourdjangoapp.com'
        recipient_list = [recipient]
        send_mail(subject, message, from_email, recipient_list)