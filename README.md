# Flake8 ElegantObjects Plugin

Detects violations of core Elegant Objects principles including the "-er" naming principle, null usage, mutable objects, code in constructors, and getter/setter patterns.

## Error Codes

### "-er" Principle Violations

- `EO001`: Class name violates -er principle
- `EO002`: Method name violates -er principle
- `EO003`: Variable name violates -er principle
- `EO004`: Function name violates -er principle
- `EO005`: Null (None) usage violates EO principle
- `EO006`: Code in constructor violates EO principle
- `EO007`: Getter/setter method violates EO principle
- `EO008`: Mutable object violation
- `EO009`: Static method violates EO principle (no static methods allowed)
- `EO010`: isinstance/type casting violates EO principle (avoid type discrimination)
- `EO011`: Public method without contract (Protocol/ABC) violates EO principle
- `EO012`: Test method contains non-assertThat statements (only assertThat allowed)
- `EO013`: ORM/ActiveRecord pattern violates EO principle
- `EO014`: Implementation inheritance violates EO principle

## Usage

**Standalone:**

```bash
python flake8/flake8_eo_plugin.py path/to/files/*.py
python flake8/flake8_eo_plugin.py --show-source path/to/files/*.py
```

**As flake8 plugin:**
The plugin is automatically registered when the package is installed.

## Philosophy

Based on Yegor Bugayenko's Elegant Objects principles, this plugin enforces object-oriented design that treats objects as living, thinking entities rather than data containers or procedure executors.

### 1. No "-er" Entities (EO001-EO004)

**Why?** Names ending in "-er" describe what objects _do_ rather than what they _are_, reducing them to mechanical task performers instead of equal partners in your design.

- ❌ `class DataProcessor` → ✅ `class ProcessedData`
- ❌ `def analyze()` → ✅ `def analysis()`
- ❌ `parser = ArgumentParser()` → ✅ `arguments = ArgumentParser()`

### 2. No Null/None (EO005)

**Why?** Null references break object-oriented thinking by representing "absence of object" - but absence cannot participate in object interactions. They lead to defensive programming and unclear contracts.

- ❌ `return None` → ✅ Return null objects with safe default behavior
- ❌ `if user is None:` → ✅ Use null object pattern or throw exceptions

### 3. No Code in Constructors (EO006)

**Why?** Constructors should be about object assembly, not computation. Complex logic in constructors violates the principle that objects should be lazy and do work only when asked.

- ❌ `self.name = name.upper()` → ✅ `self.name = name` (transform on access)
- ❌ `self.items = [process(x) for x in data]` → ✅ `self.data = data` (process lazily)

### 4. No Getters/Setters (EO007)

**Why?** Getters and setters expose internal state, breaking encapsulation. They encourage "tell, don't ask" violations and treat objects as data containers rather than behavioral entities.

- ❌ `def get_value()` / `def set_value()` → ✅ Objects should expose behavior, not data
- ❌ `user.getName()` → ✅ `user.introduce_yourself()` or `user.greet(visitor)`

### 5. No Mutable Objects (EO008)

**Why?** Mutable objects introduce temporal coupling and make reasoning about code difficult. Immutable objects are thread-safe, predictable, and easier to test.

- ❌ `@dataclass class Data` → ✅ `@dataclass(frozen=True) class Data`
- ❌ `items = []` → ✅ `items: tuple = ()`

### 6. No Static Methods (EO009)

**Why?** Static methods belong to classes, not objects, breaking object-oriented design. They can't be overridden, can't be mocked easily, and promote procedural thinking. Every static method is a candidate for a new class.

- ❌ `@staticmethod def process()` → ✅ Create dedicated objects for behavior
- ❌ `Math.sqrt(x)` → ✅ `SquareRoot(x).value()`

### 7. No Type Discrimination (EO010)

**Why?** Using `isinstance`, type casting, or reflection is a form of object discrimination. It violates polymorphism by treating objects unequally based on their type rather than their behavior contracts.

- ❌ `isinstance(obj, str)` → ✅ Design common interfaces and use polymorphism
- ❌ `if type(x) == int:` → ✅ Let objects decide how to behave

### 8. No Public Methods Without Contracts (EO011)

**Why?** Public methods without explicit contracts (Protocol/ABC) create implicit dependencies and unclear expectations. Contracts make object collaboration explicit and testable.

- ❌ `class Service:` with ad-hoc public methods → ✅ `class Service(Protocol):` with defined contracts
- ❌ Implicit interfaces → ✅ Explicit protocols that can be tested and verified

### 9. Test Methods: Only assertThat (EO012)

**Why?** Test methods should contain only one assertion statement (preferably `assertThat`). Multiple statements create complex tests that are hard to understand and maintain. Each test should verify one specific behavior.

- ❌ `x = 5; y = calculate(x); assert y > 0` → ✅ `assertThat(calculate(5), is_(greater_than(0)))`
- ❌ Multiple assertions per test → ✅ One focused assertion per test

### 10. No ORM/ActiveRecord (EO013)

**Why?** ORM and ActiveRecord patterns mix data persistence concerns with business logic, violating single responsibility. They create anemic domain models and tight coupling to databases.

- ❌ `user.save()`, `Model.find()` → ✅ Separate repository objects
- ❌ Mixing persistence with business logic → ✅ Clean separation of concerns

### 11. No Implementation Inheritance (EO014)

**Why?** Implementation inheritance creates tight coupling between parent and child classes, making code fragile and hard to test. It violates composition over inheritance and creates deep hierarchies that are difficult to understand.

- ❌ `class UserList(list):` → ✅ `class UserList:` with composition
- ❌ Inheriting concrete implementations → ✅ Inherit only from abstractions (ABC/Protocol)

The plugin detects the "hall of shame" naming patterns: Manager, Controller, Helper, Handler, Writer, Reader, Converter, Validator, Router, Dispatcher, Observer, Listener, Sorter, Encoder, Decoder, Analyzer, etc.

## Configuration

The plugin is integrated with flake8. Add to your `.flake8` config:

```ini
[flake8]
select = E,W,F,EO
per-file-ignores =
    tests/*:EO012  # Allow non-assertThat in tests if needed
```

### Testing

Run the plugin tests:

```bash
python -m pytest tests/test_eo_violations.py -v
```
