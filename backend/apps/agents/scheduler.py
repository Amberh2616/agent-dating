"""
APScheduler 調度器 - Generative Agents 版本
Agent Scheduler - Windows-friendly alternative to Celery Beat

Enhanced for Generative Agents with:
- Agent tick simulation (every 10 seconds)
- Reflection generation (every 30 minutes)
- Daily goal generation (daily at 00:00)
- AI conversation trigger (every hour)
- Cleanup tasks (hourly)

使用方式:
    python manage.py runscheduler

或在 Django 啟動時自動啟動 (settings.py 中配置)
"""

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from django.conf import settings

logger = logging.getLogger(__name__)

# 全局調度器實例
scheduler = None


def start_scheduler():
    """
    啟動 APScheduler

    調度任務 (Generative Agents):
    - run_agent_simulation: 每 10 秒執行一次 (Agent Tick)
    - trigger_reflections: 每 30 分鐘執行一次 (反思生成)
    - generate_daily_goals: 每天 00:00 執行一次 (每日目標)
    - trigger_ai_conversations: 每小時執行一次 (AI 代聊)
    - cleanup: 每小時執行一次 (清理舊資料)
    """
    global scheduler

    if scheduler is not None:
        logger.warning("Scheduler already running")
        return

    scheduler = BackgroundScheduler()

    # 1. Agent Tick - 每 10 秒
    scheduler.add_job(
        run_simulation_job,
        trigger=IntervalTrigger(seconds=10),
        id='agent_simulation',
        name='Agent Simulation Tick (Generative Agents)',
        replace_existing=True,
        max_instances=1,
    )

    # 2. Reflection Generation - 每 30 分鐘
    scheduler.add_job(
        trigger_reflections_job,
        trigger=IntervalTrigger(minutes=30),
        id='reflections',
        name='Reflection Generation',
        replace_existing=True,
        max_instances=1,
    )

    # 3. Daily Goals - 每天 00:00
    scheduler.add_job(
        generate_daily_goals_job,
        trigger=CronTrigger(hour=0, minute=0),
        id='daily_goals',
        name='Daily Goal Generation',
        replace_existing=True,
    )

    # 4. AI Conversations - 每小時
    scheduler.add_job(
        trigger_ai_conversations_job,
        trigger=IntervalTrigger(hours=1),
        id='ai_conversations',
        name='AI Conversation Trigger',
        replace_existing=True,
    )

    # 5. Cleanup - 每小時
    scheduler.add_job(
        cleanup_job,
        trigger=IntervalTrigger(hours=1),
        id='cleanup',
        name='Hourly Cleanup',
        replace_existing=True,
    )

    scheduler.start()
    logger.info("APScheduler started with Generative Agents tasks")


def stop_scheduler():
    """停止調度器"""
    global scheduler
    if scheduler:
        scheduler.shutdown(wait=False)
        scheduler = None
        logger.info("APScheduler stopped")


def run_simulation_job():
    """
    執行 Agent 模擬 (由 APScheduler 調用)

    注意: 這會觸發 Celery 任務，所以仍需要 Celery worker 運行
    """
    from .tasks import run_agent_simulation

    try:
        # 使用 Celery 異步執行
        run_agent_simulation.delay()
    except Exception as e:
        logger.error(f"Error triggering agent simulation: {e}")

        # Celery 不可用時，直接執行 (同步)
        try:
            run_agent_simulation()
        except Exception as e2:
            logger.error(f"Error running agent simulation directly: {e2}")


def trigger_ai_conversations_job():
    """
    觸發 AI 代聊任務 (由 APScheduler 調用)

    注意: 這會觸發 Celery 任務
    """
    from .tasks import trigger_scheduled_ai_conversations

    try:
        # 使用 Celery 異步執行
        trigger_scheduled_ai_conversations.delay()
    except Exception as e:
        logger.error(f"Error triggering AI conversations: {e}")

        # Celery 不可用時，直接執行 (同步)
        try:
            trigger_scheduled_ai_conversations()
        except Exception as e2:
            logger.error(f"Error running AI conversations directly: {e2}")


def trigger_reflections_job():
    """
    觸發反思生成任務 (Generative Agents)
    Generate reflections for agents with enough memories
    """
    from .models import Agent
    from .services.reflection_service import reflection_service

    logger.info("Triggering scheduled reflections")

    try:
        # Get online agents
        agents = Agent.objects.filter(is_online=True)[:20]

        reflection_count = 0
        for agent in agents:
            try:
                if reflection_service.should_reflect(str(agent.id)):
                    language = agent.user.preferred_language if agent.user else 'zh-hant'
                    reflections = reflection_service.generate_reflection(
                        str(agent.id),
                        language=language
                    )
                    if reflections:
                        reflection_count += len(reflections)
            except Exception as e:
                logger.error(f"Error generating reflection for {agent.name}: {e}")

        if reflection_count > 0:
            logger.info(f"Generated {reflection_count} reflections total")

    except Exception as e:
        logger.error(f"Error in trigger_reflections_job: {e}")


def generate_daily_goals_job():
    """
    生成每日目標任務 (Generative Agents)
    Generate daily goals for all online agents
    """
    from .models import Agent
    from .services.intent_service import intent_service

    logger.info("Generating daily goals for all agents")

    try:
        agents = Agent.objects.filter(is_online=True)

        goal_count = 0
        for agent in agents:
            try:
                language = agent.user.preferred_language if agent.user else 'zh-hant'
                intents = intent_service.generate_daily_goals(
                    str(agent.id),
                    language=language
                )
                goal_count += len(intents)
            except Exception as e:
                logger.error(f"Error generating goals for {agent.name}: {e}")

        logger.info(f"Generated {goal_count} daily goals total")

    except Exception as e:
        logger.error(f"Error in generate_daily_goals_job: {e}")


def cleanup_job():
    """
    清理任務 (Enhanced for Generative Agents)
    - 刪除舊的 AgentAction 記錄
    - 刪除舊的 InteractionLog 記錄
    - 清理過期的意圖
    - 衰減舊記憶
    """
    from .models import AgentAction, InteractionLog, Agent
    from .services.intent_service import intent_service
    from .services.memory_service import memory_service
    from django.utils import timezone
    from datetime import timedelta

    logger.info("Running cleanup tasks")

    try:
        # 1. 刪除 24 小時前的已完成動作
        old_actions = AgentAction.objects.filter(
            status='completed',
            completed_at__lt=timezone.now() - timedelta(hours=24)
        )
        action_count = old_actions.count()
        old_actions.delete()
        if action_count > 0:
            logger.info(f"Cleaned up {action_count} old agent actions")

        # 2. 刪除 7 天前的交互日誌
        old_logs = InteractionLog.objects.filter(
            created_at__lt=timezone.now() - timedelta(days=7)
        )
        log_count = old_logs.count()
        old_logs.delete()
        if log_count > 0:
            logger.info(f"Cleaned up {log_count} old interaction logs")

        # 3. 清理過期意圖
        expired_count = intent_service.cleanup_expired_intents()
        if expired_count > 0:
            logger.info(f"Marked {expired_count} intents as expired")

        # 4. 衰減舊記憶 (每個 Agent)
        agents = Agent.objects.all()[:50]  # Limit batch size
        for agent in agents:
            try:
                memory_service.decay_old_memories(
                    str(agent.id),
                    days=30,
                    decay_factor=0.9
                )
            except Exception:
                pass

    except Exception as e:
        logger.error(f"Error in cleanup job: {e}")


# Django 管理命令 runscheduler
class Command:
    """
    Django 管理命令: python manage.py runscheduler

    用法:
        python manage.py runscheduler
    """
    help = 'Starts the APScheduler for agent simulation'

    def handle(self, *args, **options):
        import signal
        import sys

        logger.info("Starting agent scheduler...")

        def signal_handler(signum, frame):
            logger.info("Received shutdown signal")
            stop_scheduler()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        start_scheduler()

        # 保持運行
        import time
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            stop_scheduler()
