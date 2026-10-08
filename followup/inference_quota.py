"""Read dollar quota using the installed SDK; never display credentials.

CLI 2.2.4's top-level quota command reports accelerator hours. Newer releases
provide `kaggle benchmarks quota`; this uses that command's documented API.
"""
import json
from kaggle import api
from kagglesdk.models.types.model_proxy_api_service import ApiGetModelProxyQuotasRequest

def balances():
    with api.build_kaggle_client() as client:
        response=client.models.model_proxy_api_client.get_model_proxy_quotas(ApiGetModelProxyQuotasRequest())
    return [dict(period=q.refill_period.name,used=q.quota_used,total=q.total_quota_allowed,
                 remaining=max(0,q.total_quota_allowed-q.quota_used),refill_at=str(q.refill_time))
            for q in response.quota_balances]

if __name__=='__main__':
    try:print(json.dumps(balances(),indent=2))
    except Exception as err:raise SystemExit('Quota unavailable: '+type(err).__name__) from None
