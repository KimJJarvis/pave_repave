#!/usr/bin/env python3
"""
Status model for representing peer information status.
"""

from typing import Self

from pydantic import BaseModel, model_validator

from pave_repave.utilities import validate_ip_format


class Status(BaseModel):
    """Represents the status of a peer in the cluster."""

    found: bool
    active_appliance: int | None = None
    primary_ip: str | None = None
    secondary_ip: str | None = None
    id: int | None = None
    msg: str | None = None

    @model_validator(mode="after")
    def validate_status(self) -> Self:
        """Validate status fields based on whether a peer was found."""
        if not self.found:
            return self

        if self.active_appliance not in (1, 2):
            msg = f"Invalid active_appliance: {self.active_appliance}"
            raise ValueError(msg)

        if self.primary_ip is None or not validate_ip_format(self.primary_ip):
            msg = f"Invalid primary_ip: {self.primary_ip}"
            raise ValueError(msg)

        if self.secondary_ip is None or not validate_ip_format(self.secondary_ip):
            msg = f"Invalid secondary_ip: {self.secondary_ip}"
            raise ValueError(msg)

        if self.id is None or self.id <= 0:
            msg = f"Invalid id: {self.id}"
            raise ValueError(msg)

        return self
