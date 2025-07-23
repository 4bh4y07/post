from flask import Flask, request, render_template_string
import os
import time
import random
import threading
from datetime import datetime
from werkzeug.utils import secure_filename
from FBTools import Start

app = Flask(__name__)

tasks = {}
logs = {}
task_counters = {}
task_id_counter = 0

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>FB Auto Comment Bot</title>
    <style>
        body { font-family: Arial; background: #f0f0f0; padding: 20px; }
        .success { color: green; }
        .fail { color: red; }
    </style>
</head>
<body>
<h2>Facebook Auto Comment Bot</h2>
<form method="post" enctype="multipart/form-data" action="/start">
    Post ID: <input type="text" name="post_id" required><br><br>
    Min Delay (s): <input type="number" name="min_delay" required><br><br>
    Max Delay (s): <input type="number" name="max_delay" required><br><br>
    Cookie File (.txt): <input type="file" name="cookie_file" required><br><br>
    Comment File (.txt): <input type="file" name="comment_file" required><br><br>
    <input type="submit" value="Start Commenting">
</form>
<hr>
<h3>Stop a Task</h3>
<form method="post" action="/stop">
    Task ID: <input type="number" name="task_id" required>
    <input type="submit" value="Stop Task">
</form>
<hr>
<h3>Live Logs</h3>
<form method="get">
    Task ID: <input type="number" name="log_task_id">
    <input type="submit" value="View Logs">
</form>
<pre>
{% if log_lines %}
{% for line in log_lines %}
<span class="{{ line[1] }}">{{ line[0] }}</span>
{% endfor %}
{% endif %}
</pre>
</body>
</html>
'''

@app.route('/')
def index():
    task_id = request.args.get('log_task_id', type=int)
    log_lines = logs.get(task_id, [])
    return render_template_string(HTML_TEMPLATE, log_lines=log_lines)

@app.route('/start', methods=['POST'])
def start():
    global task_id_counter

    post_id = request.form['post_id']
    min_delay = int(request.form['min_delay'])
    max_delay = int(request.form['max_delay'])

    cookie_file = request.files['cookie_file']
    comment_file = request.files['comment_file']

    cookie_path = f"/tmp/{secure_filename(cookie_file.filename)}"
    comment_path = f"/tmp/{secure_filename(comment_file.filename)}"
    cookie_file.save(cookie_path)
    comment_file.save(comment_path)

    cookies = load_lines(cookie_path)
    comments = load_lines(comment_path)

    if not cookies or not comments:
        return "Failed to load cookies or comments."

    task_id = task_id_counter
    tasks[task_id] = {'running': True}
    logs[task_id] = []
    task_counters[task_id] = 1

    thread = threading.Thread(
        target=comment_loop,
        args=(task_id, cookies, comments, post_id, min_delay, max_delay),
        daemon=True
    )
    thread.start()

    task_id_counter += 1
    return f"✅ Started Task ID: {task_id} — <a href='/?log_task_id={task_id}'>View Logs</a>"

@app.route('/stop', methods=['POST'])
def stop():
    task_id = int(request.form['task_id'])
    if task_id in tasks:
        tasks[task_id]['running'] = False
        return f"🛑 Stopped Task ID: {task_id}"
    return "❌ Invalid Task ID"

def load_lines(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]
    except Exception as e:
        print(f"Error reading file: {e}")
        return []

def comment_loop(task_id, cookie_list, comments, post_id, min_d, max_d):
    while tasks.get(task_id, {}).get('running', False):
        for cookie in cookie_list:
            if not tasks.get(task_id, {}).get('running', False):
                break
            try:
                acc = Start(cookie=cookie)
                comment_text = random.choice(comments)
                count = task_counters[task_id]
                full_comment = f"{comment_text} {count}"

                response = acc.CommentToPost(post=post_id, text=full_comment)
                now = datetime.now().strftime("%H:%M:%S")

                if response.get("status") == "success":
                    msg = f"[{now}] ✅ Sent: {full_comment}"
                    log(task_id, msg, "success")
                    print(msg)
                else:
                    err = response.get("error", "Unknown error")
                    msg = f"[{now}] ❌ Failed: {full_comment} | Reason: {err}"
                    log(task_id, msg, "fail")
                    print(msg)

                task_counters[task_id] += 1
                time.sleep(random.randint(min_d, max_d))
            except Exception as e:
                now = datetime.now().strftime("%H:%M:%S")
                err = f"[{now}] ⚠️ Error: {str(e)}"
                log(task_id, err, "fail")
                print(err)

def log(task_id, text, status):
    if task_id not in logs:
        logs[task_id] = []
    logs[task_id].append((text, status))
    if len(logs[task_id]) > 300:
        logs[task_id] = logs[task_id][-300:]

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4000, debug=True)
