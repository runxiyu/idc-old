# this thigng works, but idc.py drops incomingmessages
import trio
from itertools import count
import ssl


PORT = 12345

CONNECTION_COUNTER = count()


ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ctx.load_cert_chain(
    "/etc/letsencrypt/live/fcm.andrewyu.org/fullchain.pem",
    "/etc/letsencrypt/live/fcm.andrewyu.org/privkey.pem",
)


async def echo_server(server_stream):
    ident = next(CONNECTION_COUNTER)
    print(f"echo_server {ident}: started")
    try:
        async for data in server_stream:
            print(f"echo_server {ident}: received data {data!r}")
            await server_stream.send_all(data)
        print(f"echo_server {ident}: connection closed")
    except Exception as exc:
        print(f"echo_server {ident}: crashed: {exc!r}")


async def tls_wrapper(server_stream):
    return await echo_server(trio.SSLStream(server_stream, ctx, server_side=True))

async def main():
    await trio.serve_tcp(tls_wrapper, PORT)

trio.run(main)
