import os
import time
import random
import logging
from instagrapi import Client
import argparse

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("instagram_bot.log"), logging.StreamHandler()]
)
logger = logging.getLogger("InstagramBot")


class InstagramBot:
    def __init__(self, username, password, session_file="instagram_session.json"):
        self.username = username
        self.password = password
        self.session_file = session_file
        self.client = Client()
        self.login()

    def login(self):
        """Login to Instagram account"""
        try:
            # Try to load session from file
            if os.path.exists(self.session_file):
                logger.info("Loading session from file")
                self.client.load_settings(self.session_file)
                self.client.login(self.username, self.password)
            else:
                logger.info("Logging in with username and password")
                self.client.login(self.username, self.password)
                # Save session to file
                self.client.dump_settings(self.session_file)

            logger.info(f"Successfully logged in as {self.username}")
        except Exception as e:
            logger.error(f"Login failed: {e}")
            raise

    def follow_user(self, username):
        """Follow a user by username"""
        try:
            user_id = self.client.user_id_from_username(username)
            self.client.user_follow(user_id)
            logger.info(f"Successfully followed user: {username}")
            return True
        except Exception as e:
            logger.error(f"Failed to follow user {username}: {e}")
            return False

    def get_user_followers(self, username, amount=10):
        """Get followers of a specific user"""
        try:
            # Get user ID from username
            user_id = self.client.user_id_from_username(username)
            logger.info(f"Getting followers for user: {username} (ID: {user_id})")

            # Get followers
            followers = self.client.user_followers(user_id, amount=amount)
            logger.info(f"Found {len(followers)} followers")

            return followers
        except Exception as e:
            logger.error(f"Failed to get followers for {username}: {e}")
            return {}

    def follow_user_followers(self, target_username, amount=10, delay_range=(15, 30)):
        """Follow a specified number of followers from a target user"""
        try:
            # Get followers
            followers = self.get_user_followers(target_username, amount=amount)

            if not followers:
                logger.warning(f"No followers found for {target_username}")
                return 0

            # Convert followers dict to list and shuffle it
            follower_list = list(followers.items())
            random.shuffle(follower_list)

            # Limit to requested amount
            follower_list = follower_list[:amount]

            follow_count = 0
            for user_id, user_info in follower_list:
                username = user_info.username

                # Check if already following this user
                try:
                    friendship_status = self.client.user_info(user_id).followed_by_viewer
                    if friendship_status:
                        logger.info(f"Already following {username}, skipping")
                        continue
                except:
                    # If we can't check status, try to follow anyway
                    pass

                # Follow user
                if self.follow_user(username):
                    follow_count += 1

                # Add random delay to avoid being rate limited
                delay = random.uniform(delay_range[0], delay_range[1])
                logger.info(f"Waiting {delay:.2f} seconds before next follow")
                time.sleep(delay)

            logger.info(f"Successfully followed {follow_count} users who follow {target_username}")
            return follow_count

        except Exception as e:
            logger.error(f"Error in follow_user_followers: {e}")
            return 0

    def unfollow_users(self, amount=10, delay_range=(15, 30)):
        """unfollow users that youre following but who dont follow you back"""
        try:

            user_id = self.client.user_id


            following = self.client.user_following(user_id)
            logger.info(f"You are following {len(following)} users")

            followers = self.client.user_followers(user_id)
            logger.info(f"You have {len(followers)} followers")

            non_followers = [user_id for user_id in following if user_id not in followers]
            logger.info(f"Found {len(non_followers)} users who dont follow you back")

            random.shuffle(non_followers)
            non_followers = non_followers[:amount]

            unfollow_count = 0
            for user_id in non_followers:
                user_info = following[user_id]
                username = user_info.username

                # Unfollow user
                try:
                    self.client.user_unfollow(user_id)
                    logger.info(f"Unfollowed {username}")
                    unfollow_count += 1

                    # Add random delay
                    delay = random.uniform(delay_range[0], delay_range[1])
                    logger.info(f"Waiting {delay:.2f} seconds before next unfollow")
                    time.sleep(delay)
                except Exception as e:
                    logger.error(f"Failed to unfollow {username}: {e}")

            logger.info(f"Successfully unfollowed {unfollow_count} users")
            return unfollow_count

        except Exception as e:
            logger.error(f"Error in unfollow_users: {e}")
            return 0


def main():
    parser = argparse.ArgumentParser(description="Instagram Follow Bot")
    parser.add_argument("--username", required=True, help="Instagram username")
    parser.add_argument("--password", required=True, help="Instagram password")
    parser.add_argument("--action", choices=["follow_followers", "unfollow"], required=True,
                        help="Action to perform")
    parser.add_argument("--target", help="Target username whose followers you want to follow")
    parser.add_argument("--amount", type=int, default=10, help="Number of users to follow/unfollow")
    parser.add_argument("--min-delay", type=float, default=15.0,
                        help="Minimum delay between actions in seconds")
    parser.add_argument("--max-delay", type=float, default=30.0,
                        help="Maximum delay between actions in seconds")

    args = parser.parse_args()

    # Create bot instance
    bot = InstagramBot(args.username, args.password)

    if args.action == "follow_followers":
        if not args.target:
            parser.error("--target is required for follow_followers action")

        logger.info(f"Starting to follow followers of {args.target}")
        count = bot.follow_user_followers(
            args.target,
            amount=args.amount,
            delay_range=(args.min_delay, args.max_delay)
        )
        print(f"✅ Successfully followed {count} users who follow {args.target}")

    elif args.action == "unfollow":
        logger.info("Starting to unfollow users who don't follow you back")
        count = bot.unfollow_users(
            amount=args.amount,
            delay_range=(args.min_delay, args.max_delay)
        )
        print(f"✅ Successfully unfollowed {count} users")


if __name__ == "__main__":
    main()