from openg2p_fastapi_common.service import BaseService


class IdTranslateService(BaseService):
    def translate(self, id: str) -> str:
        """
        Get an ID and return it.
        This method should be implemented in concrete subclasses.
        """
        pass
