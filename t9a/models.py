from django.db import models
from django.contrib.auth.models import User


class UserRenamed(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    old_username = models.CharField(max_length=128, null=True)
    new_username = models.CharField(max_length=128, null=True)


class Deployments(models.Model):
    name = models.CharField(max_length=256)

    def __str__(self):
        return f'{self.id}. {self.name}'


class Secondaries(models.Model):
    name = models.CharField(max_length=256)

    def __str__(self):
        return f'{self.id}. {self.name}'


class Army(models.Model):
    name = models.CharField(max_length=16)
    long_name = models.CharField(max_length=256)

    def __str__(self):
        return f'{self.name}'


class Map(models.Model):
    name = models.CharField(max_length=256)

    def __str__(self):
        return f'{self.name}'


class Lists(models.Model):
    owner = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    army = models.ForeignKey('Army', null=True, on_delete=models.SET_NULL)
    list = models.TextField()
    name = models.CharField(max_length=256)
    uses_supplement = models.BooleanField(default=False)

    class Meta:
        ordering = ['army', 'owner', 'name']

    def __str__(self):
        return f'{self.army}, {self.owner}, {self.name}'


class Games(models.Model):
    event_list = [
        (0, 'test'),
        (1, 'grand'),
        (2, 'local'),
        (3, 'league'),
        (4, 'casual')
    ]
    date = models.DateField()
    map = models.ForeignKey('Map', null=True, on_delete=models.SET_NULL)
    deploy = models.ForeignKey('Deployments', null=True, on_delete=models.SET_NULL)
    secondary = models.ForeignKey('Secondaries', null=True, on_delete=models.SET_NULL)
    turns = models.IntegerField()
    event = models.CharField(max_length=256)
    event_type = models.IntegerField(choices=event_list, default=0)
    points_event = models.IntegerField()

    def __str__(self):
        return f'{self.date}, {self.event}'

    def csv_array_header(self):
        return [
            'game_id',
            'date',
            'map',
            'deployment',
            'secondary',
            'turns',
            'event_name',
            'event_type',
            'event_points',
        ]

    def csv_array(self):
        return [
            self.id,
            self.date,
            self.map.name,
            self.deploy.name,
            self.secondary.name,
            self.turns,
            self.event,
            self.get_event_type_display(),
            self.points_event
        ]


class Results(models.Model):
    choice_list = [
        (1, 'win'),
        (0, 'draw'),
        (-1, 'loose')
    ]
    game = models.ForeignKey('Games', null=True, on_delete=models.SET_NULL)
    player = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    secondary = models.IntegerField(choices=choice_list)
    score = models.IntegerField()
    result = models.IntegerField(choices=choice_list)
    list = models.ForeignKey('Lists', null=True, on_delete=models.SET_NULL)
    comment = models.TextField(blank=True)
    points = models.IntegerField()
    approved = models.BooleanField(null=True)
    first = models.BooleanField()

    def __str__(self):
        return f'{self.game.date}, {self.game.id}, {self.player}'

    def csv_array_header(self):
        return [
            'player',
            'result',
            'score',
            'secondary',
            'points',
            'starting_plyer',
            'army',
            'list',
            'comment',
        ]

    def csv_array(self):
        return [
            self.player,
            self.get_result_display(),
            self.score,
            self.get_secondary_display(),
            self.points,
            self.first,
            self.list.army.name,
            self.list.name,
            self.comment
        ]
