from agent2.formatting.parsers.parse_typescript import parse_typescript_elements
from agent2.element import Element

def debug_parse_and_print(code: str):
    print("=== TESTING PARSER ON THIS CODE ===")
    # Line the code, starting with zero
    
    for i, line in enumerate(code.split("\n")):
        print(f"{i} | {line}")
    print("\n=== PARSER OUTPUT ===")
    
    elements = parse_typescript_elements(code)
    
    def print_element(element: Element, indent=0):
        prefix = "  " * indent
        print(f"{prefix}Identifier: {element.identifier}")
        print(f"{prefix}Start line: {element.line_start}")
        print(f"{prefix}Description: {element.description[:50] + '...' if element.description and len(element.description) > 50 else element.description}")
        print(f"{prefix}Content preview: {element.content[:100]}...")
        print(f"{prefix}Contains {len(element.elements)} sub-elements")
        for child in element.elements:
            print()
            print_element(child, indent + 1)
    
    if not elements:
        print("No elements found!")
    else:
        for idx, elem in enumerate(elements):
            print(f"Top-level element #{idx + 1}:")
            print_element(elem)
            print("\n" + "-" * 80 + "\n")

# Test case 1: TypeScript classes, interfaces, and type annotations
test_code_1 = '''
/**
 * Interface for representing a point in 2D space
 */
interface Point {
    x: number;
    y: number;
    distanceFrom(other: Point): number;
}

@decorator1
@decorator2
class Container<T> {
    private value: T;
    
    /**
     * Create a new container
     * @param initialValue - The initial value to store
     */
    constructor(initialValue: T) {
        this.value = initialValue;
    }
    
    /**
     * Get the stored value
     * @returns The contained value
     */
    getValue(): T {
        return this.value;
    }
    
    /**
     * Set the stored value
     * @param newValue - The new value to store
     */
    setValue(newValue: T): void {
        this.value = newValue;
    }
}

/**
 * Type alias for a function that processes numbers
 */
type NumberProcessor = (input: number) => number;

/**
 * Function overload demonstration
 */
function process(input: number): number;
function process(input: string): string;
function process(input: any): any {
    if (typeof input === 'number') {
        return input * 2;
    } else if (typeof input === 'string') {
        return input.toUpperCase();
    }
    return input;
}

/**
 * Function with complex type parameters
 */
function transform<T, U>(items: T[], transformer: (item: T) => U): U[] {
    return items.map(transformer);
}
'''

debug_parse_and_print(test_code_1)

# Test case 2: Advanced TypeScript features
test_code_2 = '''
/**
 * Enum for representing directions
 */
enum Direction {
    North = "NORTH",
    South = "SOUTH",
    East = "EAST",
    West = "WEST"
}

/**
 * Namespace for utility functions
 */
namespace Utils {
    /**
     * Format a string in the namespace
     */
    export function formatString(input: string): string {
        return input.trim();
    }
    
    /**
     * Nested namespace
     */
    export namespace Math {
        /**
         * Calculate sum
         */
        export function sum(numbers: number[]): number {
            return numbers.reduce((a, b) => a + b, 0);
        }
    }
    
    /**
     * Interface inside namespace
     */
    export interface Formatter<T> {
        format(input: T): string;
    }
}

/**
 * Class implementing generic interface
 */
class StringFormatter implements Utils.Formatter<string> {
    /**
     * Implementation of format method
     */
    format(input: string): string {
        return `Formatted: ${input}`;
    }
}

/**
 * Abstract class example
 */
abstract class Shape {
    /**
     * Constructor with optional parameter
     */
    constructor(protected color?: string) {}
    
    /**
     * Abstract method
     */
    abstract calculateArea(): number;
    
    /**
     * Concrete method
     */
    getColor(): string {
        return this.color || "transparent";
    }
}

/**
 * Class with property initializers
 */
class Config {
    // Property with type and initializer
    timeout: number = 1000;
    
    // Private property with type
    private host: string = "localhost";
    
    // Readonly property
    readonly version: string = "1.0.0";
    
    /**
     * Method using properties
     */
    getConnectionString(): string {
        return `${this.host}:${this.timeout}`;
    }
}
'''

debug_parse_and_print(test_code_2)

# Test case 3: Complex type patterns
test_code_3 = '''
/**
 * Complex mapped type
 */
type Readonly<T> = {
    readonly [P in keyof T]: T[P];
};

/**
 * Utility type with conditional type
 */
type ExtractReturnType<T extends (...args: any[]) => any> = T extends (...args: any[]) => infer R ? R : never;

/**
 * Function with complex return type
 */
function createState<T>(): [T | undefined, (newState: T) => void] {
    let state: T | undefined;
    
    function setState(newState: T): void {
        state = newState;
    }
    
    return [state, setState];
}

/**
 * Class with static methods and properties
 */
class MathUtils {
    /**
     * Static property
     */
    static readonly PI: number = 3.14159;
    
    /**
     * Private static property
     */
    private static precision: number = 0.00001;
    
    /**
     * Static method
     */
    static round(value: number): number {
        return Math.round(value);
    }
    
    /**
     * Static generic method
     */
    static identity<T>(value: T): T {
        return value;
    }
}

/**
 * Interface extending multiple interfaces
 */
interface Named {
    name: string;
}

interface Aged {
    age: number;
}

interface Person extends Named, Aged {
    email: string;
}

/**
 * Function with intersection types
 */
function mergeObjects<T, U>(obj1: T, obj2: U): T & U {
    return { ...obj1, ...obj2 };
}

// Class with decorators
/**
 * Class decorator
 */
@logged
class DecoratedClass {
    /**
     * Method with parameter decorator
     */
    greet(@required name: string): string {
        return `Hello ${name}`;
    }
}
'''

debug_parse_and_print(test_code_3)
