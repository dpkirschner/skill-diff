"""Filter implementations for identifying target URLs."""

from .filter import BaseFilter
from .job_link_filter import JobLinkFilter

__all__ = ["BaseFilter", "JobLinkFilter"]
