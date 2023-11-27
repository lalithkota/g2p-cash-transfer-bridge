#!/usr/bin/env python3

from g2p_cash_transfer_bridge_api.app import Initializer as ApiInitializer
from gctb_translate_id_fa.app import Initializer as TranslateIdInitializer
from openg2p_common_g2pconnect_id_mapper.app import (
    Initializer as G2pConnectMapperInitializer,
)
from openg2p_fastapi_common.ping import PingInitializer

main_init = ApiInitializer()
G2pConnectMapperInitializer()
TranslateIdInitializer()
PingInitializer()
main_init.main()
