from agent2.formatting.parsers.parse_cpp import parse_cpp_elements
from agent2.element import Element

def debug_parse_and_print(code: str):
    print("=== TESTING PARSER ON THIS CODE ===")
    # Line the code, starting with zero
    
    for i, line in enumerate(code.split("\n")):
        print(f"{i} | {line}")
    print("\n=== PARSER OUTPUT ===")
    
    elements = parse_cpp_elements(code)
    
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
/**
 * Main file utilities
 * Header documentation
 */

namespace utils {
    /// Vector utility class
    /// Provides common vector operations
    class VectorUtils {
    public:
        /**
         * Calculate dot product of two vectors
         * @param v1 First vector
         * @param v2 Second vector
         */
        double dotProduct(const std::vector<double>& v1, const std::vector<double>& v2) {
            double result = 0.0;
            for (size_t i = 0; i < v1.size(); ++i) {
                result += v1[i] * v2[i];
            }
            return result;
        }
        
        /// Normalize a vector to unit length
        template<typename T>
        std::vector<T> normalize(const std::vector<T>& vec) {
            T length = 0;
            for (const auto& v : vec) {
                length += v * v;
            }
            length = std::sqrt(length);
            
            std::vector<T> result(vec.size());
            for (size_t i = 0; i < vec.size(); ++i) {
                result[i] = vec[i] / length;
            }
            return result;
        }
    };
    
    namespace detail {
        /// Internal helper struct
        struct InternalHelper {
            void helperMethod() {
                // Implementation
            }
            
            template<typename T>
            class NestedTemplate {
                T process(T input) {
                    return input * 2;
                }
            };
        };
    }
}

/// Simple data structure
struct Point {
    double x;
    double y;
    
    /// Calculate distance from origin
    double distanceFromOrigin() const {
        return std::sqrt(x*x + y*y);
    }
};

/// Process integer values
void process(int value) {
    // Process integers
}

/// Process floating point values
void process(double value) {
    // Process doubles
}

/// Process string values
void process(const std::string& value) {
    // Process strings
}
'''

debug_parse_and_print(test_code_1)

# Test case 2: Edge cases and tricky formatting
test_code_2 = '''
/// Template with multiple parameters and weird spacing
template <
    typename T,
    typename U = int
>
class TemplateWithDefaults   {
public:
    /**
     * Complex method signature
     * with strange formatting
     */
    void   complexMethod  (
        const std::string& param1,
        int param2,
        std::function<void(int, double)> callback
    ) const;
    
    T getData() const { return data; }
private:
    T data;
};

namespace /* anonymous */ {
    /// Function in anonymous namespace
    void helperFunction() {
        // Implementation...
    }
}

struct  EmptyStruct {
};

class   ClassWithMacros 
{
public:
#define HELPER_MACRO(x) x * x

    /// Method with preprocessor directives
    int methodWithPreprocessor(int x) {
#ifdef DEBUG
        return x;
#else
        return x * 2;
#endif
    }
};

/// Trailing comment shouldn't be included in element */ 
void trailingCommentFunc() {}

// Regular comment (not a doc comment)
class UncommentedClass {
    // Another regular comment
    void uncommentedMethod();
};
'''

debug_parse_and_print(test_code_2)
