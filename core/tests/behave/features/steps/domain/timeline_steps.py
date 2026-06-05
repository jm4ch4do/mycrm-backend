"""Then steps specific to timeline tests."""

from behave import then
from dateutil.parser import parse as parse_datetime


@then('the timeline is sorted by "{field}" descending')
def step_verify_timeline_sorting(context, field):
    """
    Verify that timeline entries are sorted by the specified field in descending order.
    
    Args:
        context: Behave context
        field: Field name to check sorting on (e.g., "created_at")
    """
    # Handle both list and paginated responses
    if isinstance(context.response_data, dict) and "results" in context.response_data:
        items = context.response_data["results"]
    else:
        items = context.response_data
    
    assert len(items) > 0, "No items to check sorting on"
    
    # Extract field values
    values = []
    for item in items:
        value = item.get(field)
        assert value is not None, f"Item missing field '{field}': {item}"
        
        # Parse datetime strings for comparison
        if field.endswith('_at'):
            value = parse_datetime(value)
        
        values.append(value)
    
    # Check descending order
    for i in range(len(values) - 1):
        assert values[i] >= values[i + 1], (
            f"Timeline not sorted by {field} descending: "
            f"{values[i]} should be >= {values[i + 1]}"
        )


@then('the response contains pagination with "{page_size}" results per page')
def step_verify_pagination(context, page_size):
    """
    Verify that the response contains pagination metadata.
    
    Args:
        context: Behave context
        page_size: Expected page size
    """
    page_size = int(page_size)
    
    assert isinstance(context.response_data, dict), "Response should be a dict for paginated results"
    assert "results" in context.response_data, "Response should have 'results' key"
    assert "count" in context.response_data, "Response should have 'count' key"
    assert "next" in context.response_data, "Response should have 'next' key"
    assert "previous" in context.response_data, "Response should have 'previous' key"
    
    results = context.response_data["results"]
    assert len(results) <= page_size, f"Page has {len(results)} results, expected max {page_size}"
