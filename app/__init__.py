from flask import Flask, render_template, url_for, request, redirect, send_from_directory, make_response
from datetime import datetime, timedelta
import requests

from flask_apscheduler import APScheduler
import traceback

import psycopg
import os

import requests
import matplotlib.pyplot as plt
from scipy.interpolate import make_interp_spline, BSpline
import numpy as np
import matplotlib.colors as mcolors
from matplotlib.patches import Polygon



def job1(of = False):
    interval = '1d'
    dlit = '10d'

    portfolio = {'AAPL': 15, 'NEE': 27, 'MA': 5, 'JPM': 12, 'MSFT': 5, 'AMAT': 8, 'TSLA': 1, 'NVDA': 1}

    data = [0]*10

    for ticker, quantity in portfolio.items():
        price = requests.get(f'https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval={interval}&range={dlit}',headers={'User-Agent': 'zip'}).json()['chart']['result'][0]['indicators']['adjclose'][0]['adjclose']
        for day, p in enumerate(price):
            data[day] += p*quantity

    r, g, b = 1, 1, 1

    fig = plt.figure(figsize=(24, 11), facecolor=(0, 0, 0), edgecolor=(0, 0, 0))
    ax = fig.add_subplot(111, frameon=False)
    ax.set_facecolor((0, 0, 0))

    ax.plot([0, len(data)-1], [data[0], data[0]], '--', color='w', linewidth=1.5, alpha=1)

    min_t = 999999
    max_t = -999999

    x = [i for i in range(len(data))]
    xnew = np.linspace(0, len(data)-1, 300)

    line = data

    spl = make_interp_spline(x, line, k=1)
    smoothy = spl(xnew)

    min_n = min(smoothy)
    min_t = min(min(data), min_n)
    max_n = max(smoothy)
    max_t = max(max(data), max_n)

    ax.plot(xnew, smoothy, color=(r, g, b), linewidth=4.5, zorder=1)

    z = np.empty((100, 1, 4), dtype=float)
    rgb = mcolors.colorConverter.to_rgb((r, g, b))
    z[:,:,:3] = rgb
    z[:,:,-1] = np.linspace(0, 0.3, 100)[:,None]

    xmin, xmax = 0, len(line)-1

    imm = ax.imshow(z, aspect='auto', extent=[xmin, xmax, min_n, max_n], origin='lower', zorder=0)

    cstack = np.column_stack([xnew, smoothy])
    cstack = np.vstack([[xmin, min_n], cstack, [xmax, min_n], [xmin, min_n]])
    clip_path = Polygon(cstack, facecolor='none', edgecolor='none', closed=True)
    ax.add_patch(clip_path)
    imm.set_clip_path(clip_path)

    range_t = max_t-min_t

    ax.set_ylim([min_t-range_t*0.1, max_t+range_t*0.1])
    ax.set_axis_off()
    fig.tight_layout()
    fig.canvas.draw()

    plt.savefig('report.png')


class Config(object):
    JOBS = [
                {
            'id': 'job1',
            'func': job1,
            'trigger': 'cron',
            'second': 0
        },
    ]

    SCHEDULER_API_ENABLED = True
    SCHEDULER_TIMEZONE = "Europe/Moscow"

app = Flask(__name__)
app.config.from_object(Config())

@app.route('/')
def ics():
    return send_from_directory('', 'report.png')

job1()
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()
