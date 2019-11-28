from flask import Flask, Response, request
import time
import random

app = Flask(__name__)
delay = 0
count = 0


@app.route('/')
def index():
    time.sleep(random.random())
    resp = Response(status=200)
    return resp


@app.route('/delay')
def increment():
    global delay
    global count
    count += 1
    inc = request.args.get('increment')
    ra = request.args.get('reset_after')
    try:
        if inc:
            delay += float(inc)
        print(delay)
        time.sleep(delay)
        if ra and count >= int(ra):
            delay = 0
            count = 0
        return Response(status=200)
    except TypeError:
        return Response(status=400)


@app.route('/unavailable')
def unavailable():
    try:
        p = request.args.get('probability')
        r = random.random()
        if r < float(p):
            return Response(status=400)
        return Response(status=200)
    except TypeError:
        return Response(status=400)


if __name__ == '__main__':
    app.run('localhost', port=4444)
