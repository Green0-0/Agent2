from agent2.formatting.parsers.parse_javascript import parse_javascript_elements
from agent2.element import Element

def debug_parse_and_print(code: str):
    print("=== TESTING PARSER ON THIS CODE ===")
    # Line the code, starting with zero
    
    for i, line in enumerate(code.split("\n")):
        print(f"{i} | {line}")
    print("\n=== PARSER OUTPUT ===")
    
    elements = parse_javascript_elements(code)
    
    def print_element(element: Element, indent=0):
        prefix = "  " * indent
        print(f"{prefix}Identifier: {element.identifier}")
        print(f"{prefix}Start line: {element.line_start}")
        print(f"{prefix}Description: {element.description[:50] + '...' if element.description and len(element.description) > 50 else element.description}")
        print(f"{prefix}Content preview: {element.content}")
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

# Test case 1: Various JavaScript constructs with JSDoc
test_code_1 = '''
/**
 * A class representing a person
 * @class
 */
 @mydecorator
class Person {
    @decorator
    @!decorator2
    constructor(name, age) {
        this.name = name;
        this.age = age;
    }
    
    /**
     * Get person details
     * @returns {string} Formatted person details
     */
    getDetails() {
        function formatDetails() {
            return `${this.name} (${this.age})`;
        }
        
        return formatDetails.call(this);
    }
    
    /**
     * Creates a worker function within this person
     * @returns {Object} Worker implementations
     */
    createWorker() {
        /**
         * Nested worker class
         */
        class Worker {
            work() {
                return `${this.employer.name} is working`;
            }
        }
        
        const asyncWorker = async () => {
            return "working asynchronously";
        };
        
        return { Worker, asyncWorker };
    }
}

/**
 * A utility function
 * @param {number} x - Input value
 * @return {number} Calculated result
 */
function calculate(x) {
    /**
     * Helper function
     */
    function square(n) {
        return n * n;
    }
    
    return square(x) + 1;
}

// Arrow function with JSDoc
/**
 * Process data asynchronously
 * @async
 * @param {Object} data - The input data
 */
const processData = async (data) => {
    const helper = {
        /**
         * Format the input
         */
        format: function(input) {
            return JSON.stringify(input);
        }
    };
    
    return helper.format(data);
};

// Object with methods
const utils = {
    /**
     * Add two numbers
     */
    add: function(a, b) {
        return a + b;
    },
    
    /**
     * Multiply two numbers
     */
    multiply(a, b) {
        return a * b;
    }
};

// Export statement with function
export function exportedFunction() {
    return "I'm exported";
}

// Duplicate function names to test overloading detection
function process(data) {
    return data.toString();
}

function process(data, options) {
    return data.toString() + JSON.stringify(options);
}
'''

debug_parse_and_print(test_code_1)

# Test case 2: Edge cases and tricky formatting
test_code_2 = '''
/**
 * A complex class with weird formatting
 */
class   WeirdClass 
{
    /**
     * Constructor with parameters
     */
    constructor  (  
        param1,
        param2  )   {
        this.value = param1 + param2;
    }

    /* Not a JSDoc comment */
    weirdMethod  (  )   {
        /**
         * Nested function
         */
        const   nested  =  function  (  )   {
            return 42;
        };
        
        return nested();
    }
    
    // Arrow function as class field
    arrowField = (x) => {
        return x * 2;
    }
    
    /**
     * Method with the same name
     */
    duplicate(x) {
        return x;
    }
    
    /**
     * Method with the same name but different params
     */
    duplicate(x, y) {
        return x + y;
    }
}

// Let declaration with function
let functionVar = function() {
    // Object with methods
    return {
        method1() {
            return "method1";
        },
        
        "method with spaces"() {
            return "spaces";
        },
        
        123() {
            return "numeric name";
        }
    };
};

// Deep nesting test
function outerFunction() {
    function middleFunction() {
        function innerFunction() {
            class DeepClass {
                deepMethod() {
                    return "very deep";
                }
            }
            return new DeepClass();
        }
        return innerFunction;
    }
    return middleFunction;
}
'''

debug_parse_and_print(test_code_2)

# Test case 3: Common JavaScript patterns
test_code_3 = '''
// Immediately Invoked Function Expression (IIFE)
const moduleData = (function() {
    /**
     * Internal helper function
     */
    function helper() {
        return "helper result";
    }
    
    return {
        /**
         * Public API method
         */
        publicMethod() {
            return helper();
        }
    };
})();

// Class inheritance
/**
 * Base class
 */
class Vehicle {
    constructor(make) {
        this.make = make;
    }
    
    drive() {
        return `Driving a ${this.make}`;
    }
}

/**
 * Derived class
 */
class Car extends Vehicle {
    constructor(make, model) {
        super(make);
        this.model = model;
    }
    
    drive() {
        return `${super.drive()} ${this.model}`;
    }
}

// Static methods
class MathUtils {
    /**
     * Static utility method
     */
    static sum(...args) {
        return args.reduce((a, b) => a + b, 0);
    }
}

// Callback patterns
function fetchData(callback) {
    // Simulating async operation
    setTimeout(() => {
        callback("data");
    }, 1000);
}

// Promises
function promiseExample() {
    return new Promise((resolve, reject) => {
        /**
         * Helper for processing in the promise
         */
        function processResult(data) {
            return data.toUpperCase();
        }
        
        resolve(processResult("success"));
    });
}
'''

debug_parse_and_print(test_code_3)
