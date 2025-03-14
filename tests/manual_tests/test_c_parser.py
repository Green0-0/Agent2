from agent2.formatting.parsers.parse_c import parse_c_elements
from agent2.element import Element

def debug_parse_and_print(code: str):
    print("=== TESTING PARSER ON THIS CODE ===")
    # Line the code, starting with zero
    
    for i, line in enumerate(code.split("\n")):
        print(f"{i} | {line}")
    print("\n=== PARSER OUTPUT ===")
    
    elements = parse_c_elements(code)
    
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

# Test case 1: Various C constructs including functions, structs, etc.
test_code_1 = '''
/**
 * Module level comment
 * that spans multiple lines
 */

// Function declaration with docstring
// Computes the square of a number
int square(int x);

/**
 * Struct representing a point in 2D space
 */
struct Point {
    int x;
    int y;
    
    // Nested struct example
    struct Color {
        unsigned char r, g, b;
    } color;
};

// Function definition with parameters
// This function is documented
int add(int a, int b) {
    // Local function (in C this is just a nested scope)
    {
        int temp = a + b;
        return temp;
    }
}

// Function with same name but different parameters (overloading signature)
float add(float a, float b) {
    return a + b;
}

typedef struct {
    char name[50];
    int age;
} Person;

enum Color {
    RED,
    GREEN,
    BLUE
};

union Data {
    int i;
    float f;
    char str[20];
};

// Complex function with nested elements
int process_data(int* data, int size) {
    // Nested declarations
    struct Result {
        int sum;
        float average;
    };
    
    // Function implementation
    struct Result result;
    result.sum = 0;
    
    for (int i = 0; i < size; i++) {
        result.sum += data[i];
    }
    
    result.average = (float)result.sum / size;
    return result.sum;
}
'''

debug_parse_and_print(test_code_1)

# Test case 2: Edge cases and more complex structures
test_code_2 = '''
// Forward declarations
struct Node;
typedef struct Node Node;

/**
 * Complex typedef with function pointer
 */
typedef int (*CompareFn)(const void*, const void*);

// Multi-level nested structures
struct OuterStruct {
    int outer_field;
    
    struct MiddleStruct {
        int middle_field;
        
        struct InnerStruct {
            int inner_field;
        } inner;
        
    } middle;
};

/* Function with complex
   parameter types */
void complex_function(int matrix[10][10], char* (*getter)(void)) {
    typedef struct {
        int x;
    } LocalType;
    
    LocalType local_var;
    local_var.x = 5;
}

// Variadic function
int printf(const char* format, ...);

// Inline function
static inline int max(int a, int b) {
    return (a > b) ? a : b;
}

// Function returning function pointer
void (*signal(int sig, void (*func)(int)))(int);

// K&R style function definition
int old_style_function(a, b)
int a;
char* b;
{
    return a;
}
'''

debug_parse_and_print(test_code_2)
