import asyncio
from collections import defaultdict
from typing import List
from uuid import uuid4

import aioredis
from asgiref.sync import async_to_sync
from django.db import models
from django.utils.functional import cached_property


class Demo(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4)
    admin_pk = models.UUIDField(default=uuid4)
    state = models.CharField(max_length=7, default='wait', choices=(
        ('pause', 'Pause'),
        ('play', 'Play'),
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
        return async_to_sync(self.get_teams)()

    async def get_teams(self):
        REDIS_POOL = await aioredis.create_redis_pool('redis://localhost')
        player_pks = await REDIS_POOL.smembers(f'demo.players-{self.pk}')
        results = await asyncio.gather(*(
            REDIS_POOL.hmget(
                f'team-{player_pk}', 'team_name', 'points', 'name',
                encoding='utf-8'
            )
            for player_pk in player_pks
        ))
        teams_dict = defaultdict(lambda: {
            'points': 0,
            'players': [],
            'total_players': 0,
        })
        for player_team_name, player_points, player_name in results:
            team = teams_dict[player_team_name]
            team['points'] += player_points
            team['players'].append({
                'name': player_name,
                'points': int(player_points),
            })
            team['total_players'] += 0
        teams_list = []
        for team_name, team_dict in teams_dict.items():
            team_dict['name'] = team_name
            team_dict['average_points'] = (
                    team_dict['points'] / team_dict['total_players']
            )
            team_dict['players'].sort(
                key=lambda player: (player['points'], player['name']),
                reverse=True,
            )
            if not team_name:
                self._team_less_group = team_dict
            else:
                teams_list.append(team_dict)
        teams_list.sort(
            key=lambda team_json: (
                team_json['average_points'], team_json['name']
            ),
            reverse=True,
        )
        return teams_list

    @cached_property
    def teamless_players(self):
        return self._team_less_group

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


class Player(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4)
    points = models.SmallIntegerField(default=0)
    name = models.CharField(max_length=63)
    skill_level = models.CharField(default='beg', max_length=3, choices=(
        ('beg', 'Beginner'),
        ('int', 'Intermediate'),
        ('adv', 'Advanced'),
    ))
    team = models.CharField(max_length=63)
