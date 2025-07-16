"""
Scheduler module for the Trading Information Scraper application.

This module provides functionality for scheduling and executing tasks at specified intervals.
"""

import logging
import signal
import sys
import time
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Union

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)


class Scheduler:
    """
    Scheduler for executing tasks at specified intervals.
    
    This class provides methods for scheduling and managing tasks.
    """
    
    def __init__(self):
        """Initialize the scheduler."""
        self.scheduler = BackgroundScheduler()
        self.jobs = {}
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)
    
    def start(self):
        """Start the scheduler."""
        try:
            self.scheduler.start()
            logger.info("Scheduler started")
        except Exception as e:
            logger.error(f"Error starting scheduler: {e}")
            raise
    
    def shutdown(self):
        """Shutdown the scheduler."""
        try:
            self.scheduler.shutdown()
            logger.info("Scheduler shut down")
        except Exception as e:
            logger.error(f"Error shutting down scheduler: {e}")
    
    def add_job(
        self,
        func: Callable,
        job_id: str,
        trigger: str = 'interval',
        **kwargs
    ) -> str:
        """
        Add a job to the scheduler.
        
        Args:
            func: Function to execute
            job_id: Unique identifier for the job
            trigger: Trigger type ('interval', 'cron', 'date')
            **kwargs: Additional arguments for the trigger
            
        Returns:
            Job ID
        """
        try:
            job = self.scheduler.add_job(func, trigger, id=job_id, **kwargs)
            self.jobs[job_id] = job
            logger.info(f"Job {job_id} added with trigger {trigger}")
            return job_id
        except Exception as e:
            logger.error(f"Error adding job {job_id}: {e}")
            raise
    
    def remove_job(self, job_id: str) -> bool:
        """
        Remove a job from the scheduler.
        
        Args:
            job_id: Job ID to remove
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.scheduler.remove_job(job_id)
            if job_id in self.jobs:
                del self.jobs[job_id]
            logger.info(f"Job {job_id} removed")
            return True
        except Exception as e:
            logger.error(f"Error removing job {job_id}: {e}")
            return False
    
    def pause_job(self, job_id: str) -> bool:
        """
        Pause a job.
        
        Args:
            job_id: Job ID to pause
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.scheduler.pause_job(job_id)
            logger.info(f"Job {job_id} paused")
            return True
        except Exception as e:
            logger.error(f"Error pausing job {job_id}: {e}")
            return False
    
    def resume_job(self, job_id: str) -> bool:
        """
        Resume a paused job.
        
        Args:
            job_id: Job ID to resume
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.scheduler.resume_job(job_id)
            logger.info(f"Job {job_id} resumed")
            return True
        except Exception as e:
            logger.error(f"Error resuming job {job_id}: {e}")
            return False
    
    def get_jobs(self) -> List[Dict]:
        """
        Get information about all jobs.
        
        Returns:
            List of job information dictionaries
        """
        try:
            jobs = []
            for job in self.scheduler.get_jobs():
                job_info = {
                    'id': job.id,
                    'name': job.name,
                    'trigger': str(job.trigger),
                    'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                    'pending': job.pending
                }
                jobs.append(job_info)
            return jobs
        except Exception as e:
            logger.error(f"Error getting jobs: {e}")
            return []
    
    def get_job(self, job_id: str) -> Optional[Dict]:
        """
        Get information about a specific job.
        
        Args:
            job_id: Job ID to get information for
            
        Returns:
            Job information dictionary or None if not found
        """
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                job_info = {
                    'id': job.id,
                    'name': job.name,
                    'trigger': str(job.trigger),
                    'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                    'pending': job.pending
                }
                return job_info
            return None
        except Exception as e:
            logger.error(f"Error getting job {job_id}: {e}")
            return None
    
    def schedule_task(
        self,
        func: Callable,
        frequency: str = 'once',
        interval: Optional[int] = None,
        time: Optional[str] = None,
        job_id: Optional[str] = None,
        **kwargs
    ) -> Optional[str]:
        """
        Schedule a task with a specified frequency.
        
        Args:
            func: Function to execute
            frequency: Frequency ('once', 'hourly', 'daily', 'weekly', 'monthly', 'interval')
            interval: Interval in seconds (for 'interval' frequency)
            time: Time of day (for 'daily', 'weekly', 'monthly' frequencies)
            job_id: Unique identifier for the job (if None, generate one)
            **kwargs: Additional arguments for the function
            
        Returns:
            Job ID or None if scheduling fails
        """
        try:
            # Generate a job ID if not provided
            if not job_id:
                job_id = f"task_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                
            # Create a wrapper function that passes kwargs to the original function
            def task_wrapper():
                try:
                    logger.info(f"Executing task {job_id}")
                    result = func(**kwargs)
                    logger.info(f"Task {job_id} completed")
                    return result
                except Exception as e:
                    logger.error(f"Error executing task {job_id}: {e}")
                    raise
            
            # Schedule based on frequency
            if frequency == 'once':
                # Execute once immediately
                self.scheduler.add_job(task_wrapper, 'date', run_date=datetime.now(), id=job_id)
                logger.info(f"Task {job_id} scheduled to run once immediately")
            
            elif frequency == 'hourly':
                # Execute every hour
                self.scheduler.add_job(task_wrapper, 'interval', hours=1, id=job_id)
                logger.info(f"Task {job_id} scheduled to run hourly")
            
            elif frequency == 'daily':
                # Execute daily at the specified time
                hour, minute = 0, 0
                if time:
                    try:
                        hour, minute = map(int, time.split(':'))
                    except ValueError:
                        logger.warning(f"Invalid time format: {time}, using 00:00")
                
                self.scheduler.add_job(
                    task_wrapper,
                    'cron',
                    hour=hour,
                    minute=minute,
                    id=job_id
                )
                logger.info(f"Task {job_id} scheduled to run daily at {hour:02d}:{minute:02d}")
            
            elif frequency == 'weekly':
                # Execute weekly at the specified time
                day_of_week = kwargs.get('day_of_week', 0)  # Monday by default
                hour, minute = 0, 0
                if time:
                    try:
                        hour, minute = map(int, time.split(':'))
                    except ValueError:
                        logger.warning(f"Invalid time format: {time}, using 00:00")
                
                self.scheduler.add_job(
                    task_wrapper,
                    'cron',
                    day_of_week=day_of_week,
                    hour=hour,
                    minute=minute,
                    id=job_id
                )
                logger.info(f"Task {job_id} scheduled to run weekly on day {day_of_week} at {hour:02d}:{minute:02d}")
            
            elif frequency == 'monthly':
                # Execute monthly at the specified time
                day = kwargs.get('day', 1)  # First day of the month by default
                hour, minute = 0, 0
                if time:
                    try:
                        hour, minute = map(int, time.split(':'))
                    except ValueError:
                        logger.warning(f"Invalid time format: {time}, using 00:00")
                
                self.scheduler.add_job(
                    task_wrapper,
                    'cron',
                    day=day,
                    hour=hour,
                    minute=minute,
                    id=job_id
                )
                logger.info(f"Task {job_id} scheduled to run monthly on day {day} at {hour:02d}:{minute:02d}")
            
            elif frequency == 'interval':
                # Execute at the specified interval
                if not interval:
                    interval = 3600  # Default to 1 hour
                
                self.scheduler.add_job(
                    task_wrapper,
                    'interval',
                    seconds=interval,
                    id=job_id
                )
                logger.info(f"Task {job_id} scheduled to run every {interval} seconds")
            
            else:
                logger.warning(f"Unknown frequency: {frequency}")
                return None
            
            # Store the job
            self.jobs[job_id] = self.scheduler.get_job(job_id)
            
            return job_id
        except Exception as e:
            logger.error(f"Error scheduling task: {e}")
            return None
    
    def run_task_now(self, job_id: str) -> bool:
        """
        Run a scheduled task immediately.
        
        Args:
            job_id: Job ID to run
            
        Returns:
            True if successful, False otherwise
        """
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                job.func()
                logger.info(f"Task {job_id} executed manually")
                return True
            else:
                logger.warning(f"Task {job_id} not found")
                return False
        except Exception as e:
            logger.error(f"Error running task {job_id}: {e}")
            return False
    
    def _handle_shutdown(self, signum, frame):
        """
        Handle shutdown signals.
        
        Args:
            signum: Signal number
            frame: Current stack frame
        """
        logger.info(f"Received signal {signum}, shutting down scheduler")
        self.shutdown()
        sys.exit(0)


def create_scheduler_from_config(config: Dict) -> Scheduler:
    """
    Create a scheduler based on configuration settings.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Configured scheduler
    """
    scheduler = Scheduler()
    
    # Start the scheduler
    scheduler.start()
    
    return scheduler