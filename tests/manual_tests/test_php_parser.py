from agent2.formatting.parsers.parse_php import parse_php_elements
from agent2.element import Element

def debug_parse_and_print(code: str):
    print("=== TESTING PARSER ON THIS CODE ===")
    # Line the code, starting with zero
    
    for i, line in enumerate(code.split("\n")):
        print(f"{i} | {line}")
    print("\n=== PARSER OUTPUT ===")
    
    elements = parse_php_elements(code)
    
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

# Complex test case 1: Class hierarchy with methods and docstrings
test_code_1 = '''<?php
/**
 * File with various PHP elements to test parser
 */

/**
 * Parent class with documentation
 * 
 * @package TestPackage
 */
class ParentClass {
    /**
     * Constructor documentation
     * @param string $name Name parameter
     */
    public function __construct(string $name) {
        $this->name = $name;
    }
    
    /**
     * Public method with documentation
     * @return string Returns a greeting
     */
    public function sayHello(): string {
        return "Hello from parent";
    }
    
    protected function internalMethod() {
        // This is just a comment, not a docstring
        $x = 1;
        
        // Define a closure - should be ignored by parser
        $closure = function() {
            return true;
        };
    }
}

/**
 * Child class extending ParentClass
 */
class ChildClass extends ParentClass {
    /**
     * Override parent method
     */
    public function sayHello(): string {
        /**
         * Inner class defined inside a method
         */
        class NestedClass {
            public function nestedMethod() {
                return "Nested";
            }
        }
        
        return parent::sayHello() . " and child";
    }
    
    /**
     * Complex method with nested elements
     */
    public function complexMethod() {
        class InnerHelper {
            /**
             * Helper method documentation
             */
            public function help() {
                return "Helping";
            }
        }
        
        return new InnerHelper();
    }
}

/**
 * Standalone function
 * @param int $x First parameter
 * @param int $y Second parameter
 * @return int Sum of parameters
 */
function add(int $x, int $y): int {
    return $x + $y;
}

// PHP 8 attributes example (if supported by tree-sitter)
#[Route("/api/users")]
class UserController {
    #[Route("/get/{id}")]
    public function getUser(int $id) {
        // Method implementation
    }
    
    /**
     * Create new user
     * @param array $userData User information
     */
    #[Route("/create")]
    public function createUser(array $userData) {
        // Method with both docstring and attribute
    }
}
'''

debug_parse_and_print(test_code_1)

# Test case 2: Interfaces, traits, and formatting edge cases
test_code_2 = '''<?php
namespace App\\Services;

/**
 * Interface documentation
 */
interface PaymentInterface {
    /**
     * Process a payment
     */
    public function processPayment(float $amount): bool;
}

/**
 * Trait documentation
 */
trait LoggableTrait {
    /**
     * Log a message
     */
    protected function log(string $message): void {
        // Implementation
    }
    
    abstract protected function getLogPrefix(): string;
}

/**
 * Implementation class
 */
class PaymentService implements PaymentInterface {
    use LoggableTrait;
    
    /**
     * Implementation of interface method
     */
    public function processPayment(float $amount): bool {
        $this->log("Processing payment: " . $amount);
        return true;
    }
    
    /**
     * Implementation of abstract method from trait
     */
    protected function getLogPrefix(): string {
        return "PAYMENT";
    }
    
    /**
     * Multiline method signature
     * @param string $provider Payment provider
     * @param array $options Configuration options
     */
    public function configureProvider(
        string $provider,
        array $options = []
    ): void {
        // Method implementation
    }
}

/**
 * Function with multiline declaration
 */
function complex_calculation(
    int $a,
    int $b,
    string $operation = 'add'
): int {
    return match($operation) {
        'add' => $a + $b,
        'multiply' => $a * $b,
        default => throw new \\InvalidArgumentException("Unknown operation")
    };
}
'''

debug_parse_and_print(test_code_2)
