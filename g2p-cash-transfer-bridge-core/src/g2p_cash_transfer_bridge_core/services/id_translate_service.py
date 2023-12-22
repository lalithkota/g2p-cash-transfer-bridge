from typing import List

from openg2p_fastapi_common.service import BaseService


class IdTranslateService(BaseService):
    async def translate(self, ids: List[str], **kwargs) -> List[str]:
        """
        Get an ID and return it.
        This method should be implemented in concrete subclasses.
        """
        raise NotImplementedError()

    def translate_sync(self, ids: List[str], **kwargs) -> List[str]:
        """
        Get an ID and return it.
        This method should be implemented in concrete subclasses.
        """
        raise NotImplementedError()
