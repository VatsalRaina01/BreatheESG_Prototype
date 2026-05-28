"""
Utility Electricity CSV Parser

Handles portal CSV exports with billing periods, meter readings,
estimated vs actual reads, and unit normalization.
"""
from datetime import datetime, date
from .base import BaseParser


# Header normalization map (case-insensitive)
HEADER_MAP = {
    'account_number': 'account_number',
    'account number': 'account_number',
    'account': 'account_number',
    'meter_number': 'meter_number',
    'meter number': 'meter_number',
    'meter': 'meter_number',
    'meter_id': 'meter_number',
    'service_address': 'service_address',
    'service address': 'service_address',
    'address': 'service_address',
    'billing_period_start': 'billing_period_start',
    'billing period start': 'billing_period_start',
    'start_date': 'billing_period_start',
    'start date': 'billing_period_start',
    'billing_period_end': 'billing_period_end',
    'billing period end': 'billing_period_end',
    'end_date': 'billing_period_end',
    'end date': 'billing_period_end',
    'days_in_period': 'days_in_period',
    'days in period': 'days_in_period',
    'days': 'days_in_period',
    'usage_kwh': 'usage_kwh',
    'usage (kwh)': 'usage_kwh',
    'usage': 'usage_kwh',
    'kwh': 'usage_kwh',
    'consumption': 'usage_kwh',
    'demand_kw': 'demand_kw',
    'demand (kw)': 'demand_kw',
    'demand': 'demand_kw',
    'kw': 'demand_kw',
    'read_type': 'read_type',
    'read type': 'read_type',
    'reading_type': 'read_type',
    'quality': 'read_type',
    'rate_schedule': 'rate_schedule',
    'rate schedule': 'rate_schedule',
    'rate': 'rate_schedule',
    'tariff': 'rate_schedule',
    'total_charges': 'total_charges',
    'total charges': 'total_charges',
    'charges': 'total_charges',
    'cost': 'total_charges',
    'amount': 'total_charges',
    'currency': 'currency',
}

# Unit conversion factors to kWh
UNIT_CONVERSIONS = {
    'kwh': 1.0,
    'mwh': 1000.0,
    'gj': 277.78,
    'wh': 0.001,
    'therm': 29.3,
    'therms': 29.3,
}


class UtilityParser(BaseParser):
    """Parses utility portal CSV exports for electricity data."""

    def parse_rows(self, rows: list[dict]) -> list[dict]:
        results = []
        for row in rows:
            result = self._parse_single_row(row)
            results.append(result)
        return results

    def _map_headers(self, row: dict) -> dict:
        """Map headers to internal field names."""
        mapped = {}
        for key, value in row.items():
            lower_key = key.lower().strip()
            internal = HEADER_MAP.get(lower_key, lower_key)
            mapped[internal] = value
        return mapped

    def _parse_date(self, value: str) -> date:
        """Parse date from common utility formats."""
        if not value or not value.strip():
            raise ValueError("Empty date")
        s = value.strip()
        formats = [
            '%Y-%m-%d',     # 2026-01-15
            '%m/%d/%Y',     # 01/15/2026
            '%d/%m/%Y',     # 15/01/2026
            '%m-%d-%Y',     # 01-15-2026
            '%Y%m%d',       # 20260115
        ]
        for fmt in formats:
            try:
                return datetime.strptime(s, fmt).date()
            except ValueError:
                continue
        raise ValueError(f"Unrecognized date format: '{value}'")

    def _parse_single_row(self, raw_row: dict) -> dict:
        """Parse a single utility row."""
        errors = []
        flags = []

        row = self._map_headers(raw_row)

        # Parse usage
        usage = None
        try:
            usage_str = row.get('usage_kwh', '').strip()
            if usage_str:
                usage = float(usage_str.replace(',', ''))
        except (ValueError, TypeError) as e:
            errors.append(f"Invalid usage value: {e}")

        # Parse billing period
        period_start = None
        period_end = None
        try:
            period_start = self._parse_date(row.get('billing_period_start', ''))
        except (ValueError, TypeError) as e:
            errors.append(f"Invalid billing period start: {e}")

        try:
            period_end = self._parse_date(row.get('billing_period_end', ''))
        except (ValueError, TypeError) as e:
            errors.append(f"Invalid billing period end: {e}")

        # Parse demand
        demand = None
        try:
            demand_str = row.get('demand_kw', '').strip()
            if demand_str:
                demand = float(demand_str.replace(',', ''))
        except (ValueError, TypeError):
            pass  # Demand is optional

        # Parse charges
        total_charges = None
        try:
            charges_str = row.get('total_charges', '').strip()
            if charges_str:
                total_charges = float(charges_str.replace(',', '').replace('$', ''))
        except (ValueError, TypeError):
            pass  # Charges are optional

        # Billing period validation
        days_in_period = None
        if period_start and period_end:
            days_in_period = (period_end - period_start).days
            if days_in_period > 35:
                flags.append({'reason': f'Long billing period: {days_in_period} days', 'severity': 'info'})
            if days_in_period < 25:
                flags.append({'reason': f'Short billing period: {days_in_period} days', 'severity': 'info'})
            if days_in_period <= 0:
                errors.append(f'Invalid billing period: end before start')

        # Read type flagging
        read_type = row.get('read_type', '').strip()
        if read_type.lower() in ('estimated', 'e', 'est'):
            flags.append({'reason': 'Estimated meter read (not actual)', 'severity': 'warning'})

        # Usage anomalies
        if usage is not None:
            if usage < 0:
                flags.append({'reason': f'Negative usage: {usage}', 'severity': 'critical'})
            if usage > 500000:
                flags.append({'reason': f'Unusually high usage: {usage:,.0f} kWh', 'severity': 'warning'})

        # If critical parse errors, fail
        if errors and usage is None:
            return {
                'parsed': False,
                'errors': errors,
                'normalized': None,
                'flags': flags,
                'raw': raw_row,
            }

        # Unit normalization (default kWh)
        unit = 'kWh'
        original_unit = 'kWh'
        conversion_factor = 1.0

        # Determine the activity date (use period end as the "reporting date")
        activity_date = period_end or period_start

        # Description
        meter = row.get('meter_number', '').strip()
        address = row.get('service_address', '').strip()
        description = f"Meter {meter}" if meter else "Electricity consumption"
        if address:
            description += f" — {address}"

        normalized = {
            'source_type': 'utility',
            'category': 'electricity',
            'scope': 'scope_2',
            'activity_date': str(activity_date) if activity_date else None,
            'description': description,
            'quantity': usage,
            'unit': unit,
            'original_unit': original_unit,
            'conversion_factor': conversion_factor,
            'amount': total_charges,
            'currency': row.get('currency', '').strip() or 'USD',
            'source_metadata': {
                'account_number': row.get('account_number', '').strip(),
                'meter_number': meter,
                'service_address': address,
                'billing_period_start': str(period_start) if period_start else None,
                'billing_period_end': str(period_end) if period_end else None,
                'days_in_period': days_in_period,
                'demand_kw': demand,
                'read_type': read_type,
                'rate_schedule': row.get('rate_schedule', '').strip(),
            },
        }

        return {
            'parsed': True,
            'errors': errors,
            'normalized': normalized,
            'flags': flags,
            'raw': raw_row,
        }
