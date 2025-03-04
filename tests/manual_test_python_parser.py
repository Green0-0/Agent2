from agent2.formatting.parsers.parse_python import parse_python_elements
from agent2.element import Element

def debug_parse_and_print(code: str):
    print("=== TESTING PARSER ON THIS CODE ===")
    # Line the code, starting with zero
    
    for i, line in enumerate(code.split("\n")):
        print(f"{i} | {line}")
    print("\n=== PARSER OUTPUT ===")
    
    elements = parse_python_elements(code)
    
    def print_element(element: Element, indent=0):
        prefix = "  " * indent
        print(f"{prefix}Identifier: {element.identifier}")
        print(f"{prefix}Start line: {element.line_start}")
        print(f"{prefix}Docstring: {element.description + '...' if element.description else '<none>'}")
        preview = element.content
        print(f"{prefix}Content preview: {preview}...")
        print(f"{prefix}Contains {len(element.elements)} sub-elements")
        for child in element.elements:
            print_element(child, indent + 1)
            print()
    
    for idx, elem in enumerate(elements):
        print(f"Top-level element #{idx + 1}:")
        print_element(elem)
        print("\n" + "-" * 80 + "\n")

# Complex test case 1: Deep nesting with mixed elements
test_code_1 = '''
"""
Module docstring here
"""

@factory_decorator(arg=123)
class MegaClass:
    """Class docstring
    spans multiple lines"""
    
    @property
    @debug_logger
    def complex_property(self):
        @nested_decorator
        def inner_function():
            """Inner function doc"""
            class InnerClass:
                def inner_method(self):
                    pass
        return inner_function
        
    def create_worker(self):
        async def async_worker():
            """Async worker doc"""
            pass
            
        class WorkerClass:
            def work(self):
                pass
        return async_worker, WorkerClass

@task_decorator(timeout=10)
def top_level_function():
    lambda_func = lambda x: x**2  # Should be ignored
    def closure_func():
        pass
    return closure_func

async def async_top_level(param: int):
    """Async function doc"""
    @async_decorator
    async def nested_async():
        pass
    return nested_async
'''

debug_parse_and_print(test_code_1)

# Test case 2: Edge cases and tricky formatting
test_code_2 = '''
@d1
@d2(  
    complex_arg=[1,2,3]
)
class WeirdClass:  
    \'\'\'Multiline
    docstring\'\'\'
    
    def empty_method(self): ...

    @decorator_with(
        multiline_args
    )
    def decorated_method(
        self, 
        param: Callable[[int], str]
    ) -> None:
        """Short doc"""
        
        @inner_decorator
        @another_decorator
        def mega_nested():
            pass
            
        return [mega_nested for _ in range(5)]

def function_with_complex_body():
    class InConditional:
        def method_in_conditional(self):
            pass
    return InConditional
'''

debug_parse_and_print(test_code_2)