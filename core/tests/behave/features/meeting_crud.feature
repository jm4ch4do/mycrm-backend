Feature: Meeting CRUD Operations
    As a CRM user
    I want to manage meetings through the API
    So that I can track calls and meetings linked to accounts, contacts, and deals

    Background:
        Given I create "accounts" through the API
            | name      | status |
            | Acme Corp | active |

    Scenario: Create and list meetings
        Given I create "meetings" through the API
            | title          | account_id |
            | Kickoff Call   | Acme Corp  |
            | Discovery Call | Acme Corp  |
            | Renewal Review | Acme Corp  |
        When I send a "GET" request to "/meetings/"
        Then the response status code is "200" and contains "3" records
        And the response contains
            | title          |
            | Kickoff Call   |
            | Discovery Call |
            | Renewal Review |

    Scenario: Filter meetings by outcome
        Given I create a new "meeting"
            | title        | account_id | outcome   |
            | Done Meeting | Acme Corp  | completed |
            | Open Meeting | Acme Corp  |           |
        When I send a "GET" request to "/meetings/"
            | field   | operator | value     |
            | outcome | eq       | completed |
        Then the response status code is "200" and contains "1" records
        And the first "meeting" should have title "Done Meeting"

    Scenario: Retrieve single meeting details
        Given I create a new "meeting"
            | title       | account_id | location |
            | Detail Test | Acme Corp  | Room A   |
        When I request details for "meetings" with "activity__title" "Detail Test"
        Then the response status code is "200"
        And the response should contain details
            | title       | location | type    |
            | Detail Test | Room A   | meeting |

    Scenario: Update meeting fields
        Given I create a new "meeting"
            | title     | account_id | location |
            | Update Me | Acme Corp  | Room A   |
        When I update "meetings" with "activity__title" "Update Me"
            | location |
            | Room B   |
        Then the "meeting" with "activity__title" "Update Me" should have "location" "Room B"

    Scenario: Complete a meeting
        Given I create a new "meeting"
            | title      | account_id |
            | My Meeting | Acme Corp  |
        When I send a "POST" request to "/meetings/{context.meeting.id}/complete/" with body
            | field   | value     |
            | outcome | completed |
        Then the response status code is "200"
        And the response should contain details
            | outcome   | activity_status |
            | completed | completed       |

    Scenario: Soft delete meeting
        Given I create a new "meeting"
            | title     | account_id |
            | Delete Me | Acme Corp  |
        When I soft delete "meetings" with "activity__title" "Delete Me"
        Then the "meeting" with "title" "Delete Me" should not appear in the list

    Scenario: Directly soft-deleted meetings are excluded from list
        Given I create a new "meeting"
            | title      | account_id |
            | To Archive | Acme Corp  |
        And I create a new "meeting"
            | title  | account_id |
            | Active | Acme Corp  |
        And I delete "activities" with "title" "To Archive" using "soft delete"
        When I send a "GET" request to "/meetings/"
        Then the response status code is "200" and contains "1" records
