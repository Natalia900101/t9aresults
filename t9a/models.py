from django.db import models


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
        return f'{self.id}. {self.name}'


class Map(models.Model):
    name = models.CharField(max_length=256)

    def __str__(self):
        return f'{self.id}. {self.name}'




