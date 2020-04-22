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

    def get(self, request, *args, **kwargs):
        player_qs = Player.objects.filter(pk=kwargs['player_pk'])
        if not player_qs:
            raise Http404('Invalid playing link')
        self.player_object = player_qs[0]
        return super().get(request, *args, **kwargs)

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

    def get(self, request, *args, **kwargs):
        if not Demo.objects.filter(id=kwargs['pk']).exists():
            raise Http404('Demo group does not exist')
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.demo_id = self.kwargs['pk']
        return super().form_valid(form)

    def get_success_url(self):
        return f'/demos/{self.kwargs["pk"]}/players/{self.object.pk}'

# # is admin
# class DemoStateView(UpdateAPIView):
#     model = Demo
#     context_object_name = 'demo'
#
#
# # is admin
# class BatchView(UpdateAPIView):
#     model = Demo
#     context_object_name = 'demo'
#
#
# # is admin
# class EntryView(UpdateAPIView):
#     model = Demo
#     context_object_name = 'demo'
#
#
# # is admin
# class FieldView(UpdateAPIView):
#     model = Demo
#     context_object_name = 'demo'
#
#
# # is admin
# class TeamsView(ListAPIView):
#     model = Team
#
#
# # is admin
# class TeamView(RetrieveUpdateDestroyAPIView):
#     model = Team
#
#
# # is admin
# class PlayersView(ListAPIView):
#     model = Player
#
#
# # is admin
# class PlayerView(RetrieveUpdateDestroyAPIView):
#     model = Player
