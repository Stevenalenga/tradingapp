"""
Alternative.me scraper module for the Trading Information Scraper application.

This module provides functionality for scraping the Crypto Fear & Greed Index from Alternative.me.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional

import requests

from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class AlternativeMeScraper(BaseScraper):
    """
    Scraper for Alternative.me Crypto Fear & Greed Index.
    
    This class provides methods for scraping the Fear & Greed Index and related market sentiment data.
    """
    
    BASE_URL = "https://api.alternative.me"
    FEAR_GREED_URL = BASE_URL + "/fng/"
    
    def __init__(self, **kwargs):
        """Initialize the Alternative.me scraper."""
        super().__init__(**kwargs)
    
    def scrape(self, days: int = 30, include_historical: bool = True) -> Dict:
        """
        Scrape Fear & Greed Index data from Alternative.me.
        
        Args:
            days: Number of days of historical data to fetch (max 200, 0 for current only)
            include_historical: Whether to include historical data analysis
            
        Returns:
            Dictionary with Fear & Greed Index data
        """
        result = {
            "timestamp": datetime.now().isoformat(),
            "source": "Alternative.me",
            "fear_greed_index": {},
            "analysis": {}
        }
        
        try:
            # Get current Fear & Greed Index
            current_data = self.get_current_fear_greed_index()
            result["fear_greed_index"]["current"] = current_data
            
            # Get historical data if requested
            if include_historical and days > 1:
                historical_data = self.get_historical_fear_greed_index(days)
                result["fear_greed_index"]["historical"] = historical_data
                
                # Perform analysis on historical data
                if historical_data:
                    result["analysis"] = self.analyze_fear_greed_trends(historical_data)
            
        except Exception as e:
            logger.error(f"Error scraping from Alternative.me: {e}")
            result["error"] = str(e)
        
        return result
    
    def get_current_fear_greed_index(self) -> Dict:
        """
        Get the current Fear & Greed Index.
        
        Returns:
            Dictionary with current Fear & Greed Index data
        """
        try:
            response = self._make_request(self.FEAR_GREED_URL)
            data = response.json()
            
            if 'data' not in data or not data['data']:
                return {"error": "No data available"}
            
            current = data['data'][0]
            
            return {
                "value": int(current.get('value', 0)),
                "value_classification": current.get('value_classification', ''),
                "timestamp": current.get('timestamp', ''),
                "time_until_update": current.get('time_until_update', ''),
                "interpretation": self._interpret_fear_greed_value(int(current.get('value', 0)))
            }
        
        except Exception as e:
            logger.error(f"Error getting current Fear & Greed Index: {e}")
            return {"error": str(e)}
    
    def get_historical_fear_greed_index(self, days: int = 30) -> List[Dict]:
        """
        Get historical Fear & Greed Index data.
        
        Args:
            days: Number of days of historical data (max 200)
            
        Returns:
            List of historical Fear & Greed Index data
        """
        try:
            # Limit days to maximum allowed by API
            days = min(days, 200)
            
            url = f"{self.FEAR_GREED_URL}?limit={days}"
            response = self._make_request(url)
            data = response.json()
            
            if 'data' not in data:
                return []
            
            historical_data = []
            for entry in data['data']:
                historical_data.append({
                    "value": int(entry.get('value', 0)),
                    "value_classification": entry.get('value_classification', ''),
                    "timestamp": entry.get('timestamp', ''),
                    "date": datetime.fromtimestamp(int(entry.get('timestamp', 0))).strftime('%Y-%m-%d') if entry.get('timestamp') else ''
                })
            
            return historical_data
        
        except Exception as e:
            logger.error(f"Error getting historical Fear & Greed Index: {e}")
            return []
    
    def analyze_fear_greed_trends(self, historical_data: List[Dict]) -> Dict:
        """
        Analyze trends in Fear & Greed Index data.
        
        Args:
            historical_data: List of historical Fear & Greed Index data
            
        Returns:
            Dictionary with trend analysis
        """
        try:
            if not historical_data:
                return {"error": "No historical data available for analysis"}
            
            values = [entry['value'] for entry in historical_data]
            classifications = [entry['value_classification'] for entry in historical_data]
            
            # Basic statistics
            current_value = values[0] if values else 0
            average_value = sum(values) / len(values) if values else 0
            min_value = min(values) if values else 0
            max_value = max(values) if values else 0
            
            # Trend analysis
            trend_direction = "neutral"
            if len(values) >= 7:
                recent_avg = sum(values[:7]) / 7  # Last 7 days
                older_avg = sum(values[7:14]) / 7 if len(values) >= 14 else average_value
                
                if recent_avg > older_avg + 5:
                    trend_direction = "increasing"
                elif recent_avg < older_avg - 5:
                    trend_direction = "decreasing"
            
            # Classification distribution
            classification_counts = {}
            for classification in classifications:
                classification_counts[classification] = classification_counts.get(classification, 0) + 1
            
            # Calculate percentages
            total_entries = len(classifications)
            classification_percentages = {
                k: (v / total_entries) * 100 for k, v in classification_counts.items()
            } if total_entries > 0 else {}
            
            # Volatility (standard deviation)
            volatility = 0
            if len(values) > 1:
                variance = sum((x - average_value) ** 2 for x in values) / len(values)
                volatility = variance ** 0.5
            
            return {
                "current_value": current_value,
                "current_classification": historical_data[0]['value_classification'] if historical_data else '',
                "period_average": round(average_value, 2),
                "period_min": min_value,
                "period_max": max_value,
                "trend_direction": trend_direction,
                "volatility": round(volatility, 2),
                "classification_distribution": classification_percentages,
                "days_analyzed": len(historical_data),
                "interpretation": self._interpret_trend_analysis(current_value, average_value, trend_direction, volatility)
            }
        
        except Exception as e:
            logger.error(f"Error analyzing Fear & Greed trends: {e}")
            return {"error": str(e)}
    
    def _interpret_fear_greed_value(self, value: int) -> Dict:
        """
        Interpret a Fear & Greed Index value.
        
        Args:
            value: Fear & Greed Index value (0-100)
            
        Returns:
            Dictionary with interpretation
        """
        try:
            interpretations = {
                "market_sentiment": "",
                "typical_behavior": "",
                "investment_implication": "",
                "risk_level": ""
            }
            
            if value <= 25:
                interpretations.update({
                    "market_sentiment": "Extreme Fear",
                    "typical_behavior": "Investors are very worried. Market may be oversold.",
                    "investment_implication": "Potential buying opportunity for contrarian investors",
                    "risk_level": "High volatility expected"
                })
            elif value <= 45:
                interpretations.update({
                    "market_sentiment": "Fear",
                    "typical_behavior": "Investors are cautious and selling",
                    "investment_implication": "Market may be approaching attractive levels",
                    "risk_level": "Moderate to high volatility"
                })
            elif value <= 55:
                interpretations.update({
                    "market_sentiment": "Neutral",
                    "typical_behavior": "Balanced market sentiment",
                    "investment_implication": "Wait for clearer directional signals",
                    "risk_level": "Normal market conditions"
                })
            elif value <= 75:
                interpretations.update({
                    "market_sentiment": "Greed",
                    "typical_behavior": "Investors are getting greedy and buying",
                    "investment_implication": "Market may be getting expensive, consider taking profits",
                    "risk_level": "Moderate volatility"
                })
            else:
                interpretations.update({
                    "market_sentiment": "Extreme Greed",
                    "typical_behavior": "Investors are very greedy. Market may be overbought.",
                    "investment_implication": "High risk of correction, consider reducing exposure",
                    "risk_level": "High volatility and correction risk"
                })
            
            return interpretations
        
        except Exception as e:
            logger.warning(f"Error interpreting Fear & Greed value: {e}")
            return {"error": "Unable to interpret value"}
    
    def _interpret_trend_analysis(self, current: int, average: float, trend: str, volatility: float) -> Dict:
        """
        Interpret the overall trend analysis.
        
        Args:
            current: Current Fear & Greed value
            average: Average value over the period
            trend: Trend direction
            volatility: Volatility measure
            
        Returns:
            Dictionary with overall interpretation
        """
        try:
            interpretation = {
                "overall_assessment": "",
                "market_phase": "",
                "recommendation": ""
            }
            
            # Determine market phase
            if current <= 25 and trend == "decreasing":
                interpretation["market_phase"] = "Capitulation/Bottom Formation"
                interpretation["overall_assessment"] = "Market is in extreme fear with declining sentiment"
                interpretation["recommendation"] = "Strong contrarian buying opportunity, but wait for trend reversal"
            elif current <= 25 and trend == "increasing":
                interpretation["market_phase"] = "Recovery from Fear"
                interpretation["overall_assessment"] = "Market showing signs of recovery from extreme fear"
                interpretation["recommendation"] = "Good accumulation opportunity as fear subsides"
            elif current >= 75 and trend == "increasing":
                interpretation["market_phase"] = "Euphoria/Top Formation"
                interpretation["overall_assessment"] = "Market in extreme greed with increasing optimism"
                interpretation["recommendation"] = "High risk of correction, consider profit-taking"
            elif current >= 75 and trend == "decreasing":
                interpretation["market_phase"] = "Peak Distribution"
                interpretation["overall_assessment"] = "Greed levels high but showing signs of cooling"
                interpretation["recommendation"] = "Caution advised, prepare for potential downturn"
            else:
                interpretation["market_phase"] = "Transitional"
                interpretation["overall_assessment"] = f"Market in {trend} trend with moderate sentiment"
                interpretation["recommendation"] = "Monitor for clearer directional signals"
            
            # Add volatility context
            if volatility > 15:
                interpretation["volatility_note"] = "High volatility indicates unstable sentiment"
            elif volatility < 5:
                interpretation["volatility_note"] = "Low volatility suggests stable sentiment"
            else:
                interpretation["volatility_note"] = "Moderate volatility indicates normal market conditions"
            
            return interpretation
        
        except Exception as e:
            logger.warning(f"Error interpreting trend analysis: {e}")
            return {"error": "Unable to interpret trend"}
    
    def get_fear_greed_summary(self) -> Dict:
        """
        Get a quick summary of the current Fear & Greed Index.
        
        Returns:
            Dictionary with Fear & Greed summary
        """
        try:
            current_data = self.get_current_fear_greed_index()
            
            if "error" in current_data:
                return current_data
            
            value = current_data.get('value', 0)
            classification = current_data.get('value_classification', '')
            
            return {
                "value": value,
                "classification": classification,
                "emoji": self._get_sentiment_emoji(value),
                "quick_interpretation": self._get_quick_interpretation(value),
                "timestamp": current_data.get('timestamp', ''),
                "source": "Alternative.me"
            }
        
        except Exception as e:
            logger.error(f"Error getting Fear & Greed summary: {e}")
            return {"error": str(e)}
    
    def _get_sentiment_emoji(self, value: int) -> str:
        """Get emoji representation for sentiment value."""
        if value <= 25:
            return "😨"  # Extreme Fear
        elif value <= 45:
            return "😟"  # Fear
        elif value <= 55:
            return "😐"  # Neutral
        elif value <= 75:
            return "😊"  # Greed
        else:
            return "🤑"  # Extreme Greed
    
    def _get_quick_interpretation(self, value: int) -> str:
        """Get quick interpretation for sentiment value."""
        if value <= 25:
            return "Market in extreme fear - potential buying opportunity"
        elif value <= 45:
            return "Fearful market - approach with caution"
        elif value <= 55:
            return "Neutral sentiment - wait for clearer signals"
        elif value <= 75:
            return "Greedy market - consider taking profits"
        else:
            return "Extreme greed - high risk of correction"
