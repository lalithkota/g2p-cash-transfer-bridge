#!/usr/bin/env python3

from g2p_payments_bridge_core.app import Initializer as CoreInitializer
from gpb_simple_mpesa_payment_backend.app import (
    Initializer as SimpleMpesaPaymentBackendInitializer,
)
from gpb_translate_id_fa.app import Initializer as TranslateIdInitializer

main_init = CoreInitializer()
TranslateIdInitializer()

SimpleMpesaPaymentBackendInitializer()


main_init.main()
