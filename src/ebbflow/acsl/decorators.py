"""Decorators used to assign special attributes to user-defined functions.

These attributes are used to identify the section type and to determine how the 
function AST tree is handled by AcslBuild.
"""

from typing import Callable

def INITIAL(func: Callable) -> Callable:
    """Decorator to identify the INITIAL section.
    
    Parameters
    ----------
    func : Callable
        The function to be decorated.
    
    Returns
    -------
    Callable
        The decorated function with added attributes.
        
    Notes
    -----
    This decorator adds the following attributes to the decorated function:
    
    * acsl_section : str
        Set to 'INITIAL' to identify the section type.
    * collect_constants : bool
        Set to True to enable constant collection.
    * collect_statevars : bool
        Set to False unless already present.
    * sort : bool
        Set to False unless already present.
    """
    func.acsl_section = 'INITIAL'
    func.collect_constants = True
    if not hasattr(func, 'collect_statevars'):
        func.collect_statevars = False
    if not hasattr(func, 'sort'):
        func.sort = False
    return func


def DYNAMIC(func: Callable) -> Callable:
    """Decorator to identify the DYNAMIC section.
    
    Parameters
    ----------
    func : Callable
        The function to be decorated.
        
    Returns
    -------
    Callable
        The decorated function with added attributes.
        
    Notes
    -----
    This decorator adds the following attributes to the decorated function:
    
    * acsl_section : str
        Set to 'DYNAMIC' to identify the section type.
    * collect_constants : bool
        Set to True to enable constant collection.
    * collect_statevars : bool
        Set to False unless already present.
    * sort : bool
        Set to False unless already present.
    """
    func.acsl_section = 'DYNAMIC'
    func.collect_constants = True
    if not hasattr(func, 'collect_statevars'):
        func.collect_statevars = False
    if not hasattr(func, 'sort'):
        func.sort = False
    return func


def DERIVATIVE(func: Callable) -> Callable:
    """Decorator to identify the DERIVATIVE section.
    
    Parameters
    ----------
    func : Callable
        The function to be decorated.
        
    Returns
    -------
    Callable
        The decorated function with added attributes.
        
    Notes
    -----
    This decorator adds the following attributes to the decorated function:
    
    * acsl_section : str
        Set to 'DERIVATIVE' to identify the section type.
    * collect_constants : bool
        Set to True to enable constant collection.
    * collect_statevars : bool
        Set to True to enable statevar collection.
    * sort : bool
        Set to True to enable sorting.
    """
    func.acsl_section = 'DERIVATIVE'
    func.collect_constants = True
    func.collect_statevars = True
    func.sort = True
    return func


def DISCRETE(func: Callable) -> Callable:
    """Decorator to identify the DISCRETE section.
    
    Parameters
    ----------
    func : Callable
        The function to be decorated.
        
    Returns
    -------
    Callable
        The decorated function with added attributes.
        
    Notes
    -----
    This decorator adds the following attributes to the decorated function:
    
    * acsl_section : str
        Set to 'DISCRETE' to identify the section type.
    * collect_constants : bool
        Set to True to enable constant collection.
    * collect_statevars : bool
        Set to False unless already present.
    * sort : bool
        Set to False unless already present.
    """
    func.acsl_section = 'DISCRETE'
    func.collect_constants = True
    if not hasattr(func, 'collect_statevars'):
        func.collect_statevars = False
    if not hasattr(func, 'sort'):
        func.sort = False
    return func


def TERMINAL(func: Callable) -> Callable:
    """Decorator to identify the TERMINAL section.
    
    Parameters
    ----------
    func : Callable
        The function to be decorated.
        
    Returns
    -------
    Callable
        The decorated function with added attributes.
        
    Notes
    -----
    This decorator adds the following attributes to the decorated function:
    
    * acsl_section : str
        Set to 'TERMINAL' to identify the section type.
    * collect_constants : bool
        Set to True to enable constant collection.
    * collect_statevars : bool
        Set to False unless already present.
    * sort : bool
        Set to False unless already present.
    """
    func.acsl_section = 'TERMINAL'
    func.collect_constants = True
    if not hasattr(func, 'collect_statevars'):
        func.collect_statevars = False
    if not hasattr(func, 'sort'):
        func.sort = False
    return func


def SORT(func: Callable) -> Callable:
    """Decorator to apply sorting to the section.
    
    Parameters
    ----------
    func : Callable
        The function to be decorated.
        
    Returns
    -------
    Callable
        The decorated function with added attributes.
        
    Notes
    -----
    This decorator adds the following attributes to the decorated function:

    * sort : bool
        Set to True to enable sorting.
    * collect_statevars : bool
        Set to True to enable statevar collection.
    """
    func.sort = True
    func.collect_statevars = True
    return func


def PROCEDURAL(func: Callable) -> Callable:
    """Decorator to set a function as a procedural block.
    
    Parameters
    ----------
    func : Callable
        The function to be decorated.
        
    Returns
    -------
    Callable
        The decorated function with added attributes.
        
    Notes
    -----
    This decorator adds the following attributes to the decorated function:
    
    * procedural : bool
        Set to True to identify the function as a procedural block.
    """
    func.procedural = True
    return func
