from django.http import Http404
from django.views.generic import DetailView, CreateView

from demo.models import Demo, Player


# creates admin session
class CreateDemoView(CreateView):
    model = Demo
    fields = ()
    context_object_name = 'demo'

    def get_success_url(self):
        return f'/demos/{self.object.id}/admin'


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
