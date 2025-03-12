"""
Utility for managing and rotating proxies.
"""

import asyncio
import aiohttp
import random
from typing import List, Optional, Dict
import logging
from ..config import ProxyConfig, PROXY_TIMEOUT

logger = logging.getLogger(__name__)

class ProxyManager:
    def __init__(self, proxies: Optional[List[ProxyConfig]] = None):
        """
        Initialize the proxy manager.
        
        Args:
            proxies (Optional[List[ProxyConfig]]): List of proxy configurations.
        """
        self.proxies = proxies or []
        self.working_proxies: List[ProxyConfig] = []
        self.failed_proxies: List[ProxyConfig] = []
        self._current_index = 0

    async def validate_proxy(self, proxy: ProxyConfig) -> bool:
        """
        Validate a proxy by testing its connection.
        
        Args:
            proxy (ProxyConfig): The proxy configuration to validate.
            
        Returns:
            bool: True if the proxy is working, False otherwise.
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    'https://httpbin.org/ip',
                    proxy=proxy.http,
                    timeout=PROXY_TIMEOUT
                ) as response:
                    if response.status == 200:
                        return True
        except Exception as e:
            logger.debug(f"Proxy validation failed for {proxy.proxy_str}: {str(e)}")
        return False

    async def validate_all_proxies(self):
        """Validate all proxies and update the working/failed lists."""
        tasks = [self.validate_proxy(proxy) for proxy in self.proxies]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        self.working_proxies = []
        self.failed_proxies = []
        
        for proxy, is_valid in zip(self.proxies, results):
            if isinstance(is_valid, bool) and is_valid:
                self.working_proxies.append(proxy)
            else:
                self.failed_proxies.append(proxy)

    def get_next_proxy(self) -> Optional[Dict[str, str]]:
        """
        Get the next working proxy in rotation.
        
        Returns:
            Optional[Dict[str, str]]: Proxy configuration dictionary or None if no working proxies.
        """
        if not self.working_proxies:
            return None
            
        proxy = self.working_proxies[self._current_index]
        self._current_index = (self._current_index + 1) % len(self.working_proxies)
        return proxy.as_dict()

    def get_random_proxy(self) -> Optional[Dict[str, str]]:
        """
        Get a random working proxy.
        
        Returns:
            Optional[Dict[str, str]]: Random proxy configuration dictionary or None if no working proxies.
        """
        if not self.working_proxies:
            return None
            
        proxy = random.choice(self.working_proxies)
        return proxy.as_dict()

    def mark_proxy_failed(self, proxy_str: str):
        """
        Mark a proxy as failed and remove it from the working proxies list.
        
        Args:
            proxy_str (str): The proxy string to mark as failed.
        """
        for proxy in self.working_proxies[:]:
            if proxy.proxy_str == proxy_str:
                self.working_proxies.remove(proxy)
                self.failed_proxies.append(proxy)
                break

    def mark_proxy_working(self, proxy_str: str):
        """
        Mark a proxy as working and move it to the working proxies list.
        
        Args:
            proxy_str (str): The proxy string to mark as working.
        """
        for proxy in self.failed_proxies[:]:
            if proxy.proxy_str == proxy_str:
                self.failed_proxies.remove(proxy)
                if proxy not in self.working_proxies:
                    self.working_proxies.append(proxy)
                break

    @property
    def has_working_proxies(self) -> bool:
        """Check if there are any working proxies available."""
        return len(self.working_proxies) > 0

    def __len__(self) -> int:
        """Get the total number of proxies."""
        return len(self.proxies)

    @property
    def working_count(self) -> int:
        """Get the number of working proxies."""
        return len(self.working_proxies)

    @property
    def failed_count(self) -> int:
        """Get the number of failed proxies."""
        return len(self.failed_proxies) 