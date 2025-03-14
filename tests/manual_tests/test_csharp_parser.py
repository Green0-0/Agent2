from agent2.formatting.parsers.parse_csharp import parse_csharp_elements
from agent2.element import Element

def debug_parse_and_print(code: str):
    print("=== TESTING PARSER ON THIS CODE ===")
    # Line the code, starting with zero
    
    for i, line in enumerate(code.split("\n")):
        print(f"{i} | {line}")
    print("\n=== PARSER OUTPUT ===")
    
    elements = parse_csharp_elements(code)
    
    def print_element(element: Element, indent=0):
        prefix = "  " * indent
        print(f"{prefix}Identifier: {element.identifier}")
        print(f"{prefix}Start line: {element.line_start}")
        print(f"{prefix}Docstring: {element.description[:60] + '...' if element.description and len(element.description) > 60 else element.description or '<none>'}")
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

# Test case 1: Namespace, class, method overloads
test_code_1 = '''
using System;
using System.Collections.Generic;

namespace TestNamespace
{
    /// <summary>
    /// Example class with documentation
    /// </summary>
    public class ExampleClass
    {
        /// <summary>
        /// Constructor documentation
        /// </summary>
        public ExampleClass()
        {
            // Constructor implementation
        }

        @RandomDecorator
        @AnotherDecorator
        public string Name { get; set; }

        /// <summary>
        /// Method with overload #1
        /// </summary>
        public void Process(int value)
        {
            // Implementation
        }

        /// <summary>
        /// Method with overload #2
        /// </summary>
        public void Process(string text)
        {
            // Different implementation
        }
    }

    /// <summary>
    /// Interface example
    /// </summary>
    public interface IWorker
    {
        /// <summary>
        /// Interface method
        /// </summary>
        void DoWork();
    }
}
'''

debug_parse_and_print(test_code_1)

# Test case 2: Nested types and complex structures
test_code_2 = '''
using System;

namespace ComplexNamespace
{
    /// <summary>
    /// Enum example
    /// </summary>
    public enum Direction
    {
        North,
        East,
        South,
        West
    }

    public class OuterClass
    {
        /// <summary>
        /// Method with multiple overloads
        /// </summary>
        public void ComplexMethod(int a, string b)
        {
            // Implementation
        }

        /// <summary>
        /// Second overload
        /// </summary>
        public void ComplexMethod(string a, int b, bool c)
        {
            // Different implementation
        }

        /// <summary>
        /// Nested class
        /// </summary>
        public class NestedOne
        {
            /// <summary>
            /// Double-nested class
            /// </summary>
            public class NestedTwo
            {
                public void NestedTwoMethod()
                {
                    // Implementation
                }
            }
        }

        /// <summary>
        /// Property with complex body
        /// </summary>
        public string ComplexProperty
        {
            get { return "value"; }
            set { /* Setter implementation */ }
        }
    }
}
'''

debug_parse_and_print(test_code_2)