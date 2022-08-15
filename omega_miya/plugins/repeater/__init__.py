from nonebot import on_message
from nonebot.exception import FinishedException
from nonebot.adapters.onebot.v11.bot import Bot
from nonebot.adapters.onebot.v11.event import GroupMessageEvent
from nonebot.adapters.onebot.v11.permission import GROUP

from omega_miya.utils.rule import group_has_permission_level


# Custom plugin usage text
__plugin_custom_name__ = '复读姬'
__plugin_usage__ = r'''【复读姬】
如同人类的本质一样复读'''


LAST_MSG: dict[int, str] = {}
"""记录上一条收到的消息"""
LAST_REPEAT_MSG: dict[int, str] = {}
"""记录上一条复读过的消息"""
REPEAT_COUNT: dict[int, int] = {}
"""记录之前相同消息重复的次数"""
LAST_MSG_USER: dict[int, int] = {}
'''记录上一条消息发送的用户QQ号'''
REPEAT_THRESHOLD: int = 5
"""复读阈值, 重复的消息达到多少条就复读"""


repeater = on_message(
    rule=group_has_permission_level(level=10),
    permission=GROUP,
    priority=100,
    block=False
)


@repeater.handle()
async def handle_ignore_msg(bot: Bot, event: GroupMessageEvent):
    """忽略特殊类型的消息"""
    msg = event.get_plaintext()
    for command_start in bot.config.command_start:
        if msg.startswith(command_start):
            raise FinishedException
    if msg.startswith('!SU'):
        raise FinishedException
    if msg.startswith('.'):
        raise FinishedException


@repeater.handle()
async def handle_repeater(event: GroupMessageEvent):
    """处理复读"""
    global LAST_MSG, LAST_REPEAT_MSG, REPEAT_COUNT, LAST_MSG_USER
    user_id = event.user_id
    group_id = event.group_id
    try:
        LAST_MSG[group_id]
    except KeyError:
        LAST_MSG[group_id] = ''
    try:
        LAST_REPEAT_MSG[group_id]
    except KeyError:
        LAST_REPEAT_MSG[group_id] = ''
    try:
        LAST_MSG_USER[group_id]
    except KeyError:
        LAST_MSG_USER[group_id] = 0

    message = event.get_message()
    raw_msg = event.raw_message

    # 如果当前消息与上一条消息不同, 或者与上一次复读的消息相同, 则重置复读计数, 并更新上一条消息LAST_MSG
    if raw_msg != LAST_MSG[group_id] or raw_msg == LAST_REPEAT_MSG[group_id] or LAST_MSG_USER[group_id] == user_id:
        LAST_MSG[group_id] = raw_msg
        REPEAT_COUNT[group_id] = 0
        return
    # 否则这条消息和上条消息一致, 开始复读计数
    else:
        REPEAT_COUNT[group_id] += 1
        LAST_REPEAT_MSG[group_id] = ''
        # 当复读计数等于2时说明已经有连续3条同样的消息了, 此时触发复读, 更新上次服务消息LAST_REPEAT_MSG, 并重置复读计数
        if REPEAT_COUNT[group_id] >= REPEAT_THRESHOLD - 1:
            REPEAT_COUNT[group_id] = 0
            LAST_MSG[group_id] = ''
            LAST_REPEAT_MSG[group_id] = raw_msg
            await repeater.send(message)