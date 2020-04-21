from django.urls import path, include

from demo.views import (
    CreateDemoView, DemoPlayerView, DemoAdminView, JoinView,
)

app_name = 'demos'

demo_urlpatterns = [
    path('players/<uuid:player_pk>', DemoPlayerView.as_view(), name='demo'),
    path('admin', DemoAdminView.as_view(), name='admin'),

    # path('state', DemoStateView().as_view(), name='state'),
    # path('batch', BatchView().as_view(), name='batch'),
    # path('entry', EntryView().as_view(), name='entry'),
    # path('field', FieldView().as_view(), name='field'),
    #
    # path('teams', TeamsView().as_view(), name='teams'),
    # path('teams/<uuid:team_pk>', TeamView().as_view(), name='team'),
    #
    # path('players', PlayersView().as_view(), name='players'),
    # path('players/<uuid:player_pk>', PlayerView().as_view(), name='player'),

    path('join', JoinView.as_view(), name='join'),
]

urlpatterns = [
    path('create', CreateDemoView.as_view(), name='create'),
    path('<uuid:pk>/', include(demo_urlpatterns)),
]
