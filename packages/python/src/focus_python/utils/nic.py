"""
Author: Sean Froning
Created Date: 5.9.2026
NIC general purpose utils
"""

from ..models import Property


class NICUtils:
    """General purpose utilities for NIC"""

    @staticmethod
    def _acuity_mix(prop: Property) -> dict:
        """Compute acuity mix percentages, defaulting safely if total_units is missing"""
        total = prop.total_units or 0
        if total <= 0:
            total_calc = sum(
                int(getattr(prop, acuity, 0) or 0)
                for acuity in (
                    "cottage_units",
                    "independent_units",
                    "assisted_units",
                    "memory_units",
                )
            )
            total = total_calc
        if total <= 0:
            return {"pct_cottage": 0.0, "pct_il": 0.0, "pct_al": 0.0, "pct_mc": 0.0}
        return {
            "pct_cottage": (prop.cottage_units or 0) / total,
            "pct_il": (prop.independent_units or 0) / total,
            "pct_al": (prop.assisted_units or 0) / total,
            "pct_mc": (prop.memory_units or 0) / total,
        }
