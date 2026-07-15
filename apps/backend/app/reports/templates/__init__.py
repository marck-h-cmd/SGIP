"""Template utilities for HTML reports"""
import os
from typing import Dict, Any


def get_template_path(template_name: str) -> str:
    """Get full path to template file"""
    return os.path.join(os.path.dirname(__file__), template_name)


def render_template(template_name: str, context: Dict[str, Any]) -> str:
    """
    Render Jinja2 template
    
    Args:
        template_name: Template filename
        context: Template context variables
    
    Returns:
        Rendered HTML string
    """
    from jinja2 import Environment, FileSystemLoader
    
    template_dir = os.path.dirname(__file__)
    env = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=True
    )
    
    template = env.get_template(template_name)
    return template.render(**context)