"""
SAP Flat File Parser

Handles semicolon-delimited exports from SAP with German headers,
German decimal format, leading zeros, and multiple date formats.
"""
import re
from datetime import datetime, date
from .base import BaseParser


# German header → internal field name mapping
GERMAN_HEADER_MAP = {
    'bestellnummer': 'po_number',
    'pos': 'item_number',
    'buchungskreis': 'company_code',
    'lieferant': 'vendor',
    'werk': 'plant_code',
    'buchungsdatum': 'posting_date',
    'materialnummer': 'material_number',
    'kurztext': 'description',
    'menge': 'quantity',
    'mengeneinheit': 'unit',
    'nettopreis': 'net_price',
    'währung': 'currency',
    'wahrung': 'currency',  # without umlaut
    'bewegungsart': 'movement_type',
    'kostenstelle': 'cost_center',
    'sachkonto': 'gl_account',
    'lagerort': 'storage_location',
    'belegart': 'document_type',
    'kontierungstyp': 'account_assignment',
    'einkaufsorganisation': 'purchasing_org',
    'einkäufergruppe': 'purchasing_group',
    'einkaufergruppe': 'purchasing_group',  # without umlaut
    'materialgruppe': 'material_group',
    'änderungsdatum': 'change_date',
    'anderungsdatum': 'change_date',  # without umlaut
}

# SAP technical field name → internal field name mapping
TECHNICAL_HEADER_MAP = {
    'ebeln': 'po_number',
    'ebelp': 'item_number',
    'bukrs': 'company_code',
    'lifnr': 'vendor',
    'werks': 'plant_code',
    'budat': 'posting_date',
    'bedat': 'po_date',
    'matnr': 'material_number',
    'txz01': 'description',
    'menge': 'quantity',
    'meins': 'unit',
    'netpr': 'net_price',
    'waers': 'currency',
    'bwart': 'movement_type',
    'kostl': 'cost_center',
    'sakto': 'gl_account',
    'lgort': 'storage_location',
    'bsart': 'document_type',
    'knttp': 'account_assignment',
    'ekorg': 'purchasing_org',
    'ekgrp': 'purchasing_group',
    'matkl': 'material_group',
    'aedat': 'change_date',
    'mblnr': 'material_doc_number',
    'mjahr': 'doc_year',
    'xblnr': 'reference_doc',
}

# English header → internal field name mapping
ENGLISH_HEADER_MAP = {
    'purchase order': 'po_number',
    'purchase_order': 'po_number',
    'po_number': 'po_number',
    'item': 'item_number',
    'item_number': 'item_number',
    'company_code': 'company_code',
    'vendor': 'vendor',
    'plant': 'plant_code',
    'plant_code': 'plant_code',
    'posting_date': 'posting_date',
    'material': 'material_number',
    'material_number': 'material_number',
    'description': 'description',
    'short_text': 'description',
    'quantity': 'quantity',
    'unit': 'unit',
    'unit_of_measure': 'unit',
    'net_price': 'net_price',
    'price': 'net_price',
    'currency': 'currency',
    'movement_type': 'movement_type',
    'cost_center': 'cost_center',
}

# Fuel-related keywords (case-insensitive) → Scope 1
FUEL_KEYWORDS = [
    'diesel', 'benzin', 'gasoline', 'petrol', 'heizöl', 'heizoel',
    'erdgas', 'natural gas', 'propan', 'propane', 'butan', 'butane',
    'lpg', 'kraftstoff', 'fuel', 'kerosin', 'kerosene',
]

# Unit normalization map
UNIT_MAP = {
    'l': 'liters',
    'ltr': 'liters',
    'liter': 'liters',
    'liters': 'liters',
    'm3': 'cubic_meters',
    'cbm': 'cubic_meters',
    'kg': 'kilograms',
    'kilogram': 'kilograms',
    't': 'tonnes',
    'to': 'tonnes',
    'gal': 'gallons',
    'st': 'pieces',
    'stk': 'pieces',
    'pc': 'pieces',
    'pcs': 'pieces',
    'au': 'activity_units',
}


class SAPParser(BaseParser):
    """Parses SAP flat file exports (semicolon-delimited, German/English headers)."""

    def parse_rows(self, rows: list[dict]) -> list[dict]:
        results = []
        for row in rows:
            result = self._parse_single_row(row)
            results.append(result)
        return results

    def _map_headers(self, row: dict) -> dict:
        """Map whatever headers the row has to internal field names."""
        mapped = {}
        for key, value in row.items():
            lower_key = key.lower().strip()
            # Try German map first, then technical, then English
            internal = (
                GERMAN_HEADER_MAP.get(lower_key)
                or TECHNICAL_HEADER_MAP.get(lower_key)
                or ENGLISH_HEADER_MAP.get(lower_key)
                or lower_key  # fallback: use as-is
            )
            mapped[internal] = value
        return mapped

    def _parse_german_decimal(self, value: str) -> float:
        """Convert German decimal format: '15.000,50' or '15000,000' → 15000.5"""
        if not value or not value.strip():
            raise ValueError(f"Empty numeric value")
        s = value.strip()
        # If contains both . and , → German format (. is thousands, , is decimal)
        if '.' in s and ',' in s:
            s = s.replace('.', '').replace(',', '.')
        # If contains only , → it's the decimal separator
        elif ',' in s:
            s = s.replace(',', '.')
        return float(s)

    def _parse_date(self, value: str) -> date:
        """Parse date from multiple SAP formats."""
        s = value.strip()
        formats = [
            ('%Y%m%d', r'^\d{8}$'),          # YYYYMMDD
            ('%d.%m.%Y', r'^\d{2}\.\d{2}\.\d{4}$'),  # DD.MM.YYYY
            ('%Y-%m-%d', r'^\d{4}-\d{2}-\d{2}$'),    # YYYY-MM-DD
        ]
        for fmt, pattern in formats:
            if re.match(pattern, s):
                try:
                    return datetime.strptime(s, fmt).date()
                except ValueError:
                    continue
        raise ValueError(f"Unrecognized date format: '{value}'")

    def _strip_leading_zeros(self, value: str) -> str:
        """Strip SAP leading zeros: '000000000050001234' → '50001234'"""
        if not value:
            return value
        stripped = value.lstrip('0')
        return stripped or '0'  # Don't return empty string for '0000'

    def _is_fuel(self, description: str) -> bool:
        """Check if the material description indicates fuel."""
        if not description:
            return False
        lower = description.lower()
        return any(kw in lower for kw in FUEL_KEYWORDS)

    def _normalize_unit(self, unit: str) -> str:
        """Normalize SAP unit codes to standard names."""
        if not unit:
            return 'unknown'
        return UNIT_MAP.get(unit.lower().strip(), unit.lower().strip())

    def _parse_single_row(self, raw_row: dict) -> dict:
        """Parse a single SAP row into a normalized record."""
        errors = []
        flags = []

        # Map headers
        row = self._map_headers(raw_row)

        # Parse quantity
        quantity = None
        try:
            quantity = self._parse_german_decimal(row.get('quantity', ''))
        except (ValueError, TypeError) as e:
            errors.append(f"Invalid quantity: {e}")

        # Parse date
        activity_date = None
        try:
            activity_date = self._parse_date(row.get('posting_date', ''))
        except (ValueError, TypeError) as e:
            errors.append(f"Invalid date: {e}")

        # Parse net price
        net_price = None
        try:
            price_str = row.get('net_price', '')
            if price_str and price_str.strip():
                net_price = self._parse_german_decimal(price_str)
        except (ValueError, TypeError):
            pass  # Price is optional

        # Get description and classify scope
        description = row.get('description', '').strip()
        is_fuel = self._is_fuel(description)
        scope = 'scope_1' if is_fuel else 'scope_3'
        category = self._categorize_fuel(description) if is_fuel else 'procurement'

        # Normalize unit
        original_unit = row.get('unit', '').strip()
        unit = self._normalize_unit(original_unit)

        # Strip leading zeros
        material_number = self._strip_leading_zeros(row.get('material_number', ''))
        vendor = self._strip_leading_zeros(row.get('vendor', ''))
        cost_center = self._strip_leading_zeros(row.get('cost_center', ''))

        # Build amount
        amount = None
        if quantity is not None and net_price is not None:
            amount = quantity * net_price

        # Anomaly detection
        if quantity is not None and quantity > 50000:
            flags.append({'reason': f'Unusually large quantity: {quantity:,.0f} {original_unit}', 'severity': 'warning'})

        if unit == 'unknown' or unit == original_unit.lower().strip():
            if original_unit and original_unit.lower().strip() not in UNIT_MAP:
                flags.append({'reason': f'Unrecognized unit: {original_unit}', 'severity': 'warning'})

        if activity_date and activity_date > date.today():
            flags.append({'reason': f'Date is in the future: {activity_date}', 'severity': 'warning'})

        if not cost_center or cost_center == '0':
            flags.append({'reason': 'Missing cost center', 'severity': 'info'})

        # If we have critical errors, mark as failed
        if errors and quantity is None:
            return {
                'parsed': False,
                'errors': errors,
                'normalized': None,
                'flags': flags,
                'raw': raw_row,
            }

        normalized = {
            'source_type': 'sap',
            'category': category,
            'scope': scope,
            'activity_date': str(activity_date) if activity_date else None,
            'description': description or f"Material {material_number}",
            'quantity': quantity,
            'unit': unit,
            'original_unit': original_unit,
            'conversion_factor': 1.0,
            'amount': amount,
            'currency': row.get('currency', '').strip() or None,
            'source_metadata': {
                'po_number': row.get('po_number', '').strip(),
                'item_number': row.get('item_number', '').strip(),
                'material_number': material_number,
                'plant_code': row.get('plant_code', '').strip(),
                'vendor': vendor,
                'cost_center': cost_center,
                'company_code': row.get('company_code', '').strip(),
                'movement_type': row.get('movement_type', '').strip(),
            },
        }

        return {
            'parsed': True,
            'errors': errors,
            'normalized': normalized,
            'flags': flags,
            'raw': raw_row,
        }

    def _categorize_fuel(self, description: str) -> str:
        """Categorize fuel type from description."""
        lower = description.lower()
        if 'diesel' in lower:
            return 'diesel_fuel'
        if 'benzin' in lower or 'gasoline' in lower or 'petrol' in lower:
            return 'gasoline'
        if 'heizöl' in lower or 'heizoel' in lower or 'heating oil' in lower:
            return 'heating_oil'
        if 'erdgas' in lower or 'natural gas' in lower:
            return 'natural_gas'
        if 'propan' in lower or 'propane' in lower:
            return 'propane'
        if 'butan' in lower or 'butane' in lower:
            return 'butane'
        return 'other_fuel'
