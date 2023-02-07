from aiohttp import web

from .anern_inverter.inverter import Inverter

_inverter = None


async def health(request):
    return web.Response(text="<h1> Async Rest API using aiohttp : Health OK </h1>",
                        content_type='text/html')


def get_inverter() -> Inverter:
    global _inverter
    if _inverter is None:
        _inverter = Inverter('/dev/ttyUSB0')
    return _inverter


async def get_metrics(request):
    inverter = get_inverter()
    data = inverter.get_qpigs()
    return web.Response(
        text='\n'.join([f'{key} {value}' for key, value in data.items()]),
        content_type='text/plain'
    )


def init():
    app = web.Application()
    app.router.add_get("/", health)
    app.router.add_get("/metrics", get_metrics)
    return app


monitoring_app = init()

if __name__ == "__main__":
    web.run_app(monitoring_app, port=8000)
