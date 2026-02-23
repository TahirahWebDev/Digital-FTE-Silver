"""
Twitter Poster - Posts content to Twitter/X using the Twitter API v2.

This module integrates with Twitter/X to publish drafted content from the
AI Employee system. Supports both standard posts and threaded posts.

Usage:
    from scripts.tools.twitter_poster import TwitterPoster
    
    poster = TwitterPoster()
    result = poster.post_tweet(
        content="Just published a new blog post about AI automation!",
        media_path=None  # Optional path to image
    )
"""

import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)

from scripts.config import TWITTER_CREDENTIALS

# Import tweepy - will be None if not available
import tweepy

TWEEPY_AVAILABLE = True

class TwitterPoster:
    """
    Handles posting content to Twitter/X.
    
    Supports single tweets, threaded tweets, and media attachments.
    """
    
    # Twitter character limits
    MAX_TWEET_LENGTH = 280
    MAX_THREAD_LENGTH = 10  # Maximum tweets in a thread
    
    def __init__(self):
        """
        Initialize the Twitter Poster with credentials from config.
        """
        self.api_key = TWITTER_CREDENTIALS.get('api_key', '')
        self.api_secret = TWITTER_CREDENTIALS.get('api_secret', '')
        self.access_token = TWITTER_CREDENTIALS.get('access_token', '')
        self.access_token_secret = TWITTER_CREDENTIALS.get('access_token_secret', '')
        self.bearer_token = TWITTER_CREDENTIALS.get('bearer_token', '')
        
        self._mock_mode = not all([
            self.api_key, 
            self.api_secret, 
            self.access_token, 
            self.access_token_secret
        ])
        
        self.client = None
        self.api = None
        
        if self._mock_mode:
            logger.info("Twitter Poster initialized in MOCK mode (missing credentials)")
        else:
            self._authenticate()
    
    def _authenticate(self) -> bool:
        """
        Authenticate with Twitter API using OAuth 1.0a.
        
        Returns:
            True if authentication successful, False otherwise
        """
        if self._mock_mode:
            return True
        
        try:
            # Authenticate using OAuth 1.0a for posting
            self.client = tweepy.Client(
                bearer_token=self.bearer_token,
                consumer_key=self.api_key,
                consumer_secret=self.api_secret,
                access_token=self.access_token,
                access_token_secret=self.access_token_secret,
                wait_on_rate_limit=True
            )
            
            # Create API object for media uploads (v1.1 still needed for this)
            auth = tweepy.OAuth1UserHandler(
                self.api_key,
                self.api_secret,
                self.access_token,
                self.access_token_secret
            )
            self.api = tweepy.API(auth, wait_on_rate_limit=True)
            
            # Test authentication
            me = self.client.get_me()
            if me and me.data:
                logger.info("Twitter authenticated as: @%s", me.data.username)
                return True
            return False
            
        except tweepy.TweepyException as e:
            logger.error("Twitter authentication failed: %s", str(e))
            self._mock_mode = True
            return False
        except Exception as e:
            logger.error("Unexpected error during Twitter authentication: %s", str(e))
            self._mock_mode = True
            return False
    
    def _create_simplified_version(self, content: str) -> str:
        """
        Create a simplified version of the content for error recovery.
        
        Args:
            content: Original content
            
        Returns:
            Simplified content that's more likely to post successfully
        """
        # Remove URLs first (they can cause issues)
        import re
        simplified = re.sub(r'http[s]?://\S+', '', content)
        
        # Remove hashtags
        simplified = re.sub(r'#\w+', '', simplified)
        
        # Remove mentions
        simplified = re.sub(r'@\w+', '', simplified)
        
        # Remove special characters but keep basic punctuation
        simplified = re.sub(r'[^\w\s\.\,\!\?\-\:\;\']', '', simplified)
        
        # Trim to safe length
        if len(simplified) > self.MAX_TWEET_LENGTH - 20:
            simplified = simplified[:self.MAX_TWEET_LENGTH - 23] + "..."
        
        return simplified.strip()
    
    def _split_into_tweets(self, content: str) -> List[str]:
        """
        Split long content into multiple tweets for a thread.
        
        Args:
            content: Content to split
            
        Returns:
            List of tweet strings
        """
        tweets = []
        
        # If content fits in one tweet, return as-is
        if len(content) <= self.MAX_TWEET_LENGTH:
            return [content]
        
        # Split by paragraphs first
        paragraphs = content.split('\n\n')
        current_tweet = ""
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            # If paragraph itself is too long, split by sentences
            if len(paragraph) > self.MAX_TWEET_LENGTH:
                # If we have accumulated content, save it first
                if current_tweet:
                    tweets.append(current_tweet.strip())
                    current_tweet = ""
                
                # Split long paragraph by sentences
                sentences = paragraph.replace('!', '!|').replace('?', '?|').split('|')
                for sentence in sentences:
                    sentence = sentence.strip()
                    if not sentence:
                        continue
                    
                    if len(sentence) > self.MAX_TWEET_LENGTH:
                        # Hard split by characters
                        while len(sentence) > self.MAX_TWEET_LENGTH:
                            tweets.append(sentence[:self.MAX_TWEET_LENGTH - 3] + "...")
                            sentence = sentence[self.MAX_TWEET_LENGTH - 3:]
                        if sentence:
                            tweets.append(sentence)
                    elif len(current_tweet) + len(sentence) + 1 <= self.MAX_TWEET_LENGTH:
                        current_tweet += " " + sentence if current_tweet else sentence
                    else:
                        tweets.append(current_tweet.strip())
                        current_tweet = sentence
            elif len(current_tweet) + len(paragraph) + 2 <= self.MAX_TWEET_LENGTH:
                current_tweet += "\n\n" + paragraph if current_tweet else paragraph
            else:
                tweets.append(current_tweet.strip())
                current_tweet = paragraph
        
        # Don't forget the last tweet
        if current_tweet:
            tweets.append(current_tweet.strip())
        
        # Limit to max thread length
        if len(tweets) > self.MAX_THREAD_LENGTH:
            tweets = tweets[:self.MAX_THREAD_LENGTH]
            tweets[-1] = tweets[-1][:self.MAX_TWEET_LENGTH - 3] + "..."
        
        return tweets
    
    def _upload_media(self, media_path: str) -> Optional[str]:
        """
        Upload media to Twitter and return media_id.
        
        Args:
            media_path: Path to image/video file
            
        Returns:
            Media ID string or None if upload fails
        """
        if self._mock_mode:
            logger.info("MOCK media upload: %s", media_path)
            return "mock_media_id"
        
        if not self.api:
            logger.error("Twitter API not initialized")
            return None
        
        try:
            media = self.api.media_upload(media_path)
            logger.info("Media uploaded successfully: %s", media.media_id)
            return media.media_id
        except tweepy.TweepyException as e:
            logger.error("Media upload failed: %s", str(e))
            return None
        except Exception as e:
            logger.error("Unexpected error during media upload: %s", str(e))
            return None
    
    def post_tweet(
        self,
        content: str,
        media_path: Optional[str] = None,
        reply_to_tweet_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Post a single tweet to Twitter.
        
        Args:
            content: Tweet content
            media_path: Optional path to media file
            reply_to_tweet_id: Optional tweet ID to reply to
            
        Returns:
            Dict with post result including tweet_id
        """
        # Validate content
        if not content or not content.strip():
            return {
                "success": False,
                "error": "Empty content",
                "content": content
            }
        
        # Handle media
        media_ids = None
        if media_path:
            media_id = self._upload_media(media_path)
            if media_id:
                media_ids = [media_id]
        
        if self._mock_mode:
            logger.info("MOCK tweet: %s", content[:100])
            if media_path:
                logger.info("MOCK media: %s", media_path)
            return {
                "success": True,
                "tweet_id": "mock_tweet_id",
                "content": content,
                "media": media_path,
                "mock": True
            }
        
        try:
            # Post the tweet
            tweet_params = {
                "text": content
            }
            if media_ids:
                tweet_params["media_ids"] = media_ids
            if reply_to_tweet_id:
                tweet_params["in_reply_to_tweet_id"] = reply_to_tweet_id
            
            response = self.client.create_tweet(**tweet_params)
            
            tweet_id = response.data["id"]
            logger.info("Tweet posted successfully: %s", tweet_id)
            
            return {
                "success": True,
                "tweet_id": tweet_id,
                "content": content,
                "media": media_path,
                "url": f"https://twitter.com/user/status/{tweet_id}"
            }
            
        except tweepy.TweepyException as e:
            logger.error("Tweet posting failed: %s", str(e))
            error_message = str(e)
            
            # Check if it's a duplicate content error
            if "duplicate" in error_message.lower():
                return {
                    "success": False,
                    "error": "Duplicate content",
                    "error_type": "duplicate",
                    "content": content
                }
            
            # Check if it's a content policy violation
            if "rules" in error_message.lower() or "policy" in error_message.lower():
                return {
                    "success": False,
                    "error": "Content policy violation",
                    "error_type": "policy",
                    "content": content
                }
            
            return {
                "success": False,
                "error": str(e),
                "content": content
            }
        except Exception as e:
            logger.error("Unexpected error posting tweet: %s", str(e))
            return {
                "success": False,
                "error": str(e),
                "content": content
            }
    
    def post_thread(
        self,
        content: str,
        media_paths: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Post a thread of tweets.
        
        Args:
            content: Long-form content to split into tweets
            media_paths: Optional list of media paths for each tweet
            
        Returns:
            Dict with thread result including all tweet IDs
        """
        tweets = self._split_into_tweets(content)
        
        if not tweets:
            return {
                "success": False,
                "error": "No content to post"
            }
        
        if len(tweets) == 1:
            # Just a single tweet
            media_path = media_paths[0] if media_paths else None
            return self.post_tweet(tweets[0], media_path)
        
        tweet_ids = []
        parent_tweet_id = None
        
        for i, tweet_content in enumerate(tweets):
            media_path = media_paths[i] if media_paths and i < len(media_paths) else None
            
            result = self.post_tweet(
                tweet_content,
                media_path,
                reply_to_tweet_id=parent_tweet_id
            )
            
            if not result["success"]:
                return {
                    "success": False,
                    "error": f"Thread failed at tweet {i + 1}",
                    "tweet_ids": tweet_ids,
                    "failed_at": i
                }
            
            tweet_ids.append(result["tweet_id"])
            parent_tweet_id = result["tweet_id"]
        
        return {
            "success": True,
            "tweet_ids": tweet_ids,
            "thread_length": len(tweet_ids),
            "urls": [f"https://twitter.com/user/status/{tid}" for tid in tweet_ids]
        }
    
    def post_with_error_recovery(
        self,
        content: str,
        media_path: Optional[str] = None,
        max_attempts: int = 3
    ) -> Dict[str, Any]:
        """
        Post a tweet with automatic error recovery.
        
        If posting fails, creates a simplified version and retries.
        
        Args:
            content: Tweet content
            media_path: Optional media path
            max_attempts: Maximum retry attempts
            
        Returns:
            Dict with post result
        """
        last_error = None
        attempt = 0
        current_content = content
        
        while attempt < max_attempts:
            attempt += 1
            logger.info("Twitter post attempt %d/%d", attempt, max_attempts)
            
            result = self.post_tweet(current_content, media_path)
            
            if result["success"]:
                result["attempts"] = attempt
                result["final_content"] = current_content
                return result
            
            last_error = result.get("error", "Unknown error")
            logger.warning("Twitter post failed (attempt %d): %s", attempt, last_error)
            
            # If we have more attempts left, try simplified version
            if attempt < max_attempts:
                current_content = self._create_simplified_version(current_content)
                logger.info("Retrying with simplified content: %s", current_content[:100])
                media_path = None  # Remove media on retry to reduce complexity
        
        # All attempts failed
        logger.error("All Twitter post attempts failed")
        return {
            "success": False,
            "error": f"All {max_attempts} attempts failed. Last error: {last_error}",
            "original_content": content,
            "attempts": attempt
        }


# Convenience function for quick posting
def post_to_twitter(
    content: str,
    media_path: Optional[str] = None,
    use_thread: bool = False
) -> Dict[str, Any]:
    """
    Quick function to post content to Twitter.
    
    Args:
        content: Content to post
        media_path: Optional media path
        use_thread: Whether to split into thread if long
        
    Returns:
        Dict with post result
    """
    poster = TwitterPoster()
    
    if use_thread:
        return poster.post_thread(content, [media_path] if media_path else None)
    else:
        return poster.post_with_error_recovery(content, media_path)


if __name__ == "__main__":
    # Test the Twitter Poster
    logging.basicConfig(level=logging.INFO)
    
    print("Testing Twitter Poster...")
    twitter = TwitterPoster()
    
    # Test single tweet
    result = twitter.post_tweet(
        content="Testing the AI Employee Vault Gold Tier! 🚀 #AI #Automation"
    )
    print(f"Single Tweet Result: {result}")
    
    # Test thread
    long_content = """
    This is a test thread to demonstrate the Twitter posting capabilities.
    
    Thread tweets are automatically split when content exceeds 280 characters.
    
    The AI Employee system can now post to multiple platforms!
    """
    result = twitter.post_thread(long_content)
    print(f"Thread Result: {result}")
    
    # Test error recovery
    result = twitter.post_with_error_recovery(
        content="Testing error recovery with a very long post " + "x" * 500
    )
    print(f"Error Recovery Result: {result}")
