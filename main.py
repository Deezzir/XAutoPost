import tweepy # type:ignore
import schedule
import time
import logging
import os
from typing import List, Optional
from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

POST_FILE = "test.txt"
INTERVAL_MINUTES = 5

def get_env_variable(name: str) -> str:
    """Get an environment variable or raise an exception."""
    value = os.getenv(name)
    if not value:
        raise EnvironmentError(f"Environment variable {name} not found.")
    return value

CONSUMER_KEY = get_env_variable("TWITTER_CONSUMER_KEY")
CONSUMER_SECRET = get_env_variable("TWITTER_CONSUMER_SECRET")
ACCESS_TOKEN = get_env_variable("TWITTER_ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = get_env_variable("TWITTER_ACCESS_TOKEN_SECRET")
BEARER_TOKEN = get_env_variable("TWITTER_BEARER_TOKEN")

CLIENT = tweepy.Client(
    consumer_key=CONSUMER_KEY,
    consumer_secret=CONSUMER_SECRET,
    access_token=ACCESS_TOKEN,
    access_token_secret=ACCESS_TOKEN_SECRET,
    bearer_token=BEARER_TOKEN
)

class TwitterPoster:
    def __init__(self, post_file: str):
        self.post_file = post_file
        self.posts = self.load_posts()
        self.current_index = 0

    def load_posts(self) -> List[str]:
        """Load and clean posts from the specified file."""
        try:
            with open(self.post_file, "r") as f:
                lines = list(dict.fromkeys([line.strip() for line in f if line.strip()]))
            return lines
        except FileNotFoundError:
            logger.error(f"Post file {self.post_file} not found.")
            return []

    def post_next(self) -> Optional[schedule.CancelJob]:
        """Post the next tweet in the list."""
        if self.current_index < len(self.posts):
            post = self.posts[self.current_index]
            try:
                logger.info(f"Posting: {post}")
                response = CLIENT.create_tweet(text=post)
                if response.errors:
                    logger.error(f"Error posting tweet: {response.errors}")
                else:
                    logger.info(f"Tweet posted successfully: {response.data}")
                self.current_index += 1
            except Exception as e:
                logger.error(f"Exception occurred while posting tweet: {e}")
            return None
        else:
            logger.info("All posts have been posted.")
            return schedule.CancelJob()

def main():
    poster = TwitterPoster(POST_FILE)
    if not poster.posts:
        logger.info("No posts to tweet.")
        return

    schedule.every(INTERVAL_MINUTES).minutes.do(poster.post_next)
    logger.info(f"Scheduled job to post every {INTERVAL_MINUTES} minutes.")

    while True:
        schedule.run_pending()
        if not schedule.get_jobs():
            logger.info("All jobs completed. Exiting.")
            break
        time.sleep(1)

if __name__ == '__main__':
    main()
