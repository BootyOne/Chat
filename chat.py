from aiohttp import web


class WSChat:
    def __init__(self, host='127.0.0.1', port=8080):
        self.host = host
        self.port = port
        self.conns = {}

    async def main_page(self, request):
        return web.FileResponse('./index.html')

    async def chat(self, request):
        web_socket = web.WebSocketResponse(autoclose=False)
        await web_socket.prepare(request)
        async for message in web_socket:
            try:
                data = message.json()
            except:
                await web_socket.pong(b"pong")
                continue
            if data["mtype"] == "TEXT":
                if data["to"]:
                    json = {'mtype': 'DM', 'id': data["id"], 'text': data["text"]}
                    await self.conns[data["to"]].send_json(json)
                    continue
                json = {'mtype': 'MSG', 'id': data["id"], 'text': data["text"]}
                for client in self.conns.values():
                    if web_socket == client:
                        continue
                    await client.send_json(json)
            if data["mtype"] == "INIT":
                self.conns[data["id"]] = web_socket
                json = {'mtype': 'USER_ENTER', 'id': data["id"]}
                for client in self.conns.values():
                    await client.send_json(json)
        leave_client = ""
        for ids in self.conns.keys():
            if self.conns[ids] == web_socket:
                leave_client = ids
                break
        del self.conns[leave_client]
        for client in self.conns.values():
            await client.send_json(
                {'mtype': 'USER_LEAVE', 'id': leave_client})
        await web_socket.close()

    def run(self):
        app = web.Application()
        app.router.add_get('/', self.main_page)
        app.router.add_get('/chat', self.chat)
        web.run_app(app, host=self.host, port=self.port)


if __name__ == '__main__':
    WSChat().run()
