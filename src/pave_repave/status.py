#!/usr/bin/env python3
"""
Status model for representing peer information status.
"""

from typing import Self

from pydantic import BaseModel, model_validator

from pave_repave.utilities import validate_ip_format


class Status(BaseModel):
    """Represents the status of a peer in the cluster."""

    active_appliance: int
    primary_ip: str
    secondary_ip: str
    id: int

    @model_validator(mode="after")
    def validate_status(self) -> Self:
        """Validate status fields."""
        if self.active_appliance not in (0, 1, 2):
            msg = f"Invalid active_appliance: {self.active_appliance}"
            raise ValueError(msg)

        if not validate_ip_format(self.primary_ip):
            msg = f"Invalid primary_ip: {self.primary_ip}"
            raise ValueError(msg)

        # Allow empty secondary_ip for standalone configurations
        if self.secondary_ip and not validate_ip_format(self.secondary_ip):
            msg = f"Invalid secondary_ip: {self.secondary_ip}"
            raise ValueError(msg)

        if self.id <= 0:
            msg = f"Invalid id: {self.id}"
            raise ValueError(msg)

        return self

    def __str__(self) -> str:
        """Return string representation of Status."""
        return (
            f'"active_appliance": {self.active_appliance},\n'
            f'"primary_ip": {self.primary_ip},\n'
            f'"secondary_ip": {self.secondary_ip},\n'
            f'"id": {self.id}'
        )
