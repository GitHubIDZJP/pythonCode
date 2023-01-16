import tornado.ioloop
import tornado.web


session_id = 1
class MainHandler(tornado.web.RequestHandler):
    def get(self):
        if not self.get_cookie("session"):
            self.set_cookie("session",str( session_id))
            session_id = session_id + 1
            self.write("Your session got a new session!")
        else:
            self.write("Your session was set!")

def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
    ])

def main():
    app = make_app()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()

if __name__ == "__main__":
    main()