from typing import List

_subscribers = dict(
    log=dict(),
    log_debug=dict(),
    log_info=dict(),
    log_warning=dict(),
    log_error=dict(),
    log_critical=dict(),
    log_workflow=dict(),
    log_metadata=dict(),
)


class EventNotFound(Exception):
    pass


def get_events() -> List[str]:
    return sorted(_subscribers)


def subscribe(event: str, func, prio: int = 50) -> None:
    if event not in _subscribers:
        raise EventNotFound(event)
    _subscribers[event].setdefault(prio, [])
    _subscribers[event][prio].append(func)


def post_event(event: str, data=None) -> None:
    if event not in _subscribers:
        raise EventNotFound(event)
    for prio in sorted(_subscribers[event]):
        for func in _subscribers[event][prio]:
            func(data)

