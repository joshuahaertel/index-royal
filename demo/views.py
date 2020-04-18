from django.urls import reverse_lazy, reverse
from django.views.generic import DetailView, CreateView

from demo.models import Demo, Player


# creates admin session
class CreateDemoView(CreateView):
    model = Demo
    fields = ()
    context_object_name = 'demo'

    def get_success_url(self):
        return f'{self.object.id}/admin'


# is a player
class DemoView(DetailView):
    model = Demo


# is admin
class DemoAdminView(DetailView):
    model = Demo
    template_name_suffix = '_detail_admin'


# creates user session
class JoinView(CreateView):
    model = Player
    fields = ()


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
