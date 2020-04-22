import asyncio
import json
from time import time

import aioredis
from channels.generic.websocket import AsyncWebsocketConsumer
from django.http import Http404


class TeamPointsConsumer(AsyncWebsocketConsumer):
    demo_pk: str = None
    demo_points_group_name: str = None

    async def get_and_update_team_points(self):
        REDIS_POOL = await aioredis.create_redis_pool('redis://localhost')
        start_time = time()
        team_pks = await REDIS_POOL.smembers(f'demo.teams-{self.demo_pk}')
        teams = {}
        for team_pk in team_pks:  # type: bytes
            team_name = await REDIS_POOL.hget(f'team-{team_pk}', 'name')
            player_pks = await REDIS_POOL.smembers(
                f'team.players-{team_pk.decode()}'
            )
            players_points = await asyncio.gather(
                REDIS_POOL.hget(f'player-{player_pk}', 'points')
                for player_pk in player_pks
            )
            teams[team_name] = sum(
                int(player_points) for player_points in players_points
            )
        await self.channel_layer.group_send(
            self.demo_points_group_name,
            {
                'type': 'update.teams.points',
                'teams': teams,
            }
        )
        print(time() - start_time)


class PlayerConsumer(TeamPointsConsumer):
    demo_group_name: str = None
    player_pk: str = None
    player_group_name: str = None

    async def connect(self):
        self.demo_pk = self.scope['url_route']['kwargs']['demo_pk']
        self.demo_group_name = f'group.demo.state-{self.demo_pk}'
        self.demo_points_group_name = f'group.demo.points-{self.demo_pk}'

        self.player_pk = self.scope['url_route']['kwargs']['player_pk']
        self.player_group_name = f'group.player-{self.player_pk}'

        await self.channel_layer.group_add(
            self.demo_group_name,
            self.channel_name,
        )
        await self.channel_layer.group_add(
            self.demo_points_group_name,
            self.channel_name,
        )
        await self.channel_layer.group_add(
            self.player_group_name,
            self.channel_name,
        )

        return await super().connect()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.demo_group_name,
            self.channel_name
        )
        await self.channel_layer.group_discard(
            self.demo_points_group_name,
            self.channel_name,
        )
        await self.channel_layer.group_discard(
            self.player_group_name,
            self.channel_name,
        )
        return await super().disconnect(close_code)

    async def receive(self, text_data=None, bytes_data=None):
        received_at = time()
        REDIS_POOL = await aioredis.create_redis_pool('redis://localhost')
        result = await REDIS_POOL.hmget(
            f'demo-{self.demo_pk}', 'field_index', 'entry_index',
            'batch_index', 'updated_at', 'state'
        )
        field_index, entry_index, batch_index, updated_at, state = result
        text_data_json = json.loads(text_data)
        user_field_index = text_data_json['field']
        user_entry_index = text_data_json['entry']
        user_batch_index = text_data_json['batch']
        correct_index = (
                user_field_index == int(field_index) and
                user_entry_index == int(entry_index) and
                user_batch_index == int(batch_index)
        )
        if not correct_index and abs(received_at - float(updated_at)) > 3:
            return

        key = (
            f'demo-field-users:'
            f'{self.demo_pk}-'
            f'{user_batch_index}-'
            f'{user_entry_index}-'
            f'{user_field_index}'
        )
        transaction = REDIS_POOL.multi_exec()
        transaction.scard(key)
        transaction.sadd(key, self.player_pk)
        transaction.expire(key, 10800)
        num_of_players, added, _ = await transaction.execute()
        if not added:
            return
        point_delta = 1 if num_of_players else 2

        player_key = f'player-{self.player_pk}'
        my_points, _ = asyncio.gather(
            REDIS_POOL.hincrby(player_key, 'points', point_delta),
            REDIS_POOL.expire(player_key, 10800),
        )

        await self.send(text_data=json.dumps({
            'type': 'update_player_points',
            'points': int(my_points)
        }))
        if state != b'play':
            await self.get_and_update_team_points()

    async def update_demo_state(self, event):
        await self.send(text_data=json.dumps({
            'type': 'update_demo_state',
        }))

    async def update_teams_points(self, event):
        await self.send(text_data=json.dumps({
            'type': 'update_teams_points',
            'teams': event['teams'],
        }))

    async def update_player(self, event):
        await self.send(text_data=json.dumps({
            'type': 'update_player',
            **event
        }))


class AdminConsumer(TeamPointsConsumer):
    connected: bool = None
    demo_group_name: str = None
    player_group_name: str = None
    playing: asyncio.Event = None
    updates: asyncio.Future = None

    async def connect(self):
        self.demo_pk = self.scope['url_route']['kwargs']['demo_pk']
        self.demo_group_name = f'group.demo-{self.demo_pk}'
        self.demo_points_group_name = f'group.demo.points-{self.demo_pk}'
        REDIS_POOL = await aioredis.create_redis_pool('redis://localhost')
        demo_key = f'demo-{self.demo_pk}'
        admin_pk, state = await REDIS_POOL.hmget(
            demo_key, 'admin_pk', 'state'
        )
        url_admin_pk = self.scope['url_route']['kwargs']['admin_pk']
        if not state or str(url_admin_pk) != (admin_pk or b'').decode():
            await self.close()
            return
        await self.channel_layer.group_add(
            self.demo_group_name,
            self.channel_name,
        )
        await self.channel_layer.group_add(
            self.demo_points_group_name,
            self.channel_name,
        )
        await super().connect()
        self.connected = True
        self.playing = asyncio.Event()
        if state == b'play':
            self.playing.set()
        asyncio.ensure_future(self.run_updates())

    async def disconnect(self, code):
        self.connected = False
        return super().disconnect(code)

    async def run_updates(self):
        while self.connected:
            await asyncio.sleep(.5)
            await self.playing.wait()
            await self.get_and_update_team_points()

    async def update_teams_points(self, event):
        await self.send(text_data=json.dumps({
            'type': 'update_teams_points',
            **event
        }))
