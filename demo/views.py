import asyncio
from uuid import uuid4

import aioredis
from asgiref.sync import async_to_sync
from django.http import Http404
from django.views.generic import DetailView, CreateView

from demo.models import Demo, Player


# creates admin session
class CreateDemoView(CreateView):
    model = Demo
    fields = ()
    context_object_name = 'demo'
    admin_pk = None
    demo_pk = None

    def get_success_url(self):
        return f'/demos/{self.demo_pk}/admin/{self.admin_pk}'

    def form_valid(self, form):
        self.demo_pk = str(uuid4())
        self.admin_pk = str(uuid4())
        return_value = super().form_valid(form)
        async_to_sync(self.create_demo)()
        return return_value

    async def create_demo(self):
        REDIS_POOL = await aioredis.create_redis_pool('redis://localhost')
        demo_key = f'demo-{self.demo_pk}'
        create = REDIS_POOL.hmset(
            demo_key,
            'admin_pk', self.admin_pk,
            'state', 'pause',
            'current_batch_index', 0,
            'current_entry_index', 0,
            'current_field_index', 0,
        )
        expire = REDIS_POOL.expire(demo_key, 10800)
        await asyncio.gather(create, expire)


# is a player
class DemoPlayerView(DetailView):
    model = Demo
    template_name_suffix = '_detail_player'
    player_object: Player = None

    @async_to_sync
    async def get_object(self, queryset=None):
        REDIS_POOL = await aioredis.create_redis_pool('redis://localhost')
        future_player = REDIS_POOL.hgetall(
            f'player-{self.kwargs["player_pk"]}', encoding='utf-8',
        )
        demo_pk = str(self.kwargs["demo_pk"])
        future_demo_state = REDIS_POOL.hgetall(
            f'demo-{demo_pk}', encoding='utf-8',
        )
        player_dict, demo_dict = await asyncio.gather(
            future_player, future_demo_state
        )
        is_valid = (
                demo_dict and
                player_dict and
                player_dict.pop('demo_pk') == demo_pk
        )
        if not is_valid:
            raise Http404('Invalid Playing Link')
        self.player_object = Player(**player_dict)
        demo_dict['current_batch_index'] = int(
            demo_dict['current_batch_index']
        )
        demo_dict['current_entry_index'] = int(
            demo_dict['current_entry_index']
        )
        demo_dict['current_field_index'] = int(
            demo_dict['current_field_index']
        )
        return Demo(**demo_dict)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['player'] = self.player_object
        return context


# is admin
class DemoAdminView(DetailView):
    model = Demo
    template_name_suffix = '_detail_admin'

    @async_to_sync
    async def get_object(self, queryset=None):
        demo_pk = self.kwargs['demo_pk']
        REDIS_POOL = await aioredis.create_redis_pool('redis://localhost')
        result = await REDIS_POOL.hmget(
            f'demo-{demo_pk}', 'admin_pk', 'state', 'current_batch_index',
            'current_entry_index', 'current_field_index', encoding='utf-8',
        )
        admin_pk, state, batch_index, entry_index, field_index = result
        if not admin_pk:
            raise Http404('Invalid request: 1')
        elif admin_pk != str(self.kwargs['admin_pk']):
            raise Http404(f'Invalid request: 2 {admin_pk} {self.kwargs["admin_pk"]}')
        return Demo(
            id=demo_pk,
            admin_id=admin_pk,
            state=state,
            current_batch_index=int(batch_index),
            current_entry_index=int(entry_index),
            current_field_index=int(field_index),
        )


# creates user session
class JoinView(CreateView):
    model = Player
    fields = ('name', 'skill_level')
    player_pk: str = None
    player_name: str = None
    player_skill: str = None

    @async_to_sync
    async def get(self, request, *args, **kwargs):
        REDIS_POOL = await aioredis.create_redis_pool('redis://localhost')
        demo_key = f'demo-{kwargs["demo_pk"]}'
        state = await REDIS_POOL.hget(
            demo_key, 'state'
        )
        if not state:
            raise Http404('Demo group does not exist')
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        self.player_pk = str(uuid4())
        form.instance.demo_id = self.kwargs['demo_pk']
        self.player_name = form.cleaned_data['name']
        self.player_skill = form.cleaned_data['skill_level']
        return_value = super().form_valid(form)
        async_to_sync(self.create_player)()
        return return_value

    async def create_player(self):
        REDIS_POOL = await aioredis.create_redis_pool('redis://localhost')
        player_key = f'player-{self.player_pk}'
        demo_pk = str(self.kwargs['demo_pk'])
        create = REDIS_POOL.hmset(
            player_key,
            'demo_pk', demo_pk,
            'points', 0,
            'team', '',
            'name', self.player_name,
            'skill_level', self.player_skill,
        )
        expire = REDIS_POOL.expire(player_key, 10800)
        demo_player_key = f'demo.players-{demo_pk}'
        add_player = REDIS_POOL.sadd(demo_player_key, self.player_pk)
        demo_players_expire = REDIS_POOL.expire(demo_player_key, 10800)
        await asyncio.gather(create, expire, add_player, demo_players_expire)

    def get_success_url(self):
        return f'/demos/{self.kwargs["demo_pk"]}/players/{self.player_pk}'
