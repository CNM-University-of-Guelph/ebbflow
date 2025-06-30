from typing import Callable
import functools

def INITIAL(func: Callable) -> Callable:
    func.acsl_section = 'INITIAL'
    func.collect_constants = True
    if not hasattr(func, 'collect_statevars'):
        func.collect_statevars = False
    if not hasattr(func, 'sort'):
        func.sort = False
    return func


def DYNAMIC(func: Callable) -> Callable:
    func.acsl_section = 'DYNAMIC'
    func.collect_constants = True
    if not hasattr(func, 'collect_statevars'):
        func.collect_statevars = False
    if not hasattr(func, 'sort'):
        func.sort = False
    return func


def DERIVATIVE(func: Callable) -> Callable:
    func.acsl_section = 'DERIVATIVE'
    func.collect_constants = True
    func.collect_statevars = True
    func.sort = True
    return func


def DISCRETE(func: Callable) -> Callable:
    func.acsl_section = 'DISCRETE'
    func.collect_constants = True
    if not hasattr(func, 'collect_statevars'):
        func.collect_statevars = False
    if not hasattr(func, 'sort'):
        func.sort = False
    return func


def TERMINAL(func: Callable) -> Callable:
    func.acsl_section = 'TERMINAL'
    func.collect_constants = True
    if not hasattr(func, 'collect_statevars'):
        func.collect_statevars = False
    if not hasattr(func, 'sort'):
        func.sort = False
    return func


def SORT(func: Callable) -> Callable:
    func.sort = True
    func.collect_statevars = True
    return func


def PROCEDURAL(func: Callable) -> Callable:
    func._procedural = True
    return func
