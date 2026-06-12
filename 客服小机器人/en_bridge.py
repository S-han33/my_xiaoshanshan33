"""
en_bridge.py — English function name mappings for cs-reply-bot

Provides English aliases for Chinese-named functions so that
English-speaking developers can work with the code seamlessly.

Usage:
    from en_bridge import intent_classify, pre_sale_process, ...
"""

from 机器人 import (
    识别意图 as intent_classify,
    售前处理 as pre_sale_process,
    售中处理 as in_sale_process,
    售后处理 as after_sale_process,
    模拟商品 as SimulateProduct,
    call_coze_workflow,
    call_platform_api,
    fetch_orders_by_user,
    main,
)
