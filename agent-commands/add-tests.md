# Add Tests

## Goal

Add extensive, high-quality test coverage for all newly added or changed code.

## Steps

1. **Identify targets:** Review changed/added code. What functions, edge cases, and error paths need coverage?
2. **Find references:** Check if there are reference implementations (upstream libraries, similar functions in codebase) with existing tests to draw inspiration from.
3. **Write strict tests:**
   - Assert specific values, not just "runs without error"
   - Test edge cases: empty inputs, nulls, boundaries, invalid data
   - Test error paths: verify correct exceptions with correct messages
   - Test return types and shapes, not just truthiness
4. **Keep concise:**
   - Use parameterized tests (`pytest.mark.parametrize`, `test.each`) for multiple inputs
   - One assertion per concept, but multiple assertions per test is fine
   - No verbose setup—extract fixtures/helpers if repeated
5. **Verify:** Run tests. Check coverage of new code if tooling available.

## Good vs Bad Tests

```python
# Bad: just checks it runs
def test_parse_config():
    result = parse_config("config.yaml")
    assert result is not None

# Good: strict assertions on structure and values
def test_parse_config():
    result = parse_config("config.yaml")
    assert result["version"] == 2
    assert result["features"] == ["a", "b"]
    assert "deprecated" not in result
```

## What Makes a Test High-Value

- Catches real regressions (would fail if logic broke)
- Tests behavior, not implementation details
- Covers edge cases that are easy to get wrong
- Documents expected behavior through assertions

## What Makes a Test Low-Value

- Only checks code doesn't throw
- Duplicates coverage from other tests
- Tightly coupled to implementation (breaks on refactor)
- Asserts obvious/trivial things

## Rules

- Every non-trivial function/method should have at least one test
- Error handling code needs tests that trigger the errors
- If you're unsure what to test, check similar code's tests first
- Prefer fewer strict tests over many weak ones
