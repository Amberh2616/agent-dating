"""
Django 管理命令: 執行 Agent 調度器

用法:
    python manage.py runscheduler

這會啟動 APScheduler，每 5 秒執行一次 Agent 模擬。
比 Celery Beat 更適合 Windows 環境。
"""

import signal
import sys
import time
import logging
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Starts the APScheduler for autonomous agent simulation'

    def add_arguments(self, parser):
        parser.add_argument(
            '--interval',
            type=int,
            default=5,
            help='Simulation interval in seconds (default: 5)'
        )
        parser.add_argument(
            '--sync',
            action='store_true',
            help='Run synchronously without Celery (for debugging)'
        )

    def handle(self, *args, **options):
        from apps.agents.scheduler import start_scheduler, stop_scheduler

        interval = options['interval']
        sync_mode = options['sync']

        self.stdout.write(self.style.SUCCESS(
            f'Starting agent scheduler (interval: {interval}s, sync: {sync_mode})'
        ))

        def signal_handler(signum, frame):
            self.stdout.write(self.style.WARNING('\nShutting down scheduler...'))
            stop_scheduler()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        if sync_mode:
            # 同步模式 (不使用 Celery)
            self._run_sync(interval)
        else:
            # 正常模式 (使用 APScheduler + Celery)
            start_scheduler()

            self.stdout.write(self.style.SUCCESS(
                'Scheduler is running. Press Ctrl+C to stop.'
            ))

            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                stop_scheduler()

    def _run_sync(self, interval):
        """
        同步模式：直接執行模擬，不使用 Celery
        適用於調試或沒有 Redis 的環境
        """
        from apps.agents.models import Agent
        from apps.agents.tasks import process_agent_tick
        from asgiref.sync import async_to_sync

        self.stdout.write(self.style.WARNING(
            'Running in sync mode (no Celery). This is for debugging only.'
        ))

        try:
            while True:
                # 獲取所有在線自主 Agent
                online_agents = Agent.objects.filter(
                    is_online=True,
                    is_autonomous=True
                )

                count = online_agents.count()
                if count > 0:
                    self.stdout.write(f'Processing {count} agents...')

                    for agent in online_agents:
                        try:
                            # 直接調用 (不通過 Celery)
                            process_agent_tick(str(agent.id))
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(
                                f'Error processing agent {agent.name}: {e}'
                            ))

                time.sleep(interval)

        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('Stopped.'))
