@action
Feature: Action API
    Background:
        Given I am "authenticated" as "a staff user"
        And I create a new "account"
            | name      |
            | Acme Corp |
        And I create a new "deal"
            | name            | account_id |
            | Enterprise Deal | Acme Corp  |

    Scenario: Admin can create, list, retrieve, update and soft-delete an action
        Given I create "actions" through the API
            | name                      | action_type |
            | Create Qualification Task | create_task |
        Then the response status code is "201"
        And the response contains field "name"
        And the response contains field "action_type"
        When I send a "GET" request to "/actions/"
        Then the response status code is "200" and contains "1" records
        And the response contains
            | name                      |
            | Create Qualification Task |
        When I request details for "actions" with "name" "Create Qualification Task"
        Then the response status code is "200"
        And the response should contain details
            | name                      |
            | Create Qualification Task |
        When I update "action" with "name" "Create Qualification Task"
            | name           |
            | Updated Action |
        Then the response status code is "200"
        And the "action" with "name" "Updated Action" should have "name" "Updated Action"
        When I soft delete "actions" with "name" "Updated Action"
        Then the response status code is "204"
        And the "action" with "name" "Updated Action" should have "is_invalid" "True"
        And the "action" with "name" "Updated Action" should not appear in the list

    Scenario: Soft-deleted action returns 404 on retrieve
        Given I create a new "action"
            | name                      |
            | Create Qualification Task |
        When I soft delete "actions" with "name" "Create Qualification Task"
        When I request details for "actions" with "name" "Create Qualification Task"
        Then the response status code is "404"

    Scenario: Dry run with valid parameters returns valid true
        Given I create a new "action"
            | name                      | action_type |
            | Create Qualification Task | create_task |
        And I store the "action" with "name" "Create Qualification Task" as "action"
        When I send a "POST" request to "/actions/{action.id}/dry_run/" with body
            | field         | value                  |
            | event_payload | {"stage": "qualified"} |
        Then the response status code is "200"
        And the response should contain details
            | valid |
            | True  |

    Scenario: Filter actions by action_type
        Given I create a new "action"
            | name        | action_type |
            | Task Action | create_task |
        And I create a new "action"
            | name        | action_type |
            | Note Action | add_note    |
        When I send a "GET" request to "/actions/?action_type=create_task"
        Then the response status code is "200" and contains "1" records
        And the response contains
            | name        | action_type |
            | Task Action | create_task |

    Scenario: Executing an action returns a success result
        Given I create a new "action"
            | name                      | action_type |
            | Create Qualification Task | create_task |
        When the automation engine executes action "Create Qualification Task" against an event
        Then the execution result status is "success"

    Scenario: Executing a failing action returns a failed result dict
        Given I create a new "action"
            | name          | action_type | parameters_json           |
            | Broken Action | create_task | {"unexpected_field": 999} |
        When the automation engine executes action "Broken Action" against an event
        Then the execution result status is "failed"
        And no exception is raised

    Scenario: Non-admin and unauthenticated users cannot access actions
        Given I am "authenticated" as "a regular user"
        When I send a "GET" request to "/actions/"
        Then the response status code is "403"
        Given I am "not authenticated"
        When I send a "GET" request to "/actions/"
        Then the response status code is "401"
