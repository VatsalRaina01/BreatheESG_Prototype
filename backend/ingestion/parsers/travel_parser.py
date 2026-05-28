"""
Corporate Travel (Concur-style) CSV Parser

Handles Concur expense report exports with flight distance calculation,
expense type routing, and cabin class classification.
"""
from datetime import datetime, date
from .base import BaseParser
from .airports import calculate_flight_distance, get_airport


# Header normalization
HEADER_MAP = {
    'report_id': 'report_id',
    'report id': 'report_id',
    'expense_report_id': 'report_id',
    'employee_name': 'employee_name',
    'employee name': 'employee_name',
    'employee': 'employee_name',
    'traveler': 'employee_name',
    'employee_id': 'employee_id',
    'employee id': 'employee_id',
    'expense_type': 'expense_type',
    'expense type': 'expense_type',
    'category': 'expense_type',
    'transaction_date': 'transaction_date',
    'transaction date': 'transaction_date',
    'date': 'transaction_date',
    'expense_date': 'transaction_date',
    'vendor': 'vendor',
    'merchant': 'vendor',
    'supplier': 'vendor',
    'description': 'description',
    'comment': 'description',
    'memo': 'description',
    'origin': 'origin',
    'from': 'origin',
    'departure': 'origin',
    'origin_city': 'origin',
    'destination': 'destination',
    'to': 'destination',
    'arrival': 'destination',
    'destination_city': 'destination',
    'cabin_class': 'cabin_class',
    'cabin class': 'cabin_class',
    'class': 'cabin_class',
    'travel_class': 'cabin_class',
    'flight_class': 'cabin_class',
    'amount': 'amount',
    'total': 'amount',
    'cost': 'amount',
    'expense_amount': 'amount',
    'currency': 'currency',
    'currency_code': 'currency',
    'payment_method': 'payment_method',
    'payment method': 'payment_method',
    'payment_type': 'payment_method',
    'receipt': 'receipt',
    'receipt_status': 'receipt',
    'has_receipt': 'receipt',
    'city': 'city',
    'location': 'city',
    'hotel_city': 'city',
    'nights': 'nights',
    'num_nights': 'nights',
    'number_of_nights': 'nights',
    'distance': 'distance',
    'distance_km': 'distance',
}

# Expense type classification
EXPENSE_TYPE_MAP = {
    'airfare': 'flight',
    'air': 'flight',
    'flight': 'flight',
    'air ticket': 'flight',
    'airline': 'flight',
    'hotel': 'hotel',
    'lodging': 'hotel',
    'accommodation': 'hotel',
    'taxi': 'taxi',
    'uber': 'taxi',
    'lyft': 'taxi',
    'ride': 'taxi',
    'rideshare': 'taxi',
    'cab': 'taxi',
    'ground transport': 'taxi',
    'car rental': 'car_rental',
    'rental car': 'car_rental',
    'car hire': 'car_rental',
    'hertz': 'car_rental',
    'avis': 'car_rental',
    'enterprise': 'car_rental',
    'train': 'train',
    'rail': 'train',
    'eurostar': 'train',
    'amtrak': 'train',
    'railway': 'train',
    'meal': 'meal',
    'meals': 'meal',
    'dining': 'meal',
    'breakfast': 'meal',
    'lunch': 'meal',
    'dinner': 'meal',
    'parking': 'other',
    'toll': 'other',
    'fuel': 'other',
    'gas': 'other',
    'other': 'other',
    'miscellaneous': 'other',
    'tips': 'other',
    'internet': 'other',
    'phone': 'other',
    'laundry': 'other',
}

CABIN_CLASS_MAP = {
    'economy': 'economy',
    'coach': 'economy',
    'y': 'economy',
    'premium economy': 'premium_economy',
    'premium': 'premium_economy',
    'w': 'premium_economy',
    'business': 'business',
    'j': 'business',
    'first': 'first',
    'f': 'first',
    'first class': 'first',
}


class TravelParser(BaseParser):
    """Parses Concur-style corporate travel CSV exports."""

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

    def _classify_expense(self, expense_type: str) -> str:
        """Classify expense type to a standard category."""
        if not expense_type:
            return 'other'
        lower = expense_type.lower().strip()
        return EXPENSE_TYPE_MAP.get(lower, 'other')

    def _classify_cabin(self, cabin: str) -> str:
        """Classify cabin class."""
        if not cabin:
            return 'unknown'
        lower = cabin.lower().strip()
        return CABIN_CLASS_MAP.get(lower, 'unknown')

    def _parse_date(self, value: str) -> date:
        """Parse date from common travel export formats."""
        if not value or not value.strip():
            raise ValueError("Empty date")
        s = value.strip()
        formats = ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%m-%d-%Y', '%Y%m%d', '%d-%b-%Y']
        for fmt in formats:
            try:
                return datetime.strptime(s, fmt).date()
            except ValueError:
                continue
        raise ValueError(f"Unrecognized date format: '{value}'")

    def _parse_single_row(self, raw_row: dict) -> dict:
        """Parse a single travel expense row."""
        errors = []
        flags = []

        row = self._map_headers(raw_row)

        # Parse amount
        amount = None
        try:
            amount_str = row.get('amount', '').strip()
            if amount_str:
                amount = float(amount_str.replace(',', '').replace('$', '').replace('€', '').replace('£', ''))
        except (ValueError, TypeError) as e:
            errors.append(f"Invalid amount: {e}")

        # Parse date
        activity_date = None
        try:
            activity_date = self._parse_date(row.get('transaction_date', ''))
        except (ValueError, TypeError) as e:
            errors.append(f"Invalid date: {e}")

        # Classify expense type
        raw_expense_type = row.get('expense_type', '').strip()
        category = self._classify_expense(raw_expense_type)

        # Classify cabin class
        raw_cabin = row.get('cabin_class', '').strip()
        cabin_class = self._classify_cabin(raw_cabin)

        # Handle flight-specific logic
        origin = row.get('origin', '').strip().upper()
        destination = row.get('destination', '').strip().upper()
        distance = None
        flight_type = None

        if category == 'flight':
            # Try to calculate distance from airport codes
            if origin and destination:
                dist = calculate_flight_distance(origin, destination)
                if dist is not None:
                    distance = round(dist, 1)
                    flight_type = 'short_haul' if dist < 3700 else 'long_haul'
                else:
                    # Check which airport is missing
                    missing = []
                    if not get_airport(origin):
                        missing.append(origin)
                    if not get_airport(destination):
                        missing.append(destination)
                    flags.append({
                        'reason': f'Unknown airport code(s): {", ".join(missing)}',
                        'severity': 'critical'
                    })
            else:
                flags.append({
                    'reason': 'Missing origin/destination airport codes for flight',
                    'severity': 'critical'
                })

            if cabin_class == 'unknown' and not raw_cabin:
                flags.append({
                    'reason': 'Missing cabin class for flight — defaulting to economy',
                    'severity': 'info'
                })
                cabin_class = 'economy'

        # Amount anomalies
        if amount is not None and amount > 5000:
            flags.append({
                'reason': f'High expense amount: ${amount:,.2f}',
                'severity': 'warning'
            })

        # Ground transport without distance
        if category in ('taxi', 'car_rental') and not row.get('distance', '').strip():
            flags.append({
                'reason': 'No distance recorded for ground transport',
                'severity': 'info'
            })

        # If critical errors prevent parsing
        if errors and amount is None:
            return {
                'parsed': False,
                'errors': errors,
                'normalized': None,
                'flags': flags,
                'raw': raw_row,
            }

        # Build description
        description_parts = []
        if raw_expense_type:
            description_parts.append(raw_expense_type)
        if origin and destination:
            description_parts.append(f"{origin}→{destination}")
        if row.get('vendor', '').strip():
            description_parts.append(row['vendor'].strip())
        if raw_cabin and category == 'flight':
            description_parts.append(f"({raw_cabin})")
        description = ' — '.join(description_parts) or row.get('description', '').strip() or category

        # Quantity: for flights = distance, for others = 1 trip
        quantity = distance if distance else 1
        unit = 'km' if distance else 'trips'

        normalized = {
            'source_type': 'travel',
            'category': category,
            'scope': 'scope_3',
            'activity_date': str(activity_date) if activity_date else None,
            'description': description,
            'quantity': quantity,
            'unit': unit,
            'original_unit': unit,
            'conversion_factor': 1.0,
            'amount': amount,
            'currency': row.get('currency', '').strip() or 'USD',
            'source_metadata': {
                'report_id': row.get('report_id', '').strip(),
                'employee_name': row.get('employee_name', '').strip(),
                'employee_id': row.get('employee_id', '').strip(),
                'expense_type': raw_expense_type,
                'vendor': row.get('vendor', '').strip(),
                'origin': origin,
                'destination': destination,
                'cabin_class': cabin_class,
                'flight_type': flight_type,
                'distance_km': distance,
                'payment_method': row.get('payment_method', '').strip(),
                'receipt': row.get('receipt', '').strip(),
            },
        }

        return {
            'parsed': True,
            'errors': errors,
            'normalized': normalized,
            'flags': flags,
            'raw': raw_row,
        }
