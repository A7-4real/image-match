from flask import Flask

app = Flask(__name__)


@app.route('/hello/', methods=['GET', 'POST'])
def welcome():
    return "Hello World!"


@app.route('/', methods=['GET', 'Post'])
def home():
    return "Welcome Home!"


if __name__ == '__main__':
    app.run(debug=True)
