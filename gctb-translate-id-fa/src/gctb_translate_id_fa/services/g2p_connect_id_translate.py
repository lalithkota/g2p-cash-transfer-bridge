from typing import List

from g2p_cash_transfer_bridge_core.services.id_translate_service import (
    IdTranslateService,
)
from openg2p_common_g2pconnect_id_mapper.models.common import MapperValue
from openg2p_common_g2pconnect_id_mapper.service.resolve import (
    MapperResolveService as IDMapperResolveService,
)
from openg2p_fastapi_common.errors import BaseAppException


class G2PConnectIdTranslateService(IdTranslateService):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._id_mapper_service = IDMapperResolveService.get_component()

    @property
    def id_mapper_service(self):
        if not self._id_mapper_service:
            self._id_mapper_service = IDMapperResolveService.get_component()
        return self._id_mapper_service

    async def translate(self, ids: List[str], max_retries=10) -> List[str]:
        res = await self.id_mapper_service.resolve_request_sync(
            [MapperValue(id=id) for id in ids], max_retries=max_retries
        )
        if not res:
            raise BaseAppException(
                "GCTB-IMS-300",
                "ID Mapper Resolve Id: No response received",
            )
        if not res.refs:
            raise BaseAppException(
                "G2P-IMS-301",
                "ID Mapper Resolve Id: Invalid Txn without any requests received",
            )
        return [res.refs[key].fa for key in res.refs]
