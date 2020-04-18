from django.views.generic import DetailView, CreateView

from demo.models import Demo, Player


# creates admin session
class CreateDemoView(CreateView):
    model = Demo
    fields = ['name']
    context_object_name = 'demo'


# is a player
class DemoView(DetailView):
    model = Demo
    context_object_name = 'demo'


# is admin
class DemoAdminView(DetailView):
    model = Demo
    context_object_name = 'demo'


# creates user session
class JoinView(CreateView):
    model = Player


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
