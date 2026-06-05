Feature: Call CRUD Operations
    As a CRM user
    I want to manage calls through the API
    So that I can track phone calls linked to accounts, contacts, and deals

    Background:
        Given I create "accounts" through the API
            | name      | status |
            | Acme Corp | active |

    Scenario: Create and list calls
        Given I create "calls" through the API
            | title          | account_id | direction |
            | Morning Call   | Acme Corp  | outbound  |
            | Follow-up Call | Acme Corp  | inbound   |
            | Cold Call      | Acme Corp  | outbound  |
        When I send a "GET" request to "/calls/"
        Then the response status code is "200" and contains "3" records
        And the response contains
            | title          |
            | Morning Call   |
            | Follow-up Call |
            | Cold Call      |

    Scenario: Filter by direction
        Given I create a new "call"
            | title         | account_id | direction |
            | Inbound Call  | Acme Corp  | inbound   |
            | Outbound Call | Acme Corp  | outbound  |
        When I send a "GET" request to "/calls/"
            | field     | operator | value   |
            | direction | eq       | inbound |
        Then the response status code is "200" and contains "1" records
        And the response should contain details
            | title        |
            | Inbound Call |

    Scenario: Filter by outcome
        Given I create a new "call"
            | title          | account_id | direction | outcome   |
            | Connected Call | Acme Corp  | outbound  | connected |
            | No Answer Call | Acme Corp  | outbound  |           |
        When I send a "GET" request to "/calls/"
            | field   | operator | value     |
            | outcome | eq       | connected |
        Then the response status code is "200" and contains "1" records
        And the response should contain details
            | title          |
            | Connected Call |

    Scenario: Retrieve single call details
        Given I create a new "call"
            | title        | account_id | direction | phone_number |
            | Detail Check | Acme Corp  | outbound  | +1-555-0100  |
        When I request details for "calls" with "activity__title" "Detail Check"
        Then the response status code is "200"
        And the response should contain details
            | title        | direction | phone_number | type |
            | Detail Check | outbound  | +1-555-0100  | call |

    Scenario: Update call fields
        Given I create a new "call"
            | title     | account_id | direction | phone_number |
            | Update Me | Acme Corp  | outbound  | +1-555-0000  |
        When I update "calls" with "activity__title" "Update Me"
            | phone_number |
            | +1-555-9999  |
        Then the "call" with "activity__title" "Update Me" should have "phone_number" "+1-555-9999"

    Scenario: Complete a call
        Given I create a new "call"
            | title   | account_id | direction |
            | My Call | Acme Corp  | outbound  |
        When I send a "POST" request to "/calls/{context.call.id}/complete_call/" with body
            | field            | value      |
            | outcome          | connected  |
            | duration_seconds | 300        |
            | summary          | Great call |
        Then the response status code is "200"
        And the response should contain details
            | outcome   | activity_status | duration_seconds |
            | connected | completed       | 300              |

    Scenario: Complete call requires outcome
        Given I create a new "call"
            | title           | account_id | direction |
            | Incomplete Call | Acme Corp  | outbound  |
        When I send a "POST" request to "/calls/{context.call.id}/complete_call/" with body
            | field   | value |
            | summary | test  |
        Then the response status code is "400"

    Scenario: Completed call rejects update
        Given I create a new "call"
            | title     | account_id | direction |
            | Done Call | Acme Corp  | outbound  |
        And I send a "POST" request to "/calls/{context.call.id}/complete_call/" with body
            | field   | value     |
            | outcome | connected |
        When I update "calls" with "activity__title" "Done Call"
            | title       |
            | Should Fail |
        Then the response status code is "400"

    Scenario: Soft delete call
        Given I create a new "call"
            | title     | account_id | direction |
            | Delete Me | Acme Corp  | outbound  |
        When I soft delete "calls" with "activity__title" "Delete Me"
        Then the "call" with "title" "Delete Me" should not appear in the list

    Scenario: Directly soft-deleted calls are excluded from list
        Given I create a new "call"
            | title      | account_id | direction |
            | To Archive | Acme Corp  | outbound  |
        And I create a new "call"
            | title  | account_id | direction |
            | Active | Acme Corp  | inbound   |
        And I delete "activities" with "title" "To Archive" using "soft delete"
        When I send a "GET" request to "/calls/"
        Then the response status code is "200" and contains "1" records

    Scenario: Other user cannot modify call
        Given I create a new "call"
            | title      | account_id | direction |
            | Owner Call | Acme Corp  | outbound  |
        And I am "authenticated" as "a regular user"
        When I update "calls" with "activity__title" "Owner Call"
            | title  |
            | Hacked |
        Then the response status code is "403"
