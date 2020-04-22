from django.urls.conf import path

from demo.consumers import PlayerConsumer, AdminConsumer

websocket_urlpatterns = [
    path('ws/demos/<uuid:demo_pk>/players/<uuid:player_pk>', PlayerConsumer),
    path('ws/demos/<uuid:demo_pk>/admin/<uuid:admin_pk>', AdminConsumer),
]
