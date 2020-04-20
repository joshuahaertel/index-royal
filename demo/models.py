from typing import List
from uuid import uuid4

from django.db import models
from django.db.models import Sum, Avg, Count
from django.utils.functional import cached_property


class Demo(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4)
    state = models.CharField(max_length=7, default='wait', choices=(
        ('wait', 'Wait'),
        ('race', 'Race'),
        ('over', 'Over'),
    ))
    current_batch_index = models.PositiveSmallIntegerField(default=0)
    current_entry_index = models.PositiveSmallIntegerField(default=0)
    current_field_index = models.PositiveSmallIntegerField(default=0)

    def __init__(self, *args, batches=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.batches: List[Batch] = batches or [DEFAULT_BATCH]

    @property
    def current_images(self):
        return self.current_batch.images

    @property
    def current_batch(self):
        return self.batches[self.current_batch_index]

    @property
    def max_batch_index(self):
        return len(self.batches) - 1

    @property
    def current_batch_max_entry_index(self):
        return len(self.current_batch.entries) - 1

    @property
    def current_entry_max_field_index(self):
        return len(self.current_entry.fields) - 1

    @property
    def current_label(self):
        entry = self.current_entry
        return entry.fields[self.current_field_index].label

    @property
    def current_entry(self):
        return self.current_batch.entries[self.current_entry_index]

    @cached_property
    def teams_in_winning_order(self):
        return self.team_set.annotate(
            average_points=Avg('player__points'),
            total_players=Count('player'),
        ).order_by('-average_points')

    @cached_property
    def teamless_players(self):
        return self.player_set.filter(team=None)

    @property
    def teamless_players_average_points(self):
        if not self.teamless_players:
            return 0.0
        points = sum(player.points for player in self.teamless_players)
        return points/len(self.teamless_players)

    @property
    def can_wait(self):
        return self.state != 'wait'

    @property
    def can_race(self):
        return self.state == 'wait'

    @property
    def can_finish(self):
        return self.state == 'wait'


class Batch:
    def __init__(self, entries=None, images=None, name=''):
        self.entries: List[Entry] = entries or []
        self.images: List[str] = images or []
        self.name: str = name


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
            Field('Name', 'josh'),
            Field('Day', '7'),
        ]
    )],
    images=[
        'demo/test-1.png',
        'demo/test-2.png',
    ],
    name='Example',
)


class Team(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4)
    demo = models.ForeignKey(Demo, models.CASCADE)
    name = models.CharField(max_length=63)

    @property
    def points(self):
        return self.player_set.aggregate(Sum('points'))['points__sum']

    @cached_property
    def players_in_best_order(self):
        return self.player_set.all().order_by('-points')


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
