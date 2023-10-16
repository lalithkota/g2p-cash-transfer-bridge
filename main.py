#!/usr/bin/env python3

from g2p_payments_bridge_core.app import Initializer as CoreInitializer
from gpb_simple_mpesa_payment_backend.app import (
    Initializer as SimpleMpesaPaymentBackendInitializer,
)
from gpb_translate_id_fa.app import Initializer as TranslateIdInitializer
from openg2p_common_g2pconnect_id_mapper.app import (
    Initializer as G2pConnectMapperInitializer,
)

main_init = CoreInitializer()
G2pConnectMapperInitializer()
TranslateIdInitializer()
SimpleMpesaPaymentBackendInitializer()


main_init.main()
