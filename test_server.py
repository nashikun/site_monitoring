from flask import Flask, Response, request
import time

app = Flask(__name__)
delay = 0
count = 0


@app.route('/')
def index():
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
        time.sleep(delay)
        if ra and count >= int(ra):
            delay = 0
            count = 0
        resp = Response(status=200)
        return resp
    except TypeError:
        resp = Response(status=400)
        return resp


if __name__ == '__main__':
    app.run('localhost', port=4444)