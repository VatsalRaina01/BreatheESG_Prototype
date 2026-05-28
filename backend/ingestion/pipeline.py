"""
Ingestion Pipeline Orchestrator

Coordinates the full data processing flow:
  Read file → Parse rows → Create RawRecords → Create NormalizedRecords → Update Job stats
"""
import csv
import hashlib
import io
from datetime import date
from decimal import Decimal, InvalidOperation

from django.utils import timezone

from ingestion.models import RawRecord
from review.models import NormalizedRecord
from ingestion.parsers.sap_parser import SAPParser
from ingestion.parsers.utility_parser import UtilityParser
from ingestion.parsers.travel_parser import TravelParser


PARSERS = {
    'sap': SAPParser,
    'utility': UtilityParser,
    'travel': TravelParser,
}


class IngestionPipeline:
    """Orchestrates file ingestion: parse → validate → normalize → persist."""

    def __init__(self, job, source_type):
        self.job = job
        self.source_type = source_type
        self.parser = PARSERS[source_type]()
        self.stats = {
            'total_rows': 0,
            'parsed_rows': 0,
            'failed_rows': 0,
            'flagged_rows': 0,
            'errors': [],
        }

    def process(self, file_obj):
        """
        Main entry point. Reads the file, parses all rows, creates records.
        
        Returns a summary dict with processing stats.
        """
        try:
            # Read file content
            content = self._read_file(file_obj)

            # Compute file hash for deduplication
            file_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
            self.job.file_hash = file_hash

            # Parse CSV into rows
            rows = self._read_csv(content)
            self.stats['total_rows'] = len(rows)

            if not rows:
                self.job.status = 'failed'
                self.job.error_log = [{'error': 'No data rows found in file'}]
                self.job.save()
                return self.stats

            # Run parser on all rows
            parsed_results = self.parser.parse_rows(rows)

            # Persist results
            self._persist_results(parsed_results)

            # Update job
            self.job.status = 'completed'
            self.job.total_rows = self.stats['total_rows']
            self.job.parsed_rows = self.stats['parsed_rows']
            self.job.failed_rows = self.stats['failed_rows']
            self.job.flagged_rows = self.stats['flagged_rows']
            self.job.completed_at = timezone.now()
            self.job.error_log = self.stats['errors'][:100]  # Cap error log
            self.job.save()

        except Exception as e:
            self.job.status = 'failed'
            self.job.error_log = [{'error': str(e)}]
            self.job.completed_at = timezone.now()
            self.job.save()
            raise

        return self.stats

    def _read_file(self, file_obj) -> str:
        """Read uploaded file content as string."""
        if hasattr(file_obj, 'read'):
            content = file_obj.read()
            if isinstance(content, bytes):
                # Try UTF-8 first, fall back to latin-1 (handles German umlauts)
                try:
                    return content.decode('utf-8')
                except UnicodeDecodeError:
                    return content.decode('latin-1')
            return content
        return str(file_obj)

    def _read_csv(self, content: str) -> list[dict]:
        """Parse CSV content into list of row dicts."""
        # Auto-detect delimiter
        delimiter = self.parser.detect_delimiter(content)

        reader = csv.DictReader(
            io.StringIO(content),
            delimiter=delimiter,
        )

        rows = []
        for row in reader:
            # Skip completely empty rows
            if any(v.strip() for v in row.values() if v):
                rows.append(dict(row))

        return rows

    def _persist_results(self, parsed_results: list[dict]):
        """Persist parsed results as RawRecords and NormalizedRecords."""
        raw_records_to_create = []
        normalized_records_to_create = []

        for i, result in enumerate(parsed_results, start=1):
            # Create RawRecord
            raw_record = RawRecord(
                tenant=self.job.tenant,
                ingestion_job=self.job,
                row_number=i,
                raw_data=result['raw'],
                parse_status='success' if result['parsed'] else 'error',
                parse_errors=result.get('errors', []),
            )
            raw_records_to_create.append(raw_record)

        # Bulk create RawRecords to get IDs
        RawRecord.objects.bulk_create(raw_records_to_create)

        # Now create NormalizedRecords for successfully parsed rows
        for i, result in enumerate(parsed_results):
            if not result['parsed']:
                self.stats['failed_rows'] += 1
                if result.get('errors'):
                    self.stats['errors'].append({
                        'row': i + 1,
                        'errors': result['errors'],
                    })
                continue

            self.stats['parsed_rows'] += 1
            normalized = result['normalized']
            flags = result.get('flags', [])

            # Parse activity_date
            activity_date = None
            if normalized.get('activity_date'):
                try:
                    parts = normalized['activity_date'].split('-')
                    activity_date = date(int(parts[0]), int(parts[1]), int(parts[2]))
                except (ValueError, IndexError):
                    pass

            # Determine flag severity (highest among all flags)
            flag_severity = ''
            if flags:
                severities = [f.get('severity', 'info') for f in flags]
                if 'critical' in severities:
                    flag_severity = 'critical'
                elif 'warning' in severities:
                    flag_severity = 'warning'
                else:
                    flag_severity = 'info'
                self.stats['flagged_rows'] += 1

            # Convert to Decimal safely
            quantity = self._to_decimal(normalized.get('quantity'))
            amount = self._to_decimal(normalized.get('amount'))
            conversion_factor = self._to_decimal(normalized.get('conversion_factor', 1.0))

            norm_record = NormalizedRecord(
                tenant=self.job.tenant,
                raw_record=raw_records_to_create[i],
                ingestion_job=self.job,
                source_type=normalized['source_type'],
                category=normalized.get('category', ''),
                scope=normalized['scope'],
                activity_date=activity_date,
                description=normalized.get('description', ''),
                quantity=quantity,
                unit=normalized.get('unit', ''),
                original_unit=normalized.get('original_unit', ''),
                conversion_factor=conversion_factor,
                amount=amount,
                currency=normalized.get('currency', ''),
                source_metadata=normalized.get('source_metadata', {}),
                is_flagged=bool(flags),
                flag_reasons=[f['reason'] for f in flags],
                flag_severity=flag_severity,
                review_status='pending',
            )
            normalized_records_to_create.append(norm_record)

        if normalized_records_to_create:
            NormalizedRecord.objects.bulk_create(normalized_records_to_create)

    def _to_decimal(self, value) -> Decimal | None:
        """Safely convert a value to Decimal."""
        if value is None:
            return None
        try:
            return Decimal(str(value))
        except (InvalidOperation, ValueError):
            return None
