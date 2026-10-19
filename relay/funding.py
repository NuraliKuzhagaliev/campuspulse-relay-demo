"""Validate recorded funding without treating owner attestations as API proof."""
from datetime import datetime, timezone, timedelta
from math import isfinite
from .domain import RelayError


def validate_funding(record, project, budget, hours, billing_account=None, at=None):
    at = at or datetime.now(timezone.utc)
    def reject(message):
        raise RelayError('ACCESS_DENIED', message)
    if not isfinite(budget) or budget <= 0 or not 1 <= hours <= 72:
        reject('An explicitly authorized positive credit-usage envelope and duration are required; personal spending remains prohibited.')
    if record.get('source') != 'gcp-free-trial' or record.get('account_type_human_confirmed') != 'free_trial':
        reject('This no-personal-spend deployment accepts a verified non-billable GCP Free Trial only. Paid accounts and unconfirmed credits are not authorized.')
    if record.get('project_id') != project or (billing_account and record.get('billing_account') != billing_account):
        reject('Funding does not match the exact project and current billing account.')
    if not all(record.get(k) is True for k in ('eligibility_human_confirmed', 'covered_services_human_confirmed', 'no_personal_spending', 'billing_open_api_verified')):
        reject('Trial eligibility, service coverage, no personal spending and actual open billing must be verified separately.')
    if record.get('credit_balance_api_verified') is not False:
        reject('Console-confirmed credit balance must not be represented as API-verified.')
    try:
        checked = datetime.fromisoformat(record['checked_at_utc'].replace('Z', '+00:00'))
        expiry = datetime.fromisoformat(record['expires_at_utc'].replace('Z', '+00:00'))
        balance = float(record['balance_usd_human_confirmed'])
        reserve = float(record['reserve_usd'])
        if checked.tzinfo is None or expiry.tzinfo is None:
            raise ValueError()
    except (KeyError, TypeError, ValueError):
        reject('Funding timestamps, balance or reserve are invalid.')
    if checked > at + timedelta(minutes=5) or checked < at - timedelta(hours=24):
        reject('Funding review is stale or future-dated. Recheck the account before provisioning.')
    if not isfinite(balance) or not isfinite(reserve) or not balance >= budget + reserve or reserve <= 0 or expiry <= at + timedelta(hours=hours):
        reject('Confirmed eligible trial credit and expiry do not cover the authorized envelope, reserve and full duration.')
    return dict(source=record['source'], project_id=project, authorized_credit_usage_usd=budget,
                personal_spending_authorized_usd=0, hours=hours, balance_api_verified=False)
