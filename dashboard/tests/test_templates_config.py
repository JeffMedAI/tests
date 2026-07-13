"""
TDD tests for app/templates_config.py — shared Jinja2Templates singleton.

RED phase: import will fail until the module is created.
"""
from fastapi.templating import Jinja2Templates
from app.templates_config import templates


class TestTemplatesConfig:
    def test_templates_is_jinja2templates(self):
        assert isinstance(templates, Jinja2Templates)

    def test_display_ts_filter_registered(self):
        assert "display_ts" in templates.env.filters

    def test_templates_env_exists(self):
        assert templates.env is not None
