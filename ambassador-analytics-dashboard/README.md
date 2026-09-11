# Ambassador Impact Dashboard

I'm a Google Student Ambassador at Rutgers, and part of the role is running events
to get students using Gemini. I was tracking how they went across a bunch of
different places (event sign in sheets, Instagram insights, the signup form, site
analytics) and it was annoying to get a full picture. So I built this to pull the
numbers into one dashboard I can actually look at, and show to people if they ask
how it's going.

It's a small Flask API with a frontend that charts everything using Chart.js.

## What it shows

- Tiles at the top with the totals: events run, attendees, Gemini signups, social reach, and site visits
- A line chart of signups and attendees month by month
- A bar chart of social reach and site visits month by month
- A table of every event with its attendance and signups

## Running it

You need Python 3.9 or newer.

```bash
pip install -r requirements.txt
python app.py     # open http://127.0.0.1:5000
```

## How it's set up

The API reads from `data/metrics.json` and serves it at a few endpoints:

- `/api/summary` gives the totals for the tiles
- `/api/timeseries` gives the month by month numbers for the charts
- `/api/events` gives the list of events

The frontend (`templates/index.html`, `static/app.js`, `static/style.css`) just
calls those and draws everything.

## Notes

The numbers in `data/metrics.json` are the ones I've been keeping so far, and I
update that file as I run more events. I kept the data separate from the code on
purpose so that later I can replace the json with real automatic pulls from the
analytics pages without changing the frontend at all. Chart.js is loaded from a CDN,
so it's the one thing that needs an internet connection to render.
