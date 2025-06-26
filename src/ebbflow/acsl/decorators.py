from typing import Callable
import functools

def INITIAL(func: Callable) -> Callable:
    func._acsl_section = 'INITIAL'
    func._collect_constants = True
    if not hasattr(func, '_collect_statevars'):
        func._collect_statevars = False
    if not hasattr(func, '_sort'):
        func._sort = False
    return func


def DYNAMIC(func: Callable) -> Callable:
    func._acsl_section = 'DYNAMIC'
    func._collect_constants = True
    if not hasattr(func, '_collect_statevars'):
        func._collect_statevars = False
    if not hasattr(func, '_sort'):
        func._sort = False
    return func


def DERIVATIVE(func: Callable) -> Callable:
    func._acsl_section = 'DERIVATIVE'
    func._collect_constants = True
    func._collect_statevars = True
    func._sort = True
    return func


def DISCRETE(func: Callable) -> Callable:
    func._acsl_section = 'DISCRETE'
    func._collect_constants = True
    if not hasattr(func, '_collect_statevars'):
        func._collect_statevars = False
    if not hasattr(func, '_sort'):
        func._sort = False
    return func


def TERMINAL(func: Callable) -> Callable:
    func._acsl_section = 'TERMINAL'
    func._collect_constants = True
    if not hasattr(func, '_collect_statevars'):
        func._collect_statevars = False
    if not hasattr(func, '_sort'):
        func._sort = False
    return func


def SORT(func: Callable) -> Callable:
    func._sort = True
    func._collect_statevars = True
    return func


def PROCEDURAL(func: Callable) -> Callable:
    func._procedural = True
    return func
