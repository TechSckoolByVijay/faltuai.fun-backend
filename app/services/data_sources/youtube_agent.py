"""
YouTube Data API Integration for Learning Resources

Uses YouTube Data API v3 to fetch:
- Educational video content and channels
- Course playlists with view counts and ratings
- Tutorial series popularity
"""

import aiohttp
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import os

logger = logging.getLogger(__name__)


class YouTubeResourceAgent:
    """Agent for discovering learning resources on YouTube"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("YOUTUBE_API_KEY")
        self.base_url = "https://www.googleapis.com/youtube/v3"
        self.session: Optional[aiohttp.ClientSession] = None
        
        if not self.api_key:
            logger.warning("YouTube API key not configured. Video search disabled.")
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close(self):
        """Close aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def search_videos(
        self,
        query: str,
        max_results: int = 25,
        order: str = "relevance",  # relevance, viewCount, rating, date
        video_duration: str = "any"  # any, short (<4min), medium (4-20min), long (>20min)
    ) -> List[Dict[str, Any]]:
        """
        Search for YouTube videos
        
        Args:
            query: Search query
            max_results: Number of results (max 50 per request)
            order: Sort order
            video_duration: Filter by duration
        """
        if not self.api_key:
            logger.error("YouTube API key not configured")
            return []
        
        endpoint = f"{self.base_url}/search"
        params = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": min(max_results, 50),
            "order": order,
            "videoDuration": video_duration,
            "key": self.api_key
        }
        
        try:
            session = await self._get_session()
            async with session.get(endpoint, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    items = data.get("items", [])
                    logger.info(f"Found {len(items)} videos for '{query}'")
                    
                    # Get video statistics for these videos
                    video_ids = [item["id"]["videoId"] for item in items]
                    stats = await self._get_video_statistics(video_ids)
                    
                    # Merge search results with statistics
                    enriched_items = []
                    for item in items:
                        video_id = item["id"]["videoId"]
                        item["statistics"] = stats.get(video_id, {})
                        enriched_items.append(item)
                    
                    return enriched_items
                else:
                    error_text = await response.text()
                    logger.error(f"YouTube API error {response.status}: {error_text}")
                    return []
        except Exception as e:
            logger.error(f"YouTube search failed for '{query}': {e}")
            return []
    
    async def _get_video_statistics(self, video_ids: List[str]) -> Dict[str, Dict]:
        """Get statistics (views, likes, etc.) for multiple videos"""
        if not video_ids:
            return {}
        
        endpoint = f"{self.base_url}/videos"
        params = {
            "part": "statistics,contentDetails",
            "id": ",".join(video_ids),
            "key": self.api_key
        }
        
        try:
            session = await self._get_session()
            async with session.get(endpoint, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    stats_map = {}
                    for item in data.get("items", []):
                        video_id = item.get("id")
                        stats_map[video_id] = {
                            "view_count": int(item.get("statistics", {}).get("viewCount", 0)),
                            "like_count": int(item.get("statistics", {}).get("likeCount", 0)),
                            "comment_count": int(item.get("statistics", {}).get("commentCount", 0)),
                            "duration": item.get("contentDetails", {}).get("duration", "")
                        }
                    
                    return stats_map
        except Exception as e:
            logger.error(f"Failed to fetch video statistics: {e}")
        
        return {}
    
    async def search_channels(
        self,
        query: str,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """Search for YouTube channels"""
        if not self.api_key:
            return []
        
        endpoint = f"{self.base_url}/search"
        params = {
            "part": "snippet",
            "q": query,
            "type": "channel",
            "maxResults": min(max_results, 50),
            "key": self.api_key
        }
        
        try:
            session = await self._get_session()
            async with session.get(endpoint, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    items = data.get("items", [])
                    
                    # Get channel statistics
                    channel_ids = [item["id"]["channelId"] for item in items]
                    stats = await self._get_channel_statistics(channel_ids)
                    
                    # Merge results
                    for item in items:
                        channel_id = item["id"]["channelId"]
                        item["statistics"] = stats.get(channel_id, {})
                    
                    return items
                else:
                    logger.error(f"YouTube channel search failed: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Channel search failed: {e}")
            return []
    
    async def _get_channel_statistics(self, channel_ids: List[str]) -> Dict[str, Dict]:
        """Get statistics for multiple channels"""
        if not channel_ids:
            return {}
        
        endpoint = f"{self.base_url}/channels"
        params = {
            "part": "statistics,snippet",
            "id": ",".join(channel_ids),
            "key": self.api_key
        }
        
        try:
            session = await self._get_session()
            async with session.get(endpoint, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    stats_map = {}
                    for item in data.get("items", []):
                        channel_id = item.get("id")
                        stats_map[channel_id] = {
                            "subscriber_count": int(item.get("statistics", {}).get("subscriberCount", 0)),
                            "video_count": int(item.get("statistics", {}).get("videoCount", 0)),
                            "view_count": int(item.get("statistics", {}).get("viewCount", 0)),
                            "description": item.get("snippet", {}).get("description", "")
                        }
                    
                    return stats_map
        except Exception as e:
            logger.error(f"Failed to fetch channel statistics: {e}")
        
        return {}
    
    async def find_learning_content(
        self,
        topic: str,
        experience_level: str,
        content_type: str = "tutorial"  # tutorial, course, crash_course, project
    ) -> Dict[str, Any]:
        """
        Find educational content for a specific topic
        
        Returns:
            - Top tutorial videos
            - Popular educational channels
            - Course playlists
        """
        logger.info(f"Finding learning content for {topic} at {experience_level} level")
        
        # Build search queries based on experience level
        level_modifier = {
            "beginner": "beginner tutorial complete guide",
            "intermediate": "intermediate advanced tutorial",
            "advanced": "advanced deep dive masterclass"
        }.get(experience_level, "tutorial")
        
        content_queries = {
            "tutorial": f"{topic} {level_modifier} 2024 2025",
            "course": f"{topic} full course {level_modifier}",
            "crash_course": f"{topic} crash course {experience_level}",
            "project": f"{topic} project tutorial {experience_level}"
        }
        
        query = content_queries.get(content_type, content_queries["tutorial"])
        
        # Search for videos
        videos = await self.search_videos(query, max_results=20, order="relevance")
        
        # Search for educational channels
        channels = await self.search_channels(f"{topic} programming tutorial", max_results=10)
        
        # Parse and rank results
        top_videos = self._rank_educational_videos(videos)
        top_channels = self._rank_channels(channels)
        
        return {
            "topic": topic,
            "experience_level": experience_level,
            "top_videos": top_videos[:10],
            "recommended_channels": top_channels[:5],
            "total_videos_found": len(videos),
            "total_channels_found": len(channels),
            "search_timestamp": datetime.utcnow().isoformat(),
            "data_source": "YouTube Data API v3"
        }
    
    async def find_course_playlists(
        self,
        topic: str,
        min_videos: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find comprehensive course playlists
        
        Playlists are better for structured learning paths
        """
        if not self.api_key:
            return []
        
        endpoint = f"{self.base_url}/search"
        params = {
            "part": "snippet",
            "q": f"{topic} complete course playlist",
            "type": "playlist",
            "maxResults": 20,
            "key": self.api_key
        }
        
        try:
            session = await self._get_session()
            async with session.get(endpoint, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    playlists = []
                    
                    for item in data.get("items", []):
                        playlist_id = item["id"]["playlistId"]
                        snippet = item.get("snippet", {})
                        
                        # Get playlist details
                        playlist_info = await self._get_playlist_details(playlist_id)
                        
                        if playlist_info and playlist_info.get("video_count", 0) >= min_videos:
                            playlists.append({
                                "title": snippet.get("title"),
                                "description": snippet.get("description"),
                                "channel_title": snippet.get("channelTitle"),
                                "playlist_id": playlist_id,
                                "url": f"https://www.youtube.com/playlist?list={playlist_id}",
                                "video_count": playlist_info.get("video_count"),
                                "thumbnails": snippet.get("thumbnails", {})
                            })
                        
                        await asyncio.sleep(0.2)  # Rate limiting
                    
                    return playlists
        except Exception as e:
            logger.error(f"Playlist search failed: {e}")
        
        return []
    
    async def _get_playlist_details(self, playlist_id: str) -> Optional[Dict]:
        """Get details about a playlist"""
        endpoint = f"{self.base_url}/playlists"
        params = {
            "part": "contentDetails",
            "id": playlist_id,
            "key": self.api_key
        }
        
        try:
            session = await self._get_session()
            async with session.get(endpoint, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    items = data.get("items", [])
                    if items:
                        return {
                            "video_count": items[0].get("contentDetails", {}).get("itemCount", 0)
                        }
        except Exception as e:
            logger.error(f"Failed to fetch playlist details: {e}")
        
        return None
    
    def _rank_educational_videos(self, videos: List[Dict]) -> List[Dict[str, Any]]:
        """Rank videos by educational value (views, engagement, recency)"""
        ranked = []
        
        for video in videos:
            snippet = video.get("snippet", {})
            stats = video.get("statistics", {})
            
            # Calculate educational score
            views = stats.get("view_count", 0)
            likes = stats.get("like_count", 0)
            
            # Engagement rate
            engagement_rate = (likes / views * 100) if views > 0 else 0
            
            # Educational indicators in title/description
            title = snippet.get("title", "").lower()
            description = snippet.get("description", "").lower()
            
            edu_keywords = ["tutorial", "course", "learn", "guide", "explained", "beginners", "complete"]
            edu_score = sum(1 for keyword in edu_keywords if keyword in title or keyword in description)
            
            # Combined score
            score = (views / 1000) + (engagement_rate * 10) + (edu_score * 100)
            
            ranked.append({
                "title": snippet.get("title"),
                "channel": snippet.get("channelTitle"),
                "description": snippet.get("description", "")[:200],
                "video_id": video["id"]["videoId"],
                "url": f"https://www.youtube.com/watch?v={video['id']['videoId']}",
                "views": views,
                "likes": likes,
                "published_at": snippet.get("publishedAt"),
                "thumbnail": snippet.get("thumbnails", {}).get("high", {}).get("url"),
                "educational_score": round(score, 2)
            })
        
        # Sort by score
        ranked.sort(key=lambda x: x["educational_score"], reverse=True)
        
        return ranked
    
    def _rank_channels(self, channels: List[Dict]) -> List[Dict[str, Any]]:
        """Rank channels by subscriber count and content quality"""
        ranked = []
        
        for channel in channels:
            snippet = channel.get("snippet", {})
            stats = channel.get("statistics", {})
            
            ranked.append({
                "channel_name": snippet.get("title"),
                "description": stats.get("description", "")[:200],
                "channel_id": channel["id"]["channelId"],
                "url": f"https://www.youtube.com/channel/{channel['id']['channelId']}",
                "subscribers": stats.get("subscriber_count", 0),
                "total_videos": stats.get("video_count", 0),
                "total_views": stats.get("view_count", 0),
                "thumbnail": snippet.get("thumbnails", {}).get("high", {}).get("url")
            })
        
        # Sort by subscribers
        ranked.sort(key=lambda x: x["subscribers"], reverse=True)
        
        return ranked


# Global instance
youtube_agent = YouTubeResourceAgent()
