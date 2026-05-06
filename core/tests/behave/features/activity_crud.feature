Feature: Activity CRUD Operations
    As a CRM user
    I want to manage activities through the API
    So that I can track engagement with accounts, contacts, and deals

    Background:
        Given I create "accounts" through the API
            | name      | status |
            | Acme Corp | active |

    Scenario: Create and list activities
        Given I create "activities" through the API
            | title          | type    | account_id |
            | Follow up call | call    | Acme Corp  |
            | Send proposal  | task    | Acme Corp  |
            | Intro meeting  | meeting | Acme Corp  |
        When I send a "GET" request to "/activities/"
        Then the response status code is "200" and contains "3" records
        And the response contains
            | title          | type    |
            | Follow up call | call    |
            | Send proposal  | task    |
            | Intro meeting  | meeting |

    Scenario: Filter activities by type
        Given I create a new "activity"
            | title       | type    | account_id |
            | Task One    | task    | Acme Corp  |
            | Meeting One | meeting | Acme Corp  |
            | Task Two    | task    | Acme Corp  |
        When I send a "GET" request to "/activities/"
            | field | operator | value |
            | type  | eq       | task  |
        Then the response status code is "200" and contains "2" records

    Scenario: Filter activities by status
        Given I create a new "activity"
            | title        | type | status    | account_id |
            | Planned Task | task | planned   | Acme Corp  |
            | Done Task    | task | completed | Acme Corp  |
        When I send a "GET" request to "/activities/"
            | field  | operator | value     |
            | status | eq       | completed |
        Then the response status code is "200" and contains "1" records
        And the first "activity" should have title "Done Task"

    Scenario: Filter activities by account
        Given I create "accounts" through the API
            | name           | status |
            | Tech Solutions | active |
        And I create a new "activity"
            | title     | type | account_id     |
            | Acme Task | task | Acme Corp      |
            | Acme Note | note | Acme Corp      |
            | Tech Task | task | Tech Solutions |
        When I request details for "activities" by "account_id" "Acme Corp"
        Then the response status code is "200" and contains "2" records
        And the response should contain details
            | title     | type |
            | Acme Note | note |
            | Acme Task | task |

    Scenario: Update activity status
        Given I create a new "activity"
            | title          | type | account_id |
            | Update Me Task | task | Acme Corp  |
        When I update "activities" with "title" "Update Me Task"
            | status    |
            | completed |
        Then the "activity" with "title" "Update Me Task" should have "status" "completed"

    Scenario: Retrieve single activity details
        Given I create a new "activity"
            | title        | type    | status  | account_id |
            | Detail Check | meeting | planned | Acme Corp  |
        When I request details for "activity" with "title" "Detail Check"
        Then the response status code is "200"
        And the response should contain details
            | title        | type    | status  |
            | Detail Check | meeting | planned |

    Scenario: Soft delete activity
        Given I create a new "activity"
            | title     | type | account_id |
            | Delete Me | task | Acme Corp  |
        When I soft delete "activities" with "title" "Delete Me"
        Then the "activity" with "title" "Delete Me" should not appear in the list

    Scenario: Create activity without entity reference fails
        When I send a "POST" request to "/activities/" with body
            | field | value       |
            | type  | task        |
            | title | Orphan Task |
        Then the response status code is "400"

    Scenario: Directly updated activity status is reflected in filter
        Given I create a new "activity"
            | title          | type | account_id |
            | Status Changer | task | Acme Corp  |
        And I update "activities" with "title" "Status Changer"
            | status    |
            | completed |
        When I send a "GET" request to "/activities/"
            | field  | operator | value     |
            | status | eq       | completed |
        Then the response status code is "200" and contains "1" records

    Scenario: Directly soft-deleted activities are excluded from list
        Given I create a new "activity"
            | title      | type | account_id |
            | To Archive | task | Acme Corp  |
        And I create a new "activity"
            | title  | type | account_id |
            | Active | task | Acme Corp  |
        And I delete "activities" with "title" "To Archive" using "soft delete"
        When I send a "GET" request to "/activities/"
        Then the response status code is "200" and contains "1" records

    Scenario: Directly hard-deleted activities are excluded from list
        Given I create a new "activity"
            | title       | type | account_id |
            | Old Meeting | task | Acme Corp  |
        And I create a new "activity"
            | title    | type | account_id |
            | Survivor | task | Acme Corp  |
        And I delete "activities" with "title" "Old Meeting"
        When I send a "GET" request to "/activities/"
        Then the response status code is "200" and contains "1" records

