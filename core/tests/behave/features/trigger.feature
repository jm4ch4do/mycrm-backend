@trigger
Feature: Trigger API
    As a CRM admin
    I want to manage automation triggers
    So that event matching rules can be configured safely

    Scenario: Authenticated permissions are enforced
        Given I am "authenticated" as "a staff user"
        And I create a new "trigger"
            | name             | event_type      |
            | Retrieve Trigger | contact.created |
        When I send a "POST" request to "/triggers/" with body
            | field      | value        |
            | name       | New Trigger  |
            | event_type | deal.updated |
        Then the response status code is "201"
        And the "trigger" with "name" "New Trigger" should have "event_type" "deal.updated"
        Given I am "authenticated" as "a regular user"
        When I send a "GET" request to "/triggers/"
        Then the response status code is "200" and contains "2" records
        When I send a "GET" request to "/triggers/{trigger.id}/"
        Then the response status code is "200"
        And the response should contain details
            | name             | event_type      |
            | Retrieve Trigger | contact.created |
        When I send a "POST" request to "/triggers/" with body
            | field      | value           |
            | name       | Blocked Trigger |
            | event_type | deal.updated    |
        Then the response status code is "403"
        When I send a "POST" request to "/triggers/{trigger.id}/activate/"
        Then the response status code is "403"

    Scenario: Unauthenticated access is denied
        Given I am "authenticated" as "a staff user"
        And I create a new "trigger"
            | name          | event_type   | is_active |
            | PublicTrigger | deal.updated | False     |
        And I am "not authenticated"
        When I send a "GET" request to "/triggers/"
        Then the response status code is "403"
        When I send a "GET" request to "/triggers/{trigger.id}/"
        Then the response status code is "403"
        When I send a "POST" request to "/triggers/" with body
            | field      | value                 |
            | name       | Unauth Create Attempt |
            | event_type | deal.updated          |
        Then the response status code is "403"
        When I send a "POST" request to "/triggers/{trigger.id}/activate/"
        Then the response status code is "403"

    Scenario: Staff user can deactivate and activate a trigger
        Given I am "authenticated" as "a staff user"
        And I create a new "trigger"
            | name           | event_type   | is_active |
            | Toggle Trigger | deal.updated | True      |
        When I send a "POST" request to "/triggers/{trigger.id}/deactivate/"
        Then the response status code is "200"
        And the response should contain details
            | is_active |
            | False     |
        When I send a "POST" request to "/triggers/{trigger.id}/activate/"
        Then the response status code is "200"
        And the response should contain details
            | is_active |
            | True      |

    Scenario: Deleting a trigger performs soft delete and hides it from list
        Given I am "authenticated" as "a staff user"
        And I create a new "trigger"
            | name                | event_type   |
            | Soft Delete Trigger | deal.updated |
        When I soft delete "triggers" with "name" "Soft Delete Trigger"
        Then the response status code is "204"
        And the "trigger" with "name" "Soft Delete Trigger" should have "is_invalid" "True"
        And the "trigger" with "name" "Soft Delete Trigger" should not appear in the list
