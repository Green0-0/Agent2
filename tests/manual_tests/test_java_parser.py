from agent2.formatting.parsers.parse_java import parse_java_elements
from agent2.element import Element

def debug_parse_and_print(code: str):
    print("=== TESTING PARSER ON THIS CODE ===")
    # Line the code, starting with zero
    
    for i, line in enumerate(code.split("\n")):
        print(f"{i} | {line}")
    print("\n=== PARSER OUTPUT ===")
    
    elements = parse_java_elements(code)
    
    def print_element(element: Element, indent=0):
        prefix = "  " * indent
        print(f"{prefix}Identifier: {element.identifier}")
        print(f"{prefix}Start line: {element.line_start}")
        print(f"{prefix}Docstring: {element.description[:50] + '...' if element.description and len(element.description) > 50 else element.description}")
        preview = element.content[:100] + "..." if len(element.content) > 100 else element.content
        print(f"{prefix}Content preview: {preview}")
        print(f"{prefix}Contains {len(element.elements)} sub-elements")
        for child in element.elements:
            print_element(child, indent + 1)
            print()
    
    for idx, elem in enumerate(elements):
        print(f"Top-level element #{idx + 1}:")
        print_element(elem)
        print("\n" + "-" * 80 + "\n")

# Test case 1: Class with overloaded methods, constructors, and annotations
test_code_1 = '''
/**
 * Main service class with multiple features
 * @author JavaDev
 */
@Service
@RequestMapping("/api")
public class UserService {
    
    private final UserRepository repository;
    
    /**
     * Default constructor
     */
    public UserService() {
        this.repository = null;
    }
    
    /**
     * Overloaded constructor with repository
     */
    public UserService(UserRepository repository) {
        this.repository = repository;
    }
    
    /**
     * Find user by ID
     */
    public User findById(Long id) {
        return repository.findById(id).orElse(null);
    }
    
    /**
     * Overloaded find method
     */
    public User findById(String username) {
        return repository.findByUsername(username);
    }
    
    /**
     * Inner configuration class
     */
    static class ServiceConfig {
        public void configure() {
            System.out.println("Configuring service");
        }
    }
}
'''

debug_parse_and_print(test_code_1)

# Test case 2: Multiple classes, interfaces, and enums with complex structures
test_code_2 = '''
/**
 * Data processing interface
 */
@FunctionalInterface
public interface Processor {
    void process(String data);
    
    default void init() {
        System.out.println("Initializing processor");
    }
}

/**
 * Simple enum for status values
 */
public enum Status {
    PENDING,
    ACTIVE,
    COMPLETED;
    
    public boolean isFinished() {
        return this == COMPLETED;
    }
}

/**
 * Complex implementation class
 */
@Component
@SuppressWarnings("unused")
public class ProcessorImpl implements Processor {
    
    @Override
    public void process(String data) {
        // Implementation
    }
    
    /**
     * Helper method with generic type
     */
    public <T extends Comparable<T>> T findMax(List<T> items) {
        return items.stream().max(Comparable::compareTo).orElse(null);
    }
    
    /**
     * Nested enum
     */
    public enum ProcessType {
        SYNC, ASYNC
    }
    
    /**
     * Nested interface
     */
    interface ProcessorCallback {
        void onComplete();
    }
}
'''

debug_parse_and_print(test_code_2)

# Test case 3: Complex annotations and nested structures
test_code_3 = '''
@Target({ElementType.TYPE, ElementType.METHOD})
@Retention(RetentionPolicy.RUNTIME)
@Documented
public @interface Transactional {
    String value() default "";
    Propagation propagation() default Propagation.REQUIRED;
    Isolation isolation() default Isolation.DEFAULT;
}

@Repository
@Transactional(
    propagation = Propagation.REQUIRES_NEW,
    isolation = Isolation.SERIALIZABLE
)
public class ComplexRepository<T, ID> {

    @Autowired
    private SessionFactory sessionFactory;
    
    /**
     * Save entity with validation
     * @param entity the entity to save
     * @return saved entity
     */
    @Transactional
    public <S extends T> S save(S entity) {
        class ValidationHelper {
            boolean validate(S entity) {
                return entity != null;
            }
        }
        
        ValidationHelper helper = new ValidationHelper();
        if (helper.validate(entity)) {
            sessionFactory.getCurrentSession().save(entity);
            return entity;
        }
        return null;
    }
    
    /**
     * Delete by ID
     */
    @Transactional
    public void deleteById(ID id) {
        // Implementation
    }
}
'''

debug_parse_and_print(test_code_3)