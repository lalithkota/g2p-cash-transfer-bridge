from openg2p_fastapi_common.controller import BaseController
from ..models.disburse import DisburseHttpRequest, DisburseHttpResponse

from openg2p_fastapi_common.context import app_registry

class DisbursementController(BaseController):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.router.add_api_route("/disburse/sync/disburse", self.post_dsbt_sync_disburse)

    async def post_dsbt_sync_disburse(request: DisburseHttpRequest) -> DisburseHttpResponse:
        try:
            # Validate the message signature here

            # Process the disbursement request here

            # Return a successful response
            response = {"message": {"ack_status": "ACK"}}
            return response
        except Exception as e:
            # Handle errors and return an error response
            response = {"message": {"ack_status": "ERR", "error": e}}
            return response
