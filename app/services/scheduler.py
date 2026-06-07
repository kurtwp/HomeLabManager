"""Scheduled network scanning using APScheduler."""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

from app.database.db import SessionLocal
from app.services.scanner import scan_network
from app.models.network import Network

# Global scheduler instance
scheduler = BackgroundScheduler()


def start_scheduler():
    """Start the background scheduler if not already running."""
    if not scheduler.running:
        scheduler.start()


def stop_scheduler():
    """Shutdown the scheduler gracefully."""
    if scheduler.running:
        scheduler.shutdown(wait=False)


def get_scheduled_jobs() -> list[dict]:
    """Get list of all scheduled scan jobs."""
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run": str(job.next_run_time) if job.next_run_time else "Paused",
            "trigger": str(job.trigger),
        })
    return jobs


def add_scan_job(
    network_id: int,
    interval_minutes: int = 60,
) -> str:
    """
    Schedule a recurring network scan.

    Args:
        network_id: ID of the network to scan
        interval_minutes: How often to scan (in minutes)

    Returns:
        Job ID
    """
    job_id = f"scan_network_{network_id}"

    # Remove existing job for this network if any
    existing = scheduler.get_job(job_id)
    if existing:
        scheduler.remove_job(job_id)

    # Get network name for the job label
    session = SessionLocal()
    network = session.query(Network).filter(Network.id == network_id).first()
    job_name = f"Scan: {network.name}" if network else f"Scan: Network {network_id}"
    session.close()

    scheduler.add_job(
        _run_scan,
        trigger=IntervalTrigger(minutes=interval_minutes),
        id=job_id,
        name=job_name,
        args=[network_id],
        replace_existing=True,
    )

    return job_id


def remove_scan_job(network_id: int) -> bool:
    """Remove a scheduled scan job for a network."""
    job_id = f"scan_network_{network_id}"
    existing = scheduler.get_job(job_id)
    if existing:
        scheduler.remove_job(job_id)
        return True
    return False


def _run_scan(network_id: int):
    """Execute a network scan (called by scheduler)."""
    session = SessionLocal()
    try:
        scan_network(session, network_id)
    except Exception as e:
        print(f"Scheduled scan failed for network {network_id}: {e}")
    finally:
        session.close()
