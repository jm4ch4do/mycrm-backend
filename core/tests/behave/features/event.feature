@event
Feature: Event API
    As a CRM operator
    I want to inspect immutable event facts
    So that I can debug and audit automation inputs

    Scenario: Admin can list all events
        Given I am "authenticated" as "a staff user"
        And I create a new "event"
            | event_type         |
            | deal.stage_changed |
        When I send a "GET" request to "/events/"
        Then the response status code is "200" and contains "1" records
        And the response contains
            | event_type         |
            | deal.stage_changed |

    Scenario: Filter events by event_type
        Given I am "authenticated" as "a staff user"
        And I create a new "event"
            | event_type     |
            | task.completed |
        And I create a new "event"
            | event_type         |
            | deal.stage_changed |
        When I send a "GET" request to "/events/"
            | field      | operator | value          |
            | event_type | eq       | task.completed |
        Then the response status code is "200" and contains "1" records
        And the response contains
            | event_type     |
            | task.completed |

    Scenario: Filter events by entity_type and entity_id
        Given I am "authenticated" as "a staff user"
        And I create a new "event"
            | entity_type |
            | Deal        |
        When I send a "GET" request to "/events/"
            | field       | operator | value |
            | entity_type | eq       | Deal  |
        Then the response status code is "200" and contains "1" records
        And the response contains
            | entity_type |
            | Deal        |

    Scenario: Admin can retrieve a single event
        Given I am "authenticated" as "a staff user"
        And I create a new "event"
            | event_type  |
            | call.logged |
        When I send a "GET" request to "/events/{event.id}/"
        Then the response status code is "200"
        And the response should contain details
            | event_type  |
            | call.logged |

    Scenario: Retrieve unknown event returns 404
        Given I am "authenticated" as "a regular user"
        When I send a "GET" request to "/events/00000000-0000-0000-0000-000000000000/"
        Then the response status code is "404"

    Scenario: Non-admin authenticated user cannot list events
        Given I am "authenticated" as "a regular user"
        When I send a "GET" request to "/events/"
        Then the response status code is "403"

    Scenario: Non-admin authenticated user can retrieve a single event
        Given I am "authenticated" as "a staff user"
        And I create a new "event"
            | event_type         |
            | deal.stage_changed |
        And I am "authenticated" as "a regular user"
        When I send a "GET" request to "/events/{event.id}/"
        Then the response status code is "200"

    Scenario: Unauthenticated user cannot access events
        Given I create a new "event"
            | event_type         |
            | deal.stage_changed |
        And I am "not authenticated"
        When I send a "GET" request to "/events/"
        Then the response status code is "403"

    Scenario: POST to events is not allowed
        Given I am "authenticated" as "a staff user"
        When I send a "POST" request to "/events/" with body
            | field          | value              |
            | event_type     | deal.stage_changed |
            | source_service | core               |
            | entity_type    | Deal               |
        Then the response status code is "405"

    Scenario: Events are ordered newest first
        Given I am "authenticated" as "a staff user"
        And I create a new "event"
            | event_type   |
            | deal.created |
        And I create a new "event"
            | event_type         |
            | deal.stage_changed |
        When I send a "GET" request to "/events/"
        Then the response status code is "200"
        And the response is ordered by "occurred_at" descending

    Scenario: Soft-deleted records are excluded from events
        Given I am "authenticated" as "a staff user"
        And I create "accounts" through the API
            | name      |
            | Acme Corp |
        And I create "deals" through the API
            | name             | account_id |
            | Soft DeletedDeal | Acme Corp  |
        And I create a new "event"
            | event_type        | entity_type | deal_id          | before_state          | after_state          |
            | deal.soft_deleted | Deal        | Soft DeletedDeal | {"is_invalid": false} | {"is_invalid": true} |
        And I delete "deals" with "name" "Soft DeletedDeal" using "soft delete"
        When I send a "GET" request to "/events/"
            | field       | operator | value |
            | entity_type | eq       | Deal  |
        Then the response status code is "200" and contains "1" records
        And the response contains
            | event_type        |
            | deal.soft_deleted |
