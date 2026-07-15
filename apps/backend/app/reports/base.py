"""Base classes for report generation"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class ReportData:
    """Standardized report data container"""
    report_type: str
    dma_id: str
    dma_name: str
    period_start: datetime
    period_end: datetime
    generated_at: datetime
    summary: Dict[str, Any]
    details: Dict[str, Any]
    metadata: Dict[str, Any]


class BaseReportGenerator(ABC):
    """Abstract base class for report generators"""
    
    @abstractmethod
    def generate(self, **kwargs) -> ReportData:
        """Generate report data"""
        pass
    
    @abstractmethod
    def get_report_type(self) -> str:
        """Return report type identifier"""
        pass


class BaseExporter(ABC):
    """Abstract base class for report exporters"""
    
    def __init__(self):
        self.mime_types = {
            "pdf": "application/pdf",
            "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "csv": "text/csv"
        }
    
    @abstractmethod
    def export(self, report_data: ReportData) -> bytes:
        """Export report to bytes"""
        pass
    
    @abstractmethod
    def get_format(self) -> str:
        """Return format identifier"""
        pass
    
    def get_mime_type(self) -> str:
        return self.mime_types.get(self.get_format(), "application/octet-stream")
    
    def get_extension(self) -> str:
        return self.get_format()


class ReportTemplate:
    """Jinja2 template wrapper for HTML-based reports"""
    
    def __init__(self, template_name: str):
        self.template_name = template_name
        self._env = None
    
    @property
    def env(self):
        if self._env is None:
            from jinja2 import Environment, FileSystemLoader
            import os
            template_dir = os.path.join(os.path.dirname(__file__), "templates")
            self._env = Environment(
                loader=FileSystemLoader(template_dir),
                autoescape=True
            )
        return self._env
    
    def render(self, **kwargs) -> str:
        template = self.env.get_template(self.template_name)
        return template.render(**kwargs)