"""Validate recorded funding without treating owner attestations as API proof."""
from datetime import datetime, timezone, timedelta
from math import isfinite
from .domain import RelayError


def validate_funding(record, project, budget, hours, billing_account=None, at=None):
    at = at or datetime.now(timezone.utc)
    def reject(message):
        raise RelayError('ACCESS_DENIED', message)
    if record.get('source')=='organizer-lab':
        return validate_organizer_window(record,project,hours,at)
    if not isfinite(budget) or budget <= 0 or not 1 <= hours <= 12:
        reject('An explicitly authorized positive credit-usage envelope and duration are required; personal spending remains prohibited.')
    if record.get('source') != 'organizer-credits' or record.get('account_type_human_confirmed') != 'organizer_credit_project':
        reject('Only the actually activated organizer project/credits are authorized. Personal billing, Free Trials and unconfirmed future credits are not accepted.')
    validate_organizer_window(dict(record,source='organizer-lab'),project,hours,at)
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


def validate_organizer_window(record,project,hours,at=None):
    """A lab may hide billing. An organizer-owned bounded envelope is distinct
    from a made-up credit balance or personal account carrying promotional credit.
    No missing balance/account value is fabricated by this path.
    """
    from .domain import instant
    at=at or datetime.now(timezone.utc)
    required=('organizer_project_ownership_verified','eligible_project_verified','service_coverage_verified','no_personal_spending','no_personal_billing_attached','activation_verified','organizer_terms_verified')
    if record.get('source')!='organizer-lab' or record.get('project_id')!=project or not all(record.get(k) is True for k in required):
        raise RelayError('ACCESS_DENIED','Actual organizer-owned project, activation, terms and covered services must be verified before provisioning.')
    start=instant(record.get('activated_at_utc'));expiry=instant(record.get('expires_at_utc'));checked=instant(record.get('checked_at_utc'))
    if not 0<hours<=12 or start>at or not timedelta(0)<expiry-start<=timedelta(hours=12,minutes=5) or checked<at-timedelta(hours=2) or checked>at+timedelta(minutes=5) or expiry<=at+timedelta(hours=hours):
        raise RelayError('ACCESS_DENIED','Activation/window review is stale, unactivated or cannot cover the planned duration and cleanup reserve.')
    if not record.get('instruction_reference') or record.get('personal_spending_authorized_usd',0)!=0 or record.get('billing_visibility') not in ('verified_organizer_account','hidden_by_organizer_lab'):
        raise RelayError('ACCESS_DENIED','Record the actual organizer instructions and billing visibility; never invent a billing account or balance.')
    return dict(source='organizer-lab',project_id=project,hours=hours,activated_at_utc=start.isoformat(),expires_at_utc=expiry.isoformat(),
                personal_spending_authorized_usd=0,credit_balance_usd=record.get('credit_balance_usd'),balance_api_verified=False,
                coverage='organizer_owned_time_bound_project',stop_new_work_at=(expiry-timedelta(minutes=60)).isoformat(),cleanup_at=(expiry-timedelta(minutes=30)).isoformat())
