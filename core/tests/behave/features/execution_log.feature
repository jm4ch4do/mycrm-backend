@execution_log
Feature: Execution Log API
    As an admin
    I want to inspect execution logs
    So that I can audit workflow runs

    Background:
        Given I am "authenticated" as "a staff user"

    Scenario: Admin can list execution logs
        Given I create a new "trigger"
            | _tid | name                  | event_type         |
            | t1   | Execution Log Trigger | deal.stage_changed |
        And I create a new "workflow"
            | _tid | name                   | trigger     |
            | w1   | Execution Log Workflow | @trigger.t1 |
        And I create a new "event"
            | _tid | event_type         | source_service | entity_type |
            | e1   | deal.stage_changed | core           | Deal        |
        And I create a new "execution_log"
            | _tid | workflow     | event     |
            | l1   | @workflow.w1 | @event.e1 |
        When I send a "GET" request to "/executions/"
        Then the response status code is "200" and contains "1" records
        And the response contains
            | id                |
            | @execution_log.l1 |

    Scenario: Filter execution logs by status
        Given I create a new "trigger"
            | _tid | name                  | event_type         |
            | t1   | Execution Log Trigger | deal.stage_changed |
        And I create a new "workflow"
            | _tid | name                   | trigger     |
            | w1   | Execution Log Workflow | @trigger.t1 |
        And I create a new "event"
            | _tid | event_type         | source_service | entity_type |
            | e1   | deal.stage_changed | core           | Deal        |
        And I create a new "execution_log"
            | _tid | workflow     | event     | status  |
            | l1   | @workflow.w1 | @event.e1 | success |
        And I create a new "execution_log"
            | _tid | workflow     | event     | status |
            | l2   | @workflow.w1 | @event.e1 | failed |
        When I send a "GET" request to "/executions/"
            | field  | operator | value   |
            | status | eq       | success |
        Then the response status code is "200" and contains "1" records
        And every item in the response has "status" "success"

    Scenario: Filter execution logs by workflow
        Given I create a new "trigger"
            | _tid | name                  | event_type         |
            | t1   | Execution Log Trigger | deal.stage_changed |
        And I create a new "workflow"
            | _tid | name                   | trigger     |
            | w1   | Execution Log Workflow | @trigger.t1 |
        And I create a new "event"
            | _tid | event_type         | source_service | entity_type |
            | e1   | deal.stage_changed | core           | Deal        |
        And I create a new "execution_log"
            | _tid | workflow     | event     |
            | l1   | @workflow.w1 | @event.e1 |
        When I send a "GET" request to "/executions/"
            | field    | operator | value        |
            | workflow | eq       | @workflow.w1 |
        Then the response status code is "200" and contains "1" records
        And every item in the response has "workflow.id" "@workflow.w1"

    Scenario: Admin can retrieve a single execution log
        Given I create a new "trigger"
            | _tid | name                  | event_type         |
            | t1   | Execution Log Trigger | deal.stage_changed |
        And I create a new "workflow"
            | _tid | name                   | trigger     |
            | w1   | Execution Log Workflow | @trigger.t1 |
        And I create a new "event"
            | _tid | event_type         | source_service | entity_type |
            | e1   | deal.stage_changed | core           | Deal        |
        And I create a new "execution_log"
            | _tid | workflow     | event     |
            | l1   | @workflow.w1 | @event.e1 |
        When I send a "GET" request to "/executions/@execution_log.l1/"
        Then the response status code is "200"
        And the response contains field "logs"

    Scenario: Retrieve unknown execution log returns 404
        When I send a "GET" request to "/executions/00000000-0000-0000-0000-000000000000/"
        Then the response status code is "404"

    Scenario: POST to executions is not allowed
        When I send a "POST" request to "/executions/" with body
            | field    | value |
            | any_data | true  |
        Then the response status code is "405"

    Scenario: DELETE execution log is not allowed
        Given I create a new "trigger"
            | _tid | name                  | event_type         |
            | t1   | Execution Log Trigger | deal.stage_changed |
        And I create a new "workflow"
            | _tid | name                   | trigger     |
            | w1   | Execution Log Workflow | @trigger.t1 |
        And I create a new "event"
            | _tid | event_type         | source_service | entity_type |
            | e1   | deal.stage_changed | core           | Deal        |
        And I create a new "execution_log"
            | _tid | workflow     | event     |
            | l1   | @workflow.w1 | @event.e1 |
        When I send a "DELETE" request to "/executions/@execution_log.l1/"
        Then the response status code is "405"

    Scenario: Execution logs are ordered newest first
        Given I create a new "trigger"
            | _tid | name                  | event_type         |
            | t1   | Execution Log Trigger | deal.stage_changed |
        And I create a new "workflow"
            | _tid | name                   | trigger     |
            | w1   | Execution Log Workflow | @trigger.t1 |
        And I create a new "event"
            | _tid | event_type         | source_service | entity_type |
            | e1   | deal.stage_changed | core           | Deal        |
        And I create a new "execution_log"
            | _tid | workflow     | event     | started_at                |
            | l1   | @workflow.w1 | @event.e1 | 2026-06-12T10:00:00+00:00 |
        And I create a new "execution_log"
            | _tid | workflow     | event     | started_at                |
            | l2   | @workflow.w1 | @event.e1 | 2026-06-12T10:05:00+00:00 |
        When I send a "GET" request to "/executions/"
        Then the response status code is "200"
        And the response is ordered by "started_at" descending

    Scenario: Executing a workflow creates a pending execution log
        Given I create a new "trigger"
            | _tid | name                      | event_type         |
            | t1   | Execution Pending Trigger | deal.stage_changed |
        And I create a new "workflow"
            | _tid | name                       | trigger     |
            | w1   | Execution Pending Workflow | @trigger.t1 |
        And I create a new "action"
            | _tid | name                | action_type | parameters_json                         |
            | a1   | Create Pending Task | create_task | {"title": "Follow up on qualification"} |
        And I create a new "event"
            | _tid | event_type         | source_service | entity_type |
            | e1   | deal.stage_changed | core           | Deal        |
        When I send a "POST" request to "/workflows/@workflow.w1/steps/" with body
            | field      | value      |
            | action_id  | @action.a1 |
            | step_order | 1          |
        Then the response status code is "201"
        When I execute workflow "Execution Pending Workflow" for event_type "deal.stage_changed"
        Then an execution log exists for workflow "Execution Pending Workflow" with status "pending"

    Scenario: Successful workflow execution finalizes log as success
        Given I create a new "trigger"
            | _tid | name                      | event_type         |
            | t1   | Execution Success Trigger | deal.stage_changed |
        And I create a new "workflow"
            | _tid | name                       | trigger     |
            | w1   | Execution Success Workflow | @trigger.t1 |
        And I create a new "action"
            | _tid | name                | action_type | parameters_json                         |
            | a1   | Create Success Task | create_task | {"title": "Follow up on qualification"} |
        And I create a new "event"
            | _tid | event_type         | source_service | entity_type |
            | e1   | deal.stage_changed | core           | Deal        |
        When I send a "POST" request to "/workflows/@workflow.w1/steps/" with body
            | field      | value      |
            | action_id  | @action.a1 |
            | step_order | 1          |
        Then the response status code is "201"
        When I execute workflow "Execution Success Workflow" for event_type "deal.stage_changed"
        And the Celery task processes the workflow execution
        Then the execution result status is "success"
        And the logs array contains one step entry

    Scenario: Failed step finalizes execution log as failed
        Given I create a new "trigger"
            | _tid | name                      | event_type         |
            | t1   | Execution Failure Trigger | deal.stage_changed |
        And I create a new "workflow"
            | _tid | name                       | trigger     |
            | w1   | Execution Failure Workflow | @trigger.t1 |
        And I create a new "action"
            | _tid | name          | action_type | parameters_json |
            | a1   | Broken Action | add_note    | {"body": ""}    |
        And I create a new "event"
            | _tid | event_type         | source_service | entity_type |
            | e1   | deal.stage_changed | core           | Deal        |
        When I send a "POST" request to "/workflows/@workflow.w1/steps/" with body
            | field      | value      |
            | action_id  | @action.a1 |
            | step_order | 1          |
        Then the response status code is "201"
        When I execute workflow "Execution Failure Workflow" for event_type "deal.stage_changed"
        And the Celery task processes the workflow execution
        Then the execution log status is "failed"
        And the step log entry contains an error message

    Scenario: Non-admin user cannot list execution logs
        Given I am "authenticated" as "a regular user"
        When I send a "GET" request to "/executions/"
        Then the response status code is "403"

    Scenario: Unauthenticated user cannot access execution logs
        Given I am "not authenticated"
        When I send a "GET" request to "/executions/"
        Then the response status code is "401"
