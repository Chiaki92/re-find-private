from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def index():
    return "Hello! Re:find is running."

if __name__ == "__main__":
    app.run(debug=True)