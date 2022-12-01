from bs4 import BeautifulSoup
from flask import request
from flask import Flask
import requests
import asyncio
import queue


app = Flask(__name__)

async def get_classnamer():
    response = requests.get('https://www.classnamer.org/')
    return response.content

def extract_words_from_classnamer_response(content):
    soup = BeautifulSoup(content, features="html.parser")
    for word in soup.findAll('p', {'id': 'classname'})[0].contents[::2]:
        yield word

def add_count(word, words_count):
    if word in words_count:
        words_count[word] += 1
    else:
        words_count[word] = 1

async def count_words_task(jobs: queue.Queue, words_count):
    while not jobs.empty():
        jobs.get()
        result = await get_classnamer()
        for word in extract_words_from_classnamer_response(result):
            add_count(word, words_count)

TASKS = 3
DEFAULT_REQUESTS_COUNT = 10

@app.route('/get_words')
async def get_words():
    requests_count_arg = request.args.get('requests_count')
    requests_count = int(requests_count) if requests_count_arg else DEFAULT_REQUESTS_COUNT
    jobs = queue.Queue()
    words_count = {}
    for job_id in range(requests_count):
        jobs.put(job_id)
    tasks = []
    for _ in range(TASKS):
        task = asyncio.create_task(count_words_task(jobs, words_count))
        tasks.append(task)
    for task in tasks:
        await task
    return words_count


if __name__ == '__main__':
        app.run()
        