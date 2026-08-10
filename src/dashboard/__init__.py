"""Local learner dashboard for the Active Skillference SkillTree runtime."""

from src.dashboard.config import DashboardConfig, make_dashboard_config
from src.dashboard.server import run_dashboard_server

__all__ = ["DashboardConfig", "make_dashboard_config", "run_dashboard_server"]
