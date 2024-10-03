# -*- coding: utf-8 -*-

""" Data models for report production."""

import dataclasses
import typing
from importlib.metadata import metadata

from qgis.core import QgsFeedback, QgsTask

from .base import MapTemporalInfo


@dataclasses.dataclass
class ReportSubmitResult:
    """Result of report submission process."""

    success: bool
    feedback: typing.Optional[QgsFeedback]
    identifier: str = "-1"
    task: QgsTask = None


@dataclasses.dataclass
class ReportOutputResult:
    """Result of site report generation process."""

    success: bool
    output_path: str
    name: str
    errors: typing.Tuple[str] = dataclasses.field(default_factory=tuple)


@dataclasses.dataclass
class SiteMetadata:
    """Information about the site."""

    country: str
    inception_date: str
    author: str
    site_reference: str
    version: str
    area_name: str
    capture_date: str
    computed_area: str


@dataclasses.dataclass
class ProjectMetadata:
    """Information about the project instance report."""

    farmer_id: str
    inception_date: str
    project: str
    author: str
    total_area: str


@dataclasses.dataclass
class SiteReportContext:
    """Information required to generate a site report."""

    metadata: typing.Union[SiteMetadata, ProjectMetadata]
    feedback: QgsFeedback
    project_dir: str
    qgs_project_path: str
    template_path: str
    temporal_info: MapTemporalInfo

    @property
    def report_dir(self) -> str:
        """Returns the path to the report directory.

        :returns: Report directory path. Returns an empty path
        if the project directory has not been set.
        :rtype: str
        """
        if not self.project_dir:
            return ""

        return f"{self.project_dir}/reports"
