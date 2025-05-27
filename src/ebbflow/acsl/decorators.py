from typing import Callable

def INITIAL(func: Callable) -> Callable:
    func._acsl_section = 'INITIAL'
    if not hasattr(func, '_sort'):
        func._sort = False
    return func


def DYNAMIC(func: Callable) -> Callable:
    func._acsl_section = 'DYNAMIC'
    if not hasattr(func, '_sort'):
        func._sort = False
    return func


def DERIVATIVE(func: Callable) -> Callable:
    func._acsl_section = 'DERIVATIVE'
    func._sort = True
    return func


def DISCRETE(func: Callable) -> Callable:
    func._acsl_section = 'DISCRETE'
    if not hasattr(func, '_sort'):
        func._sort = False
    return func


def TERMINAL(func: Callable) -> Callable:
    func._acsl_section = 'TERMINAL'
    if not hasattr(func, '_sort'):
        func._sort = False
    return func


def SORT(func: Callable) -> Callable:
    func._sort = True
    return func
