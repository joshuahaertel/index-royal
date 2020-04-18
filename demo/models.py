from typing import List
from uuid import uuid4

from django.db import models


class Demo(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4)
    state = models.CharField(max_length=7, choices=(
        ('wait', 'Wait'),
        ('play', 'Play'),
        ('index', 'Index'),
        ('over', 'Over'),
    ))
    current_batch = models.PositiveSmallIntegerField(default=0)
    current_entry = models.PositiveSmallIntegerField(default=0)
    current_field = models.PositiveSmallIntegerField(default=0)
    competing = models.CharField(default=False)

    def __init__(self, *args, batches=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.batches: List[Batch] = batches or []


class Batch:
    def __init__(self, entries=None, images=None):
        self.entries: List[Entry] = entries or []
        self.images: List[str] = images or []


class Entry:
    def __init__(self, fields=None):
        self.fields: List[Field] = fields or []


class Field:
    def __init__(self, label, value=None):
        self.label: str = label
        self.value: str = value


class Team(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4)
    demo = models.ForeignKey(Demo, models.CASCADE)
    name = models.CharField(max_length=63)


class BasePlayer(models.Model):
    points = models.SmallIntegerField(default=0)
    team = models.ForeignKey(Team, models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=63)

    class Meta:
        abstract = True


class Player(BasePlayer, models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4)
    demo = models.ForeignKey(Demo, models.CASCADE)


class Admin(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4)
    demo = models.OneToOneField(Demo, models.CASCADE)


class PlayingAdmin(Admin, BasePlayer):
    pass
