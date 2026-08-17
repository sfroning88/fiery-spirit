"""
Author: Sean Froning
Created Date: 5.16.2026
Class objects for property schemas
"""

from typing import Optional
from decimal import Decimal
from datetime import date
from ..enums import NICState, TrainingFunction
from ._base_focus import BaseFocus


class Property(BaseFocus):
    """Normalized Property"""

    id: Optional[str] = None
    name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[NICState] = None
    zip: Optional[str] = None
    year_built: Optional[int] = None
    year_renovated: Optional[int] = None
    unit_size: Optional[Decimal] = None
    cottage_units: Optional[int] = None
    independent_units: Optional[int] = None
    assisted_units: Optional[int] = None
    memory_units: Optional[int] = None
    total_units: Optional[int] = None
    total_beds: Optional[int] = None
    msa_id: Optional[str] = None
    msa_population: Optional[int] = None


class PropertySnapshot(BaseFocus):
    """Normalized Property Snapshot"""

    reported_at: Optional[date] = None
    occupancy: Optional[Decimal] = None
    total_revenues: Optional[Decimal] = None
    repairs_maintenance: Optional[Decimal] = None
    payroll: Optional[Decimal] = None
    utilities: Optional[Decimal] = None
    contract_services: Optional[Decimal] = None
    raw_food: Optional[Decimal] = None
    culinary_supplies: Optional[Decimal] = None
    administrative: Optional[Decimal] = None
    marketing_promotions: Optional[Decimal] = None
    activities: Optional[Decimal] = None
    other_expenses: Optional[Decimal] = None
    controllable_expenses: Optional[Decimal] = None
    management_fee: Optional[Decimal] = None
    real_estate_taxes: Optional[Decimal] = None
    insurance: Optional[Decimal] = None
    non_controllable_expenses: Optional[Decimal] = None
    total_expenses: Optional[Decimal] = None
    operating_margin: Optional[Decimal] = None
    controllable_prd: Optional[Decimal] = None
    function: Optional[TrainingFunction] = None
    property_id: Optional[str] = None
