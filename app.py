# import os
# os.environ["QT_QUICK_BACKEND"] = "software"

import sys
import threading
from flask import Flask, Response, request, jsonify, render_template
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QHBoxLayout
from PyQt6.QtWebEngineWidgets import QWebEngineView

from werkzeug.wsgi import FileWrapper
import io
from PyQt6.QtCore import QUrl

# Initialize Flask app
app = Flask(__name__)

global STATE
STATE = {}

@app.route('/')
def root():
    return render_template('index.html')

@app.route('/rd', methods=['POST'])
def rd():
    req = request.get_json()
    print(f"Received request: {req}") 
    key = req['_key']
    
    if key not in STATE:
        STATE[key] = {
            'im': b'',
            'filename': 'none.png',
            'events': []
        }

    if req['filename'] == STATE[key]['filename']:
        attachment = io.BytesIO(b'')
    else:
        attachment = io.BytesIO(STATE[key]['im'])

    w = FileWrapper(attachment)
    resp = Response(w, mimetype='text/plain', direct_passthrough=True)
    resp.headers['filename'] = STATE[key]['filename']
    
    return resp

@app.route('/event_post', methods=['POST'])
def event_post():
    global STATE

    req = request.get_json()
    key = req['_key']

    STATE[key]['events'].append(request.get_json())
    return jsonify({'ok': True})

@app.route('/new_session', methods=['POST'])
def new_session():
    global STATE

    req = request.get_json()
    key = req['_key']
    STATE[key] = {
        'im': b'',
        'filename': 'none.png',
        'events': []
    }

    return jsonify({'ok': True})

@app.route('/capture_post', methods=['POST'])
def capture_post():
    global STATE

    with io.BytesIO() as image_data:
        filename = list(request.files.keys())[0]
        key = filename.split('_')[1]
        request.files[filename].save(image_data)
        STATE[key]['im'] = image_data.getvalue()
        STATE[key]['filename'] = filename

    return jsonify({'ok': True})

@app.route('/events_get', methods=['POST'])
def events_get():
    req = request.get_json()
    key = req['_key']
    events_to_execute = STATE[key]['events'].copy()
    STATE[key]['events'] = []
    return jsonify({'events': events_to_execute})

# Function to start Flask server
def start_flask():
    app.run('0.0.0.0', port=5000, debug=False)

class WebWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Flask Web Interface")

        self.setStyleSheet(""" 
            QMainWindow {
                background: #f4f4f9;
                border: none;
            }
            QWebEngineView {
                border-radius: 10px;
                border: 1px solid #ddd;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 10px 20px;
                font-size: 14px;
                border-radius: 5px;
                border: none;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #388e3c;
            }
        """)

        self.browser = QWebEngineView()
        self.browser.setUrl(QUrl("http://127.0.0.1:5000"))

        layout = QVBoxLayout()
        layout.addWidget(self.browser)

        toolbar_layout = QHBoxLayout()

        reload_button = QPushButton('Reload')
        reload_button.clicked.connect(self.reload_page)
        toolbar_layout.addWidget(reload_button)

        back_button = QPushButton('Back')
        back_button.clicked.connect(self.go_back)
        toolbar_layout.addWidget(back_button)

        forward_button = QPushButton('Forward')
        forward_button.clicked.connect(self.go_forward)
        toolbar_layout.addWidget(forward_button)

        main_layout = QVBoxLayout()
        main_layout.addLayout(toolbar_layout)
        main_layout.addLayout(layout)

        container = QWidget()
        container.setLayout(main_layout)

        self.setCentralWidget(container)
        self.setGeometry(100, 100, 1024, 768)
        self.show()

    def reload_page(self):
        self.browser.reload()

    def go_back(self):
        self.browser.back()

    def go_forward(self):
        self.browser.forward()

# Running Flask in a background thread
flask_thread = threading.Thread(target=start_flask, daemon=True)
flask_thread.start()

# Running the PyQt6 application
app = QApplication(sys.argv)
window = WebWindow()
sys.exit(app.exec())
