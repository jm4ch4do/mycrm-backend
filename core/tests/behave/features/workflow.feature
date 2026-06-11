@workflow
Feature: Workflow API
    Background:
        Given I am "authenticated" as "a staff user"
        And I create a new "trigger"
            | name               | event_type         |
            | Deal Stage Trigger | deal.stage_changed |

    Scenario: Admin can create and list workflows
        Given I create "workflows" through the API
            | name                  | trigger_id         |
            | Qualify Deal Workflow | Deal Stage Trigger |
        Then the response status code is "201"
        And the response contains field "name"
        And the response contains field "trigger"
        When I send a "GET" request to "/workflows/"
        Then the response status code is "200" and contains "1" records
        And the response contains
            | name                  |
            | Qualify Deal Workflow |

    Scenario: Admin can activate, deactivate, and soft-delete a workflow
        Given I create a new "workflow"
            | name               | trigger_id         | is_active |
            | Lifecycle Workflow | Deal Stage Trigger | False     |
        And I store the "workflow" with "name" "Lifecycle Workflow" as "workflow"
        When I send a "POST" request to "/workflows/{workflow.id}/activate/"
        Then the response status code is "200"
        And the "workflow" with "name" "Lifecycle Workflow" should have "is_active" "True"
        When I send a "POST" request to "/workflows/{workflow.id}/deactivate/"
        Then the response status code is "200"
        And the "workflow" with "name" "Lifecycle Workflow" should have "is_active" "False"
        When I soft delete "workflows" with "name" "Lifecycle Workflow"
        Then the response status code is "204"
        And the "workflow" with "name" "Lifecycle Workflow" should have "is_invalid" "True"
        And the "workflow" with "name" "Lifecycle Workflow" should not appear in the list

    Scenario: Admin can add a step to a workflow
        Given I create a new "workflow"
            | name                  | trigger_id         |
            | Qualify Deal Workflow | Deal Stage Trigger |
        And I create a new "action"
            | name       |
            | Send Email |
        And I store the "workflow" with "name" "Qualify Deal Workflow" as "workflow"
        When I send a "POST" request to "/workflows/{workflow.id}/steps/" with body
            | field      | value       |
            | action_id  | {action.id} |
            | step_order | 1           |
        Then the response status code is "201"
        And the "workflow" with "name" "Qualify Deal Workflow" has "1" related "workflow_steps"

    Scenario: Duplicate step_order returns 400
        Given I create a new "workflow"
            | name                  | trigger_id         |
            | Qualify Deal Workflow | Deal Stage Trigger |
        And I create a new "action"
            | name       |
            | Send Email |
        And I store the "workflow" with "name" "Qualify Deal Workflow" as "workflow"
        When I send a "POST" request to "/workflows/{workflow.id}/steps/" with body
            | field      | value       |
            | action_id  | {action.id} |
            | step_order | 1           |
        Then the response status code is "201"
        When I send a "POST" request to "/workflows/{workflow.id}/steps/" with body
            | field      | value       |
            | action_id  | {action.id} |
            | step_order | 1           |
        Then the response status code is "400"

    Scenario: Admin can remove a step from a workflow
        Given I create a new "workflow"
            | name                  | trigger_id         |
            | Qualify Deal Workflow | Deal Stage Trigger |
        And I create a new "action"
            | name       |
            | Send Email |
        And I store the "workflow" with "name" "Qualify Deal Workflow" as "workflow"
        When I send a "POST" request to "/workflows/{workflow.id}/steps/" with body
            | field      | value       |
            | action_id  | {action.id} |
            | step_order | 1           |
        Then the response status code is "201"
        When I send a "DELETE" request to "/workflows/{workflow.id}/steps/1/"
        Then the response status code is "204"

    Scenario: Executing a workflow creates an ExecutionLog
        Given I create a new "workflow"
            | name                    | trigger_id         | is_active |
            | Executable Workflow One | Deal Stage Trigger | True      |
        And I create a new "action"
            | name       |
            | Send Email |
        And I store the "workflow" with "name" "Executable Workflow One" as "workflow"
        When I send a "POST" request to "/workflows/{workflow.id}/steps/" with body
            | field      | value       |
            | action_id  | {action.id} |
            | step_order | 1           |
        Then the response status code is "201"
        When I execute workflow "Executable Workflow One" for event_type "deal.stage_changed"
        Then an execution log exists for workflow "Executable Workflow One" with status "pending"

    Scenario: Inactive workflow is skipped by execution engine
        Given I create a new "workflow"
            | name                    | trigger_id         | is_active |
            | Executable Workflow Two | Deal Stage Trigger | False     |
        When I execute workflow "Executable Workflow Two" for event_type "deal.stage_changed"
        Then the captured exception is "WorkflowInactiveError"

    Scenario: Non-admin user cannot access workflows
        Given I am "authenticated" as "a regular user"
        When I send a "GET" request to "/workflows/"
        Then the response status code is "403"

    Scenario: Unauthenticated user cannot access workflows
        Given I am "not authenticated"
        When I send a "GET" request to "/workflows/"
        Then the response status code is "401"
