import requests
from datetime import datetime, timedelta, UTC
import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Google Sheets setup
creds_json = os.environ["GOOGLE_CREDENTIALS"]
creds_dict = json.loads(creds_json)
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open("MatchTweets").sheet1  # Your sheet name

# Hashtags
HASHTAGS_URL = "https://raw.githubusercontent.com/EuroStreamsHub/Streams/main/hashtag.json"
hashtags_data = requests.get(HASHTAGS_URL).json()
team_hashtags = {team: tag for league in hashtags_data.values() for team, tag in league.items()}

# Streams URL
STREAMS_URL = "https://eurostreamshub.github.io/Streams/index.html"

# Fetch matches
API_URL = "https://streamed.pk/api/matches/football"
matches = requests.get(API_URL).json()

now = datetime.now(UTC)
twelve_hours = now + timedelta(hours=12)

hashtags_sentence = []

# Gather hashtags for matches in next 12 hours
for m in matches:
    kickoff = datetime.fromtimestamp(m["date"] / 1000, UTC)
    if now <= kickoff <= twelve_hours:
        # Split teams
        if " vs " in m["title"].lower():
            parts = m["title"].replace("VS", "vs").split("vs")
        elif " v " in m["title"].lower():
            parts = m["title"].replace(" V ", " v ").split("v")
        else:
            continue

        teams = [t.strip() for t in parts]
        # Only include if both teams are in hashtag.json
        if all(team in team_hashtags for team in teams):
            tags = [team_hashtags[team] for team in teams]
            hashtags_sentence.extend(tags)

# Split into 280-character tweets with Streams link
tweets = []
current = ""

for tag in hashtags_sentence:
    # +1 for space
    if len(current) + len(tag) + 1 + len(STREAMS_URL) <= 280:
        current += tag + " "
    else:
        tweets.append(current.strip() + " " + STREAMS_URL)
        current = tag + " "

if current:
    tweets.append(current.strip() + " " + STREAMS_URL)

# Write each tweet as a row in Google Sheet
for tweet in tweets:
    # Optional: check duplicates if needed
    sheet.append_row([tweet])
    print("Added to sheet:", tweet)
