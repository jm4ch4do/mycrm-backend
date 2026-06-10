@rule
Feature: Rule API
    As a CRM admin
    I want to manage automation rules
    So that trigger-driven workflows only run when business conditions pass

    Background:
        Given I am "authenticated" as "a staff user"
        And I create a new "trigger"
            | name               | event_type         |
            | Deal Stage Trigger | deal.stage_changed |

    Scenario: Admin can create a rule
        Given I create "rules" through the API
            | name                      | trigger_id         |
            | Deal Stage Qualified Rule | Deal Stage Trigger |
        Then the response status code is "201"
        And the response contains field "name"
        And the response contains field "trigger"
        And the response contains field "conditions"

    Scenario: Admin can list rules
        Given I create a new "rule"
            | name                      | trigger_id         |
            | Deal Stage Qualified Rule | Deal Stage Trigger |
        When I send a "GET" request to "/rules/"
        Then the response status code is "200" and contains "1" records
        And the response contains
            | name                      |
            | Deal Stage Qualified Rule |

    Scenario: Admin can retrieve a single rule
        Given I create a new "rule"
            | name                      | trigger_id         |
            | Deal Stage Qualified Rule | Deal Stage Trigger |
        When I request details for "rules" with "name" "Deal Stage Qualified Rule"
        Then the response status code is "200"
        And the response should contain details
            | name                      |
            | Deal Stage Qualified Rule |

    Scenario: Admin can update a rule
        Given I create a new "rule"
            | name                      | trigger_id         |
            | Deal Stage Qualified Rule | Deal Stage Trigger |
        When I update "rule" with "name" "Deal Stage Qualified Rule"
            | evaluation_order |
            | 5                |
        Then the response status code is "200"
        And the "rule" with "name" "Deal Stage Qualified Rule" should have "evaluation_order" "5"

    Scenario: Admin can soft-delete a rule
        Given I create a new "rule"
            | name                      | trigger_id         |
            | Deal Stage Qualified Rule | Deal Stage Trigger |
        When I soft delete "rules" with "name" "Deal Stage Qualified Rule"
        Then the response status code is "204"
        And the "rule" with "name" "Deal Stage Qualified Rule" should have "is_invalid" "True"
        And the "rule" with "name" "Deal Stage Qualified Rule" should not appear in the list

    Scenario: Soft-deleted rule returns 404 on retrieve
        Given I create a new "rule"
            | name                      | trigger_id         |
            | Deal Stage Qualified Rule | Deal Stage Trigger |
        When I soft delete "rules" with "name" "Deal Stage Qualified Rule"
        When I request details for "rules" with "name" "Deal Stage Qualified Rule"
        Then the response status code is "404"

    Scenario: Evaluate rule with passing payload returns true
        Given I create a new "rule"
            | name                      | trigger_id         |
            | Deal Stage Qualified Rule | Deal Stage Trigger |
        When I send a "POST" request to "/rules/{rule.id}/evaluate/" with body
            | field         | value                  |
            | event_payload | {"stage": "qualified"} |
        Then the response status code is "200"
        And the response should contain details
            | result |
            | True   |

    Scenario: Evaluate rule with failing payload returns false
        Given I create a new "rule"
            | name                      | trigger_id         |
            | Deal Stage Qualified Rule | Deal Stage Trigger |
        When I send a "POST" request to "/rules/{rule.id}/evaluate/" with body
            | field         | value                    |
            | event_payload | {"stage": "prospecting"} |
        Then the response status code is "200"
        And the response should contain details
            | result |
            | False  |

    Scenario: Can list multiple rules
        Given I create a new "rule"
            | name     | trigger_id         | evaluation_order |
            | Rule One | Deal Stage Trigger | 1                |
        And I create a new "rule"
            | name     | trigger_id         | evaluation_order |
            | Rule Two | Deal Stage Trigger | 2                |
        When I send a "GET" request to "/rules/"
        Then the response status code is "200" and contains "2" records

    Scenario: Non-admin user cannot access rules
        Given I am "authenticated" as "a regular user"
        When I send a "GET" request to "/rules/"
        Then the response status code is "403"

    Scenario: Unauthenticated user cannot access rules
        Given I am "not authenticated"
        When I send a "GET" request to "/rules/"
        Then the response status code is "403"

    Scenario: Inactive rule is skipped during trigger evaluation
        Given I create a new "rule"
            | name          | trigger_id         | is_active |
            | Inactive Rule | Deal Stage Trigger | False     |
        When I send a "POST" request to "/rules/{rule.id}/evaluate/" with body
            | field         | value                  |
            | event_payload | {"stage": "qualified"} |
        Then the response status code is "200"