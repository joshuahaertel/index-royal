from typing import List
from uuid import uuid4

from django.db import models
from django.db.models import Sum, Avg


class Demo(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4)
    state = models.CharField(max_length=7, default='wait', choices=(
        ('wait', 'Wait'),
        ('play', 'Play'),
        ('index', 'Index'),
        ('over', 'Over'),
    ))
    current_batch = models.PositiveSmallIntegerField(default=0)
    current_entry = models.PositiveSmallIntegerField(default=0)
    current_field = models.PositiveSmallIntegerField(default=0)

    def __init__(self, *args, batches=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.batches: List[Batch] = batches or [DEFAULT_BATCH]

    @property
    def current_images(self):
        if self.state in {'wait', 'over'}:
            return ()
        return self._current_batch.images

    @property
    def _current_batch(self):
        return self.batches[self.current_batch]

    @property
    def current_label(self):
        if self.state in {'wait', 'over'}:
            return ()
        entry = self._current_batch.entries[self.current_entry]
        return entry.fields[self.current_field].label

    @property
    def teams_in_winning_order(self):
        return self.team_set.annotate(
            average_points=Avg('player__points')
        ).order_by('-average_points')


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


DEFAULT_BATCH = Batch(
    entries=[Entry(
        fields=[
            Field('name', 'josh'),
            Field('day', '7'),
        ]
    )],
    images=[
        'demo/test-1.png',
        'demo/test-2.png',
    ],
)


class Team(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4)
    demo = models.ForeignKey(Demo, models.CASCADE)
    name = models.CharField(max_length=63)

    @property
    def points(self):
        return self.player_set.aggregate(Sum('points'))['points__sum']


class BasePlayer(models.Model):
    points = models.SmallIntegerField(default=0)
    team = models.ForeignKey(Team, models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=63)
    skill_level = models.CharField(default='beg', max_length=3, choices=(
        ('beg', 'Beginner'),
        ('int', 'Intermediate'),
        ('adv', 'Advanced'),
    ))

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
