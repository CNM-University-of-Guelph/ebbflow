from typing import Callable

def INITIAL(func: Callable) -> Callable:
    func._acsl_section = 'INITIAL'
    return func


def DYNAMIC(func: Callable) -> Callable:
    func._acsl_section = 'DYNAMIC'
    return func


def DERIVATIVE(func: Callable) -> Callable:
    func._acsl_section = 'DERIVATIVE'
    return func


def DISCRETE(func: Callable) -> Callable:
    func._acsl_section = 'DISCRETE'
    return func


def TERMINAL(func: Callable) -> Callable:
    func._acsl_section = 'TERMINAL'
    return func
