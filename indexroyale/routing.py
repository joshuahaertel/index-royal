from channels.routing import ProtocolTypeRouter, URLRouter

import demo.routing

application = ProtocolTypeRouter({
    # (http->django views is added by default)
    'websocket': URLRouter(demo.routing.websocket_urlpatterns),
})
