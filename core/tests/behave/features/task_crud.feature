Feature: Task CRUD Operations
    As a CRM user
    I want to manage tasks through the API
    So that I can track to-dos linked to accounts, contacts, and deals

    Background:
        Given I create "accounts" through the API
            | name      | status |
            | Acme Corp | active |

    Scenario: Create and list tasks
        Given I create "tasks" through the API
            | title          | account_id |
            | Follow up call | Acme Corp  |
            | Send proposal  | Acme Corp  |
            | Intro meeting  | Acme Corp  |
        When I send a "GET" request to "/tasks/"
        Then the response status code is "200" and contains "3" records
        And the response contains
            | title          |
            | Follow up call |
            | Send proposal  |
            | Intro meeting  |

    Scenario: Filter tasks by state
        Given I create a new "task"
            | title          | account_id | state     |
            | Open task      | Acme Corp  | open      |
            | Completed task | Acme Corp  | completed |
        When I send a "GET" request to "/tasks/"
            | field | operator | value |
            | state | eq       | open  |
        Then the response status code is "200" and contains "1" records
        And the first "task" should have title "Open task"

    Scenario: Filter tasks by priority
        Given I create a new "task"
            | title       | account_id | priority |
            | High prio   | Acme Corp  | high     |
            | Low prio    | Acme Corp  | low      |
            | Medium prio | Acme Corp  | medium   |
        When I send a "GET" request to "/tasks/"
            | field    | operator | value |
            | priority | eq       | high  |
        Then the response status code is "200" and contains "1" records
        And the first "task" should have title "High prio"

    Scenario: Filter tasks by category
        Given I create a new "task"
            | title      | account_id | category  |
            | Admin task | Acme Corp  | admin     |
            | Follow up  | Acme Corp  | follow_up |
        When I send a "GET" request to "/tasks/"
            | field    | operator | value |
            | category | eq       | admin |
        Then the response status code is "200" and contains "1" records
        And the first "task" should have title "Admin task"

    Scenario: Retrieve single task details
        Given I create a new "task"
            | title        | account_id | priority | category |
            | Detail Check | Acme Corp  | high     | admin    |
        When I request details for "tasks" with "activity__title" "Detail Check"
        Then the response status code is "200"
        And the response should contain details
            | title        | priority | category | state |
            | Detail Check | high     | admin    | open  |

    Scenario: Update task fields
        Given I create a new "task"
            | title     | account_id | priority |
            | Update Me | Acme Corp  | low      |
        When I update "tasks" with "activity__title" "Update Me"
            | priority | category |
            | high     | admin    |
        Then the "task" with "activity__title" "Update Me" should have "priority" "high"

    Scenario: Update task title
        Given I create a new "task"
            | title     | account_id |
            | Old Title | Acme Corp  |
        When I update "tasks" with "activity__title" "Old Title"
            | title     |
            | New Title |
        Then the response status code is "200"
        And the response should contain details
            | title     |
            | New Title |

    Scenario: Complete a task
        Given I create a new "task"
            | title   | account_id |
            | My Task | Acme Corp  |
        When I send a "POST" request to "/tasks/{context.task.id}/complete/"
        Then the response status code is "200"
        And the response should contain details
            | state     | activity_status |
            | completed | completed       |

    Scenario: Soft delete task
        Given I create a new "task"
            | title     | account_id |
            | Delete Me | Acme Corp  |
        When I soft delete "tasks" with "activity__title" "Delete Me"
        Then the "task" with "title" "Delete Me" should not appear in the list

    Scenario: Create task without entity reference fails
        When I send a "POST" request to "/tasks/" with body
            | field | value       |
            | title | Orphan Task |
        Then the response status code is "400"

    Scenario: Directly soft-deleted tasks are excluded from list
        Given I create a new "task"
            | title      | account_id |
            | To Archive | Acme Corp  |
        And I create a new "task"
            | title  | account_id |
            | Active | Acme Corp  |
        And I delete "activities" with "title" "To Archive" using "soft delete"
        When I send a "GET" request to "/tasks/"
        Then the response status code is "200" and contains "1" records

    Scenario: Completed state is reflected in filter
        Given I create a new "task"
            | title         | account_id |
            | State Changer | Acme Corp  |
        And I send a "POST" request to "/tasks/{context.task.id}/complete/"
        When I send a "GET" request to "/tasks/"
            | field | operator | value     |
            | state | eq       | completed |
        Then the response status code is "200" and contains "1" records
